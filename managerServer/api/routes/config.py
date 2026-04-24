"""System configuration routes (FleetDM-style)"""
from flask import Blueprint, jsonify, request
from models import row_to_user, row_to_system_config
from routes.auth import get_user_from_token
from penguin_dal.flask_ext import get_db
import json

config_bp = Blueprint('config', __name__)


def require_admin(user_id: int) -> bool:
    """Check if user is global_admin"""
    db = get_db()
    user_row = db.users[user_id]
    if not user_row or user_row.role != 'global_admin':
        return False
    return True


@config_bp.route('', methods=['GET'])
def get_all_config():
    """Get all system configuration (admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    db = get_db()
    config_rows = db(db.system_config.id > 0).select()

    config_dict = {}
    for row in config_rows:
        config = row_to_system_config(row)
        value = config.config_value
        if config.config_type == 'json' and value:
            try:
                value = json.loads(value)
            except Exception:
                pass
        elif config.config_type == 'boolean':
            value = value.lower() == 'true' if value else False
        elif config.config_type == 'integer':
            value = int(value) if value else 0

        config_dict[config.config_key] = {
            'value': value,
            'type': config.config_type,
            'description': config.description,
            'updated_at': config.updated_at.isoformat() if config.updated_at else None
        }

    return jsonify({'config': config_dict})


@config_bp.route('/<key>', methods=['GET'])
def get_config(key: str):
    """Get a specific configuration value"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    row = db(db.system_config.config_key == key).select().first()
    if not row:
        return jsonify({'error': 'Configuration not found'}), 404

    config = row_to_system_config(row)
    value = config.config_value
    if config.config_type == 'json' and value:
        try:
            value = json.loads(value)
        except Exception:
            pass
    elif config.config_type == 'boolean':
        value = value.lower() == 'true' if value else False
    elif config.config_type == 'integer':
        value = int(value) if value else 0

    return jsonify({
        'config_key': config.config_key,
        'value': value,
        'type': config.config_type,
        'description': config.description
    })


@config_bp.route('', methods=['PATCH'])
def update_config():
    """Update system configuration (admin only, FleetDM-style bulk update)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    db = get_db()
    updated = []
    errors = []

    for key, value in data.items():
        row = db(db.system_config.config_key == key).select().first()
        if not row:
            errors.append(f'Configuration key "{key}" not found')
            continue

        config = row_to_system_config(row)

        if config.config_type == 'json':
            new_value = json.dumps(value)
        elif config.config_type == 'boolean':
            new_value = 'true' if value else 'false'
        else:
            new_value = str(value)

        db(db.system_config.config_key == key).update(
            config_value=new_value,
            updated_by=user_id,
        )
        updated.append(key)

    return jsonify({
        'updated': updated,
        'errors': errors
    })


@config_bp.route('/<key>', methods=['PUT'])
def set_config(key: str):
    """Set a specific configuration value (admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    if not require_admin(user_id):
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    if 'value' not in data:
        return jsonify({'error': 'Value required'}), 400

    db = get_db()
    row = db(db.system_config.config_key == key).select().first()
    if not row:
        return jsonify({'error': 'Configuration not found'}), 404

    config = row_to_system_config(row)
    value = data['value']

    if config.config_type == 'json':
        new_value = json.dumps(value)
    elif config.config_type == 'boolean':
        new_value = 'true' if value else 'false'
    else:
        new_value = str(value)

    db(db.system_config.config_key == key).update(
        config_value=new_value,
        updated_by=user_id,
    )

    return jsonify({
        'config_key': config.config_key,
        'value': value,
        'updated': True
    })
