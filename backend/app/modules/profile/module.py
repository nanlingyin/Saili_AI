from app.core.module_registry import ModuleDefinition
from app.modules.profile.routes import router


def get_module() -> ModuleDefinition:
    return ModuleDefinition(
        name="profile",
        dependencies=["auth"],
        router=router,
    )
