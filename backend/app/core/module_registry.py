from dataclasses import dataclass, field
from typing import Dict, List, Optional

from fastapi import APIRouter


@dataclass(frozen=True)
class ModuleDefinition:
    name: str
    dependencies: List[str] = field(default_factory=list)
    router: Optional[APIRouter] = None


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: Dict[str, ModuleDefinition] = {}

    def register(self, module_def: ModuleDefinition) -> None:
        if module_def.name in self._modules:
            raise ValueError(f"duplicate module: {module_def.name}")
        self._modules[module_def.name] = module_def

    def resolve_order(self) -> List[ModuleDefinition]:
        ordered: List[ModuleDefinition] = []
        state: Dict[str, str] = {}

        def visit(name: str) -> None:
            status = state.get(name)
            if status == "temp":
                raise ValueError(f"cycle detected at module: {name}")
            if status == "perm":
                return
            if name not in self._modules:
                raise ValueError(f"missing dependency: {name}")

            state[name] = "temp"
            module_def = self._modules[name]
            for dep in module_def.dependencies:
                visit(dep)
            state[name] = "perm"
            ordered.append(module_def)

        for module_name in list(self._modules.keys()):
            visit(module_name)

        return ordered