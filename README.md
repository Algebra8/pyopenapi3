pyopenapi3
===========

``pyopenapi3`` converts Python objects to the 
[OpenAPI 3 Specification](https://swagger.io/specification). 
It can be used to easily manage your API descriptions, particularly when using 
packages such as 
[connexion](https://connexion.readthedocs.io/en/latest/). 
For a quick guide on how to use ``pyopenapi3``, take a peak at the example below. Or, check out how it can be 
[used with `connexion`](#connexion-example). 
Other examples can be found in
[pyopenapi3/examples](https://github.com/Algebra8/pyopenapi3/tree/main/examples).

> :warning: Please note that `pyopenapi3` is still **experimental**. 
> Some features may not be complete.


## Quick guide

```python

# Example script.

from pyopenapi3 import OpenApiBuilder, create_schema
from pyopenapi3.data_types import String, Object, DateTime, Array
from pyopenapi3.objects import Op, Response, RequestBody, JSONMediaType

# Explicit builds are required for Info and Paths.
# Optional builds include Servers, Components, Tags, and External Docs.
#
# Note that if a Server object is not explicitly included, a default
# server will be added according to the OpenAPI3 specification.
# For more info, see:
# https://swagger.io/docs/specification/api-host-and-base-path/
open_ = OpenApiBuilder()


@open_.info
class Info:

    title = "Title for example"
    version = "0.1"
    description = "Description for example."


# Builder for components.
cmp = open_.component


# Build the Pet component.
# Can be referenced at "#/components/schemas/Pet".
@cmp.schema
class Pet:

    # Declare a schema field. In this case it is `name` with
    # type `String`. Any args passed into `schema_field` will
    # be passed along as attrs for the object, unless they are
    # Component level attrs, such as `required`.
    @cmp.schema_field(
        example="123", read_only=True
    )
    def id(self) -> String:
        """Unique identifier"""
        # OpenAPI3 output:
        #
        # {
        #     'id': {
        #         'type': 'string',
        #         'description': 'Unique identifier',
        #         'example': '123',
        #         'readOnly': True
        #     }
        # }

    @cmp.schema_field(
        required=True, example="Susie",
        min_length=1, max_length=100
    )
    def name(self) -> String:
        """Pet's name"""

    # `Object` is an in-line description for a Free-Form Object.
    # For a more complicated object, use `Component.schema` decorator.
    @cmp.schema_field
    def tags(self) -> Object:
        """Custom tags"""

    @cmp.schema_field(
        read_only=True,
        example="2020-07-07T15:49:51.230+02:00"
    )
    def created(self) -> DateTime:
        """Creation time"""


# A Component Parameter object.
# Can be referenced at "#/components/parameters/PetId".
@cmp.parameter
class PetId:

    name = "pet_id"
    description = "Pet's Unique Identifier"
    in_field = "path"

    # `create_schema` exposes the functionality seen in the decorator
    # `Component.schema_field.` It is useful for creating complex schemas,
    # such as a `String` with `pattern="^[a-zA-Z0-9-]+$"`.
    # For simple schemas just pass in the `pyopenapi3.data_type`, which in
    # this case would be `String`.
    schema = create_schema(String, pattern="^[a-zA-Z0-9-]+$")

    required = True


# Builder for paths.
paths = open_.path


@paths
class PetsWithId:

    # For paths with path parameters, use string formatting
    # with the format {name:OpenApiBuilder().component.parameter}.
    # In this case, the path `path` will include a path parameter
    # with name `pet_id` and schema `PetId`.
    path = "/pets/{pet_id:PetId}"

    # Each path can contain one of the valid HTTP operations:
    # get, post, put, patch, delete, head, options, and trace.

    # Each operation is represented by a class method that does
    # not take any arguments and returns an `Op` object.

    # The `Op` object must have __getitem__ called with the first
    # argument as the operation's `RequestBody` and the second as
    # a list of `Response`s with unique status codes.

    # If a `RequestBody` is not required for the given operation,
    # use Ellipses: `Op[..., [response1, response2]]`.

    # To include media type content to `RequestBody`s or `Response`s,
    # pass in a list of `pyopenapi3.objects.MediaType` objects, e.g.
    # `content=[JSONMediaType(...), XMLMediaType(...)]`, where each
    # `MediaType` object takes a schema. A simple schema such as `String`
    # can be used, or for more complex schemas use `create_schema()`.
    # For more information on media types, see:
    # https://swagger.io/docs/specification/media-types/

    # In `get_responses` below, a `pyopenapi3.data_types.Array` is used
    # as the schema for a `JSONMediaType` object.
    # There are three arrays in `pyopenapi3`:
    #   * SingleArray => Array[String]; defines an array of strings:
    #         {
    #             'type': 'array',
    #             'items': {'type': 'string'}
    #         }
    #   * MixedTypeArray => Array[String, Integer]; defines a Mixed-Type Array:
    #         {
    #             'type': 'array',
    #             'items': {
    #                 'oneOf': [
    #                     {'type': 'string'},
    #                     {'type: 'integer'}
    #                 ]
    #             }
    #         }
    #   * AnyTypeArray => Array[...]; defines an array of arbitrary types:
    #         {
    #             'type': 'array',
    #             'items': {}
    #         }

    get_responses = [  # responses for get operation
        Response(
            status=200,
            description="Return pets",
            content=[JSONMediaType(Array[Pet])]
        )
    ]

    # Add operation level attrs using `OpenApiBuilder().paths.op`
    # decorator, such as `tags`, `operation_id`, `summary`.
    @paths.op(tags=["Pets"], operation_id="app.get")
    def get(self) -> Op[..., get_responses]:
        """Get a single pet."""

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


if __name__ == '__main__':
    with open('example.json', 'w') as f:
        f.write(open_.json(indent=2))

    with open('example.yaml', 'w') as q:
        q.write(open_.yaml())

```

#### JSON output

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Title for example",
    "version": "0.1",
    "description": "Description for example."
  },
  "servers": [
    {
      "url": "/",
      "description": "Default server"
    }
  ],
  "paths": {
    "/pets/{pet_id}": {
      "get": {
        "tags": [
          "Pets"
        ],
        "description": "Get a single pet.",
        "operationId": "app.get",
        "responses": {
          "200": {
            "description": "Return pets",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": {
                    "$ref": "#/components/schemas/Pet"
                  }
                }
              }
            }
          }
        }
      },
      "put": {
        "tags": [
          "Pets"
        ],
        "description": "Create or update a pet",
        "operationId": "app.put_get",
        "responses": {
          "201": {
            "description": "New pet created"
          },
          "200": {
            "description": "Pet updated"
          }
        },
        "requestBody": {
          "description": "Request body required for PUT op. OpenAPI3 uses Request body instead of body parameters.",
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/Pet"
              }
            }
          },
          "required": true
        }
      },
      "parameters": [
        {
          "$ref": "#/components/parameters/PetId"
        }
      ]
    }
  },
  "components": {
    "schemas": {
      "Pet": {
        "required": [
          "name"
        ],
        "type": "object",
        "properties": {
          "name": {
            "maxLength": 100,
            "minLength": 1,
            "type": "string",
            "description": "Pet's name",
            "example": "Susie"
          },
          "tags": {
            "type": "object",
            "description": "Custom tags"
          },
          "id": {
            "type": "string",
            "description": "Unique identifier",
            "readOnly": true,
            "example": "123"
          },
          "created": {
            "type": "string",
            "description": "Creation time",
            "format": "date-time",
            "readOnly": true,
            "example": "2020-07-07T15:49:51.230+02:00"
          }
        }
      }
    },
    "parameters": {
      "PetId": {
        "name": "pet_id",
        "in": "path",
        "description": "Pet's Unique Identifier",
        "required": true,
        "schema": {
          "pattern": "^[a-zA-Z0-9-]+$",
          "type": "string"
        }
      }
    }
  }
}
```

#### YAML output

```yaml
openapi: 3.0.0
info:
  title: Title for example
  version: '0.1'
  description: Description for example.
