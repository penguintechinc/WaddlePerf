"""Authentication routes for WaddlePerf Unified API"""
from quart import Blueprint, request, jsonify, current_app
from functools import wraps
import jwt
from typing import Optional, Tuple
from penguin_libs.validation import IsStrongPassword
from services.auth_service import AuthService

_password_validator = IsStrongPassword(min_length=8)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


def _get_auth_service() -> AuthService:
    """Get AuthService instance from app context"""
    return current_app.auth_service


def _get_bearer_token(headers: dict) -> Optional[str]:
    """Extract bearer token from Authorization header

    Args:
        headers: Request headers dictionary

    Returns:
        Token string or None
    """
    auth_header = headers.get('Authorization', '')
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == 'bearer':
        return parts[1]
    return None


def _verify_token(f):
    """Decorator to verify JWT token from Authorization header

    Args:
        f: Route handler function

    Returns:
        Wrapped function with token verification
    """
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        token = _get_bearer_token(request.headers)
        if not token:
            return jsonify({'error': 'Missing authorization token'}), 401

        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET'],
                algorithms=['HS256']
            )
            if payload.get('token_type') != 'access':
                return jsonify({'error': 'Invalid token type'}), 401
            # Add user_id to kwargs
            kwargs['user_id'] = payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except (jwt.InvalidTokenError, jwt.DecodeError):
            return jsonify({'error': 'Invalid token'}), 401

        return await f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['POST'])
async def login():
    """Authenticate user with email/username and password

    Request body:
        {
            "email": "user@example.com",  // or "username": "user"
            "password": "password123",
            "mfa_token": "123456" (optional)
        }

    Returns:
        {
            "success": true,
            "access_token": "jwt_token",
            "refresh_token": "jwt_token",
            "user_id": 1,
            "mfa_required": false
        }
    """
    try:
        data = await request.get_json()
        # Support both email and username fields for flexibility
        email = data.get('email', '').strip() or data.get('username', '').strip()
        password = data.get('password', '')
        mfa_token = data.get('mfa_token')

        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400

        auth_service = _get_auth_service()
        result = await auth_service.authenticate(email, password, mfa_token)

        if not result.success:
            status_code = 401 if not result.mfa_required else 403
            return jsonify({
                'error': result.error,
                'mfa_required': result.mfa_required
            }), status_code

        return jsonify({
            'success': True,
            'access_token': result.access_token,
            'refresh_token': result.refresh_token,
            'user_id': result.user_id
        }), 200
    except Exception as e:
        return jsonify({'error': f'Login error: {str(e)}'}), 500


@auth_bp.route('/refresh', methods=['POST'])
async def refresh_token():
    """Refresh access token using refresh token

    Request body:
        {
            "refresh_token": "jwt_refresh_token"
        }

    Returns:
        {
            "success": true,
            "access_token": "new_jwt_token",
            "user_id": 1
        }
    """
    try:
        data = await request.get_json()
        refresh_token = data.get('refresh_token', '').strip()

        if not refresh_token:
            return jsonify({'error': 'Refresh token required'}), 400

        auth_service = _get_auth_service()
        result = await auth_service.refresh_access_token(refresh_token)

        if not result.success:
            return jsonify({'error': result.error}), 401

        return jsonify({
            'success': True,
            'access_token': result.access_token,
            'user_id': result.user_id
        }), 200
    except Exception as e:
        return jsonify({'error': f'Token refresh error: {str(e)}'}), 500


@auth_bp.route('/logout', methods=['POST'])
@_verify_token
async def logout(user_id: int):
    """Revoke all tokens for authenticated user

    Returns:
        {
            "success": true
        }
    """
    try:
        auth_service = _get_auth_service()
        result = await auth_service.revoke_tokens(user_id)

        if not result.success:
            return jsonify({'error': result.error}), 500

        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': f'Logout error: {str(e)}'}), 500


