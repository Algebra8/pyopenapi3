from pyopenapi3.builder import OpenApiBuilder
from pyopenapi3.objects import Int64, Email
from pyopenapi3.utils import create_schema

from pydantic import BaseModel
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


comp = open_bldr.component
# open_bldr.as_yaml('ncus.yaml')

with open('ncus.yaml', 'w') as f:
    yaml.dump(comp.as_dict(), f, allow_unicode=True)


def make_camel(s: str):
    assert s

    camel: str
    no_unders = s.split('_')

    if len(no_unders) == 1:
        camel = no_unders[0].capitalize()
    else:
        camel = (
                no_unders[0]
                + ''.join([word.capitalize() for word in no_unders[1:]])
        )
    return camel


@open_bldr.info
class Info:

    title = "A customer based store"
    version = "1.0.0"
    description: "A customer based store"
    terms_of_service = "These are the terms of service."


# @open_bldr.server
# class Server1:
#
#     url = 'path/to/server1'
#     description = "Server 1"
#
#
# @open_bldr.server
# class Server2:
#
#     url = 'path/to/server2'
#     description = "Server 2"
#     variables = {
#         'customerId': {
#             'default': 'demo',
#             'description': 'Customer ID assigned by service provider.'
#         },
#         'port': {
#             'enum': ['443', '8443'],
#             'default': '443'
#         }
#     }


servers = open_bldr.server


with open('defser.yaml', 'w') as f:
    yaml.dump(servers.as_dict(), f, allow_unicode=True)

