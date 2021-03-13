from pyopenapi3.builder import OpenApiBuilder
from pyopenapi3.objects import Int64, Email, RequestBody, Response
from pyopenapi3.utils import create_schema, parse_name_and_type_from_fmt_str
from pyopenapi3.schemas import (
    RequestBodySchema,
    MediaType,
    ReferenceSchema,
    ParamSchema,
    SchemaMapping
)


from pydantic import BaseModel, Field, ValidationError, AnyUrl, EmailStr
from typing import Optional

import yaml

open_bldr = OpenApiBuilder()


@open_bldr.component()
class Customer:
    """A customer"""

    @open_bldr.component()
    def id(self) -> Int64:
        """An id"""
        ...

    @open_bldr.component()
    def email(self) -> Email:
        """An email"""
        ...


@open_bldr.info
class Info:

    title = "A customer based store"
    version = "1.0.0"
    description: "A customer based store"
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


@open_bldr.server
class Server1:

    url = 'path/to/server1'
    description = "Server 1"


@open_bldr.server
class Server2:

    url = 'path/to/server2'
    description = "Server 2"
    variables = {
        'customerId': {
            'default': 'demo',
            'description': 'Customer ID assigned by service provider.'
        },
        'port': {
            'enum': ['443', '8443'],
            'default': '443'
        }
    }


@open_bldr.path
class Path1:

    path = '/user'

    request_body = RequestBody(
        required=True,
        description="The request body",
        content=[('application/json', Int64), ('application/xml', Email)]
    )

    response = Response(status=200, description="The response")

    def get(self) -> (..., [response]):
        ...


# @open_bldr.path
# class Path2:
#
#     path = '/some_users/{email:Email}'



@open_bldr.path
class Users:

    # `id` should be automatically placed in
    # each method's parameter as "in: path".
    # TODO Figure out how to yank `id` out of formatted str `path`.
    path = '/users/{id:Int64}'

    get_response_200 = Response(
        status=200, description="a list of users",
        content=[("application/json", Customer)]
    )
    get_response_404 = Response(
        status=404, description="an error"
    )
    get_responses = [get_response_200, get_response_404]
    get_body = RequestBody(
        description='Some request body',
        required=True,
        content=[("application/json", Customer), ("application/xml", Int64)]
    )

    @open_bldr.path.query_param(name='ar', field=Int64)
    @open_bldr.path.meta(tags=['tag1'], summary='summary1')
    def get(self) -> (..., get_responses):
        """Get all users"""

    @open_bldr.path.query_param(name='ar', field=Int64)
    @open_bldr.path.meta(tags=['tag1'], summary='summary1')
    def post(self) -> (get_body, get_responses):
        """post to all users"""


open_bldr.as_yaml('path.yaml')









































