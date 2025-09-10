from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')  # ou configure direto

    db.init_app(app)
    migrate.init_app(app, db)

    # registre blueprints/rotas aqui

    return app