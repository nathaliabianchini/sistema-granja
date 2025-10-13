from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    from app.models import db
    
    db.init_app(app)

    from app.routes import bp
    app.register_blueprint(bp)
    
    with app.app_context():
        db.create_all()
        from app.controllers.auth_controller import create_default_admin
        create_default_admin()

    return app