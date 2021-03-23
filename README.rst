``pyopenapi3`` converts Python objects to the
`OpenAPI 3 Specification <https://swagger.io/specification/>`_. It can be
used to easily manage your API descriptions, particularly when using packages
such as `connexion <https://connexion.readthedocs.io/en/latest/>`_. Take a peak at what can be done
with the example below. More exhaustive examples can be found in
`pyopenapi3/examples <https://github.com/Algebra8/pyopenapi3/tree/main/src/pyopenapi3/examples>`_.

.. warning::

    Please note that this package is still in an experimental stage. Some features
    may not be complete.

.. code-block::

    # Brief example for `pyopenapi3`.

    from pyopenapi3 import OpenApiBuilder

    open_bldr = OpenApiBuilder()

    @open_bldr.info
    class Info:

        title = "Pet store api."
        version = "0.0.1"
        description = "A store for buying pets online."

    @open_bldr.path
    class Path1:

        path = '/users/{id:Int64}'

        responses = [
            Response(status=200, description="ok"),
            Response(status=404, description="not found")
        ]
        request_body = RequestBody(
            description="A request body",
            content=[JSONMediaType(Int64)]
        )

        @open_bldr.path.op(summary="Some summary for the get")
        @open_bldr.path.query_param(name='email', schema=Email, required=True)
        def get(self) -> Op[..., responses]:
            """Get request for path."""


    component = open_bldr.component


    @component.schema
    class Customer:
        """A store's customer"""

        @component.schema_field(read_only=True)
        def id(self) -> Int64:
            """Unique identifier for the customer"""

        @component.schema_field(read_only=True, example="some_user@gmail.com")
        def email(self) -> Email:
            """Customer's email address"""

        @component.schema_field(read_only=True, example="Mike")
        def firstName(self) -> String:
            """Customer's first name"""

        @component.schema_field(read_only=True, example="Cat")
        def lastName(self) -> String:
            """Customer's last name"""

    @component.schema
    class Store:
        """A store for buying things"""

        @component.schema_field(read_only=True)
        def id(self) -> Int64:
            """Store's unique identification number"""

        @component.schema_field
        def customer(self) -> Customer:
            """The store's customer"""

        @component.schema_field
        def someArray(self) -> Array[Customer, Int32]:
            """Just some array that can accept one of Customer or Int32"""

        @component.schema_field
        def anyArray(self) -> Array[...]:
            """An array that accepts anything"""

    open_bldr.json(indent=2)

This will result in the following JSON file:

.. code-block::

    {
      "openapi": "3.0.0",
      "info": {
        "title": "Pet store api.",
        "version": "0.0.1",
        "description": "A store for buying pets online."
      },
      "servers": [
        {
          "url": "/",
          "description": "Default server"
        }
      ],
      "paths": {
        "/users/{id}": {
          "get": {
            "summary": "Some summary for the get",
            "description": "Get request for path.",
            "parameters": [
              {
                "name": "email",
                "in_field": "query",
                "required": true,
                "schema_field": {
                  "type": "string",
                  "format": "email"
                }
              }
            ],
            "responses": {
              "404": {
                "description": "not found"
              },
              "200": {
                "description": "ok"
              }
            }
          },
          "parameters": [
            {
              "name": "id",
              "in_field": "path",
              "required": true,
              "schema_field": {
                "type": "integer",
                "format": "int64"
              }
            }
          ]
        }
      },
      "components": {
        "schemas": {
          "Customer": {
            "type": "object",
            "properties": {
              "id": {
                "type": "integer",
                "description": "Unique identifier for the customer",
                "format": "int64",
                "read_only": true
              },
              "email": {
                "type": "string",
                "description": "Customer's email address",
                "format": "email",
                "read_only": true,
                "example": "some_user@gmail.com"
              },
              "firstName": {
                "type": "string",
                "description": "Customer's first name",
                "read_only": true,
                "example": "Mike"
              },
              "lastName": {
                "type": "string",
                "description": "Customer's last name",
                "read_only": true,
                "example": "Cat"
              }
            }
          },
          "Store": {
            "type": "object",
            "properties": {
              "id": {
                "type": "integer",
                "description": "Store's unique identification number",
                "format": "int64",
                "read_only": true
              },
              "someArray": {
                "type": "array",
                "items": {
                  "one_of": [
                    {
                      "ref": "#/components/schemas/Customer"
                    },
                    {
                      "type": "integer",
                      "format": "int32"
                    }
                  ]
                },
                "description": "Just some array that can accept one of Customer or Int32"
              },
              "anyArray": {
                "type": "array",
                "items": {},
                "description": "An array that accepts anything"
              },
              "customer": {
                "ref": "#/components/schemas/Customer"
              }
            }
          }
        }
      }
    }
