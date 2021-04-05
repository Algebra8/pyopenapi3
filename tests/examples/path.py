path = {
  "/pets": {
    "get": {
      "description": "Returns all pets from the system that the user has access to",
      "responses": {
        "200": {
          "description": "A list of pets.",
          "content": {
            "application/json": {
              "schema": {
                "type": "array",
                "items": {
                  "$ref": "#/components/schemas/pet"
                }
              }
            }
          }
        }
      }
    }
  }
}

global_path_with_reference_parameter = {
  'parameters': [
    {'$ref': '#/components/parameters/PetID'}
  ]
}

global_path_with_schema_parameter = {
  'parameters': [
    {
      'name': 'pet_name',
      'in': 'path',
      'required': True,
      'schema': {'type': 'string'}
    }
  ]
}
