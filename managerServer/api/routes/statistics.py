"""Statistics query routes"""
from flask import Blueprint, jsonify, request
from routes.auth import get_user_from_token
from penguin_dal.flask_ext import get_db
from sqlalchemy import text

stats_bp = Blueprint('statistics', __name__)


@stats_bp.route('/recent', methods=['GET'])
def recent_tests():
    """Get recent test results"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    limit = request.args.get('limit', 100, type=int)

    query = text("""
        SELECT * FROM v_recent_server_tests
        UNION ALL
        SELECT * FROM v_recent_client_tests
        ORDER BY created_at DESC
        LIMIT :limit
    """)

    db = get_db()
    with db.engine.connect() as conn:
        results = conn.execute(query, {'limit': limit})
        rows = [dict(r._mapping) for r in results]

    return jsonify({
        'results': rows
    })


@stats_bp.route('/device/<device_serial>', methods=['GET'])
def device_stats(device_serial: str):
    """Get statistics for a specific device"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    query = text("""
        SELECT * FROM v_device_test_stats
        WHERE device_serial = :serial
    """)

    db = get_db()
    with db.engine.connect() as conn:
        results = conn.execute(query, {'serial': device_serial})
        rows = [dict(r._mapping) for r in results]

    return jsonify({
        'device': device_serial,
        'statistics': rows
    })
