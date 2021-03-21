import pytest

import sys
import os
# TODO remove when setup included.
pyopenpath = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..',
        'src/'
    )
)
sys.path.insert(0, pyopenpath)

from pyopenapi3.builders import (
    InfoBuilder,
    ServerBuilder,
    PathsBuilder,
    ComponentBuilder
)
from pyopenapi3.objects import (
    Component,
    Response,
    RequestBody,
    Op,
    Array,
    JSONMediaType,
    Int32,
    String,
    Int64
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


    schemas = comp.build.schemas
    example_schemas = component_examples.component['components']['schemas']

    # for schema in example_schemas:
        # assert schemas[schema].dict() == example_schemas[schema]
    # assert schemas['GeneralError'] == example_schemas['GeneralError']
    # assert schemas['Category'] == example_schemas['Category']
    print(schemas['Category'].dict())
