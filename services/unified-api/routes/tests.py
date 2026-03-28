"""Test result routes for WaddlePerf Unified API"""
from quart import Blueprint, request, jsonify, current_app
from typing import Dict, Any, Tuple
from services.test_service import TestService

tests_bp = Blueprint('tests', __name__, url_prefix='/api/v1/tests')


@tests_bp.route('/', methods=['GET'])
async def list_tests() -> Tuple[Dict[str, Any], int]:
    """List test results with optional filtering.

    Query parameters:
        device_id: Filter by device ID
        test_type: Filter by test type (from metadata)
        status: Filter by status (pending, running, completed, failed, skipped)
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        org_id: Filter by organization ID (required)
        limit: Maximum number of results (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        JSON response with test results list
    """
    org_id = request.args.get('org_id', None, type=int)
    device_id = request.args.get('device_id', None, type=int)
    test_type = request.args.get('test_type', None, type=str)
    status = request.args.get('status', None, type=str)
    start_date = request.args.get('start_date', None, type=str)
    end_date = request.args.get('end_date', None, type=str)
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    if not org_id:
        return {'status': 'error', 'message': 'Missing required query parameter: org_id'}, 400

    service = TestService(current_app.db)
    results = await service.list_tests(
        org_id=org_id,
        device_id=device_id,
        test_type=test_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

    return {'status': 'success', 'data': results}, 200


@tests_bp.route('/<int:test_id>', methods=['GET'])
async def get_test(test_id: int) -> Tuple[Dict[str, Any], int]:
    """Get test result details.

    Args:
        test_id: Test result ID

    Returns:
        JSON response with test result details
    """
    service = TestService(current_app.db)
    test_result = await service.get_test(test_id)

    if not test_result:
        return {'status': 'error', 'message': 'Test result not found'}, 404

    return {'status': 'success', 'data': test_result}, 200


@tests_bp.route('/', methods=['POST'])
async def create_test() -> Tuple[Dict[str, Any], int]:
    """Create test result from testServer.

    JSON body:
        test_id: Unique test identifier (required)
        name: Test name (required)
        organization_id: Organization ID (required)
        device_id: Device ID (optional)
        organization_unit_id: Org unit ID (optional)
        status: Test status (default: pending)
        duration_ms: Execution time in milliseconds
        success: Test success flag
        error_message: Error message if failed
        metrics: Performance metrics JSON
        metadata: Flexible metadata JSON
        test_output: Raw test output
        started_at: Start timestamp
        completed_at: Completion timestamp

    Returns:
        JSON response with created test result
    """
    data = await request.get_json()

    if not data:
        return {'status': 'error', 'message': 'Request body is required'}, 400

    required_fields = ['test_id', 'name', 'organization_id']
    for field in required_fields:
        if field not in data:
            return {'status': 'error', 'message': f'Missing required field: {field}'}, 400

    service = TestService(current_app.db)
    test_result = await service.create_test(data)

    if not test_result:
        return {'status': 'error', 'message': 'Failed to create test result'}, 400

    return {'status': 'success', 'data': test_result}, 201


@tests_bp.route('/<int:test_id>', methods=['DELETE'])
async def delete_test(test_id: int) -> Tuple[Dict[str, Any], int]:
    """Delete test result.

    Args:
        test_id: Test result ID

    Returns:
        JSON response
    """
    service = TestService(current_app.db)
    success = await service.delete_test(test_id)

    if not success:
        return {'status': 'error', 'message': 'Test result not found'}, 404

    return {'status': 'success', 'message': 'Test result deleted'}, 200
