from .app import app

import main.routes
import main.api_routes

# Register API routes
main.api_routes.register_api_routes(app)