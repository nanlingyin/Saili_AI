from app.core.module_registry import ModuleDefinition
from app.modules.forum.routes import router


def get_module() -> ModuleDefinition:
    return ModuleDefinition(
        name="forum",
        dependencies=["auth"],
        router=router,
    )
