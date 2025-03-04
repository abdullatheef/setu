from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, Expense, ExpenseGroup
from .. import db
from datetime import datetime
from flask import request
from sqlalchemy import func
from sqlalchemy.orm import joinedload

expense_bp = Blueprint('expense', __name__)

@expense_bp.route('/', methods=['POST'])
@jwt_required()
def add_expense():
    data = request.get_json()

    # Validate input
    if 'total_amount' not in data or 'date' not in data or 'note' not in data or 'split' not in data:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    from_user = g.user

    if not from_user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    try:
        date = datetime.strptime(data['date'], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Save expense group
    expense_group = ExpenseGroup(created_by=from_user.id, total_amount=data['total_amount'], note=data['note'], date=date)
    db.session.add(expense_group)
    db.session.flush()  # Get group ID before commit

    # Save individual expenses
    for entry in data['split']:
        to_user = User.query.filter_by(username=entry['username']).first()

        if not to_user:
            return jsonify({"status": "error", "message": f"User '{entry['username']}' not found"}), 404

        expense = Expense(
            group_id=expense_group.id,
            from_user_id=from_user.id,  # Always the logged-in user
            to_user_id=to_user.id,
            amount=entry['amount']
        )
        db.session.add(expense)

    db.session.commit()
    return jsonify({"status": "success", "message": "Expense group added successfully"}), 201





@expense_bp.route('/', methods=['GET'])
@jwt_required()
def list_expenses():
    user = g.user

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    total_balance = 0
    expenses_list = []

    # Fetch all expenses where the user is involved (for total_balance calculation)
    all_expenses = Expense.query.filter(
        (Expense.from_user_id == user.id) | (Expense.to_user_id == user.id)
    ).all()

    # Calculate total balance from all expenses (active only)
    for expense in all_expenses:
        is_payer = expense.from_user_id == user.id
        amount = expense.amount if is_payer else -expense.amount
        if expense.status == "active":
            total_balance += amount

    # Fetch only paginated results, joining with ExpenseGroup
    paginated_expenses = Expense.query.join(ExpenseGroup).filter(
        (Expense.from_user_id == user.id) | (Expense.to_user_id == user.id)
    ).order_by(ExpenseGroup.date.desc()).options(joinedload(Expense.group))\
    .paginate(page=page, per_page=per_page, error_out=False)

    # Process paginated expenses
    for expense in paginated_expenses.items:
        is_payer = expense.from_user_id == user.id
        counterparty = User.query.get(expense.to_user_id if is_payer else expense.from_user_id)

        expenses_list.append({
            "id": expense.id,
            "username": counterparty.username,
            "amount": abs(expense.amount),
            "type": "credit" if is_payer else "debit",
            "date": expense.group.date.strftime("%Y-%m-%d"),  # Using group date
            "status": expense.status
        })

    return jsonify({
        "total_balance": total_balance,
        "expenses": expenses_list,
        "pagination": {
            "page": paginated_expenses.page,
            "per_page": paginated_expenses.per_page,
            "total_pages": paginated_expenses.pages,
            "total_items": paginated_expenses.total
        }
    }), 200


@expense_bp.route('/<int:expense_id>/close', methods=['PUT'])
@jwt_required()
def close_expense(expense_id):
    user = g.user

    expense = Expense.query.filter_by(id=expense_id).first()

    if not expense:
        return jsonify({"status": "error", "message": "Expense not found"}), 404

    if expense.from_user_id != user.id and expense.to_user_id != user.id:
        return jsonify({"status": "error", "message": "Not authorized"}), 403

    expense.status = "closed"
    db.session.commit()

    return jsonify({"message": "Expense marked as closed"}), 200




@expense_bp.route('/net-settlement', methods=['GET'])
@jwt_required()
def get_net_settlement():
    user = g.user

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    usernames = request.args.getlist('usernames')  # List of usernames
    if not usernames:
        return jsonify({"status": "error", "message": "No usernames provided"}), 400

    total_balance = 0
    settlements = []

    for username in usernames:
        counterparty = User.query.filter_by(username=username).first()
        if not counterparty:
            continue

        # Total amount current user has given to counterparty
        total_given = db.session.query(func.sum(Expense.amount)).filter(
            Expense.from_user_id == user.id,
            Expense.to_user_id == counterparty.id,
            Expense.status == "active"
        ).scalar() or 0

        # Total amount current user has received from counterparty
        total_received = db.session.query(func.sum(Expense.amount)).filter(
            Expense.from_user_id == counterparty.id,
            Expense.to_user_id == user.id,
            Expense.status == "active"
        ).scalar() or 0

        # Corrected Net Amount Calculation
        net_amount = total_given - total_received  # Positive means they owe you, Negative means you owe them
        total_balance += net_amount

        settlements.append({
            "username": username,
            "amount": abs(net_amount),
            "type": "credit" if net_amount > 0 else "debit"  # Fix here
        })

    return jsonify({
        "total_balance": total_balance,
        "settlements": settlements
    }), 200


@expense_bp.route('/net-settlement', methods=['POST'])
@jwt_required()
def settle_expenses():
    user = g.user

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    data = request.get_json()
    username = data.get("username")

    if not username:
        return jsonify({"status": "error", "message": "Username is required"}), 400

    counterparty = User.query.filter_by(username=username).first()
    if not counterparty:
        return jsonify({"status": "error", "message": "User not found"}), 404

    # Update all active expenses between current user and counterparty
    db.session.query(Expense).filter(
        ((Expense.from_user_id == user.id) & (Expense.to_user_id == counterparty.id)) |
        ((Expense.from_user_id == counterparty.id) & (Expense.to_user_id == user.id)),
        Expense.status == "active"
    ).update({"status": "closed"}, synchronize_session=False)

    db.session.commit()

    return jsonify({"message": f"All expenses with {username} have been settled."}), 200
