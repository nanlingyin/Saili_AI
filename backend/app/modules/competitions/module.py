from app.core.module_registry import ModuleDefinition
from app.modules.competitions.routes import router


def get_module() -> ModuleDefinition:
    return ModuleDefinition(
        name="competitions",
        dependencies=[],
        router=router,
    )