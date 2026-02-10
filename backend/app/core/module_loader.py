import importlib
from typing import Iterable, List

from app.core.module_registry import ModuleDefinition, ModuleRegistry


def load_modules(module_paths: Iterable[str]) -> List[ModuleDefinition]:
    registry = ModuleRegistry()

    for module_path in module_paths:
        module = importlib.import_module(module_path)
        if not hasattr(module, "get_module"):
            raise ValueError(f"module has no get_module(): {module_path}")
        module_def = module.get_module()
        registry.register(module_def)

    return registry.resolve_order()