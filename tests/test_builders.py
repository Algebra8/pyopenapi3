from pyopenapi3.builders import (
    InfoBuilder,
    ServerBuilder,
    PathsBuilder,
    ComponentBuilder
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
    Component
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

    assert component.build.dict() == component_examples.object_lvl_test
