"""Enrollment secrets routes (FleetDM-style team secrets)"""
from flask import Blueprint, jsonify, request
from models import (
    row_to_user, row_to_organization, row_to_enrollment_secret,
    row_to_device_enrollment, row_to_client_config, row_to_system_config,
    generate_enrollment_secret,
)
from routes.auth import get_user_from_token
from penguin_dal.flask_ext import get_db
from datetime import datetime
import random

enrollment_bp = Blueprint('enrollment', __name__)


def require_admin(user_id: int):
    """Check if user is global_admin or ou_admin.

    Returns (is_admin: bool, user_record or None).
    """
    db = get_db()
    user_row = db.users[user_id]
    if not user_row:
        return False, None
    user = row_to_user(user_row)
    if user.role not in ['global_admin', 'ou_admin']:
        return False, user
    return True, user


@enrollment_bp.route('/secrets', methods=['GET'])
def list_secrets():
    """List enrollment secrets (admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    db = get_db()
    if user.role == 'global_admin':
        secret_rows = db(db.ou_enrollment_secrets.id > 0).select()
    else:
        secret_rows = db(db.ou_enrollment_secrets.ou_id == user.ou_id).select()

    return jsonify({
        'secrets': [row_to_enrollment_secret(r).to_dict(include_secret=True) for r in secret_rows]
    })


@enrollment_bp.route('/secrets/<int:ou_id>', methods=['GET'])
def get_ou_secrets(ou_id: int):
    """Get enrollment secrets for a specific OU (FleetDM: GET /api/v1/fleet/teams/:id/secrets)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    if user.role == 'ou_admin' and user.ou_id != ou_id:
        return jsonify({'error': 'Access denied'}), 403

    db = get_db()
    secret_rows = db(
        (db.ou_enrollment_secrets.ou_id == ou_id) &
        (db.ou_enrollment_secrets.is_active == True)
    ).select()

    ou_row = db.organization_units[ou_id]
    if not ou_row:
        return jsonify({'error': 'Organization not found'}), 404

    return jsonify({
        'ou': row_to_organization(ou_row).to_dict(),
        'secrets': [row_to_enrollment_secret(r).to_dict(include_secret=True) for r in secret_rows]
    })


@enrollment_bp.route('/secrets/<int:ou_id>', methods=['POST'])
def create_secret(ou_id: int):
    """Create a new enrollment secret for an OU (admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    if user.role == 'ou_admin' and user.ou_id != ou_id:
        return jsonify({'error': 'Access denied'}), 403

    db = get_db()
    ou_row = db.organization_units[ou_id]
    if not ou_row:
        return jsonify({'error': 'Organization not found'}), 404

    ou = row_to_organization(ou_row)
    request_data = request.get_json() or {}
    name = request_data.get('name', f'{ou.name} Enrollment Secret')

    new_id = db.ou_enrollment_secrets.insert(
        ou_id=ou_id,
        secret=generate_enrollment_secret(),
        name=name,
        is_active=True,
        created_by=user_id,
    )

    secret_row = db.ou_enrollment_secrets[new_id]
    if not secret_row:
        return jsonify({'error': 'Failed to create enrollment secret'}), 500

    return jsonify({
        'message': 'Enrollment secret created',
        'secret': row_to_enrollment_secret(secret_row).to_dict(include_secret=True)
    }), 201


@enrollment_bp.route('/secrets/<int:secret_id>', methods=['DELETE'])
def delete_secret(secret_id: int):
    """Delete (deactivate) an enrollment secret"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    db = get_db()
    secret_row = db.ou_enrollment_secrets[secret_id]
    if not secret_row:
        return jsonify({'error': 'Enrollment secret not found'}), 404

    secret = row_to_enrollment_secret(secret_row)

    if user.role == 'ou_admin' and user.ou_id != secret.ou_id:
        return jsonify({'error': 'Access denied'}), 403

    # Soft delete (deactivate)
    db(db.ou_enrollment_secrets.id == secret_id).update(is_active=False)

    return jsonify({'message': 'Enrollment secret deactivated'})


