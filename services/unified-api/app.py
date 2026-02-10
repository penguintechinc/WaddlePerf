"""Main Quart application factory for WaddlePerf Unified API"""
import logging
import asyncio
from typing import Optional
from quart import Quart, jsonify, current_app
from quart_cors import cors
from pydal import DAL
from penguintechinc_utils.logging import get_logger

from config import Config
from database.schema import initialize_schema
from database.connection import get_dal, close_dal
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

    # Configure logging
    logging.basicConfig(level=config_obj.LOG_LEVEL)

    # Configure CORS
    cors_origins = [origin.strip() for origin in config_obj.CORS_ORIGINS.split(',')]
    cors(app, allow_origin=cors_origins)

    # Initialize database schema (SQLAlchemy - one-time creation)
    try:
        initialize_schema(config_obj)
    except Exception as e:
        logger.warning(f"Schema initialization warning (may already exist): {str(e)}")

    # Initialize PyDAL for runtime operations
    db = get_dal(config_obj)
    app.db = db
    app.config_obj = config_obj

    # Initialize services
    app.auth_service = AuthService(db, config_obj)

    # Store database instance for later access
    @app.before_serving
    async def setup_db():
        """Setup database connection on app startup"""
        logger.info("Database initialized on app startup")

    @app.after_serving
    async def cleanup_db():
        """Close database connection on app shutdown"""
        close_dal(app.db)
        logger.info("Database connection closed on app shutdown")

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
            # Check database connectivity
            health_row = app.db.executesql('SELECT 1')
            db_healthy = health_row is not None

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
