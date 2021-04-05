import pytest

from pyopenapi3 import OpenApiBuilder, create_schema
from pyopenapi3.builders import (
    InfoBuilder,
    ServerBuilder,
    PathsBuilder,
    ComponentBuilder,
)
from pyopenapi3.objects import (
    Response,
    Op,
    JSONMediaType,
)
from pyopenapi3.data_types import (
    Array,
    Int32,
    Int64,
    String,
    Component,
    Object
)
# from pyopenapi3.objects import Response, Array
from .examples import (
    server as server_examples,
    info as info_examples,
    path as path_examples,
    component as component_examples,
)


def test_info_object_success():
    info_bldr = InfoBuilder()

    @info_bldr
    class InfoObjectSuccess:
        title = "Sample Pet Store App"
        version = "1.0.1"
        description = "This is a sample server for a pet store."
        terms_of_service = "http://example.com/terms/"
        contact = {
            'name': "API Support",
            'url': "http://www.example.com/support",
            'email': "support@example.com"
        }
        license = {
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
        }

    assert info_bldr.build.dict() == info_examples.info_object_example


def test_default_server():
    server_bldr = ServerBuilder()

    servers = [s.dict() for s in server_bldr.build]
    assert servers == server_examples.default_server['servers']


def test_one_server_object_success():
    server_bldr = ServerBuilder()

    @server_bldr
    class Server:

        url = "https://development.gigantic-server.com/v1"
        description = "Development server"

    servers = [s.dict() for s in server_bldr.build]

    assert servers == server_examples.single_server["servers"]


def test_multiple_servers_success():
    server_builder = ServerBuilder()

    @server_builder
    class DevServer:

        url = "https://development.gigantic-server.com/v1"
        description = "Development server"

    @server_builder
    class StageServer:

        url = "https://staging.gigantic-server.com/v1"
        description = "Staging server"

    @server_builder
    class ProdServer:

        url = "https://api.gigantic-server.com/v1"
        description = "Production server"

    servers = [s.dict() for s in server_builder.build]

    assert servers == server_examples.multiple_servers['servers']


def test_server_with_vars_success():
    server_bldr = ServerBuilder()
    user_name_var = {
        "default": "demo",
        "description": (
            "this value is assigned by the service provider, "
            "in this example `gigantic-server.com`"
        )
    }
    port_var = {
        "enum": [
            "8443",
            "443"
        ],
        "default": "8443"
    }
    base_path_var = {"default": "v2"}

    @server_bldr
    class VarServer:

        url = "https://{username}.gigantic-server.com:{port}/{basePath}"
        description = "The production API server"
        variables = {
            "username": user_name_var,
            "port": port_var,
            "basePath": base_path_var
        }

    servers = [s.dict() for s in server_bldr.build]
    assert servers == server_examples.server_with_vars['servers']


def test_path_success():
    path_bldr = PathsBuilder()

    class pet(Component):
        ...

    response = Response(
        status=200, description="A list of pets.",
        content=[JSONMediaType(Array[pet])]
    )

    @path_bldr
    class Path:

        path = '/pets'

        def get(self) -> Op[..., [response]]:
            """Returns all pets from the system that the user has access to"""
            ...

    assert path_bldr.build['/pets'].dict() == path_examples.path['/pets']


@pytest.fixture
def _allowed_types():
    """Tear down for global `pyopenapi3.builders._allowed_types`."""

    # Clean up global `_allowed_types`; any test that indirectly
    # makes use of `pyopenapi3.builders._allowed_types` but can be
    # directly affected, such as in `test_paths_path__break`, should
    # use this fixture. This is because any allowed type should be
    # available for the entire running process.
    import pyopenapi3
    pyopenapi3.builders._allowed_types = {}
    yield


def test_path_with_path_parameter():
    open_bldr = OpenApiBuilder()

    @open_bldr.component.parameter
    class PetID:

        name = "pet_id"
        description = "Pet's Unique identifier"
        in_field = "path"
        schema = create_schema(String, pattern="^[a-zA-Z0-9-]+$")
        required = True

    @open_bldr.path
    class Path:

        path = "/pets/{pet_id:PetID}"

    p = open_bldr.path.build["/pets/{pet_id}"]

    assert p.dict() == path_examples.path_with_parameter


