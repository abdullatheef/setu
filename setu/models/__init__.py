from .. import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))

    # Sent friend requests
    # sent_friendships = db.relationship(
    #     'Friend', foreign_keys='Friend.user_id', backref='requester', lazy=True, overlaps="requester,sent_friendships"
    # )

    # # Received friend requests
    # received_friendships = db.relationship(
    #     'Friend', foreign_keys='Friend.friend_id', backref='receiver', lazy=True, overlaps="receiver,received_friendships"
    # )


class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # User who initiated the friendship
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Friend's user ID
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Define relationships with overlaps to avoid conflicts
    user = db.relationship("User", foreign_keys=[user_id], backref="friends")
    friend = db.relationship("User", foreign_keys=[friend_id], backref="friend_of")



class ConnectionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')




class ExpenseGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(255))
    date = db.Column(db.Date, nullable=False)

    creator = db.relationship('User', backref='expense_groups')
    expenses = db.relationship('Expense', backref='group', lazy=True, cascade="all, delete-orphan")

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('expense_group.id'), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Who paid
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)    # Who owes
    amount = db.Column(db.Float, nullable=False)

    from_user = db.relationship('User', foreign_keys=[from_user_id], backref='expenses_paid')
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='expenses_owed')
    status = db.Column(db.String(10), nullable=False, default="active")  # 'active' or 'closed'