@enrollment_bp.route('/enroll', methods=['POST'])
def enroll_device():
    """Enroll a device using a secret (public endpoint)"""
    data = request.get_json()

    required_fields = ['secret', 'device_serial', 'device_hostname', 'device_os',
                       'device_os_version', 'client_type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    db = get_db()

    # Find the secret
    secret_row = db(
        (db.ou_enrollment_secrets.secret == data['secret']) &
        (db.ou_enrollment_secrets.is_active == True)
    ).select().first()

    if not secret_row:
        return jsonify({'error': 'Invalid or inactive enrollment secret'}), 401

    secret = row_to_enrollment_secret(secret_row)

    # Check if device is already enrolled (FleetDM: permanent OU assignment)
    existing_row = db(
        db.device_enrollments.device_serial == data['device_serial']
    ).select().first()

    if existing_row:
        # Update metadata but don't change OU
        db(db.device_enrollments.id == existing_row.id).update(
            device_hostname=data['device_hostname'],
            device_os=data['device_os'],
            device_os_version=data['device_os_version'],
            client_version=data.get('client_version'),
            last_seen=datetime.utcnow(),
            is_active=True,
        )
        return jsonify({
            'message': 'Device already enrolled, metadata updated',
            'ou_id': existing_row.ou_id,
            'device_id': existing_row.id
        })

    # New enrollment
    new_id = db.device_enrollments.insert(
        ou_id=secret.ou_id,
        enrollment_secret_id=secret.id,
        device_serial=data['device_serial'],
        device_hostname=data['device_hostname'],
        device_os=data['device_os'],
        device_os_version=data['device_os_version'],
        client_type=data['client_type'],
        client_version=data.get('client_version'),
        enrolled_ip=request.remote_addr,
        last_seen=datetime.utcnow(),
        is_active=True,
    )

    new_device_row = db.device_enrollments[new_id]

    return jsonify({
        'message': 'Device enrolled successfully',
        'ou_id': new_device_row.ou_id,
        'device_id': new_id
    }), 201


@enrollment_bp.route('/devices', methods=['GET'])
def list_devices():
    """List enrolled devices (admin and reporter access)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    user_row = db.users[user_id]
    if not user_row:
        return jsonify({'error': 'User not found'}), 404

    user = row_to_user(user_row)

    if user.role in ['global_admin', 'global_reporter']:
        device_rows = db(db.device_enrollments.is_active == True).select()
    elif user.role in ['ou_admin', 'ou_reporter']:
        device_rows = db(
            (db.device_enrollments.ou_id == user.ou_id) &
            (db.device_enrollments.is_active == True)
        ).select()
    else:
        return jsonify({'error': 'Insufficient permissions'}), 403

    return jsonify({
        'devices': [row_to_device_enrollment(r).to_dict() for r in device_rows]
    })


@enrollment_bp.route('/devices/<int:device_id>', methods=['GET'])
def get_device(device_id: int):
    """Get device details"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    user_row = db.users[user_id]
    device_row = db.device_enrollments[device_id]

    if not device_row:
        return jsonify({'error': 'Device not found'}), 404

    user = row_to_user(user_row)
    device = row_to_device_enrollment(device_row)

    if user.role in ['ou_admin', 'ou_reporter'] and user.ou_id != device.ou_id:
        return jsonify({'error': 'Access denied'}), 403

    return jsonify(device.to_dict())


@enrollment_bp.route('/devices/<int:device_id>/heartbeat', methods=['POST'])
def device_heartbeat(device_id: int):
    """Update device last_seen timestamp"""
    db = get_db()
    device_row = db.device_enrollments[device_id]
    if not device_row:
        return jsonify({'error': 'Device not found'}), 404

    db(db.device_enrollments.id == device_id).update(last_seen=datetime.utcnow())

    return jsonify({'message': 'Heartbeat recorded'})


# ============================================
# Client Configuration Endpoints
# ============================================

@enrollment_bp.route('/config', methods=['GET'])
def get_client_config():
    """Get client configuration for enrolled device (used by clients on check-in)"""
    device_serial = request.args.get('device_serial')
    db = get_db()

    if device_serial:
        device_row = db(
            db.device_enrollments.device_serial == device_serial
        ).select().first()
        if not device_row:
            return jsonify({'error': 'Device not enrolled'}), 404
        ou_id = device_row.ou_id
    else:
        user_id = get_user_from_token()
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        user_row = db.users[user_id]
        ou_id = user_row.ou_id

    # Get OU-specific config or fall back to default
    config_row = db(db.client_configs.ou_id == ou_id).select().first()
    if not config_row:
        config_row = db(db.client_configs.is_default == True).select().first()

    if not config_row:
        return jsonify({'error': 'No configuration available'}), 404

    config = row_to_client_config(config_row)

    # Calculate actual schedule with random offset
    config_data = dict(config.config_data) if config.config_data else {}
    if 'schedule' in config_data:
        base_interval = config_data['schedule'].get('interval_seconds', 300)
        offset_percent = config_data['schedule'].get('offset_percent', 15)

        offset_range = base_interval * (offset_percent / 100.0)
        actual_offset = random.uniform(-offset_range, offset_range)
        actual_interval = int(base_interval + actual_offset)

        config_data['schedule']['actual_interval_seconds'] = actual_interval
        config_data['schedule']['next_check_in'] = datetime.utcnow().timestamp() + actual_interval

    # Get client check-in interval
    checkin_min_row = db(
        db.system_config.config_key == 'client_checkin_min_seconds'
    ).select().first()
    checkin_max_row = db(
        db.system_config.config_key == 'client_checkin_max_seconds'
    ).select().first()

    checkin_min_val = int(checkin_min_row.config_value) if checkin_min_row else 1800
    checkin_max_val = int(checkin_max_row.config_value) if checkin_max_row else 3600

    next_checkin_seconds = random.randint(checkin_min_val, checkin_max_val)

    return jsonify({
        'config': config_data,
        'config_name': config.config_name,
        'ou_id': config.ou_id,
        'next_checkin_seconds': next_checkin_seconds,
        'next_checkin_at': datetime.utcnow().timestamp() + next_checkin_seconds
    })


@enrollment_bp.route('/configs', methods=['GET'])
def list_client_configs():
    """List all client configurations (admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    db = get_db()
    if user.role == 'global_admin':
        config_rows = db(db.client_configs.id > 0).select()
    else:
        # OU admin: their OU configs + defaults
        config_rows = db(
            (db.client_configs.ou_id == user.ou_id) |
            (db.client_configs.is_default == True)
        ).select()

    return jsonify({
        'configs': [row_to_client_config(r).to_dict() for r in config_rows]
    })


@enrollment_bp.route('/configs/<int:ou_id>', methods=['GET'])
def get_ou_config(ou_id: int):
    """Get configuration for a specific OU"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    if user.role == 'ou_admin' and user.ou_id != ou_id:
        return jsonify({'error': 'Access denied'}), 403

    db = get_db()
    config_row = db(db.client_configs.ou_id == ou_id).select().first()
    if not config_row:
        config_row = db(db.client_configs.is_default == True).select().first()

    if not config_row:
        return jsonify({'error': 'No configuration found'}), 404

    return jsonify(row_to_client_config(config_row).to_dict())


@enrollment_bp.route('/configs/<int:ou_id>', methods=['PUT'])
def update_ou_config(ou_id: int):
    """Update or create configuration for an OU (admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    is_admin, user = require_admin(user_id)
    if not is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    if user.role == 'ou_admin' and user.ou_id != ou_id:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    if not data or 'config_data' not in data:
        return jsonify({'error': 'config_data required'}), 400

    db = get_db()
    ou_row = db.organization_units[ou_id]
    if not ou_row:
        return jsonify({'error': 'Organization not found'}), 404

    ou = row_to_organization(ou_row)

    existing_row = db(db.client_configs.ou_id == ou_id).select().first()
    if not existing_row:
        new_id = db.client_configs.insert(
            ou_id=ou_id,
            user_id=user_id,
            config_name=data.get('config_name', f'{ou.name} Configuration'),
            config_data=data['config_data'],
            is_default=False,
        )
        config_row = db.client_configs[new_id]
    else:
        updates = {'config_data': data['config_data'], 'user_id': user_id}
        if 'config_name' in data:
            updates['config_name'] = data['config_name']
        db(db.client_configs.ou_id == ou_id).update(**updates)
        config_row = db(db.client_configs.ou_id == ou_id).select().first()

    return jsonify({
        'message': 'Configuration updated',
        'config': row_to_client_config(config_row).to_dict()
    })


@enrollment_bp.route('/configs/default', methods=['GET'])
def get_default_config():
    """Get the default configuration"""
    db = get_db()
    config_row = db(db.client_configs.is_default == True).select().first()
    if not config_row:
        return jsonify({'error': 'No default configuration found'}), 404

    return jsonify(row_to_client_config(config_row).to_dict())


@enrollment_bp.route('/configs/default', methods=['PUT'])
def update_default_config():
    """Update the default configuration (global admin only)"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    user_row = db.users[user_id]
    if not user_row or user_row.role != 'global_admin':
        return jsonify({'error': 'Global admin access required'}), 403

    data = request.get_json()
    if not data or 'config_data' not in data:
        return jsonify({'error': 'config_data required'}), 400

    config_row = db(db.client_configs.is_default == True).select().first()
    if not config_row:
        return jsonify({'error': 'Default configuration not found'}), 404

    updates = {'config_data': data['config_data'], 'user_id': user_id}
    if 'config_name' in data:
        updates['config_name'] = data['config_name']

    db(db.client_configs.is_default == True).update(**updates)

    updated_row = db(db.client_configs.is_default == True).select().first()
    return jsonify({
        'message': 'Default configuration updated',
        'config': row_to_client_config(updated_row).to_dict()
    })
