from app.core.module_registry import ModuleDefinition
from app.modules.reminders.routes import router


def get_module() -> ModuleDefinition:
    return ModuleDefinition(
        name="reminders",
        dependencies=["favorites"],
        router=router,
    )