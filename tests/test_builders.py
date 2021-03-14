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

from pyopenapi3.builder import InfoBuilder, ServerBuilder
from .examples import info as info_examples, server as server_examples


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

    assert info_bldr.builds.dict() == info_examples.info_object_example


def test_one_server_object_success():
    server_bldr = ServerBuilder()

    @server_bldr
    class Server:

        url = "https://development.gigantic-server.com/v1"
        description = "Development server"

    assert server_bldr.as_dict() == server_examples.single_server


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

    assert server_builder.as_dict() == server_examples.multiple_servers


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

    assert server_bldr.as_dict() == server_examples.server_with_vars

