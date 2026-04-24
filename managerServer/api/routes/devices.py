"""
Device management routes for WaddlePerf Manager Server
"""
from flask import Blueprint, jsonify, request
from functools import wraps
from datetime import datetime
from sqlalchemy import text
from models import row_to_device_enrollment, row_to_user
from penguin_dal.flask_ext import get_db
from penguintechinc_utils.logging import get_logger

logger = get_logger(__name__)
devices_bp = Blueprint('devices', __name__)


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get('session_id') or request.headers.get('X-Session-ID')

        if not session_id:
            return jsonify({'error': 'Authentication required'}), 401

        db = get_db()
        # Validate session: must exist and not be expired
        session_row = db(
            (db.sessions.session_id == session_id) &
            (db.sessions.expires_at > datetime.utcnow())
        ).select().first()

        if not session_row:
            return jsonify({'error': 'Invalid or expired session'}), 401

        user_row = db.users[session_row.user_id]
        if not user_row or not user_row.is_active:
            return jsonify({'error': 'Invalid or expired session'}), 401

        request.user = row_to_user(user_row)
        return f(*args, **kwargs)

    return decorated_function


@devices_bp.route('/devices', methods=['GET'])
@require_auth
def get_devices():
    """Get list of enrolled devices with last seen status"""
    user = request.user
    role = user.role
    ou_id = user.ou_id

    db = get_db()

    # Build parameterised query with role-based filtering
    # TIMESTAMPDIFF is MySQL-specific; use raw SQL for the join + computed column
    base_where = "1=1"
    params: dict = {}

    if role in ['ou_admin', 'ou_reporter']:
        base_where += " AND de.ou_id = :ou_id"
        params['ou_id'] = ou_id
    elif role not in ['global_admin', 'global_reporter']:
        return jsonify({'error': 'Insufficient permissions'}), 403

    # Extra filters from query params
    if 'ou_id' in request.args and role in ['global_admin', 'global_reporter']:
        base_where += " AND de.ou_id = :filter_ou_id"
        params['filter_ou_id'] = int(request.args['ou_id'])

    if 'status' in request.args:
        status_filter = request.args['status']
        if status_filter == 'online':
            base_where += " AND TIMESTAMPDIFF(MINUTE, de.last_seen, NOW()) < 5"
        elif status_filter == 'offline':
            base_where += " AND TIMESTAMPDIFF(HOUR, de.last_seen, NOW()) >= 1"

    if 'search' in request.args:
        base_where += " AND (de.device_serial LIKE :search OR de.device_hostname LIKE :search)"
        params['search'] = f"%{request.args['search']}%"

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    offset = (page - 1) * per_page

    count_sql = text(f"""
        SELECT COUNT(*) as total
        FROM device_enrollments de
        WHERE {base_where}
    """)

    data_sql = text(f"""
        SELECT
            de.*,
            ou.name AS ou_name,
            TIMESTAMPDIFF(MINUTE, de.last_seen, NOW()) AS minutes_since_last_seen
        FROM device_enrollments de
        LEFT JOIN organization_units ou ON de.ou_id = ou.id
        WHERE {base_where}
        ORDER BY de.last_seen DESC, de.enrolled_at DESC
        LIMIT :limit OFFSET :offset
    """)
    params['limit'] = per_page
    params['offset'] = offset

    with db.engine.connect() as conn:
        total_result = conn.execute(count_sql, params)
        total = total_result.scalar() or 0

        data_result = conn.execute(data_sql, params)
        rows = list(data_result)

    devices = []
    for row in rows:
        row_dict = dict(row._mapping)
        # Build device_dict from the raw row (mirrors DeviceEnrollmentRecord.to_dict)
        device_dict = {
            'id': row_dict['id'],
            'ou_id': row_dict['ou_id'],
            'device_serial': row_dict['device_serial'],
            'device_hostname': row_dict['device_hostname'],
            'device_os': row_dict['device_os'],
            'device_os_version': row_dict['device_os_version'],
            'client_type': row_dict['client_type'],
            'client_version': row_dict['client_version'],
            'enrolled_ip': row_dict['enrolled_ip'],
            'enrolled_at': row_dict['enrolled_at'].isoformat() if row_dict.get('enrolled_at') else None,
            'last_seen': row_dict['last_seen'].isoformat() if row_dict.get('last_seen') else None,
            'is_active': bool(row_dict['is_active']),
            'ou_name': row_dict.get('ou_name'),
            'minutes_since_last_seen': row_dict.get('minutes_since_last_seen'),
        }

        minutes_since = row_dict.get('minutes_since_last_seen')
        last_seen = row_dict.get('last_seen')
        if last_seen is None:
            status = 'never'
        elif minutes_since is None:
            status = 'never'
        elif minutes_since < 5:
            status = 'online'
        elif minutes_since < 60:
            status = 'recent'
        elif minutes_since < 1440:
            status = 'offline'
        else:
            status = 'stale'

        device_dict['status'] = status
        devices.append(device_dict)

    return jsonify({
        'devices': devices,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
    })


