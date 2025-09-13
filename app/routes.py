from flask import Blueprint, request, jsonify
from app.controllers.auth_controller import register, sign_in
from app.controllers.usuario_controller import get_user, get_users, deactivate_user
from app.controllers.aves_controller import register_poultry, get_poultries, get_poultry, update_poultry, delete_poultry
from app.controllers.gerenciamento_usuario_controller import update_user_data, get_user_by_cpf, change_password, get_user_activity_logs, get_all_users_for_admin, forgot_password
from app.controllers.notificacoes_controller import create_notification, get_notifications, delete_notifications, get_user_notifications, mark_notification_as_read, get_notifications_count, get_notification_history, get_notifications_grouped
from app.decorators import production_access, read_only_access, admin_required
from datetime import datetime

bp = Blueprint('routes', __name__)

@bp.route('/api/auth/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        
        required_fields = ['nome', 'email', 'cpf', 'senha', 'tipo_usuario', 'id_granja',
                          'data_nascimento', 'endereco', 'data_admissao', 
                          'carteira_trabalho', 'telefone']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        data_nascimento = datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date()
        data_admissao = datetime.strptime(data['data_admissao'], '%Y-%m-%d').date()
        
        return register(
            nome=data['nome'],
            email=data['email'],
            cpf=data['cpf'],
            senha=data['senha'],
            tipo_usuario=data['tipo_usuario'],
            id_granja=data['id_granja'],
            sexo=data['sexo'],
            data_nascimento=data_nascimento,
            endereco=data['endereco'],
            data_admissao=data_admissao,
            carteira_trabalho=data['carteira_trabalho'],
            telefone=data['telefone']
        )
        
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

@bp.route('/api/auth/login', methods=['POST'])
def login_user():
    try:
        data = request.get_json()
        
        if 'email' not in data or 'senha' not in data:
            return jsonify({'error': 'Email and password are required'}), 400

        return sign_in(data['email'], data['senha'])
        
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

@bp.route('/api/users', methods=['GET'])
def list_users():
    return get_users()

@bp.route('/api/users/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    return get_user(user_id)

@bp.route('/api/users/<user_id>/deactivate', methods=['POST'])
def deactivate_user_route(user_id):
    return deactivate_user(user_id)

@bp.route('/api/register-grange', methods=['POST'])
def register_grange():
    from app.controllers.auth_controller import register_grange
    return register_grange()


@bp.route('/api/register-poultry', methods=['POST'])
@production_access  
def register_poultry_route():
    try:
        data = request.get_json()

        required_fields = ['id_lote', 'raca_ave', 'data_nascimento', 'tempo_de_vida', 'media_peso', 
                          'caracteristicas_geneticas', 'tipo_alojamento', 'historico_vacinas']

        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório não preenchido: {field}'}), 400

        data_nascimento = datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date()

        return register_poultry(
            id_lote=data['id_lote'],
            raca_ave=data['raca_ave'],
            data_nascimento=data_nascimento,
            tempo_de_vida=data['tempo_de_vida'],
            media_peso=data['media_peso'],
            caracteristicas_geneticas=data['caracteristicas_geneticas'],
            tipo_alojamento=data['tipo_alojamento'],
            historico_vacinas=data['historico_vacinas'],
            observacoes=data.get('observacoes')
        )

    except ValueError as e:
        return jsonify({'error': f'Formato de data inválido: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@bp.route('/api/poultries', methods=['GET'])
@read_only_access  
def list_poultries():
    id_ave = request.args.get('id_ave')
    raca = request.args.get('raca')
    id_lote = request.args.get('id_lote')
    data_nascimento = request.args.get('data_nascimento')
    incluir_inativas = request.args.get('incluir_inativas', 'false').lower() == 'true'
    
    return get_poultries(id_ave=id_ave, raca=raca, id_lote=id_lote, 
                        data_nascimento=data_nascimento, incluir_inativas=incluir_inativas)

@bp.route('/api/poultries/<ave_id>', methods=['GET'])
@read_only_access 
def get_poultry_by_id(ave_id):
    return get_poultry(ave_id)

@bp.route('/api/poultries/<ave_id>', methods=['PUT'])
@production_access  
def update_poultry_route(ave_id):
    try:
        data = request.get_json()
        return update_poultry(ave_id, **data)
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@bp.route('/api/poultries/<ave_id>', methods=['DELETE'])
@admin_required  
def delete_poultry_route(ave_id):
    try:
        data = request.get_json()
        motivo_exclusao = data.get('motivo_exclusao')
        
        if not motivo_exclusao:
            return jsonify({'error': 'Motivo da exclusão é obrigatório'}), 400
            
        return delete_poultry(ave_id, motivo_exclusao)
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@bp.route('/api/users/<user_id>/update', methods=['PUT'])
@admin_required
def update_user_route(user_id):
    return update_user_data(user_id)

@bp.route('/api/users/search-by-cpf', methods=['POST'])
@read_only_access
def search_user_by_cpf():
    return get_user_by_cpf()

@bp.route('/api/users/change-password', methods=['POST'])
@read_only_access
def change_user_password():
    return change_password()

@bp.route('/api/users/forgot-password', methods=['POST'])
def forgot_user_password():
    return forgot_password()

@bp.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_list_users():
    return get_all_users_for_admin()

@bp.route('/api/admin/activity-logs', methods=['GET'])
@admin_required
def admin_activity_logs():
    user_id = request.args.get('user_id')
    return get_user_activity_logs(user_id)

@bp.route('/api/admin/activity-logs/<user_id>', methods=['GET'])
@admin_required
def admin_user_activity_logs(user_id):
    return get_user_activity_logs(user_id)

@bp.route('/api/notifications/avisos', methods=['POST'])
@production_access
def create_notification_aviso():
    return create_notification()

@bp.route('/api/notifications/avisos', methods=['GET'])
@read_only_access
def list_notifications():
    return get_notifications()

@bp.route('/api/notifications/avisos/<aviso_id>', methods=['DELETE'])
@read_only_access
def delete_notification_aviso(aviso_id):
    return delete_notifications(aviso_id)

@bp.route('/api/notifications/avisos/<aviso_id>/history', methods=['GET'])
@read_only_access
def get_notification_history(aviso_id):
    return get_notification_history(aviso_id)

@bp.route('/api/notifications', methods=['GET'])
@read_only_access
def list_user_notifications():
    return get_user_notifications()

@bp.route('/api/notifications/grouped', methods=['GET'])
@read_only_access
def list_notifications_grouped():
    return get_notifications_grouped()

@bp.route('/api/notifications/<notification_id>/read', methods=['POST'])
@read_only_access
def mark_notification_read(notification_id):
    return mark_notification_as_read(notification_id)

@bp.route('/api/notifications/count', methods=['GET'])
@read_only_access
def get_notification_count():
    return get_notifications_count()

@bp.route('/api/admin/check-stock', methods=['POST'])
@admin_required
def check_stock_notifications():
    from app.utils import check_stock_levels
    try:
        low_items_count = check_stock_levels()
        if low_items_count > 0:
            return jsonify({
                'message': f'Notificação de estoque baixo criada para {low_items_count} itens'
            }), 200
        else:
            return jsonify({'message': 'Nenhum item com estoque baixo encontrado'}), 200
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@bp.route('/api/admin/notify-maintenance', methods=['POST'])
@admin_required
def send_maintenance_notification():
    from app.utils import notify_maintenance_due
    try:
        success = notify_maintenance_due()
        if success:
            return jsonify({'message': 'Notificação de manutenção enviada com sucesso'}), 200
        else:
            return jsonify({'error': 'Erro ao enviar notificação de manutenção'}), 500
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@bp.route('/api/admin/notify-reports', methods=['POST'])
@admin_required
def send_report_notification():
    from app.utils import notify_report_due
    try:
        success = notify_report_due()
        if success:
            return jsonify({'message': 'Notificação de relatório enviada com sucesso'}), 200
        else:
            return jsonify({'message': 'Notificação de relatório não é necessária hoje'}), 200
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500