from pyopenapi3 import OpenApiBuilder, create_schema

from pyopenapi3.data_types import String, Int32, Array, DateTime, Object
from pyopenapi3.objects import Op, Response, RequestBody, JSONMediaType

open_bldr = OpenApiBuilder()


@open_bldr.info
class Info:

    title = "Pet Shop Example API"
    version: "0.1"
    description: "Simple example API to store and retrieve pets"


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

    @paths.op(tags=["Pets"], operation_id=["app.get_pets"])
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

    @paths.op(tags=["Pets"], operation_id=["app.get_pet"])
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

    @paths.op(tags=["Pets"], operation_id=["app.put_get"])
    def put(self) -> Op[put_body, put_responses]:
        """Create or update a pet"""

    delete_responses = [
        Response(status=204, description="Pet was deleted"),
        Response(status=404, description="Pet does not exist")
    ]

    @paths.op(tags=["Pets"], operation_id=["app.delete_pet"])
    def delete(self) -> Op[..., delete_responses]:
        """Remove a pet"""
