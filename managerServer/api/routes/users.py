"""User management routes"""
from flask import Blueprint, request, jsonify
from models import row_to_user, hash_password, generate_api_key
from routes.auth import get_user_from_token
from penguin_dal.flask_ext import get_db

users_bp = Blueprint('users', __name__)


@users_bp.route('', methods=['GET'])
def list_users():
    """List all users (with pagination)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    db = get_db()
    offset = (page - 1) * per_page
    user_rows = db(db.users.id > 0).select(
        limitby=(offset, per_page),
        orderby=db.users.id,
    )
    total = db(db.users.id > 0).count()

    users = [row_to_user(r).to_dict() for r in user_rows]

    return jsonify({
        'users': users,
        'total': total,
        'page': page,
        'per_page': per_page
    })


@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id: int):
    """Get user by ID"""
    requester_id = get_user_from_token()
    if not requester_id:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    user_row = db.users[user_id]
    if not user_row:
        return jsonify({'error': 'User not found'}), 404

    user = row_to_user(user_row)
    include_sensitive = (requester_id == user_id)

    return jsonify(user.to_dict(include_sensitive=include_sensitive))


@users_bp.route('', methods=['POST'])
def create_user():
    """Create new user"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()

    # Validate required fields
    required = ['username', 'email', 'password']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    db = get_db()

    # Check if username/email already exists
    if db(db.users.username == data['username']).select().first():
        return jsonify({'error': 'Username already exists'}), 409

    if db(db.users.email == data['email']).select().first():
        return jsonify({'error': 'Email already exists'}), 409

    # Create user
    new_id = db.users.insert(
        username=data['username'],
        email=data['email'],
        password_hash=hash_password(data['password']),
        api_key=generate_api_key(),
        role=data.get('role', 'user'),
        ou_id=data.get('ou_id'),
        mfa_enabled=False,
        mfa_secret=None,
        is_active=True,
    )

    user_row = db.users[new_id]
    if not user_row:
        return jsonify({'error': 'Failed to create user'}), 500

    return jsonify(row_to_user(user_row).to_dict(include_sensitive=True)), 201


@users_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id: int):
    """Update user"""
    requester_id = get_user_from_token()
    if not requester_id:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    user_row = db.users[user_id]
    if not user_row:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    updates = {}

    if 'email' in data:
        updates['email'] = data['email']
    if 'role' in data:
        updates['role'] = data['role']
    if 'ou_id' in data:
        updates['ou_id'] = data['ou_id']
    if 'is_active' in data:
        updates['is_active'] = data['is_active']

    if updates:
        db(db.users.id == user_id).update(**updates)

    updated_row = db.users[user_id]
    return jsonify(row_to_user(updated_row).to_dict())


@users_bp.route('/<int:user_id>/password', methods=['PUT'])
def change_password(user_id: int):
    """Change user password"""
    requester_id = get_user_from_token()
    if not requester_id:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    user_row = db.users[user_id]
    if not user_row:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if 'password' not in data:
        return jsonify({'error': 'Password required'}), 400

    db(db.users.id == user_id).update(password_hash=hash_password(data['password']))

    return jsonify({'message': 'Password updated successfully'})


@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id: int):
    """Delete user"""
    requester_id = get_user_from_token()
    if not requester_id:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    user_row = db.users[user_id]
    if not user_row:
        return jsonify({'error': 'User not found'}), 404

    db(db.users.id == user_id).delete()

    return jsonify({'message': 'User deleted successfully'})
