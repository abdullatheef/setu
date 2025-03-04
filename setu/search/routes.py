from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required
from ..models import User, Friend
from .. import db

search_bp = Blueprint('search', __name__)

@search_bp.route('/', methods=['GET'])
@jwt_required()
def search_users():
    query = request.args.get('q', '').strip()  # Get query parameter and remove leading/trailing spaces
    if not query:
        return jsonify({"status": "error", "message": "No query provided"}), 400

    # Search in username, email, and phone
    users = User.query.filter(
        (User.username.ilike(f"%{query}%")) |
        (User.email.ilike(f"%{query}%")) |
        (User.phone.ilike(f"%{query}%"))
    ).all()

    results = [{'username': user.username, 'email': user.email, 'phone': user.phone} for user in users]
    return jsonify(results), 200

@search_bp.route('/friend', methods=['GET'])
@jwt_required()
def search_friends():
    user = g.user  # Get current user from global request context

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    query = request.args.get('q', '').strip()  # Get query parameter and remove spaces
    if not query:
        return jsonify({"status": "error", "message": "No query provided"}), 400

    # Get friend IDs (user is either user_id or friend_id)
    friend_ids = db.session.query(Friend.friend_id).filter(Friend.user_id == user.id).union(
        db.session.query(Friend.user_id).filter(Friend.friend_id == user.id)
    ).subquery()

    # Search in friends
    friends = User.query.filter(
        User.id.in_(friend_ids),  # Ensure search is only among friends
        (User.username.ilike(f"%{query}%")) |
        (User.email.ilike(f"%{query}%")) |
        (User.phone.ilike(f"%{query}%"))
    ).all()

    results = [{'username': friend.username, 'email': friend.email, 'phone': friend.phone} for friend in friends]
    return jsonify(results), 200