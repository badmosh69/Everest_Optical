from flask import Flask
from config import Config
from extensions import db, login_manager, bcrypt, migrate
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from models.user import User

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    from routes.customer_routes import customer_bp
    app.register_blueprint(customer_bp)
    from routes.prescription_routes import prescription_bp
    app.register_blueprint(prescription_bp)
    from routes.order_routes import order_bp
    app.register_blueprint(order_bp)
    from routes.inventory_routes import inventory_bp
    app.register_blueprint(inventory_bp)
    from routes.audit_routes import audit_bp
    app.register_blueprint(audit_bp)

    # Register Audit Listeners
    # Move import inside to avoid circular deps if any, or top level if clean
    from services.audit_service import register_audit_listeners
    with app.app_context():
        register_audit_listeners()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
