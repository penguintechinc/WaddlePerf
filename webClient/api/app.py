"""
WaddlePerf webClient API - Flask backend with WebSocket support
Proxies test requests to testServer and handles authentication with managerServer
"""

import os
import logging
import secrets
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
import requests
import pymysql
from pymysql.cursors import DictCursor
import bcrypt
import jwt
from penguintechinc_utils.logging import get_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Enable CORS for React frontend
CORS(app, supports_credentials=True, origins=os.getenv('FRONTEND_URL', 'http://localhost:3000').split(','))

# Initialize SocketIO with CORS support
socketio = SocketIO(
    app,
    cors_allowed_origins=os.getenv('FRONTEND_URL', 'http://localhost:3000').split(','),
    cors_credentials=True
)

# Configuration
MANAGER_URL = os.getenv('MANAGER_URL', 'http://localhost:5001')
TESTSERVER_URL = os.getenv('TESTSERVER_URL', 'http://localhost:8080')
AUTH_ENABLED = os.getenv('AUTH_ENABLED', 'true').lower() == 'true'

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'waddleperf'),
    'password': os.getenv('DB_PASS', 'waddleperf'),
    'database': os.getenv('DB_NAME', 'waddleperf'),
    'cursorclass': DictCursor,
    'autocommit': True
}


@dataclass
class User:
    """User data class"""
    id: int
    username: str
    email: str
    api_key: str
    role: str
    ou_id: Optional[int] = None


def get_db_connection():
    """Get database connection"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


def validate_session(session_id: str) -> Optional[User]:
    """Validate session against database"""
    if not AUTH_ENABLED:
        return None

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.user_id, s.data, s.expires_at, u.username, u.email, u.api_key, u.role, u.ou_id
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_id = %s AND s.expires_at > NOW()
            """, (session_id,))
            result = cursor.fetchone()

            if result:
                return User(
                    id=result['user_id'],
                    username=result['username'],
                    email=result['email'],
                    api_key=result['api_key'],
                    role=result['role'],
                    ou_id=result['ou_id']
                )
    except Exception as e:
        logger.error(f"Session validation error: {e}")
    finally:
        if conn:
            conn.close()

    return None


def validate_api_key(api_key: str) -> Optional[User]:
    """Validate API key against database"""
    if not AUTH_ENABLED:
        return None

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email, api_key, role, ou_id
                FROM users
                WHERE api_key = %s AND is_active = TRUE
            """, (api_key,))
            result = cursor.fetchone()

            if result:
                return User(
                    id=result['id'],
                    username=result['username'],
                    email=result['email'],
                    api_key=result['api_key'],
                    role=result['role'],
                    ou_id=result['ou_id']
                )
    except Exception as e:
        logger.error(f"API key validation error: {e}")
    finally:
        if conn:
            conn.close()

    return None


def get_authenticated_user() -> Optional[User]:
    """Get authenticated user from session or API key"""
    if not AUTH_ENABLED:
        return None

    # Check session
    session_id = session.get('session_id')
    if session_id:
        user = validate_session(session_id)
        if user:
            return user

    # Check API key in Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        api_key = auth_header[7:]
        user = validate_api_key(api_key)
        if user:
            return user

    return None


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Check database connectivity
        conn = get_db_connection()
        conn.close()
        db_status = 'healthy'
    except Exception as e:
        logger.error(f"Health check DB error: {e}")
        db_status = 'unhealthy'

    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'database': db_status,
        'auth_enabled': AUTH_ENABLED,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint - authenticates with managerServer"""
    if not AUTH_ENABLED:
        return jsonify({'error': 'Authentication disabled'}), 400

    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    conn = None
    try:
        # Validate credentials against database
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email, password_hash, api_key, role, ou_id
                FROM users
                WHERE username = %s AND is_active = TRUE
            """, (username,))
            user_data = cursor.fetchone()

        if not user_data:
            logger.warning(f"Login failed: user not found - {username}")
            return jsonify({'error': 'Invalid credentials'}), 401

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
            logger.warning(f"Login failed: invalid password - {username}")
            return jsonify({'error': 'Invalid credentials'}), 401

        # Create session
        session_id = secrets.token_hex(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)

        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sessions (session_id, user_id, expires_at)
                VALUES (%s, %s, %s)
            """, (session_id, user_data['id'], expires_at))

        session['session_id'] = session_id

        logger.info(f"User logged in: {username}")

        return jsonify({
            'success': True,
            'user': {
                'id': user_data['id'],
                'username': user_data['username'],
                'email': user_data['email'],
                'role': user_data['role']
            },
            'session_id': session_id
        })

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    if not AUTH_ENABLED:
        return jsonify({'error': 'Authentication disabled'}), 400

    session_id = session.get('session_id')
    if session_id:
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
            conn.close()
        except Exception as e:
            logger.error(f"Logout error: {e}")

    session.clear()
    return jsonify({'success': True})


