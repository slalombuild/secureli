import pkg_resources


def secureli_version() -> str:
    """Leverage package resources to determine the current version of secureli"""
    return pkg_resources.get_distribution("secureli").version
