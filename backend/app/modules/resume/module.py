from app.core.module_registry import ModuleDefinition
from app.modules.resume.routes import router


def get_module() -> ModuleDefinition:
    return ModuleDefinition(
        name="resume",
        dependencies=["auth"],
        router=router,
    )
