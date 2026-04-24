"""Main Quart application factory for WaddlePerf Unified API"""
import logging
import asyncio
from typing import Optional
from quart import Quart, jsonify, current_app
from quart_cors import cors
from penguintechinc_utils.logging import get_logger

from config import Config
from database.connection import init_dal, get_db, build_db_uri
from routes import auth_bp, organizations_bp, devices_bp
from services.auth_service import AuthService

logger = get_logger(__name__)


def create_app(config_obj: Optional[Config] = None) -> Quart:
    """Create and configure the Quart application.

    Args:
        config_obj: Optional Config object. If None, creates a new Config instance.

    Returns:
        Configured Quart application instance
    """
    # Initialize configuration
    if config_obj is None:
        config_obj = Config()

    # Create Quart app instance
    app = Quart(__name__)

    # Load configuration
    app.config['SECRET_KEY'] = config_obj.SECRET_KEY
    app.config['DEBUG'] = config_obj.DEBUG
    app.config['ENV'] = config_obj.FLASK_ENV
    app.config['JWT_SECRET'] = config_obj.JWT_SECRET
    app.config['JWT_EXPIRATION_HOURS'] = config_obj.JWT_EXPIRATION_HOURS

    # Set DATABASE_URI for penguin-dal init_dal()
    app.config['DATABASE_URI'] = build_db_uri(config_obj)

    # Configure logging
    logging.basicConfig(level=config_obj.LOG_LEVEL)

    # Configure CORS
    cors_origins = [origin.strip() for origin in config_obj.CORS_ORIGINS.split(',')]
    cors(app, allow_origin=cors_origins)

    # Initialize penguin-dal (registers before_serving reflect + after_serving close)
    init_dal(app, pool_size=config_obj.DB_POOL_SIZE)

    # Store config for later access
    app.config_obj = config_obj

    @app.before_serving
    async def setup_services():
        """Initialize services after DB reflection is complete."""
        db = get_db()
        app.db = db
        app.auth_service = AuthService(db, config_obj)
        logger.info("Services initialized on app startup")

    # Register blueprints with API versioning
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(organizations_bp, url_prefix='/api/v1/orgs')
    app.register_blueprint(devices_bp, url_prefix='/api/v1/devices')

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    async def health_check():
        """Health check endpoint that verifies database connectivity.

        Returns:
            JSON response with health status and database health
        """
        try:
            db = get_db()
            # Check database connectivity via a simple count query
            from penguin_dal.query import AsyncQuerySet
            from sqlalchemy import text
            from sqlalchemy.ext.asyncio import AsyncSession

            async with db.engine.connect() as conn:
                await conn.execute(text('SELECT 1'))
            db_healthy = True

            return jsonify({
                'status': 'healthy' if db_healthy else 'unhealthy',
                'service': 'unified-api',
                'database': 'healthy' if db_healthy else 'unhealthy',
                'timestamp': __import__('datetime').datetime.utcnow().isoformat()
            }), 200 if db_healthy else 503

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                'status': 'unhealthy',
                'service': 'unified-api',
                'database': 'unhealthy',
                'error': str(e),
                'timestamp': __import__('datetime').datetime.utcnow().isoformat()
            }), 503

    # WebSocket route handler placeholder
    @app.websocket('/ws')
    async def websocket_handler(ws):
        """WebSocket connection handler.

        Handles WebSocket connections for real-time updates and communication.
        """
        try:
            while True:
                data = await ws.receive()
                # Echo received data back to client
                await ws.send(data)
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")

    # Error handlers
    @app.errorhandler(404)
    async def not_found(error):
        """Handle 404 Not Found errors"""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404

    @app.errorhandler(500)
    async def internal_error(error):
        """Handle 500 Internal Server errors"""
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500

    logger.info(f"Quart application created successfully (env={config_obj.FLASK_ENV})")

    return app


# Create module-level app instance for production deployment
app = create_app()


if __name__ == '__main__':
    # Create application instance for local development
    config = Config()
    dev_app = create_app(config)

    # Run with hypercorn
    import hypercorn.asyncio

    asyncio.run(
        hypercorn.asyncio.serve(
            dev_app,
            hypercorn.Config(
                bind=['0.0.0.0:5000'],
                workers=1,
                debug=config.DEBUG
            )
        )
    )