@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    if not AUTH_ENABLED:
        return jsonify({'authenticated': False, 'auth_enabled': False})

    user = get_authenticated_user()
    if user:
        return jsonify({
            'authenticated': True,
            'auth_enabled': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        })

    return jsonify({'authenticated': False, 'auth_enabled': True})


def validate_test_params(data: Dict[str, Any], test_type: str) -> tuple[bool, Optional[str]]:
    """Validate test parameters with input sanitization"""
    target = data.get('target', '').strip()
    if not target:
        return False, 'Target host is required'

    # Basic hostname/IP validation
    if len(target) > 255:
        return False, 'Target host too long'

    # Validate port if provided
    port = data.get('port')
    if port is not None:
        try:
            port = int(port)
            if port < 1 or port > 65535:
                return False, 'Invalid port number'
        except (ValueError, TypeError):
            return False, 'Invalid port number'

    # Validate timeout
    timeout = data.get('timeout', 30)
    try:
        timeout = int(timeout)
        if timeout < 1 or timeout > 300:
            return False, 'Timeout must be between 1 and 300 seconds'
    except (ValueError, TypeError):
        return False, 'Invalid timeout value'

    # Validate count
    count = data.get('count', 10)
    try:
        count = int(count)
        if count < 1 or count > 1000:
            return False, 'Count must be between 1 and 1000'
    except (ValueError, TypeError):
        return False, 'Invalid count value'

    return True, None


