"""Client result upload routes"""
from flask import Blueprint, jsonify, request
from routes.auth import get_user_from_token
from penguin_dal.flask_ext import get_db
from sqlalchemy import text
import json

results_bp = Blueprint('results', __name__)


@results_bp.route('/upload', methods=['POST'])
def upload_results():
    """Upload test results from clients"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()

    # Validate required fields
    required = ['device_serial', 'device_hostname', 'device_os', 'device_os_version',
                'test_type', 'target_host', 'target_ip']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # Insert into client_test_results using raw SQL via engine
    query = text("""
        INSERT INTO client_test_results (
            user_id, device_serial, device_hostname, device_os, device_os_version,
            test_type, protocol_detail, target_host, target_ip,
            latency_ms, throughput_mbps, jitter_ms, packet_loss_percent, raw_results
        ) VALUES (
            :user_id, :device_serial, :device_hostname, :device_os, :device_os_version,
            :test_type, :protocol_detail, :target_host, :target_ip,
            :latency_ms, :throughput_mbps, :jitter_ms, :packet_loss_percent, :raw_results
        )
    """)

    db = get_db()
    with db.engine.begin() as conn:
        conn.execute(query, {
            'user_id': user_id,
            'device_serial': data['device_serial'],
            'device_hostname': data['device_hostname'],
            'device_os': data['device_os'],
            'device_os_version': data['device_os_version'],
            'test_type': data['test_type'],
            'protocol_detail': data.get('protocol_detail'),
            'target_host': data['target_host'],
            'target_ip': data['target_ip'],
            'latency_ms': data.get('latency_ms'),
            'throughput_mbps': data.get('throughput_mbps'),
            'jitter_ms': data.get('jitter_ms'),
            'packet_loss_percent': data.get('packet_loss_percent'),
            'raw_results': json.dumps(data.get('raw_results', {}))
        })

    return jsonify({'message': 'Results uploaded successfully'}), 201
