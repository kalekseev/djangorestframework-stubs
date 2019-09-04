import importlib
from functools import partial
from typing import Callable, Dict, Optional

from mypy.nodes import MDEF, SymbolTableNode, TypeInfo, Var
from mypy.options import Options
from mypy.plugin import ClassDefContext, FunctionContext, Plugin
from mypy.types import Instance
from mypy.types import Type as MypyType
from mypy.types import TypedDictType
from mypy_django_plugin import main as mypy_django_main
from mypy_django_plugin.django.context import DjangoContext
from mypy_django_plugin.lib.helpers import add_new_class_for_module
from mypy_drf_plugin.lib import fullnames, helpers
from mypy_drf_plugin.transformers import serializers


def transform_serializer_class(ctx: ClassDefContext) -> None:
    sym = ctx.api.lookup_fully_qualified_or_none(fullnames.BASE_SERIALIZER_FULLNAME)
    if sym is not None and isinstance(sym.node, TypeInfo):
        helpers.get_drf_metadata(sym.node)["serializer_bases"][ctx.cls.fullname] = 1

    serializers.make_meta_nested_class_inherit_from_any(ctx)


def redefine_and_typecheck_serializer_fields(ctx: FunctionContext, django_context: DjangoContext) -> MypyType:
    assert isinstance(ctx.default_return_type, Instance)
    module_path, klass = ctx.default_return_type.type.fullname().rsplit(".", 1)
    module = importlib.import_module(module_path)
    ser = getattr(module, klass)
    from rest_framework.serializers import ModelSerializer

    if ser is ModelSerializer or not issubclass(ser, ModelSerializer) or not hasattr(ser, "Meta"):
        return ctx.default_return_type

    def ninit(self):
        ModelSerializer.__init__(self, instance=None)

    methods = {"__init__": ninit}
    if hasattr(ser, "Meta"):
        methods["Meta"] = type("Meta", (ser.Meta,), {})
    FakeSerializer = type("FakeSerializer", (ser,), methods)
    fields = FakeSerializer().fields
    required_keys = {}
    for name, field in fields.items():
        fmodule = ctx.api.modules[field.__module__]
        ftype = fmodule.names[field.__class__.__name__]
        required_keys[name] = Instance(ftype.node, [])
    object_type = ctx.api.named_generic_type("mypy_extensions._TypedDict", [])
    typed_dict_type = TypedDictType(required_keys, required_keys=set(fields.keys()), fallback=object_type)
    smodule = ctx.api.modules[module_path]
    new_class = add_new_class_for_module(smodule, ser.__name__ + "Fields", [object_type], {})
    new_class.typeddict_type = typed_dict_type

    ser_type_info = ctx.default_return_type.type
    var = Var("fields", typed_dict_type)
    var.info = ser_type_info
    var.is_initialized_in_class = True
    var.is_property = True
    var._fullname = ser_type_info.fullname() + "." + var.name()

    ctx.default_return_type.type.names["fields"] = SymbolTableNode(MDEF, var, plugin_generated=True)
    return ctx.default_return_type


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

    def get_base_class_hook(self, fullname: str) -> Optional[Callable[[ClassDefContext], None]]:
        if fullname in self._get_currently_defined_serializers():
            return transform_serializer_class
        return None

    def _get_typeinfo_or_none(self, class_name: str) -> Optional[TypeInfo]:
        sym = self.lookup_fully_qualified(class_name)
        if sym is not None and isinstance(sym.node, TypeInfo):
            return sym.node
        return None

    def get_function_hook(self, fullname: str) -> Optional[Callable[[FunctionContext], MypyType]]:
        info = self._get_typeinfo_or_none(fullname)
        if info:
            if info.has_base(fullnames.SERIALIZER_FULLNAME):
                return partial(redefine_and_typecheck_serializer_fields, django_context=self.django_context)
        return None


def plugin(version):
    return NewSemanalDRFPlugin
