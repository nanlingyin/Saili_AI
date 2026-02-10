from app.core.module_registry import ModuleDefinition
from app.modules.recommendations.routes import router


def get_module() -> ModuleDefinition:
    return ModuleDefinition(
        name="recommendations",
        dependencies=["competitions"],
        router=router,
    )