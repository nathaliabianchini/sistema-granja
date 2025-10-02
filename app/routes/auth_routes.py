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
            if form.username.data == 'admin' and form.password.data == '123123':
                session['user_logged_in'] = True
                session['user_email'] = 'Administrador'
                session['user_tipo'] = 'administrador'
                flash('Login de administrador realizado com sucesso!', 'success')
                return redirect(url_for('dashboard.index'))
            
            # Verifica se o usuário existe no banco
            from app.models.database import Usuarios
            try:
                usuario = Usuarios.get(
                    (Usuarios.username == form.username.data) & 
                    (Usuarios.senha == form.password.data)
                )

                session['user_logged_in'] = True
                session['user_email'] = usuario.username
                session['user_tipo'] = usuario.tipo_usuario
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard.index'))
                
            except Usuarios.DoesNotExist:
                flash('Usuário ou senha inválidos.', 'danger')
                return render_template('auth/login.html', form=form)
            
        except Exception as e:
            flash('Erro interno do sistema. Tente novamente.', 'danger')
            return render_template('auth/login.html', form=form)
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register_user():
    # Apenas administradores podem acessar
    if not session.get('user_logged_in') or session.get('user_tipo') != 'administrador':
        flash('Acesso negado. Apenas administradores podem registrar usuários.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        try:            
            from app.models.database import Usuarios
                        
            # Verificar se username já existe
            try:
                usuario_existente = Usuarios.get(Usuarios.username == form.username.data)
                flash('Nome de usuário já existe! Escolha outro.', 'danger')
                return render_template('auth/register.html', form=form)
            except Usuarios.DoesNotExist:
                pass
                        
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
                        
            # Criar novo usuário
            novo_usuario = Usuarios.create(**dados_usuario)
                        
            flash(f'✅ Usuário "{form.nome.data}" cadastrado com sucesso! Username: {form.username.data}', 'success')
            
            # Limpar formulário após sucesso
            return redirect(url_for('auth.register_user'))
            
        except Exception as e:         
            flash(f'❌ Erro ao cadastrar usuário: {str(e)}', 'danger')
    
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'❌ {field}: {error}', 'danger')
    
    return render_template('auth/register.html', form=form)
    
@auth_bp.route('/usuarios/editar/<int:id_usuario>', methods=['GET', 'POST'])
def editar_usuario(id_usuario):
    # Apenas administradores podem acessar
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
        flash(f'❌ Erro ao carregar usuário: {str(e)}', 'danger')
        return redirect(url_for('auth.listar_usuarios'))
    
    form = RegisterForm()
    
    if request.method == 'POST':

        senha_original = form.senha.data
        senha_vazia = not senha_original or senha_original.strip() == ''
        
        if senha_vazia:
            form.senha.data = 'password123'
            form.confirma_senha.data = 'password123'  
        
        form_valido = form.validate()
        
        if form_valido:
            try:
                
                # Atualizar dados do usuário
                usuario.nome = form.nome.data
                usuario.username = form.username.data
                usuario.email = form.email.data
                usuario.cpf = form.cpf.data
                
                # Só atualiza senha se foi preenchida originalmente
                if not senha_vazia:
                    usuario.senha = senha_original
                                
                usuario.tipo_usuario = form.tipo_usuario.data
                usuario.id_granja = form.id_granja.data
                usuario.sexo = form.sexo.data
                usuario.data_nascimento = form.data_nascimento.data
                usuario.endereco = form.endereco.data
                usuario.data_admissao = form.data_admissao.data
                usuario.carteira_trabalho = form.carteira_trabalho.data
                usuario.telefone = form.telefone.data
                
                usuario.save()
                
                flash(f'✅ Usuário "{usuario.nome}" atualizado com sucesso!', 'success')
                return redirect(url_for('auth.listar_usuarios'))
                
            except Exception as e:
                flash(f'❌ Erro ao atualizar usuário: {str(e)}', 'danger')
        else:
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


@auth_bp.route('/sair')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/usuarios')
def listar_usuarios():
    # Apenas administradores podem acessar
    if not session.get('user_logged_in') or session.get('user_tipo') != 'administrador':
        flash('Acesso negado. Apenas administradores podem gerenciar usuários.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:      
        from app.models.database import db, Usuarios
        
        # Garantir conexão
        if db.is_closed():
            db.connect()
        
        # Buscar usuários
        usuarios = list(Usuarios.select())
        
        return render_template('auth/listar_usuarios.html', usuarios=usuarios)
        
    except Exception as e: 
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
    # Apenas administradores podem acessar
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