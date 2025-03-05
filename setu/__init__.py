from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import jwt_required, get_jwt_identity, JWTManager
from flask_cors import CORS  # ✅ Import CORS

db = SQLAlchemy()
jwt = JWTManager()

def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object('setu.config.Config')

    if config:
        app.config.update(config)  # ✅ Apply test-specific config

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, supports_credentials=True)  # ✅ Enable CORS globally

    with app.app_context():
        from .auth.routes import auth_bp
        from .profile.routes import profile_bp
        from .search.routes import search_bp
        from .connections.routes import connections_bp
        from .expense.routes import expense_bp

        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(profile_bp, url_prefix='/profile')
        app.register_blueprint(search_bp, url_prefix='/search')
        app.register_blueprint(connections_bp, url_prefix='/connect')
        app.register_blueprint(expense_bp, url_prefix='/expense')

        db.create_all()
    return app


app = create_app()

@app.before_request
@jwt_required(optional=True)  # Optional allows unauthenticated requests
def load_current_user():
    from .models import User
    current_username = get_jwt_identity()
    if current_username:
        user = User.query.filter_by(username=current_username).first()
        g.user = user  # Attach user object to global request context
    else:
        g.user = None  # No user authenticated
