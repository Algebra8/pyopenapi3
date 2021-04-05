"""Example usage of `connexion`.

Connexion parts are taken from (https://github.com/hjacobs/connexion-
example/blob/master/app.py).
"""

import os
from typing import Optional, Dict, List, Any, Tuple, Union
import datetime
import logging
from pathlib import Path

import connexion
from connexion import NoContent

from pyopenapi3 import OpenApiBuilder, create_schema
from pyopenapi3.data_types import String, Int32, Array, DateTime, Object
from pyopenapi3.objects import Op, Response, RequestBody, JSONMediaType


# pyopenapi3
open_bldr = OpenApiBuilder()


@open_bldr.info
class Info:

    title = "Pet Shop Example API"
    version = "0.1"
    description = "Simple example API to store and retrieve pets"


component = open_bldr.component


@component.schema
class Pet:

    @component.schema_field(example="123", read_only=True)
    def id(self) -> String:
        """Unique identifier"""

    @component.schema_field(
        required=True, example="Susie",
        min_length=1, max_length=100
    )
    def name(self) -> String:
        """Pet's name"""

    @component.schema_field(required=True, example="cat", min_length=1)
    def animal_type(self) -> String:
        """Kind of animal"""

    # Object is an in-line description for a Free-Form Object.
    # For a more complicated object, use `Component.schema`.
    @component.schema_field
    def tags(self) -> Object:
        """Custom tags"""

    @component.schema_field(
        read_only=True,
        example="2020-07-07T15:49:51.230+02:00"
    )
    def created(self) -> DateTime:
        """Creation time"""


@component.parameter
class PetId:

    name = "pet_id"
    description = "Pet's Unique Identifier"
    in_field = "path"
    schema = create_schema(String, pattern="^[a-zA-Z0-9-]+$")
    required = True


paths = open_bldr.path


@paths
class Pets:

    path = "/pets"

    get_responses = [
        Response(
            status=200,
            description="Return pets",
            content=[JSONMediaType(Array[Pet])]
        )
    ]

    @paths.op(tags=["Pets"], operation_id="app.get_pets")
    @paths.query_param(
        name="animal_type",
        schema=create_schema(String, pattern="^[a-zA-Z0-9]*$")
    )
    @paths.query_param(
        name="limit",
        schema=create_schema(Int32, minimum=0, default=100)
    )
    def get(self) -> Op[..., get_responses]:
        """Get all pets."""
        # Note: docstrings for function populate the operation's
        # `description` field. For `summary`, include `summary="..."`
        # as an arg in `@paths.op(...)`.


@open_bldr.path
class PetsWithId:

    # `pet_id` will be a `path` param which is defined
    # by the class `PetId`, which is decorated by
    # `@open_bldr.component.parameter`.
    path = "/pets/{pet_id:PetId}"

    get_responses = [
        Response(
            status=200,
            description="Return pet",
            content=[JSONMediaType(Pet)]
        ),
        Response(status=404, description="Pet does not exist")
    ]

    @paths.op(tags=["Pets"], operation_id="app.get_pet")
    def get(self) -> Op[..., get_responses]:
        """Get a single pet"""

    put_responses = [
        Response(status=200, description="Pet updated"),
        Response(status=201, description="New pet created")
    ]
    put_body = RequestBody(
        description="Request body required for PUT op. "
                    "OpenAPI3 uses Request body instead of "
                    "body parameters.",
        content=[JSONMediaType(Pet)],
        required=True
    )

    @paths.op(tags=["Pets"], operation_id="app.put_get")
    def put(self) -> Op[put_body, put_responses]:
        """Create or update a pet"""

    delete_responses = [
        Response(status=204, description="Pet was deleted"),
        Response(status=404, description="Pet does not exist")
    ]

    @paths.op(tags=["Pets"], operation_id="app.delete_pet")
    def delete(self) -> Op[..., delete_responses]:
        """Remove a pet"""


# Connexion
Pet = Dict[str, Any]
Response = Tuple[str, int]

PETS: Dict[str, Pet] = {}


def get_pets(
    limit: int,
    animal_type: Optional[str] = None
) -> Dict[str, List[Pet]]:
    return {
        'pets': [
            pet for pet in PETS.values()
            if animal_type is None or
            pet['animal_type'] == animal_type[:limit]
        ]
    }


def get_pet(pet_id: str) -> Union[Pet, Response]:
    return PETS.get(pet_id, False) or ('Not found', 404)


def put_get(pet_id: str, pet: Pet) -> Response:
    exists = pet_id in PETS
    pet['id'] = pet_id

    if exists:
        logging.info(f'Updating pet {pet_id}..')
        PETS[pet_id].update(pet)
    else:
        logging.info(f'Creating pet {pet_id}..')
        pet['created'] = datetime.datetime.utcnow()
        PETS[pet_id] = pet
    return NoContent, (200 if exists else 201)


def delete_pet(pet_id: str) -> Response:
    if pet_id in PETS:
        logging.info(f'Deleting pet {pet_id}..')
        del PETS[pet_id]
        return NoContent, 204
    else:
        return NoContent, 404


logging.basicConfig(level=logging.INFO)
app = connexion.App(__name__)

s = 'swagger.yaml'
swagger_dir = os.path.abspath(os.path.dirname(__file__))
swagger_path = Path(swagger_dir) / s
with open(swagger_path, 'w') as f:
    f.write(open_bldr.yaml())

app.add_api(s)
application = app.app


if __name__ == '__main__':
    print("Beginning server...")
    app.run(port=8080, server='gevent')
