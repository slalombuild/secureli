from importlib.metadata import version


def secureli_version() -> str:
    """Leverage package resources to determine the current version of secureli"""
    return version("secureli")
