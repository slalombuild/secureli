import inspect

import pytest
from dependency_injector.providers import Factory

from secureli.container import Container


@pytest.fixture()
def container() -> Container:
    return Container()


def test_that_container_loads(container: Container):
    # Raises an error if any dependencies aren't provided or have no defaults.
    container.check_dependencies()

    # Check each element in the container. If it's a factory (meaning, a function that produces an object)
    # then attempt to resolve it and its dependencies. Any error that occurs will cause this test to fail!
    for provider in container.traverse():
        if type(provider) is Factory:
            try:
                provider()
            except TypeError as e:
                required_arg_spec = list(
                    inspect.getfullargspec(provider.cls.__init__).args[1:]
                )
                provided_args = list(provider.kwargs.keys())

                if provided_args != required_arg_spec:
                    pytest.fail(
                        f"Error resolving {provider.cls.__name__}: args required mismatched provided ({str(e)})"
                    )