@app.route('/api/test/<test_type>', methods=['POST'])
def run_test(test_type: str):
    """Proxy test request to testServer"""
    if test_type not in ['http', 'tcp', 'udp', 'icmp', 'http_trace', 'tcp_trace', 'udp_trace', 'traceroute']:
        return jsonify({'error': 'Invalid test type'}), 400

    # Check authentication if enabled
    user = None
    if AUTH_ENABLED:
        user = get_authenticated_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json()

    # Validate parameters
    valid, error = validate_test_params(data, test_type)
    if not valid:
        return jsonify({'error': error}), 400

    try:
        # Prepare test request
        test_request = {
            'test_type': test_type,
            'target': data.get('target'),
            'port': data.get('port'),
            'timeout': data.get('timeout', 30),
            'count': data.get('count', 10),
            'protocol_detail': data.get('protocol_detail'),
            'device_serial': data.get('device_serial', 'webclient-' + secrets.token_hex(4)),
            'device_hostname': data.get('device_hostname', 'webclient'),
            'device_os': 'Browser',
            'device_os_version': request.headers.get('User-Agent', 'Unknown')[:100]
        }

        headers = {}
        if user:
            headers['Authorization'] = f'ApiKey {user.api_key}'

        # Forward to testServer
        response = requests.post(
            f'{TESTSERVER_URL}/api/v1/test/{test_type}',
            json=test_request,
            headers=headers,
            timeout=data.get('timeout', 30) + 10
        )

        if response.status_code == 200:
            logger.info(f"Test completed: {test_type} to {data.get('target')}")
            return jsonify(response.json())
        else:
            logger.error(f"Test failed: {response.status_code} - {response.text}")
            return jsonify({'error': 'Test execution failed', 'details': response.text}), response.status_code

    except requests.exceptions.RequestException as e:
        logger.error(f"Test server communication error: {e}")
        return jsonify({'error': 'Failed to communicate with test server'}), 503
    except Exception as e:
        logger.error(f"Test execution error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@socketio.on('connect')  # pragma: no cover
def handle_connect():  # pragma: no cover
    """Handle WebSocket connection"""  # pragma: no cover
    logger.info(f"WebSocket client connected: {request.sid}")  # pragma: no cover
    emit('connected', {'status': 'connected'})  # pragma: no cover


@socketio.on('disconnect')  # pragma: no cover
def handle_disconnect():  # pragma: no cover
    """Handle WebSocket disconnection"""  # pragma: no cover
    logger.info(f"WebSocket client disconnected: {request.sid}")  # pragma: no cover


@socketio.on('start_test')  # pragma: no cover
def handle_start_test(data):  # pragma: no cover
    """Handle test execution via WebSocket for real-time updates"""  # pragma: no cover
    test_type = data.get('test_type')  # pragma: no cover

    if test_type not in ['http', 'tcp', 'udp', 'icmp', 'http_trace', 'tcp_trace', 'udp_trace', 'traceroute']:  # pragma: no cover
        emit('error', {'error': 'Invalid test type'})  # pragma: no cover
        return  # pragma: no cover

    # Check authentication if enabled
    user = None  # pragma: no cover
    if AUTH_ENABLED:  # pragma: no cover
        session_id = data.get('session_id')  # pragma: no cover
        api_key = data.get('api_key')  # pragma: no cover

        if session_id:  # pragma: no cover
            user = validate_session(session_id)  # pragma: no cover
        elif api_key:  # pragma: no cover
            user = validate_api_key(api_key)  # pragma: no cover

        if not user:  # pragma: no cover
            emit('error', {'error': 'Authentication required', 'status': 401})  # pragma: no cover
            return  # pragma: no cover

    # Validate parameters
    valid, error = validate_test_params(data, test_type)  # pragma: no cover
    if not valid:  # pragma: no cover
        emit('error', {'error': error})  # pragma: no cover
        return  # pragma: no cover

    try:  # pragma: no cover
        emit('test_started', {'status': 'started', 'test_type': test_type})  # pragma: no cover

        # Prepare test request
        test_request = {  # pragma: no cover
            'test_type': test_type,  # pragma: no cover
            'target': data.get('target'),  # pragma: no cover
            'port': data.get('port'),  # pragma: no cover
            'timeout': data.get('timeout', 30),  # pragma: no cover
            'count': data.get('count', 10),  # pragma: no cover
            'protocol_detail': data.get('protocol_detail'),  # pragma: no cover
            'device_serial': data.get('device_serial', 'webclient-' + secrets.token_hex(4)),  # pragma: no cover
            'device_hostname': data.get('device_hostname', 'webclient'),  # pragma: no cover
            'device_os': 'Browser',  # pragma: no cover
            'device_os_version': 'WebSocket Client'  # pragma: no cover
        }  # pragma: no cover

        headers = {}  # pragma: no cover
        if user:  # pragma: no cover
            headers['Authorization'] = f'ApiKey {user.api_key}'  # pragma: no cover
            logger.info(f"WebSocket test: Authenticated as user {user.username} (ID: {user.id})")  # pragma: no cover
        else:  # pragma: no cover
            logger.warning("WebSocket test: No authentication (AUTH_ENABLED=False)")  # pragma: no cover

        # Execute test and stream results
        logger.info(f"Sending test request to testServer: {TESTSERVER_URL}/api/v1/test/{test_type}")  # pragma: no cover
        response = requests.post(  # pragma: no cover
            f'{TESTSERVER_URL}/api/v1/test/{test_type}',  # pragma: no cover
            json=test_request,  # pragma: no cover
            headers=headers,  # pragma: no cover
            timeout=data.get('timeout', 30) + 10,  # pragma: no cover
            stream=True  # pragma: no cover
        )  # pragma: no cover

        logger.info(f"testServer response: {response.status_code}")  # pragma: no cover
        if response.status_code == 200:  # pragma: no cover
            # Try to parse as streaming JSON or return complete result
            try:  # pragma: no cover
                result = response.json()  # pragma: no cover

                # Simulate streaming for better UX if we got complete result
                if isinstance(result, dict):  # pragma: no cover
                    # Send progress updates
                    count = data.get('count', 10)  # pragma: no cover
                    for i in range(count):  # pragma: no cover
                        emit('test_progress', {  # pragma: no cover
                            'progress': (i + 1) / count * 100,  # pragma: no cover
                            'current_index': i + 1,  # pragma: no cover
                            'total': count  # pragma: no cover
                        })  # pragma: no cover
                        socketio.sleep(0.1)  # pragma: no cover

                    emit('test_complete', result)  # pragma: no cover
                else:  # pragma: no cover
                    emit('test_complete', result)  # pragma: no cover

            except Exception as e:  # pragma: no cover
                logger.error(f"Error parsing test result: {e}")  # pragma: no cover
                emit('error', {'error': 'Failed to parse test results'})  # pragma: no cover
        else:  # pragma: no cover
            logger.error(f"testServer returned {response.status_code}: {response.text[:200]}")  # pragma: no cover
            emit('error', {'error': 'Test execution failed', 'status': response.status_code})  # pragma: no cover

    except requests.exceptions.RequestException as e:  # pragma: no cover
        logger.error(f"Test server communication error: {e}")  # pragma: no cover
        emit('error', {'error': 'Failed to communicate with test server'})  # pragma: no cover
    except Exception as e:  # pragma: no cover
        logger.error(f"WebSocket test error: {e}")  # pragma: no cover
        emit('error', {'error': 'Internal server error'})  # pragma: no cover


if __name__ == '__main__':  # pragma: no cover
    logger.info(f"Starting webClient API server")  # pragma: no cover
    logger.info(f"Auth enabled: {AUTH_ENABLED}")  # pragma: no cover
    logger.info(f"Manager URL: {MANAGER_URL}")  # pragma: no cover
    logger.info(f"TestServer URL: {TESTSERVER_URL}")  # pragma: no cover

    socketio.run(app, host='0.0.0.0', port=5000, debug=os.getenv('DEBUG', 'false').lower() == 'true')  # pragma: no cover
