"""Statistics routes for WaddlePerf Unified API"""
from quart import Blueprint, request, jsonify, current_app
from typing import Dict, Any, Tuple
from services.stats_service import StatsService

stats_bp = Blueprint('stats', __name__, url_prefix='/api/v1/stats')


@stats_bp.route('/summary', methods=['GET'])
async def get_summary() -> Tuple[Dict[str, Any], int]:
    """Get overall statistics summary.

    Query parameters:
        org_id: Organization ID (required)
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)

    Returns:
        JSON response with overall statistics:
            - total_tests: Total number of tests
            - success_count: Number of successful tests
            - failure_count: Number of failed tests
            - success_rate: Success percentage
            - avg_duration_ms: Average test duration
            - avg_latency_ms: Average latency metric
    """
    org_id = request.args.get('org_id', None, type=int)
    start_date = request.args.get('start_date', None, type=str)
    end_date = request.args.get('end_date', None, type=str)

    if not org_id:
        return {'status': 'error', 'message': 'Missing required query parameter: org_id'}, 400

    service = StatsService(current_app.db)
    summary = await service.get_summary(org_id=org_id, start_date=start_date, end_date=end_date)

    return {'status': 'success', 'data': summary}, 200


@stats_bp.route('/by-device', methods=['GET'])
async def get_by_device() -> Tuple[Dict[str, Any], int]:
    """Get statistics aggregated by device.

    Query parameters:
        org_id: Organization ID (required)
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        limit: Maximum number of devices (default: 50)

    Returns:
        JSON response with per-device statistics:
            - device_id: Device identifier
            - device_name: Device name
            - total_tests: Total tests on device
            - success_count: Successful tests
            - success_rate: Success percentage
            - avg_duration_ms: Average duration
    """
    org_id = request.args.get('org_id', None, type=int)
    start_date = request.args.get('start_date', None, type=str)
    end_date = request.args.get('end_date', None, type=str)
    limit = request.args.get('limit', 50, type=int)

    if not org_id:
        return {'status': 'error', 'message': 'Missing required query parameter: org_id'}, 400

    service = StatsService(current_app.db)
    stats = await service.get_by_device(
        org_id=org_id, start_date=start_date, end_date=end_date, limit=limit
    )

    return {'status': 'success', 'data': stats}, 200


@stats_bp.route('/by-type', methods=['GET'])
async def get_by_type() -> Tuple[Dict[str, Any], int]:
    """Get statistics aggregated by test type.

    Query parameters:
        org_id: Organization ID (required)
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        limit: Maximum number of test types (default: 50)

    Returns:
        JSON response with per-test-type statistics:
            - test_type: Test type name
            - total_tests: Total tests of type
            - success_count: Successful tests
            - success_rate: Success percentage
            - avg_duration_ms: Average duration
    """
    org_id = request.args.get('org_id', None, type=int)
    start_date = request.args.get('start_date', None, type=str)
    end_date = request.args.get('end_date', None, type=str)
    limit = request.args.get('limit', 50, type=int)

    if not org_id:
        return {'status': 'error', 'message': 'Missing required query parameter: org_id'}, 400

    service = StatsService(current_app.db)
    stats = await service.get_by_type(
        org_id=org_id, start_date=start_date, end_date=end_date, limit=limit
    )

    return {'status': 'success', 'data': stats}, 200


@stats_bp.route('/trends', methods=['GET'])
async def get_trends() -> Tuple[Dict[str, Any], int]:
    """Get time-series data for trends analysis.

    Query parameters:
        org_id: Organization ID (required)
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        interval: Time interval (hourly, daily, weekly) (default: daily)
        metric: Metric to trend (success_rate, avg_duration, count) (default: success_rate)

    Returns:
        JSON response with time-series data:
            - timestamps: List of time points
            - values: List of metric values
            - metric: Metric name
            - interval: Time interval used
    """
    org_id = request.args.get('org_id', None, type=int)
    start_date = request.args.get('start_date', None, type=str)
    end_date = request.args.get('end_date', None, type=str)
    interval = request.args.get('interval', 'daily', type=str)
    metric = request.args.get('metric', 'success_rate', type=str)

    if not org_id:
        return {'status': 'error', 'message': 'Missing required query parameter: org_id'}, 400

    if interval not in ['hourly', 'daily', 'weekly']:
        return {'status': 'error', 'message': 'Invalid interval. Must be hourly, daily, or weekly'}, 400

    if metric not in ['success_rate', 'avg_duration', 'count']:
        return {'status': 'error', 'message': 'Invalid metric. Must be success_rate, avg_duration, or count'}, 400

    service = StatsService(current_app.db)
    trends = await service.get_trends(
        org_id=org_id,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        metric=metric
    )

    return {'status': 'success', 'data': trends}, 200


@stats_bp.route('/recent', methods=['GET'])
async def get_recent() -> Tuple[Dict[str, Any], int]:
    """Get recent test results.

    Query parameters:
        org_id: Organization ID (required)
        limit: Number of recent tests to return (default: 20, max: 100)
        device_id: Filter by device ID (optional)

    Returns:
        JSON response with recent test results
    """
    org_id = request.args.get('org_id', None, type=int)
    limit = request.args.get('limit', 20, type=int)
    device_id = request.args.get('device_id', None, type=int)

    if not org_id:
        return {'status': 'error', 'message': 'Missing required query parameter: org_id'}, 400

    if limit > 100:
        limit = 100

    service = StatsService(current_app.db)
    recent = await service.get_recent(org_id=org_id, device_id=device_id, limit=limit)

    return {'status': 'success', 'data': recent}, 200
