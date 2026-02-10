"""
Device management routes for WaddlePerf Manager Server
"""
from flask import Blueprint, jsonify, request
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func, case
from models import db, DeviceEnrollment, OrganizationUnit, OUEnrollmentSecret, User, Session
from penguintechinc_utils.logging import get_logger

logger = get_logger(__name__)
devices_bp = Blueprint('devices', __name__)


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get session from cookie or header
        session_id = request.cookies.get('session_id') or request.headers.get('X-Session-ID')

        if not session_id:
            return jsonify({'error': 'Authentication required'}), 401

        # Validate session
        session = Session.query.filter_by(session_id=session_id).filter(
            Session.expires_at > datetime.utcnow()
        ).first()

        if not session or not session.user or not session.user.is_active:
            return jsonify({'error': 'Invalid or expired session'}), 401

        request.user = session.user
        return f(*args, **kwargs)

    return decorated_function


@devices_bp.route('/devices', methods=['GET'])
@require_auth
def get_devices():
    """Get list of enrolled devices with last seen status"""
    user = request.user
    role = user.role
    ou_id = user.ou_id

    # Base query
    query = db.session.query(
        DeviceEnrollment,
        OrganizationUnit.name.label('ou_name'),
        func.timestampdiff(db.text('MINUTE'), DeviceEnrollment.last_seen, func.now()).label('minutes_since_last_seen')
    ).outerjoin(OrganizationUnit, DeviceEnrollment.ou_id == OrganizationUnit.id)

    # Filter by role
    if role in ['ou_admin', 'ou_reporter']:
        # Only show devices in user's OU
        query = query.filter(DeviceEnrollment.ou_id == ou_id)
    elif role not in ['global_admin', 'global_reporter']:
        # Regular users can't see device list
        return jsonify({'error': 'Insufficient permissions'}), 403

    # Add filters from query params
    if 'ou_id' in request.args and role in ['global_admin', 'global_reporter']:
        query = query.filter(DeviceEnrollment.ou_id == int(request.args['ou_id']))

    if 'status' in request.args:
        status_filter = request.args['status']
        if status_filter == 'online':
            query = query.filter(
                func.timestampdiff(db.text('MINUTE'), DeviceEnrollment.last_seen, func.now()) < 5
            )
        elif status_filter == 'offline':
            query = query.filter(
                func.timestampdiff(db.text('HOUR'), DeviceEnrollment.last_seen, func.now()) >= 1
            )

    if 'search' in request.args:
        search = f"%{request.args['search']}%"
        query = query.filter(
            db.or_(
                DeviceEnrollment.device_serial.like(search),
                DeviceEnrollment.device_hostname.like(search)
            )
        )

    # Order by last seen
    query = query.order_by(DeviceEnrollment.last_seen.desc().nullslast(), DeviceEnrollment.enrolled_at.desc())

    # Pagination
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Format results
    devices = []
    for device, ou_name, minutes_since in pagination.items:
        device_dict = device.to_dict()
        device_dict['ou_name'] = ou_name
        device_dict['minutes_since_last_seen'] = minutes_since

        # Determine status
        if device.last_seen is None:
            status = 'never'
        elif minutes_since is None:
            status = 'never'
        elif minutes_since < 5:
            status = 'online'
        elif minutes_since < 60:
            status = 'recent'
        elif minutes_since < 1440:  # 24 hours
            status = 'offline'
        else:
            status = 'stale'

        device_dict['status'] = status
        devices.append(device_dict)

    return jsonify({
        'devices': devices,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@devices_bp.route('/devices/<int:device_id>', methods=['GET'])
@require_auth
def get_device(device_id):
    """Get detailed information about a specific device"""
    user = request.user
    role = user.role
    ou_id = user.ou_id

    device = DeviceEnrollment.query.filter_by(id=device_id).first()

    if not device:
        return jsonify({'error': 'Device not found'}), 404

    # Check permissions
    if role in ['ou_admin', 'ou_reporter']:
        if device.ou_id != ou_id:
            return jsonify({'error': 'Insufficient permissions'}), 403
    elif role not in ['global_admin', 'global_reporter']:
        return jsonify({'error': 'Insufficient permissions'}), 403

    device_dict = device.to_dict()
    device_dict['ou_name'] = device.organization.name if device.organization else None
    device_dict['enrollment_secret_name'] = device.enrollment_secret.name if device.enrollment_secret else None

    return jsonify(device_dict)


@devices_bp.route('/devices/<int:device_id>/deactivate', methods=['POST'])
@require_auth
def deactivate_device(device_id):
    """Deactivate a device (only admins)"""
    user = request.user
    role = user.role
    ou_id = user.ou_id

    if role not in ['global_admin', 'ou_admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403

    device = DeviceEnrollment.query.filter_by(id=device_id).first()

    if not device:
        return jsonify({'error': 'Device not found'}), 404

    if role == 'ou_admin' and device.ou_id != ou_id:
        return jsonify({'error': 'Insufficient permissions'}), 403

    device.is_active = False
    db.session.commit()

    logger.info(f"Device {device_id} deactivated by user {user.username}")

    return jsonify({'success': True, 'message': 'Device deactivated'})


@devices_bp.route('/devices/<int:device_id>/reactivate', methods=['POST'])
@require_auth
def reactivate_device(device_id):
    """Reactivate a device (only admins)"""
    user = request.user
    role = user.role
    ou_id = user.ou_id

    if role not in ['global_admin', 'ou_admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403

    device = DeviceEnrollment.query.filter_by(id=device_id).first()

    if not device:
        return jsonify({'error': 'Device not found'}), 404

    if role == 'ou_admin' and device.ou_id != ou_id:
        return jsonify({'error': 'Insufficient permissions'}), 403

    device.is_active = True
    db.session.commit()

    logger.info(f"Device {device_id} reactivated by user {user.username}")

    return jsonify({'success': True, 'message': 'Device reactivated'})


@devices_bp.route('/devices/stats', methods=['GET'])
@require_auth
def get_device_stats():
    """Get device statistics (counts by status)"""
    user = request.user
    role = user.role
    ou_id = user.ou_id

    # Base query
    query = DeviceEnrollment.query

    if role in ['ou_admin', 'ou_reporter']:
        query = query.filter_by(ou_id=ou_id)
    elif role not in ['global_admin', 'global_reporter']:
        return jsonify({'error': 'Insufficient permissions'}), 403

    stats = {
        'total': query.count(),
        'active': query.filter_by(is_active=True).count(),
        'inactive': query.filter_by(is_active=False).count(),
        'online': query.filter(
            func.timestampdiff(db.text('MINUTE'), DeviceEnrollment.last_seen, func.now()) < 5
        ).count(),
        'recent': query.filter(
            func.timestampdiff(db.text('MINUTE'), DeviceEnrollment.last_seen, func.now()).between(5, 59)
        ).count(),
        'offline': query.filter(
            func.timestampdiff(db.text('HOUR'), DeviceEnrollment.last_seen, func.now()).between(1, 23)
        ).count(),
        'stale': query.filter(
            db.or_(
                DeviceEnrollment.last_seen.is_(None),
                func.timestampdiff(db.text('HOUR'), DeviceEnrollment.last_seen, func.now()) >= 24
            )
        ).count()
    }

    return jsonify(stats)
