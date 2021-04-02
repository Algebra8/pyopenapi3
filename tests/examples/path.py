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

path_with_parameter = {
  'parameters': [
    {
      'name': 'pet_id', 
      'in': 'path', 
      'required': True, 
      'schema': {'$ref': '#/components/schemas/PetID'}
    }
  ]
}
