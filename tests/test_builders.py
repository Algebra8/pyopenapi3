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
from .examples.info import info_object_example


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

    assert info_bldr.builds.dict() == info_object_example


def test_server_object_success():
    ...