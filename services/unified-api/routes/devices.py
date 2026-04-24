"""Device routes for WaddlePerf Unified API"""
from quart import Blueprint, request, jsonify, current_app
from typing import Dict, Any, Tuple
from services.device_service import DeviceService

devices_bp = Blueprint('devices', __name__, url_prefix='/api/v1/devices')


@devices_bp.route('/', methods=['GET'])
async def list_devices() -> Tuple[Dict[str, Any], int]:
    """List devices with optional filtering.

    Query parameters:
        org_id: Filter by organization ID
        limit: Maximum number of results (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        JSON response with devices list
    """
    org_id = request.args.get('org_id', None, type=int)
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    service = DeviceService(current_app.db)
    devices = await service.list_devices(org_id=org_id, limit=limit, offset=offset)

    return {'status': 'success', 'data': devices}, 200


@devices_bp.route('/<int:device_id>', methods=['GET'])
async def get_device(device_id: int) -> Tuple[Dict[str, Any], int]:
    """Get device details.

    Args:
        device_id: Device ID

    Returns:
        JSON response with device details
    """
    service = DeviceService(current_app.db)
    device = await service.get_device(device_id)

    if not device:
        return {'status': 'error', 'message': 'Device not found'}, 404

    return {'status': 'success', 'data': device}, 200


@devices_bp.route('/enroll', methods=['POST'])
async def enroll_device() -> Tuple[Dict[str, Any], int]:
    """Enroll device with enrollment secret.

    JSON body:
        enrollment_secret: Enrollment secret token (required)
        org_id: Organization ID (required)
        device_name: Device name (required)
        device_type: Device type (laptop, desktop, mobile, tablet, other)
        os_type: Operating system (windows, macos, linux, ios, android, other)
        os_version: OS version
        hardware_id: Hardware ID
        mac_address: MAC address
        ip_address: IP address
        device_metadata: Additional metadata JSON

    Returns:
        JSON response with enrolled device
    """
    data = await request.get_json()

    if not data:
        return {'status': 'error', 'message': 'Request body is required'}, 400

    required_fields = ['enrollment_secret', 'org_id', 'device_name']
    for field in required_fields:
        if field not in data:
            return {'status': 'error', 'message': f'Missing required field: {field}'}, 400

    enrollment_secret = data.pop('enrollment_secret')
    org_id = data.pop('org_id')

    service = DeviceService(current_app.db)
    device = await service.enroll_device(enrollment_secret, org_id, data)

    if not device:
        return {'status': 'error', 'message': 'Invalid or expired enrollment secret'}, 400

    return {'status': 'success', 'data': device}, 201


@devices_bp.route('/<int:device_id>', methods=['PUT'])
async def update_device(device_id: int) -> Tuple[Dict[str, Any], int]:
    """Update device.

    Args:
        device_id: Device ID

    JSON body:
        device_name: Device name
        device_type: Device type
        os_type: Operating system
        os_version: OS version
        hardware_id: Hardware ID
        mac_address: MAC address
        ip_address: IP address
        status: Device status (active, inactive, disabled, compromised)
        last_checkin: Last checkin timestamp
        last_sync: Last sync timestamp
        device_metadata: Additional metadata JSON

    Returns:
        JSON response with updated device
    """
    data = await request.get_json()
    if not data:
        return {'status': 'error', 'message': 'Request body is required'}, 400

    service = DeviceService(current_app.db)
    device = await service.update_device(device_id, data)

    if not device:
        return {'status': 'error', 'message': 'Device not found'}, 404

    return {'status': 'success', 'data': device}, 200


@devices_bp.route('/<int:device_id>', methods=['DELETE'])
async def delete_device(device_id: int) -> Tuple[Dict[str, Any], int]:
    """Delete device.

    Args:
        device_id: Device ID

    Returns:
        JSON response
    """
    service = DeviceService(current_app.db)
    success = await service.delete_device(device_id)

    if not success:
        return {'status': 'error', 'message': 'Device not found'}, 404

    return {'status': 'success', 'message': 'Device deleted'}, 200


@devices_bp.route('/enrollment-secrets', methods=['POST'])
async def create_enrollment_secret() -> Tuple[Dict[str, Any], int]:
    """Create enrollment secret.

    JSON body:
        org_id: Organization ID (required)
        secret_name: Secret name
        description: Secret description
        is_active: Is secret active (default: True)
        max_uses: Maximum number of uses
        expires_at: Expiration datetime

    Returns:
        JSON response with created enrollment secret
    """
    data = await request.get_json()

    if not data or 'org_id' not in data:
        return {'status': 'error', 'message': 'Missing required field: org_id'}, 400

    org_id = data.pop('org_id')

    service = DeviceService(current_app.db)
    secret = await service.create_enrollment_secret(org_id, data)

    return {'status': 'success', 'data': secret}, 201


@devices_bp.route('/enrollment-secrets', methods=['GET'])
async def list_enrollment_secrets() -> Tuple[Dict[str, Any], int]:
    """List enrollment secrets for organization.

    Query parameters:
        org_id: Organization ID (required)
        limit: Maximum number of results (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        JSON response with enrollment secrets list
    """
    org_id = request.args.get('org_id', None, type=int)
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    if not org_id:
        return {'status': 'error', 'message': 'Missing required query parameter: org_id'}, 400

    service = DeviceService(current_app.db)
    secrets = await service.list_enrollment_secrets(org_id, limit=limit, offset=offset)

    return {'status': 'success', 'data': secrets}, 200
