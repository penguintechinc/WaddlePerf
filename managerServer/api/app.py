"""Main Flask application for managerServer API"""
import logging
from flask import Flask
from flask_cors import CORS
from config import Config
from penguin_dal.flask_ext import init_dal


def create_app(config=None):
    """Application factory"""
    app = Flask(__name__)

    # Load configuration
    cfg = config or Config()
    app.config['SECRET_KEY'] = cfg.SECRET_KEY
    app.config['DATABASE_URL'] = cfg.DATABASE_URL

    # Setup logging
    logging.basicConfig(level=cfg.LOG_LEVEL.upper())

    # Initialize extensions
    init_dal(app, uri=cfg.DATABASE_URL)
    CORS(app, origins=cfg.CORS_ORIGINS)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.users import users_bp
    from routes.organizations import orgs_bp
    from routes.statistics import stats_bp
    from routes.results import results_bp
    from routes.config import config_bp
    from routes.enrollment import enrollment_bp
    from routes.devices import devices_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(orgs_bp, url_prefix='/api/v1/organizations')
    app.register_blueprint(stats_bp, url_prefix='/api/v1/statistics')
    app.register_blueprint(results_bp, url_prefix='/api/v1/results')
    app.register_blueprint(config_bp, url_prefix='/api/v1/config')
    app.register_blueprint(enrollment_bp, url_prefix='/api/v1/enrollment')
    app.register_blueprint(devices_bp, url_prefix='/api/v1')

    # Health check
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'version': cfg.API_VERSION}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
