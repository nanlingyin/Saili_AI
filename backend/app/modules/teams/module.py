from app.core.module_registry import ModuleDefinition
from app.modules.teams.routes import router


def get_module() -> ModuleDefinition:
    return ModuleDefinition(
        name="teams",
        dependencies=["auth"],
        router=router,
    )
