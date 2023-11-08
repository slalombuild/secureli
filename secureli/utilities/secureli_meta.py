from secureli.utilities.package import get_installed_version

def secureli_version() -> str:
    return get_installed_version()

if __name__ == "__main__":
   print(secureli_version())