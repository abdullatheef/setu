from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User
from .. import db

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/', methods=['GET'])
@jwt_required()
def get_profile():
    user = g.user
    # user = User.query.filter_by(username=current_user['username']).first()
    return jsonify({'username': user.username, 'email': user.email, 'phone': user.phone}), 200

@profile_bp.route('/', methods=['PUT'])
@jwt_required()
def update_profile():
    data = request.get_json()
    user = g.user
    if 'email' in data:
        user.email = data['email']
    if 'phone' in data:
        user.phone = data['phone']
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200