@devices_bp.route('/devices/<int:device_id>', methods=['GET'])
@require_auth
def get_device(device_id: int):
    """Get detailed information about a specific device"""
    user = request.user
    role = user.role
    ou_id = user.ou_id

    db = get_db()
    device_row = db(db.device_enrollments.id == device_id).select().first()

    if not device_row:
        return jsonify({'error': 'Device not found'}), 404

    if role in ['ou_admin', 'ou_reporter']:
        if device_row.ou_id != ou_id:
            return jsonify({'error': 'Insufficient permissions'}), 403
    elif role not in ['global_admin', 'global_reporter']:
        return jsonify({'error': 'Insufficient permissions'}), 403

    device = row_to_device_enrollment(device_row)
    device_dict = device.to_dict()

    # Fetch related names
    ou_row = db.organization_units[device.ou_id]
    device_dict['ou_name'] = ou_row.name if ou_row else None

    secret_row = db.ou_enrollment_secrets[device.enrollment_secret_id]
    device_dict['enrollment_secret_name'] = secret_row.name if secret_row else None

    return jsonify(device_dict)


@devices_bp.route('/devices/<int:device_id>/deactivate', methods=['POST'])
@require_auth
def deactivate_device(device_id: int):
    """Deactivate a device (only admins)"""
    user = request.user
    role = user.role
    ou_id = user.ou_id

    if role not in ['global_admin', 'ou_admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403

    db = get_db()
    device_row = db(db.device_enrollments.id == device_id).select().first()

    if not device_row:
        return jsonify({'error': 'Device not found'}), 404

    if role == 'ou_admin' and device_row.ou_id != ou_id:
        return jsonify({'error': 'Insufficient permissions'}), 403

    db(db.device_enrollments.id == device_id).update(is_active=False)

    logger.info(f"Device {device_id} deactivated by user {user.username}")

    return jsonify({'success': True, 'message': 'Device deactivated'})


@devices_bp.route('/devices/<int:device_id>/reactivate', methods=['POST'])
@require_auth
def reactivate_device(device_id: int):
    """Reactivate a device (only admins)"""
    user = request.user
    role = user.role
    ou_id = user.ou_id

    if role not in ['global_admin', 'ou_admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403

    db = get_db()
    device_row = db(db.device_enrollments.id == device_id).select().first()

    if not device_row:
        return jsonify({'error': 'Device not found'}), 404

    if role == 'ou_admin' and device_row.ou_id != ou_id:
        return jsonify({'error': 'Insufficient permissions'}), 403

    db(db.device_enrollments.id == device_id).update(is_active=True)

    logger.info(f"Device {device_id} reactivated by user {user.username}")

    return jsonify({'success': True, 'message': 'Device reactivated'})


@devices_bp.route('/devices/stats', methods=['GET'])
@require_auth
def get_device_stats():
    """Get device statistics (counts by status)"""
    user = request.user
    role = user.role
    ou_id = user.ou_id

    db = get_db()

    base_where = "1=1"
    params: dict = {}

    if role in ['ou_admin', 'ou_reporter']:
        base_where += " AND ou_id = :ou_id"
        params['ou_id'] = ou_id
    elif role not in ['global_admin', 'global_reporter']:
        return jsonify({'error': 'Insufficient permissions'}), 403

    stats_sql = text(f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) AS inactive,
            SUM(CASE WHEN TIMESTAMPDIFF(MINUTE, last_seen, NOW()) < 5 THEN 1 ELSE 0 END) AS online,
            SUM(CASE WHEN TIMESTAMPDIFF(MINUTE, last_seen, NOW()) BETWEEN 5 AND 59 THEN 1 ELSE 0 END) AS recent,
            SUM(CASE WHEN TIMESTAMPDIFF(HOUR, last_seen, NOW()) BETWEEN 1 AND 23 THEN 1 ELSE 0 END) AS offline,
            SUM(CASE WHEN last_seen IS NULL OR TIMESTAMPDIFF(HOUR, last_seen, NOW()) >= 24 THEN 1 ELSE 0 END) AS stale
        FROM device_enrollments
        WHERE {base_where}
    """)

    with db.engine.connect() as conn:
        result = conn.execute(stats_sql, params)
        row = result.first()

    if not row:
        stats = {'total': 0, 'active': 0, 'inactive': 0, 'online': 0, 'recent': 0, 'offline': 0, 'stale': 0}
    else:
        row_dict = dict(row._mapping)
        stats = {
            'total': int(row_dict.get('total') or 0),
            'active': int(row_dict.get('active') or 0),
            'inactive': int(row_dict.get('inactive') or 0),
            'online': int(row_dict.get('online') or 0),
            'recent': int(row_dict.get('recent') or 0),
            'offline': int(row_dict.get('offline') or 0),
            'stale': int(row_dict.get('stale') or 0),
        }

    return jsonify(stats)
