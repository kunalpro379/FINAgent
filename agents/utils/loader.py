import importlib
from typing import Any


def import_from_string(dotted_path: str) -> Any:
    """Load an attribute/class/function from a dotted module path."""
    if not isinstance(dotted_path, str) or "." not in dotted_path:
        raise ImportError(f"Invalid import path: {dotted_path}")
    module_path, attr_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    try:
        return getattr(module, attr_name)
    except AttributeError as exc:
        raise ImportError(f"Module '{module_path}' has no attribute '{attr_name}'") from exc


