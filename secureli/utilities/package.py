import subprocess
import sys
from importlib import metadata
import pathlib

import pkg_resources
import setuptools
import toml

def get_installed_version(name: str = 'secureli', print_output: bool = False) -> str:
    version = metadata.distribution("secureli").version
    if print_output:
        print(f'\nINSTALLED VERSION: v{version}')

def get_all_versions(name: str='secureli', print_output: bool=False) -> str:
    versions = str(subprocess.run([sys.executable, '-m', 'pip', 'install', '{}==random'.format(name)], capture_output=True, text=True))
    versions = versions[versions.find('(from versions:')+25:]
    versions = versions[:versions.find(')')]
    versions = versions.replace(' ','').split(',')
    if print_output:
        print('\nALL VERSIONS:')
        output ='\n - v'.join(versions)
        print(f' - v{output}')
    return versions

def get_latest_version(name: str='secureli', print_output: bool=False) -> str:
    version = get_all_versions(name, print_output)[-1]
    if print_output:
        print(f'\nLATEST VERSION: v{version}')
    return version


def get_project_version(name: str='secureli', print_output: bool=False) -> str:
    """
    TODO Where would we find this? 
    .secureli.yaml? We would need to add the version, either manually or maybe during init...
    """

def is_latest_version(name: str = 'secureli', print_output: bool=False) -> bool:
    latest = get_latest_version(name, print_output)
    installed = get_installed_version(name, print_output)
    is_latest = installed == latest
    if print_output:
        print(f'\nIS LATEST VERSION: {is_latest}')
    return is_latest

def is_correct_version_installed(name: str = 'secureli', print_output: bool=False) -> bool:
    from secureli.utilities.secureli_meta import secureli_version 
    installed = get_installed_version(name, print_output)
    project = get_project_version(name, print_output)
    if print_output:
        print(f'\PROJECT VERSION: {project}')
    return project == installed
    
if __name__ == "__main__":
   is_latest_version(print_output=True)
   is_correct_version_installed(print_output=True)