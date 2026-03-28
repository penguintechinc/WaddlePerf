"""Authentication routes for managerServer API"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import jwt
import hashlib
import pyotp
from models import row_to_user, row_to_jwt_token, hash_password
from config import Config
from penguin_dal.flask_ext import get_db

auth_bp = Blueprint('auth', __name__)
cfg = Config()


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login with username/password, returns JWT token"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    mfa_code = data.get('mfa_code')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    db = get_db()
    user_row = db(
        (db.users.username == username) & (db.users.is_active == True)
    ).select().first()

    if not user_row:
        return jsonify({'error': 'Invalid credentials'}), 401

    user = row_to_user(user_row)
    if not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Check MFA if enabled
    if user.mfa_enabled:
        if not mfa_code:
            return jsonify({'error': 'MFA code required', 'mfa_required': True}), 401

        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(mfa_code):
            return jsonify({'error': 'Invalid MFA code'}), 401

    # Generate JWT
    token = generate_jwt(user.id)

    # Store token hash in database
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db.jwt_tokens.insert(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + cfg.JWT_EXPIRATION,
        issued_at=datetime.utcnow(),
        revoked=False,
    )

    return jsonify({
        'token': token,
        'user': user.to_dict(include_sensitive=True),
        'expires_in': int(cfg.JWT_EXPIRATION.total_seconds())
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Revoke JWT token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Invalid authorization header'}), 401

    token = auth_header.split(' ')[1]
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    db = get_db()
    db(db.jwt_tokens.token_hash == token_hash).update(revoked=True)

    return jsonify({'message': 'Logged out successfully'})


@auth_bp.route('/mfa/setup', methods=['POST'])
def mfa_setup():
    """Setup MFA for current user"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    user_row = db.users[user_id]
    if not user_row:
        return jsonify({'error': 'User not found'}), 404

    user = row_to_user(user_row)

    # Generate MFA secret
    secret = pyotp.random_base32()
    db(db.users.id == user_id).update(mfa_secret=secret, mfa_enabled=False)

    # Generate QR code URI
    totp = pyotp.TOTP(secret)
    qr_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name=cfg.MFA_ISSUER
    )

    return jsonify({
        'secret': secret,
        'qr_uri': qr_uri
    })


@auth_bp.route('/mfa/verify', methods=['POST'])
def mfa_verify():
    """Verify and enable MFA"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    code = data.get('code')

    if not code:
        return jsonify({'error': 'MFA code required'}), 400

    db = get_db()
    user_row = db.users[user_id]
    if not user_row or not user_row.mfa_secret:
        return jsonify({'error': 'MFA not set up'}), 400

    totp = pyotp.TOTP(user_row.mfa_secret)
    if not totp.verify(code):
        return jsonify({'error': 'Invalid MFA code'}), 401

    db(db.users.id == user_id).update(mfa_enabled=True)

    return jsonify({'message': 'MFA enabled successfully'})


def generate_jwt(user_id: int) -> str:
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + cfg.JWT_EXPIRATION,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, cfg.JWT_SECRET, algorithm='HS256')


def get_user_from_token():
    """Extract user ID from JWT token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(token, cfg.JWT_SECRET, algorithms=['HS256'])

        # Check if token is revoked
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        db = get_db()
        jwt_row = db(
            (db.jwt_tokens.token_hash == token_hash) & (db.jwt_tokens.revoked == False)
        ).select().first()

        if not jwt_row:
            return None

        return payload.get('user_id')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