def test_paths_path__break(_allowed_types):
    path_bldr = PathsBuilder()

    with pytest.raises(ValueError):
        @path_bldr
        class Path:

            # Should break because `PetID` is not a component parameter
            # schema and is not a `pyopenapi3.data_types.Field` Type.
            path = "/pets/{pet_id:PetID}"


def test_path_parameter_in_field__fail():
    comp = ComponentBuilder()

    with pytest.raises(ValueError):

        @comp.parameter
        class PetID:

            name = "pet_id"
            description = "Pet's Unique identifier"
            # Should fail with anything not in `ParamBuilder
            # ._allowable_in_fields`.
            in_field = "notpath"
            schema = create_schema(String, pattern="^[a-zA-Z0-9-]+$")
            required = True


def test_components_builder():
    comp = ComponentBuilder()

    @comp.schema
    class GeneralError:

        @comp.schema_field
        def code(self) -> Int32:
            ...

        @comp.schema_field
        def message(self) -> String:
            ...

    @comp.schema
    class Category:

        @comp.schema_field
        def id(self) -> Int64:
            ...

        @comp.schema_field
        def name(self) -> String:
            ...

    @comp.schema
    class Tag:

        @comp.schema_field
        def id(self) -> Int64:
            ...

        @comp.schema_field
        def name(self) -> String:
            ...

    @comp.response
    class NotFound:

        description = "Entity not found."

    @comp.response
    class IllegalInput:

        description = "Illegal input for operation."

    @comp.response
    class GeneralError:

        description = "General Error"
        content = [JSONMediaType(GeneralError)]

    @comp.parameter
    class skipParam:

        name = "skip"
        in_field = "query"
        description = "number of items to skip"
        required = True
        schema = Int32

    @comp.parameter
    class limitParam:

        name = "limit"
        in_field = "query"
        description = "max records to return"
        required = True
        schema = Int32

    example_components = component_examples.component['components']

    schemas = comp.build.schemas
    example_schemas = example_components['schemas']
    assert schemas == example_schemas

    responses = comp.build.responses
    example_responses = example_components['responses']
    assert responses == example_responses

    parameters = comp.build.parameters
    example_parameters = example_components['parameters']
    assert parameters == example_parameters


def test_component_with_object_level_fields():
    component = ComponentBuilder()

    @component.schema
    class Pet:

        @component.schema_field(
            required=True, example="Susie",
            min_length=1, max_length=100
        )
        def name(self) -> String:
            """Pet's name"""

        @component.schema_field(required=True, example="cat", min_length=1)
        def animal_type(self) -> String:
            """Kind of animal"""

    example_cpy = component_examples.object_lvl_test.copy()
    d = component.build.dict()
    # The `required` list is not predictable. That is, it is not clear
    # before runtime whether the list will be ["name", "animal_type"]
    # or ["animal_type", "name"]. Since we need to test these lists in an
    # unordered fashion, we pop them out of each dict instance and compare
    # their sets. Then we can test the rest of the key/vals.
    required_list = d['schemas']['Pet'].pop('required')
    example_required_list = example_cpy['schemas']['Pet'].pop('required')
    assert set(required_list) == set(example_required_list)
    assert d == example_cpy


def test_component_with_inline_object():
    c = ComponentBuilder()

    @c.schema
    class Pet:

        @c.schema_field
        def tags(self) -> Object:
            """Custom tags"""

    assert c.build.dict() == {
        'schemas': {
            'Pet': {
                'type': 'object',
                'properties': {
                    'tags': {
                        'type': 'object',
                        'description': 'Custom tags'
                    }
                }
            }
        }
    }


def test_component_parameter_references():
    """Test that a component parameter gets referenced correctly."""
    c = ComponentBuilder()

    @c.parameter
    class PetId:

        name = "pet_id"
        description = "Pet's Unique Identifier"
        in_field = "path"
        schema = create_schema(String, pattern="^[a-zA-Z0-9-]+$")

    @c.schema
    class Pet:

        @c.schema_field
        def pet_id(self) -> PetId:
            ...

    assert c.build.dict() == component_examples.param_reference_comp
