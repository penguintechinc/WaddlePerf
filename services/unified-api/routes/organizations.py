"""Organization routes for WaddlePerf Unified API"""
from quart import Blueprint, request, jsonify, current_app
from typing import Dict, Any, Tuple
from services.org_service import OrganizationService

organizations_bp = Blueprint('organizations', __name__, url_prefix='/api/v1/organizations')


@organizations_bp.route('/', methods=['GET'])
async def list_organizations() -> Tuple[Dict[str, Any], int]:
    """List all organizations.

    Query parameters:
        limit: Maximum number of results (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        JSON response with organizations list
    """
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    service = OrganizationService(current_app.db)
    organizations = await service.list_organizations(limit=limit, offset=offset)

    return {'status': 'success', 'data': organizations}, 200


@organizations_bp.route('/<int:org_id>', methods=['GET'])
async def get_organization(org_id: int) -> Tuple[Dict[str, Any], int]:
    """Get organization details.

    Args:
        org_id: Organization ID

    Returns:
        JSON response with organization details
    """
    service = OrganizationService(current_app.db)
    org = await service.get_organization(org_id)

    if not org:
        return {'status': 'error', 'message': 'Organization not found'}, 404

    return {'status': 'success', 'data': org}, 200


@organizations_bp.route('/', methods=['POST'])
async def create_organization() -> Tuple[Dict[str, Any], int]:
    """Create new organization.

    JSON body:
        name: Organization name (required)
        description: Organization description
        contact_email: Contact email
        contact_phone: Contact phone
        address: Organization address
        status: Status (active, inactive, archived)

    Returns:
        JSON response with created organization
    """
    data = await request.get_json()

    if not data or 'name' not in data:
        return {'status': 'error', 'message': 'Missing required field: name'}, 400

    service = OrganizationService(current_app.db)
    org = await service.create_organization(data)

    return {'status': 'success', 'data': org}, 201


@organizations_bp.route('/<int:org_id>', methods=['PUT'])
async def update_organization(org_id: int) -> Tuple[Dict[str, Any], int]:
    """Update organization.

    Args:
        org_id: Organization ID

    JSON body:
        name: Organization name
        description: Organization description
        contact_email: Contact email
        contact_phone: Contact phone
        address: Organization address
        status: Status (active, inactive, archived)

    Returns:
        JSON response with updated organization
    """
    data = await request.get_json()
    if not data:
        return {'status': 'error', 'message': 'Request body is required'}, 400

    service = OrganizationService(current_app.db)
    org = await service.update_organization(org_id, data)

    if not org:
        return {'status': 'error', 'message': 'Organization not found'}, 404

    return {'status': 'success', 'data': org}, 200


@organizations_bp.route('/<int:org_id>', methods=['DELETE'])
async def delete_organization(org_id: int) -> Tuple[Dict[str, Any], int]:
    """Delete organization.

    Args:
        org_id: Organization ID

    Returns:
        JSON response
    """
    service = OrganizationService(current_app.db)
    success = await service.delete_organization(org_id)

    if not success:
        return {'status': 'error', 'message': 'Organization not found'}, 404

    return {'status': 'success', 'message': 'Organization deleted'}, 200


@organizations_bp.route('/<int:org_id>/units', methods=['GET'])
async def list_organizational_units(org_id: int) -> Tuple[Dict[str, Any], int]:
    """List organizational units (OUs) for organization.

    Args:
        org_id: Organization ID

    Query parameters:
        limit: Maximum number of results (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        JSON response with OUs list
    """
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    service = OrganizationService(current_app.db)
    ous = await service.list_organizational_units(org_id, limit=limit, offset=offset)

    return {'status': 'success', 'data': ous}, 200


@organizations_bp.route('/<int:org_id>/units', methods=['POST'])
async def create_organizational_unit(org_id: int) -> Tuple[Dict[str, Any], int]:
    """Create organizational unit (OU).

    Args:
        org_id: Organization ID

    JSON body:
        name: OU name (required)
        description: OU description
        parent_id: Parent OU ID
        policy_data: JSON policy data
        status: Status (active, inactive, archived)

    Returns:
        JSON response with created OU
    """
    data = await request.get_json()

    if not data or 'name' not in data:
        return {'status': 'error', 'message': 'Missing required field: name'}, 400

    service = OrganizationService(current_app.db)
    ou = await service.create_organizational_unit(org_id, data)

    return {'status': 'success', 'data': ou}, 201


@organizations_bp.route('/<int:org_id>/units/<int:ou_id>', methods=['PUT'])
async def update_organizational_unit(org_id: int, ou_id: int) -> Tuple[Dict[str, Any], int]:
    """Update organizational unit (OU).

    Args:
        org_id: Organization ID
        ou_id: Organizational unit ID

    JSON body:
        name: OU name
        description: OU description
        parent_id: Parent OU ID
        policy_data: JSON policy data
        status: Status (active, inactive, archived)

    Returns:
        JSON response with updated OU
    """
    data = await request.get_json()
    if not data:
        return {'status': 'error', 'message': 'Request body is required'}, 400

    service = OrganizationService(current_app.db)
    ou = await service.update_organizational_unit(org_id, ou_id, data)

    if not ou:
        return {'status': 'error', 'message': 'Organizational unit not found'}, 404

    return {'status': 'success', 'data': ou}, 200


@organizations_bp.route('/<int:org_id>/units/<int:ou_id>', methods=['DELETE'])
async def delete_organizational_unit(org_id: int, ou_id: int) -> Tuple[Dict[str, Any], int]:
    """Delete organizational unit (OU).

    Args:
        org_id: Organization ID
        ou_id: Organizational unit ID

    Returns:
        JSON response
    """
    service = OrganizationService(current_app.db)
    success = await service.delete_organizational_unit(org_id, ou_id)

    if not success:
        return {'status': 'error', 'message': 'Organizational unit not found'}, 404

    return {'status': 'success', 'message': 'Organizational unit deleted'}, 200
