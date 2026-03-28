"""Organization management routes"""
from flask import Blueprint, jsonify, request
from models import row_to_organization
from routes.auth import get_user_from_token
from penguin_dal.flask_ext import get_db

orgs_bp = Blueprint('organizations', __name__)


@orgs_bp.route('', methods=['GET'])
def list_organizations():
    """List all organization units"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    org_rows = db(db.organization_units.id > 0).select()
    return jsonify({'organizations': [row_to_organization(r).to_dict() for r in org_rows]})


@orgs_bp.route('/<int:org_id>', methods=['GET'])
def get_organization(org_id: int):
    """Get organization by ID"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    org_row = db.organization_units[org_id]
    if not org_row:
        return jsonify({'error': 'Organization not found'}), 404

    return jsonify(row_to_organization(org_row).to_dict())


@orgs_bp.route('', methods=['POST'])
def create_organization():
    """Create new organization"""
    user_id = get_user_from_token()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()

    if 'name' not in data:
        return jsonify({'error': 'Name required'}), 400

    db = get_db()
    new_id = db.organization_units.insert(
        name=data['name'],
        description=data.get('description'),
    )

    org_row = db.organization_units[new_id]
    if not org_row:
        return jsonify({'error': 'Failed to create organization'}), 500

    return jsonify(row_to_organization(org_row).to_dict()), 201
