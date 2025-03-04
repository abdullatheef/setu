from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, ConnectionRequest, Friend
from .. import db

connections_bp = Blueprint('connect', __name__)

@connections_bp.route('/', methods=['POST'])
@jwt_required()
def send_connection_request():
    requester = g.user

    data = request.get_json()
    receiver_username = data.get('receiver')

    if not receiver_username:
        return jsonify({"status": "error", "message": "Receiver username is required"}), 400

    receiver = User.query.filter_by(username=receiver_username).first()
    
    if not receiver:
        return jsonify({"status": "error", "message": "Receiver not found"}), 404

    if requester.id == receiver.id:
        return jsonify({"status": "error", "message": "You cannot send a request to yourself"}), 400

    # Check if request already exists
    existing_request = ConnectionRequest.query.filter(
        ((ConnectionRequest.requester_id == requester.id) & (ConnectionRequest.receiver_id == receiver.id)) |
        ((ConnectionRequest.requester_id == receiver.id) & (ConnectionRequest.receiver_id == requester.id))
    ).first()

    if existing_request:
        return jsonify({"status": "error", "message": "Connection request already exists"}), 400

    # Create new connection request
    connection_request = ConnectionRequest(requester_id=requester.id, receiver_id=receiver.id)
    db.session.add(connection_request)
    db.session.commit()

    return jsonify({"status": "success", "message": "Connection request sent"}), 201

@connections_bp.route('/', methods=['GET'])
@jwt_required()
def list_connection_requests():
    user = g.user

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    # Get all pending requests where the current user is the receiver
    connection_requests = ConnectionRequest.query.filter_by(receiver_id=user.id, status='pending').all()

    results = [
        {
            "id": req.id,
            "requester": User.query.get(req.requester_id).username,  # Fetching requester's username
            "status": req.status
        }
        for req in connection_requests
    ]

    return jsonify({"status": "success", "requests": results}), 200



@connections_bp.route('/<int:request_id>/action', methods=['PUT'])
@jwt_required()
def accept_connection_request(request_id):
    user = g.user

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    # Fetch the connection request
    connection_request = ConnectionRequest.query.filter_by(id=request_id, receiver_id=user.id).first()

    if not connection_request:
        return jsonify({"status": "error", "message": "Connection request not found or already accepted"}), 404
    data = request.get_json()
    action = data.get('action')
    if action not in ["accept", "deny"]:
        return jsonify({"message": "Denied the request."}), 200
    # Add both users to the friends table
    new_friendship = Friend(user_id=user.id, friend_id=connection_request.requester_id)
    # new_friendship2 = Friend(user_id=connection_request.requester_id, friend_id=user.id)

    db.session.add(new_friendship)
    # db.session.add(new_friendship2)

    # Update the connection request status
    connection_request.status = action
    db.session.commit()

    return jsonify({"status": "success", "message": "Connection request accepted"}), 200
