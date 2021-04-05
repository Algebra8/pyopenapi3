component = {
  "components": {
    "schemas": {
      "GeneralError": {
        "type": "object",
        "properties": {
          "code": {
            "type": "integer",
            "format": "int32"
          },
          "message": {
            "type": "string"
          }
        }
      },
      "Category": {
        "type": "object",
        "properties": {
          "id": {
            "type": "integer",
            "format": "int64"
          },
          "name": {
            "type": "string"
          }
        }
      },
      "Tag": {
        "type": "object",
        "properties": {
          "id": {
            "type": "integer",
            "format": "int64"
          },
          "name": {
            "type": "string"
          }
        }
      }
    },
    "parameters": {
      "skipParam": {
        "name": "skip",
        "in": "query",
        "description": "number of items to skip",
        "required": True,
        "schema": {
          "type": "integer",
          "format": "int32"
        }
      },
      "limitParam": {
        "name": "limit",
        "in": "query",
        "description": "max records to return",
        "required": True,
        "schema": {
          "type": "integer",
          "format": "int32"
        }
      }
    },
    "responses": {
      "NotFound": {
        "description": "Entity not found."
      },
      "IllegalInput": {
        "description": "Illegal input for operation."
      },
      "GeneralError": {
        "description": "General Error",
        "content": {
          "application/json": {
            "schema": {
              "$ref": "#/components/schemas/GeneralError"
            }
          }
        }
      }
    },
    "securitySchemes": {
      "api_key": {
        "type": "apiKey",
        "name": "api_key",
        "in": "header"
      },
      "petstore_auth": {
        "type": "oauth2",
        "flows": {
          "implicit": {
            "authorizationUrl": "http://example.org/api/oauth/dialog",
            "scopes": {
              "write:pets": "modify pets in your account",
              "read:pets": "read your pets"
            }
          }
        }
      }
    }
  }
}

object_lvl_test = {
  "schemas": {
    "Pet": {
      "required": [
        "name",
        "animal_type",
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
        "animal_type": {
          "minLength": 1,
          "type": "string",
          "description": "Kind of animal",
          "example": "cat"
        }
      }
    }
  }
}

param_reference_comp = {
  "schemas": {
    "Pet": {
      "type": "object",
      "properties": {
        "pet_id": {
          "$ref": "#/components/parameters/PetId"
        }
      }
    }
  },
  "parameters": {
    "PetId": {
      "name": "pet_id",
      "in": "path",
      "description": "Pet's Unique Identifier",
      "schema": {
        "pattern": "^[a-zA-Z0-9-]+$",
        "type": "string"
      }
    }
  }
}

param_component = {
  "parameters": {
    "PetID": {
      "name": "pet_id",
      "in": "path",
      "description": "Pet's Unique identifier",
      "required": True,
      "schema": {
        "pattern": "^[a-zA-Z0-9-]+$",
        "type": "string"
      }
    }
  }
}
