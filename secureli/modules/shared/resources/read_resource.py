from pathlib import Path


def read_resource(resource_name: str) -> str:
    """
    Resolves the provided resource name into a string containing the contents of said resource
    :param resource_name: The name of the resource file, which should be contained in the "files" folder
    :raises ValueError: if the provided resource name does not resolve to an existing file
    :return: The contents of the resolved resource as a string, or raises a ValueError
    """
    resources_folder = Path(__file__).parent
    resource_path = resources_folder / "files" / resource_name

    if not resource_path.exists() or not resource_path.is_file():
        raise ValueError(f"Path {resource_path} not found or not a file")

    with open(resource_path, encoding="utf8") as resource_file:
        return resource_file.read()
