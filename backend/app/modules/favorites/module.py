from app.core.module_registry import ModuleDefinition
from app.modules.favorites.routes import router


def get_module() -> ModuleDefinition:
    return ModuleDefinition(
        name="favorites",
        dependencies=["competitions"],
        router=router,
    )