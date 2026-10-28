"""Write the OpenAPI schema to stdout without starting the server."""

import json

from app.main import app

print(json.dumps(app.openapi(), indent=2))
