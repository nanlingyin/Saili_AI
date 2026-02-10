from app.core.module_registry import ModuleDefinition
from app.modules.auth.routes import router


def get_module() -> ModuleDefinition:
    return ModuleDefinition(
        name="auth",
        dependencies=[],
        router=router,
    )