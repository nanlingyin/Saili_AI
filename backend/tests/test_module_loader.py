from app.core.config import MODULE_PATHS
from app.core.module_loader import load_modules


def test_module_loader_registers_sample():
    modules = load_modules(MODULE_PATHS)
    names = [module.name for module in modules]

    assert "sample" in names