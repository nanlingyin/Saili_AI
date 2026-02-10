from app.core.module_registry import ModuleDefinition
from app.modules.admin.routes import router


def get_module() -> ModuleDefinition:
    return ModuleDefinition(
        name="admin",
        dependencies=["auth", "competitions"],
        router=router,
    )