@auth_bp.route('/forgot-password', methods=['POST'])
async def forgot_password():
    """Send password reset email to user

    Request body:
        {
            "email": "user@example.com"
        }

    Returns:
        {
            "success": true,
            "message": "Password reset email sent"
        }
    """
    try:
        data = await request.get_json()
        email = data.get('email', '').strip()

        if not email:
            return jsonify({'error': 'Email required'}), 400

        auth_service = _get_auth_service()
        result = await auth_service.send_password_reset_email(email)

        if not result.success:
            return jsonify({'error': result.error}), 500

        return jsonify({
            'success': True,
            'message': 'Password reset email sent'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Forgot password error: {str(e)}'}), 500


@auth_bp.route('/reset-password', methods=['POST'])
async def reset_password():
    """Reset password using reset token

    Request body:
        {
            "token": "reset_token",
            "new_password": "newpassword123"
        }

    Returns:
        {
            "success": true,
            "message": "Password reset successful"
        }
    """
    try:
        data = await request.get_json()
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '')

        if not token or not new_password:
            return jsonify({'error': 'Token and new_password required'}), 400

        password_result = _password_validator(new_password)
        if not password_result.is_valid:
            return jsonify({'error': password_result.error}), 400

        auth_service = _get_auth_service()
        result = await auth_service.reset_password(token, new_password)

        if not result.success:
            return jsonify({'error': result.error}), 400

        return jsonify({
            'success': True,
            'message': 'Password reset successful'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Reset password error: {str(e)}'}), 500


@auth_bp.route('/change-password', methods=['POST'])
@_verify_token
async def change_password(user_id: int):
    """Change password for authenticated user

    Request body:
        {
            "current_password": "oldpassword123",
            "new_password": "newpassword123"
        }

    Returns:
        {
            "success": true,
            "message": "Password changed successfully"
        }
    """
    try:
        data = await request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')

        if not current_password or not new_password:
            return jsonify({
                'error': 'Current and new passwords required'
            }), 400

        password_result = _password_validator(new_password)
        if not password_result.is_valid:
            return jsonify({'error': password_result.error}), 400

        auth_service = _get_auth_service()
        result = await auth_service.change_password(
            user_id,
            current_password,
            new_password
        )

        if not result.success:
            return jsonify({'error': result.error}), 400

        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'error': f'Change password error: {str(e)}'
        }), 500


@auth_bp.route('/mfa/setup', methods=['POST'])
@_verify_token
async def setup_mfa(user_id: int):
    """Generate MFA secret and QR code for user

    Returns:
        {
            "success": true,
            "mfa_secret": "base32_secret",
            "mfa_qr_code": "base64_png_data"
        }
    """
    try:
        auth_service = _get_auth_service()
        result = await auth_service.setup_mfa(user_id)

        if not result.success:
            return jsonify({'error': result.error}), 500

        return jsonify({
            'success': True,
            'mfa_secret': result.mfa_secret,
            'mfa_qr_code': result.mfa_qr_code
        }), 200
    except Exception as e:
        return jsonify({'error': f'MFA setup error: {str(e)}'}), 500


@auth_bp.route('/mfa/verify', methods=['POST'])
@_verify_token
async def verify_mfa(user_id: int):
    """Verify and enable MFA for user

    Request body:
        {
            "mfa_secret": "base32_secret",
            "mfa_token": "123456"
        }

    Returns:
        {
            "success": true,
            "message": "MFA enabled successfully"
        }
    """
    try:
        data = await request.get_json()
        mfa_secret = data.get('mfa_secret', '').strip()
        mfa_token = data.get('mfa_token', '').strip()

        if not mfa_secret or not mfa_token:
            return jsonify({
                'error': 'MFA secret and token required'
            }), 400

        auth_service = _get_auth_service()
        result = await auth_service.verify_and_enable_mfa(
            user_id,
            mfa_secret,
            mfa_token
        )

        if not result.success:
            return jsonify({'error': result.error}), 400

        return jsonify({
            'success': True,
            'message': 'MFA enabled successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': f'MFA verification error: {str(e)}'}), 500


@auth_bp.route('/status', methods=['GET'])
async def auth_status():
    """Check authentication status of current user

    Returns authenticated: true with user info if valid token present,
    otherwise returns authenticated: false.

    Returns:
        {
            "authenticated": true/false,
            "auth_enabled": true,
            "user": {
                "id": 1,
                "username": "user",
                "email": "user@example.com",
                "role": "user"
            }
        }
    """
    try:
        token = _get_bearer_token(request.headers)
        if not token:
            return jsonify({
                'authenticated': False,
                'auth_enabled': True
            }), 200

        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET'],
                algorithms=['HS256']
            )
            if payload.get('token_type') != 'access':
                return jsonify({
                    'authenticated': False,
                    'auth_enabled': True
                }), 200

            user_id = payload.get('user_id')
            auth_service = _get_auth_service()
            user = await auth_service.get_user_by_id(user_id)

            if not user:
                return jsonify({
                    'authenticated': False,
                    'auth_enabled': True
                }), 200

            return jsonify({
                'authenticated': True,
                'auth_enabled': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            }), 200

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.DecodeError):
            return jsonify({
                'authenticated': False,
                'auth_enabled': True
            }), 200

    except Exception as e:
        return jsonify({
            'authenticated': False,
            'auth_enabled': True,
            'error': str(e)
        }), 200


@auth_bp.route('/mfa/disable', methods=['POST'])
@_verify_token
async def disable_mfa(user_id: int):
    """Disable MFA for user

    Request body:
        {
            "password": "user_password"
        }

    Returns:
        {
            "success": true,
            "message": "MFA disabled successfully"
        }
    """
    try:
        data = await request.get_json()
        password = data.get('password', '')

        if not password:
            return jsonify({'error': 'Password required'}), 400

        auth_service = _get_auth_service()
        result = await auth_service.disable_mfa(user_id, password)

        if not result.success:
            return jsonify({'error': result.error}), 400

        return jsonify({
            'success': True,
            'message': 'MFA disabled successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': f'MFA disable error: {str(e)}'}), 500
