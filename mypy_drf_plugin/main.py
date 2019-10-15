import importlib
from functools import partial
from typing import Callable, Dict, Optional, TYPE_CHECKING

from mypy.nodes import MDEF, SymbolTableNode, TypeInfo, Var, Decorator, FuncDef, Block, Argument
from mypy.options import Options
from mypy.plugin import ClassDefContext, Plugin
from mypy.types import Instance
from mypy.types import Type as MypyType
from mypy.types import TypedDictType, CallableType, AnyType
from mypy_django_plugin import main as mypy_django_main
from mypy_django_plugin.django.context import DjangoContext
from mypy_django_plugin.lib.helpers import get_private_descriptor_type

from mypy_drf_plugin.lib import fullnames, helpers
from mypy_drf_plugin.transformers import serializers

if TYPE_CHECKING:
    import mypy.plugin


def transform_serializer_class(ctx: ClassDefContext) -> None:
    sym = ctx.api.lookup_fully_qualified_or_none(fullnames.BASE_SERIALIZER_FULLNAME)
    if sym is not None and isinstance(sym.node, TypeInfo):
        helpers.get_drf_metadata(sym.node)["serializer_bases"][ctx.cls.fullname] = 1

    serializers.make_meta_nested_class_inherit_from_any(ctx)


def redefine_and_typecheck_serializer_fields(ctx: ClassDefContext, django_context: DjangoContext) -> MypyType:
    module_path, klass = ctx.cls.fullname.rsplit(".", 1)
    module = importlib.import_module(module_path)
    try:
        ser = getattr(module, klass)
    except AttributeError:
        return
    from rest_framework.serializers import ModelSerializer, ListSerializer

    if not (issubclass(ser, ModelSerializer) and hasattr(ser, "Meta")):
        return

    def ninit(self):
        ModelSerializer.__init__(self, instance=None)

    methods = {"__init__": ninit, "Meta": ser.Meta}
    FakeSerializer = type("FakeSerializer", (ser,), methods)
    fields = FakeSerializer().fields
    field_types = {}
    data_types = {}
    for name, field in fields.items():
        try:
            fmodule = ctx.api.modules[field.__module__]
            ftype = fmodule.names[field.__class__.__name__]
        except KeyError:
            field_types[name] = AnyType(1)
            data_types[field.source] = AnyType(1)
        else:
            field_types[name] = Instance(ftype.node, [])
            data_types[field.source] = get_private_descriptor_type(
                ftype.node, "_pyi_field_actual_type", is_nullable=getattr(field, "allow_null", False)
            )
    target_module = ctx.api.modules[module_path]
    target_class_name = ser.__name__
    if "fields" not in ctx.cls.info.names:
        add_property_returning_typed_dict(ctx, field_types, "fields", target_module, target_class_name)
    add_property_returning_typed_dict(
        ctx,
        data_types,
        "data",
        target_module,
        target_class_name,
        is_list=isinstance(ser, ListSerializer),
        is_data_defined="data" in ctx.cls.info.names,
    )


def add_property_returning_typed_dict(
    ctx: ClassDefContext,
    typed_dict_keys: dict,
    property_name: str,
    target_module,
    target_class_name: str,
    is_list: bool = False,
    is_data_defined: bool = False,
) -> None:
    object_type = ctx.api.named_type_or_none("typing._TypedDict", [])

    ret_type = TypedDictType(typed_dict_keys, required_keys=set(), fallback=object_type)
    if is_list:
        ret_type = ctx.api.named_type_or_none("typing.List", [ret_type])

    ser_type_info = ctx.cls.info
    var = Var(property_name)
    var.info = ser_type_info
    var.is_initialized_in_class = True
    var.is_property = True

    arg_var = Var("self", None)
    arg = Argument(arg_var, type_annotation=None, initializer=None, kind=0)
    func = FuncDef(name=property_name, arguments=[arg], body=Block([]))
    func.info = ser_type_info
    func._fullname = ser_type_info.fullname() + "." + var.name()
    func.is_property = True
    func.is_decorated = True
    func.type = CallableType(
        arg_types=[AnyType(1)], arg_kinds=[0], arg_names=["self"], ret_type=ret_type, fallback=object_type
    )
    dec = Decorator(func=func, decorators=[], var=var)

    if not is_data_defined:
        ctx.cls.info.names[property_name] = SymbolTableNode(MDEF, dec, plugin_generated=True)
    if property_name == "data":
        ctx.cls.info.names["_pyi_data"] = ctx.cls.info.names[property_name]


def handle_serializer_class(ctx: ClassDefContext, django_context: DjangoContext, base_process: bool) -> MypyType:
    if base_process:
        transform_serializer_class(ctx)
    if not ctx.api.final_iteration:
        ctx.api.defer()
        return
    redefine_and_typecheck_serializer_fields(ctx, django_context)


def handle_return_type(ctx: "mypy.plugin.AnalyzeTypeContext", django_context: DjangoContext) -> MypyType:
    func = ctx.api.visit_unbound_type(ctx.type.args[0])
    if "_pyi_data" in func.type.names:
        func = func.type.names["_pyi_data"]
        if func.type:
            return func.type.ret_type
    return ctx.api.named_type("typing.Mapping", [])


class NewSemanalDRFPlugin(Plugin):
    def __init__(self, options: Options) -> None:
        super().__init__(options)

        django_settings_module = mypy_django_main.extract_django_settings_module(options.config_file)
        self.django_context = DjangoContext(django_settings_module)

    def _get_currently_defined_serializers(self) -> Dict[str, int]:
        base_serializer_sym = self.lookup_fully_qualified(fullnames.BASE_SERIALIZER_FULLNAME)
        if base_serializer_sym is not None and isinstance(base_serializer_sym.node, TypeInfo):
            return base_serializer_sym.node.metadata.setdefault("drf", {}).setdefault(
                "serializer_bases", {fullnames.BASE_SERIALIZER_FULLNAME: 1}
            )
        else:
            return {}

    def _get_typeinfo_or_none(self, class_name: str) -> Optional[TypeInfo]:
        sym = self.lookup_fully_qualified(class_name)
        if sym is not None and isinstance(sym.node, TypeInfo):
            return sym.node
        return None

    def get_base_class_hook(self, fullname: str) -> Optional[Callable[[ClassDefContext], None]]:
        info = self._get_typeinfo_or_none(fullname)
        base_process = fullname in self._get_currently_defined_serializers()
        if info:
            if info.has_base(fullnames.SERIALIZER_FULLNAME):
                return partial(handle_serializer_class, django_context=self.django_context, base_process=base_process)
        return None

    def get_type_analyze_hook(self, fullname: str) -> Optional[Callable[["mypy.plugin.AnalyzeTypeContext"], MypyType]]:
        if fullname.endswith("types.SerializerDataType"):
            return partial(handle_return_type, django_context=self.django_context)
        return None


def plugin(version):
    return NewSemanalDRFPlugin
