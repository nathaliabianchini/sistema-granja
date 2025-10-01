from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.forms.auth_forms import LoginForm, RegisterForm
from app.controllers.auth_controller import sign_in, register
import json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Se já está logado, vai direto para o dashboard
    if session.get('user_logged_in'):
        return redirect(url_for('dashboard.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        try:
            # VERIFICAR SE É O ADMINISTRADOR FIXO
            if form.username.data == 'admin' and form.password.data == '123123':
                session['user_logged_in'] = True
                session['user_email'] = 'Administrador'
                session['user_tipo'] = 'administrador'
                flash('Login de administrador realizado com sucesso!', 'success')
                return redirect(url_for('dashboard.index'))
            
            # VERIFICAR SE USUÁRIO EXISTE NO BANCO DE DADOS
            from app.models.database import Usuarios
            try:
                # Buscar usuário pelo username
                usuario = Usuarios.get(
                    (Usuarios.username == form.username.data) & 
                    (Usuarios.senha == form.password.data)
                )
                
                # Se chegou aqui, usuário existe e senha está correta
                session['user_logged_in'] = True
                session['user_email'] = usuario.username
                session['user_tipo'] = usuario.tipo_usuario
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard.index'))
                
            except Usuarios.DoesNotExist:
                # Usuário não encontrado ou senha incorreta
                flash('Usuário ou senha inválidos.', 'danger')
                return render_template('auth/login.html', form=form)
            
        except Exception as e:
            flash('Erro interno do sistema. Tente novamente.', 'danger')
            return render_template('auth/login.html', form=form)
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register_user():
    # APENAS ADMINISTRADORES PODEM ACESSAR REGISTRO
    if not session.get('user_logged_in') or session.get('user_tipo') != 'administrador':
        flash('Acesso negado. Apenas administradores podem registrar usuários.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = RegisterForm()
    
    print(f"DEBUG - Form submitted: {form.validate_on_submit()}")
    print(f"DEBUG - Form data: {form.data}")
    print(f"DEBUG - Form errors: {form.errors}")
    
    if form.validate_on_submit():
        try:
            print("DEBUG - Iniciando cadastro...")
            
            # CRIAR USUÁRIO DIRETAMENTE NO BANCO
            from app.models.database import Usuarios
            
            print("DEBUG - Importou Usuarios")
            
            # Verificar se username já existe
            try:
                usuario_existente = Usuarios.get(Usuarios.username == form.username.data)
                flash('Nome de usuário já existe! Escolha outro.', 'danger')
                return render_template('auth/register.html', form=form)
            except Usuarios.DoesNotExist:
                print("DEBUG - Username disponível")
                pass
            except Exception as e:
                print(f"DEBUG - Erro ao verificar username: {e}")
            
            # DADOS PARA CRIAR
            dados_usuario = {
                'nome': form.nome.data,
                'username': form.username.data,
                'email': form.email.data,
                'cpf': form.cpf.data,
                'senha': form.senha.data,
                'tipo_usuario': form.tipo_usuario.data,
                'id_granja': form.id_granja.data,
                'sexo': form.sexo.data,
                'data_nascimento': form.data_nascimento.data,
                'endereco': form.endereco.data,
                'data_admissao': form.data_admissao.data,
                'carteira_trabalho': form.carteira_trabalho.data,
                'telefone': form.telefone.data
            }
            
            print(f"DEBUG - Dados para criar: {dados_usuario}")
            
            # Criar novo usuário
            novo_usuario = Usuarios.create(**dados_usuario)
            
            print(f"DEBUG - Usuário criado com ID: {novo_usuario.id_usuario}")
            
            flash(f'✅ Usuário "{form.nome.data}" cadastrado com sucesso! Username: {form.username.data}', 'success')
            
            # Limpar formulário após sucesso
            return redirect(url_for('auth.register_user'))
            
        except Exception as e:
            print(f"DEBUG - ERRO DETALHADO: {e}")
            print(f"DEBUG - Tipo do erro: {type(e)}")
            import traceback
            print(f"DEBUG - Traceback: {traceback.format_exc()}")
            
            flash(f'❌ Erro ao cadastrar usuário: {str(e)}', 'danger')
    
    # Se chegou aqui, formulário não foi validado ou é GET
    if form.errors:
        print(f"DEBUG - Erros de validação: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'❌ {field}: {error}', 'danger')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/debug/tabela')
def debug_tabela():
    try:
        from app.models.database import db, Usuarios
        
        # Verificar conexão
        if not db.is_connection_usable():
            db.connect()
        
        # Tentar criar tabela se não existir
        db.create_tables([Usuarios], safe=True)
        
        # Contar usuários
        total = Usuarios.select().count()
        
        return f"""
        <h1>Debug - Banco de Dados</h1>
        <p><strong>Conexão:</strong> ✅ OK</p>
        <p><strong>Tabela usuarios:</strong> ✅ Criada</p>
        <p><strong>Total de usuários:</strong> {total}</p>
        <p><a href="/register">Voltar para cadastro</a></p>
        """
        
    except Exception as e:
        return f"""
        <h1>Debug - ERRO</h1>
        <p><strong>Erro:</strong> {e}</p>
        <p><strong>Tipo:</strong> {type(e)}</p>
        """

@auth_bp.route('/recrear-tabela-usuarios')
def recrear_tabela_usuarios():
    try:
        from app.models.database import db, Usuarios
        from datetime import date
        
        html = "<h1>🔧 RECRIANDO TABELA USUARIOS</h1>"
        
        # 1. Conectar ao banco
        if db.is_closed():
            db.connect()
        html += "<p>✅ Conectado ao banco</p>"
        
        # 2. DELETAR tabela antiga (isso vai apagar dados!)
        db.drop_tables([Usuarios], safe=True)
        html += "<p>🗑️ Tabela antiga removida</p>"
        
        # 3. CRIAR tabela nova com estrutura correta
        db.create_tables([Usuarios], safe=True)
        html += "<p>✅ Nova tabela criada</p>"
        
        # 4. Criar usuário de teste
        usuario_teste = Usuarios.create(
            nome='Usuario Teste',
            username='teste',
            email='teste@granja.com',
            cpf='12345678901',
            senha='123456',
            tipo_usuario='funcionario',
            id_granja='GRANJA001',
            sexo='M',
            data_nascimento=date(1990, 1, 1),
            endereco='Rua Teste, 123',
            data_admissao=date.today(),
            carteira_trabalho='123456',
            telefone='11999999999'
        )
        html += f"<p>✅ Usuário de teste criado (ID: {usuario_teste.id_usuario})</p>"
        
        # 5. Testar seleção
        usuarios = list(Usuarios.select())
        html += f"<p>✅ Teste de SELECT: {len(usuarios)} usuários encontrados</p>"
        
        # 6. Mostrar estrutura da tabela
        html += "<h2>📋 Estrutura da Tabela:</h2>"
        cursor = db.execute_sql("PRAGMA table_info(usuarios)")
        colunas = cursor.fetchall()
        
        html += "<table border='1'><tr><th>ID</th><th>Nome da Coluna</th><th>Tipo</th><th>Not Null</th><th>Default</th><th>PK</th></tr>"
        for coluna in colunas:
            html += f"<tr><td>{coluna[0]}</td><td>{coluna[1]}</td><td>{coluna[2]}</td><td>{coluna[3]}</td><td>{coluna[4]}</td><td>{coluna[5]}</td></tr>"
        html += "</table>"
        
        html += "<h2>🧪 CREDENCIAIS DE TESTE:</h2>"
        html += "<ul>"
        html += "<li><strong>Username:</strong> teste</li>"
        html += "<li><strong>Senha:</strong> 123456</li>"
        html += "</ul>"
        
        html += "<br><p><a href='/usuarios'>🔗 Testar módulo usuários</a></p>"
        html += "<p><a href='/'>🏠 Voltar ao sistema</a></p>"
        
        return html
        
    except Exception as e:
        import traceback
        return f"""
        <h1>❌ ERRO AO RECRIAR TABELA</h1>
        <p><strong>Erro:</strong> {e}</p>
        <p><strong>Tipo:</strong> {type(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        """   
    
@auth_bp.route('/usuarios/editar/<int:id_usuario>', methods=['GET', 'POST'])
def editar_usuario(id_usuario):
    # APENAS ADMINISTRADORES PODEM ACESSAR
    if not session.get('user_logged_in') or session.get('user_tipo') != 'administrador':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:
        from app.models.database import Usuarios
        usuario = Usuarios.get_by_id(id_usuario)
        
    except Usuarios.DoesNotExist:
        flash('❌ Usuário não encontrado.', 'danger')
        return redirect(url_for('auth.listar_usuarios'))
    except Exception as e:
        print(f"DEBUG: Erro ao buscar usuário: {str(e)}")
        flash(f'❌ Erro ao carregar usuário: {str(e)}', 'danger')
        return redirect(url_for('auth.listar_usuarios'))
    
    form = RegisterForm()
    
    if request.method == 'POST':
        print("="*50)
        print("DEBUG: POST recebido!")
        print(f"DEBUG: form.data ANTES: {form.data}")
        print(f"DEBUG: form.errors ANTES: {form.errors}")
        
        # CAPTURAR SENHA ORIGINAL
        senha_original = form.senha.data
        senha_vazia = not senha_original or senha_original.strip() == ''
        print(f"DEBUG: Senha original: '{senha_original}'")
        print(f"DEBUG: Senha vazia: {senha_vazia}")
        
        # Se senha vazia, colocar valor temporário EM AMBOS OS CAMPOS
        if senha_vazia:
            form.senha.data = 'password123'
            form.confirma_senha.data = 'password123'  # ← ADICIONADO
            print("DEBUG: Senha e confirmação temporárias definidas")
        
        # VALIDAR FORMULÁRIO
        form_valido = form.validate()
        print(f"DEBUG: Formulário válido: {form_valido}")
        print(f"DEBUG: form.errors DEPOIS: {form.errors}")
        
        if form_valido:
            try:
                print("DEBUG: Iniciando atualização do usuário...")
                
                # Atualizar dados do usuário
                usuario.nome = form.nome.data
                usuario.username = form.username.data
                usuario.email = form.email.data
                usuario.cpf = form.cpf.data
                
                # Só atualiza senha se foi preenchida originalmente
                if not senha_vazia:
                    usuario.senha = senha_original
                    print(f"DEBUG: Senha atualizada para: {senha_original}")
                else:
                    print("DEBUG: Senha mantida (não alterada)")
                
                usuario.tipo_usuario = form.tipo_usuario.data
                usuario.id_granja = form.id_granja.data
                usuario.sexo = form.sexo.data
                usuario.data_nascimento = form.data_nascimento.data
                usuario.endereco = form.endereco.data
                usuario.data_admissao = form.data_admissao.data
                usuario.carteira_trabalho = form.carteira_trabalho.data
                usuario.telefone = form.telefone.data
                
                print("DEBUG: Tentando salvar no banco...")
                usuario.save()
                print("DEBUG: Usuário salvo com sucesso!")
                
                flash(f'✅ Usuário "{usuario.nome}" atualizado com sucesso!', 'success')
                return redirect(url_for('auth.listar_usuarios'))
                
            except Exception as e:
                print(f"DEBUG: ERRO ao salvar: {str(e)}")
                import traceback
                print(f"DEBUG: Traceback: {traceback.format_exc()}")
                flash(f'❌ Erro ao atualizar usuário: {str(e)}', 'danger')
        else:
            print("DEBUG: Formulário NÃO VÁLIDO!")
            print("DEBUG: Listando erros detalhados:")
            for field_name, field_errors in form.errors.items():
                print(f"  - {field_name}: {field_errors}")
        
        print("="*50)
    
    # Preencher formulário com dados atuais (apenas no GET)
    if request.method == 'GET':
        form.nome.data = usuario.nome
        form.username.data = usuario.username
        form.email.data = usuario.email
        form.cpf.data = usuario.cpf
        form.tipo_usuario.data = usuario.tipo_usuario
        form.id_granja.data = usuario.id_granja
        form.sexo.data = usuario.sexo
        form.data_nascimento.data = usuario.data_nascimento
        form.endereco.data = usuario.endereco
        form.data_admissao.data = usuario.data_admissao
        form.carteira_trabalho.data = usuario.carteira_trabalho
        form.telefone.data = usuario.telefone
    
    return render_template('auth/editar_usuarios.html', form=form, usuario=usuario)

@auth_bp.route('/debug/completo')
def debug_completo():
    html = "<h1>🔍 DIAGNÓSTICO COMPLETO</h1>"
    
    try:
        # 1. Testar importação
        html += "<h2>1. Importações:</h2>"
        from app.models.database import db, Usuarios
        html += "✅ Importação OK<br>"
        
        # 2. Testar conexão
        html += "<h2>2. Conexão com Banco:</h2>"
        if db.is_closed():
            db.connect()
        html += "✅ Conexão OK<br>"
        
        # 3. Verificar se tabela existe
        html += "<h2>3. Verificar Tabela:</h2>"
        tabelas = db.get_tables()
        html += f"Tabelas no banco: {tabelas}<br>"
        
        if 'usuarios' in tabelas:
            html += "✅ Tabela 'usuarios' existe<br>"
        else:
            html += "❌ Tabela 'usuarios' NÃO existe<br>"
            # Criar tabela
            db.create_tables([Usuarios], safe=True)
            html += "✅ Tabela criada agora<br>"
        
        # 4. Testar seleção
        html += "<h2>4. Testar SELECT:</h2>"
        usuarios = list(Usuarios.select())
        html += f"✅ SELECT OK - {len(usuarios)} usuários encontrados<br>"
        
        # 5. Listar usuários
        html += "<h2>5. Usuários no Banco:</h2>"
        if usuarios:
            html += "<table border='1'><tr><th>ID</th><th>Nome</th><th>Username</th></tr>"
            for u in usuarios:
                html += f"<tr><td>{u.id_usuario}</td><td>{u.nome}</td><td>{u.username}</td></tr>"
            html += "</table>"
        else:
            html += "❌ Nenhum usuário no banco<br>"
            
            # Criar usuário de teste
            html += "<h3>Criando usuário de teste...</h3>"
            from datetime import date
            teste = Usuarios.create(
                nome='Usuario Teste',
                username='teste',
                email='teste@teste.com',
                cpf='12345678901',
                senha='123456',
                tipo_usuario='funcionario',
                id_granja='GRANJA001',
                sexo='M',
                data_nascimento=date.today(),
                endereco='Rua Teste, 123',
                data_admissao=date.today(),
                carteira_trabalho='123456',
                telefone='11999999999'
            )
            html += f"✅ Usuário teste criado com ID: {teste.id_usuario}<br>"
        
        html += "<br><a href='/usuarios'>🔗 Testar módulo usuários</a>"
        html += "<br><a href='/'>🏠 Voltar ao sistema</a>"
        
    except Exception as e:
        html += f"<h2>❌ ERRO:</h2>"
        html += f"<p><strong>Erro:</strong> {e}</p>"
        html += f"<p><strong>Tipo:</strong> {type(e)}</p>"
        
        import traceback
        html += f"<pre>{traceback.format_exc()}</pre>"
    
    return html

@auth_bp.route('/sair')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/usuarios')
def listar_usuarios():
    # APENAS ADMINISTRADORES PODEM ACESSAR
    if not session.get('user_logged_in') or session.get('user_tipo') != 'administrador':
        flash('Acesso negado. Apenas administradores podem gerenciar usuários.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:
        # Debug detalhado
        print("DEBUG: Iniciando listar_usuarios...")
        
        from app.models.database import db, Usuarios
        print("DEBUG: Importação OK")
        
        # Garantir conexão
        if db.is_closed():
            db.connect()
        print("DEBUG: Conexão OK")
        
        # Tentar criar tabela se não existir
        db.create_tables([Usuarios], safe=True)
        print("DEBUG: Tabela verificada/criada")
        
        # Buscar usuários
        usuarios = list(Usuarios.select())
        print(f"DEBUG: {len(usuarios)} usuários encontrados")
        
        return render_template('auth/listar_usuarios.html', usuarios=usuarios)
        
    except Exception as e:
        print(f"DEBUG: ERRO DETALHADO: {e}")
        print(f"DEBUG: Tipo do erro: {type(e)}")
        import traceback
        print(f"DEBUG: Traceback completo: {traceback.format_exc()}")
        
        flash(f'Erro detalhado: {str(e)}', 'danger')
        return redirect(url_for('dashboard.index'))
    
@auth_bp.route('/usuarios/excluir/<int:id_usuario>', methods=['POST'])
def excluir_usuario(id_usuario):
    # APENAS ADMINISTRADORES PODEM ACESSAR
    if not session.get('user_logged_in') or session.get('user_tipo') != 'administrador':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:
        from app.models.database import Usuarios
        
        # CORREÇÃO: Usar sintaxe correta
        usuario = Usuarios.get(Usuarios.id_usuario == id_usuario)
        nome_usuario = usuario.nome
        usuario.delete_instance()
        
        flash(f'✅ Usuário "{nome_usuario}" excluído com sucesso!', 'success')
    except Usuarios.DoesNotExist:
        flash('❌ Usuário não encontrado.', 'danger')
    except Exception as e:
        flash(f'❌ Erro ao excluir usuário: {str(e)}', 'danger')
    
    return redirect(url_for('auth.listar_usuarios'))



@auth_bp.route('/usuarios/toggle/<int:id_usuario>', methods=['POST'])
def toggle_usuario(id_usuario):
    # APENAS ADMINISTRADORES PODEM ACESSAR
    if not session.get('user_logged_in') or session.get('user_tipo') != 'administrador':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:
        from app.models.database import Usuarios
        usuario = Usuarios.get(Usuarios.id_usuario == id_usuario)
        # Assumindo que há um campo 'ativo' no modelo
        usuario.ativo = not usuario.ativo
        usuario.save()
        status = "ativado" if usuario.ativo else "desativado"
        flash(f'Usuário {status} com sucesso!', 'success')
    except Exception as e:
        flash('Erro ao alterar status do usuário.', 'danger')
    
    return redirect(url_for('auth.listar_usuarios'))