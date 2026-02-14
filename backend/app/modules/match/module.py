from app.core.module_registry import ModuleDefinition
from app.modules.match.routes import router


def get_module() -> ModuleDefinition:
    return ModuleDefinition(
        name="match",
        dependencies=["competitions"],
        router=router,
    )
