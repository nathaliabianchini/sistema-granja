from flask import Flask, redirect, url_for, session

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'sua-chave-secreta'
    
    # Configurar banco
    from app.models.database import db, Lote, Producao, Usuarios, EstoqueVacina, Vacinacao
    if not db.is_connection_usable():
        db.connect()
    db.create_tables([Lote, Producao, Usuarios, EstoqueVacina, Vacinacao], safe=True)

    # Registrar blueprints WEB (páginas)
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.producao_routes import producao_web
    from app.routes.aves_routes import aves_bp
    from app.routes.estoque_vacina_routes import estoque_vacina_web
    from app.routes.vacina_routes import vacina_web 
    from app.api.endpoints.producao_api import producao_api
    from app.routes.routes import bp as api_routes
    from app.routes.insumo_routes import insumo_web 

    # Registrar todos os blueprints
    app.register_blueprint(auth_bp)                           
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')  
    app.register_blueprint(producao_web, url_prefix='/producoes')
    app.register_blueprint(aves_bp)
    
    app.register_blueprint(estoque_vacina_web)  
    app.register_blueprint(vacina_web)          
    
    app.register_blueprint(producao_api)                      
    app.register_blueprint(api_routes, url_prefix='/api')     

    app.register_blueprint(insumo_web, url_prefix='/insumos') 
    
    # Rota principal - VERIFICAR LOGIN PRIMEIRO
    @app.route('/')
    def index():
        # Se o usuário NÃO está logado, vai para o login
        if not session.get('user_logged_in'):
            return redirect(url_for('auth.login'))
        # Se está logado, vai para o dashboard
        return redirect(url_for('dashboard.index'))
    
    return app