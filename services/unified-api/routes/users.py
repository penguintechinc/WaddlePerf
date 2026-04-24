"""User management routes using Quart async blueprint"""

from quart import Blueprint, request, jsonify
from flask_security import auth_required, roles_required, current_user
from services.user_service import UserService
from typing import Dict, Any

users_bp = Blueprint('users', __name__)


async def _get_user_service():
    """Helper to get UserService instance"""
    from quart import current_app
    return UserService(current_app.db)


@users_bp.route('/', methods=['GET'])
@auth_required('token')
async def list_users() -> tuple[Dict[str, Any], int]:
    """List users with pagination and search.

    Query Parameters:
        - page (int): Page number (default: 1)
        - limit (int): Items per page (default: 20)
        - search (str): Search by email, username, first_name, or last_name

    Returns:
        JSON with user list, total count, and pagination info
    """
    try:
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=20, type=int)
        search = request.args.get('search', default='', type=str)

        # Validate pagination params
        page = max(1, page)
        limit = max(1, min(limit, 100))

        service = await _get_user_service()
        result = await service.list_users(page=page, limit=limit, search=search)

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/<int:user_id>', methods=['GET'])
@auth_required('token')
async def get_user(user_id: int) -> tuple[Dict[str, Any], int]:
    """Get user details by ID.

    Args:
        user_id: User ID to retrieve

    Returns:
        JSON with user details including roles
    """
    try:
        service = await _get_user_service()
        user = await service.get_user(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify(user), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/', methods=['POST'])
@auth_required('token')
@roles_required('admin')
async def create_user() -> tuple[Dict[str, Any], int]:
    """Create new user (admin only).

    Request JSON:
        - email (str, required): User email (must be unique)
        - username (str, required): Username (must be unique)
        - password (str, required): User password (will be hashed)
        - first_name (str, optional): First name
        - last_name (str, optional): Last name
        - active (bool, optional): Active status (default: True)
        - role_ids (list, optional): List of role IDs to assign

    Returns:
        JSON with created user details
    """
    try:
        data = await request.get_json()

        # Validate required fields
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        if not data.get('username'):
            return jsonify({'error': 'Username is required'}), 400
        if not data.get('password'):
            return jsonify({'error': 'Password is required'}), 400

        service = await _get_user_service()
        user = await service.create_user(data)

        return jsonify(user), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/<int:user_id>', methods=['PUT'])
@auth_required('token')
async def update_user(user_id: int) -> tuple[Dict[str, Any], int]:
    """Update user (admin or self only).

    Args:
        user_id: User ID to update

    Request JSON:
        - first_name (str, optional): First name
        - last_name (str, optional): Last name
        - active (bool, optional): Active status
        - password (str, optional): New password (only if not admin)
        - role_ids (list, optional): Role IDs (admin only)

    Returns:
        JSON with updated user details
    """
    try:
        # Check authorization: admin or self
        if current_user.id != user_id and 'admin' not in [r.name for r in current_user.roles]:
            return jsonify({'error': 'Unauthorized: can only update own profile'}), 403

        data = await request.get_json()
        service = await _get_user_service()
        user = await service.update_user(user_id, data)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify(user), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@auth_required('token')
@roles_required('admin')
async def delete_user(user_id: int) -> tuple[Dict[str, Any], int]:
    """Delete user (admin only).

    Args:
        user_id: User ID to delete

    Returns:
        JSON with confirmation message
    """
    try:
        service = await _get_user_service()
        success = await service.delete_user(user_id)

        if not success:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'message': f'User {user_id} deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
