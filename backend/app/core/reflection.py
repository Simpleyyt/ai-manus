import importlib
from typing import Any


def import_string(dotted_path: str) -> Any:
    """Import a class, function, or variable by its full dotted path.

    Examples::

        cls = import_string("app.infrastructure.external.task.redis_task.RedisStreamTask")
        func = import_string("app.infrastructure.external.search.get_search_engine")
    """
    try:
        module_path, attr_name = dotted_path.rsplit(".", 1)
    except ValueError:
        raise ImportError(f"'{dotted_path}' is not a valid dotted path")

    module = importlib.import_module(module_path)

    try:
        return getattr(module, attr_name)
    except AttributeError:
        raise ImportError(
            f"Module '{module_path}' has no attribute '{attr_name}'"
        )
