from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config # type: ignore
from controllers.producao_controller import producao_bp # type: ignore
from controllers.insumo_controller import insumo_bp # type: ignore

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    from controllers.vacina_controller import vacina_bp # type: ignore
    app.register_blueprint(vacina_bp, url_prefix='/api/vacinas')
    app.register_blueprint(producao_bp, url_prefix='/api/producao')
    app.register_blueprint(insumo_bp, url_prefix='/api/insumos')
    
    with app.app_context():
        db.create_all()
    
    return app

from flask import Flask
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)