servers:
- url: /
  description: Default server
paths:
  /pets/{pet_id}:
    get:
      tags:
      - Pets
      description: Get a single pet.
      operationId: app.get
      responses:
        '200':
          description: Return pets
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Pet'
    put:
      tags:
      - Pets
      description: Create or update a pet
      operationId: app.put_get
      responses:
        '201':
          description: New pet created
        '200':
          description: Pet updated
      requestBody:
        description: Request body required for PUT op. OpenAPI3 uses Request body
          instead of body parameters.
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Pet'
        required: true
    parameters:
    - $ref: '#/components/parameters/PetId'
components:
  schemas:
    Pet:
      required:
      - name
      type: object
      properties:
        name:
          maxLength: 100
          minLength: 1
          type: string
          description: Pet's name
          example: Susie
        tags:
          type: object
          description: Custom tags
        id:
          type: string
          description: Unique identifier
          readOnly: true
          example: '123'
        created:
          type: string
          description: Creation time
          format: date-time
          readOnly: true
          example: '2020-07-07T15:49:51.230+02:00'
  parameters:
    PetId:
      name: pet_id
      in: path
      description: Pet's Unique Identifier
      required: true
      schema:
        pattern: ^[a-zA-Z0-9-]+$
        type: string
```

## Connexion example

To run the `connexion` example, clone the repo, create and source a virtual
environment, and run the following `make` command:

```bash
>>> make connexion-example
```

This will install `pyopenapi3`, `connexion`, and any other required pacakge
and run a `gevent` server with `Flask` at `localhost:8080`.
