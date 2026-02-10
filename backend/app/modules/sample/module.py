from app.core.module_registry import ModuleDefinition
from app.modules.sample.routes import router


def get_module() -> ModuleDefinition:
    return ModuleDefinition(
        name="sample",
        dependencies=[],
        router=router,
    )