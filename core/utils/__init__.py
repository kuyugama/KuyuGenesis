import inspect

from .paginator import Paginator


def params_generator(scope, variables, ignore_types=False):
    annotations = inspect.get_annotations(scope)

    params = {}
    for name, type_ in annotations.items():
        if name.startswith("__") or name.endswith("_"):
            continue
        if not ignore_types and not isinstance(variables.get_account(name), type_):
            continue
        params[name] = variables.get_account(name)

    return params
