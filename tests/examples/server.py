

default_server = {
  'servers': [
    {
      'url': '/',
      'description': 'Default server'
    }
  ]
}

single_server = {
  "servers": [
    {
      "url": "https://development.gigantic-server.com/v1",
      "description": "Development server"
    }
  ]
}

multiple_servers = {
  "servers": [
    {
      "url": "https://development.gigantic-server.com/v1",
      "description": "Development server"
    },
    {
      "url": "https://staging.gigantic-server.com/v1",
      "description": "Staging server"
    },
    {
      "url": "https://api.gigantic-server.com/v1",
      "description": "Production server"
    }
  ]
}

server_with_vars = {
  "servers": [
    {
      "url": "https://{username}.gigantic-server.com:{port}/{basePath}",
      "description": "The production API server",
      "variables": {
        "username": {
          "default": "demo",
          "description": ("this value is assigned by the service provider, "
                          "in this example `gigantic-server.com`")
        },
        "port": {
          "enum": [
            "8443",
            "443"
          ],
          "default": "8443"
        },
        "basePath": {
          "default": "v2"
        }
      }
    }
  ]
}
