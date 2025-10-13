import re
from datetime import datetime, date, timedelta
from typing import Optional, List

def validate_password(password):
    if len(password) > 8:
        return False, "Senha deve ter no máximo 8 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    return True, "Senha válida"

def generate_matricula():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"MAT{timestamp}"

def validate_cpf(cpf):
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    if len(cpf) != 11:
        return False
    
    if cpf == cpf[0] * 11:
        return False
    
    def calculate_digit(cpf_partial):
        sum_val = 0
        for i, digit in enumerate(cpf_partial):
            sum_val += int(digit) * (len(cpf_partial) + 1 - i)
        remainder = sum_val % 11
        return 0 if remainder < 2 else 11 - remainder
    
    first_digit = calculate_digit(cpf[:9])
    second_digit = calculate_digit(cpf[:10])
    
    return cpf[-2:] == f"{first_digit}{second_digit}"

def validate_cnpj(cnpj):
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj) != 14:
        return False
    
    if cnpj == cnpj[0] * 14:
        return False
    
    def calculate_cnpj_digit(cnpj_partial, weights):
        sum_val = sum(int(cnpj_partial[i]) * weights[i] for i in range(len(cnpj_partial)))
        remainder = sum_val % 11
        return 0 if remainder < 2 else 11 - remainder
    
    first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    first_digit = calculate_cnpj_digit(cnpj[:12], first_weights)
    second_digit = calculate_cnpj_digit(cnpj[:13], second_weights)
    
    return cnpj[-2:] == f"{first_digit}{second_digit}"

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def format_phone(phone):
    phone = re.sub(r'[^0-9]', '', phone)
    if len(phone) == 11:
        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    elif len(phone) == 10:
        return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
    return phone

def format_cpf(cpf):
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf

def format_cnpj(cnpj):
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj) == 14:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return cnpj

def log_user_activity(user_id, action, details=None):
    from app.models import UserActivityLog, db
    
    try:
        log_entry = UserActivityLog(**{
            'user_id': user_id,
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow()
        })
        
        db.session.add(log_entry)
        db.session.commit()
    except Exception:
        pass

def create_automatic_notification(titulo: str, conteudo: str, categoria: str, prioridade: str = 'NORMAL', destinatarios: Optional[List[str]] = None):
    from app.models import Avisos, NotificacaoUsuario, HistoricoAvisos, Usuarios, db
    from app.models import CategoriaNotificacao, PrioridadeNotificacao
    
    try:
        if destinatarios is None:
            all_users = Usuarios.query.filter_by(is_ativo=True).all()
            destinatarios_ids = [user.id_usuario for user in all_users]
        else:
            destinatarios_ids = destinatarios
        
        categoria_enum = CategoriaNotificacao(categoria)
        prioridade_enum = PrioridadeNotificacao(prioridade)
        
        novo_aviso = Avisos(**{
            'titulo': titulo,
            'conteudo': conteudo,
            'categoria': categoria_enum,
            'prioridade': prioridade_enum,
            'criado_por': None
        })
        
        db.session.add(novo_aviso)
        db.session.flush()
        
        for user_id in destinatarios_ids:
            notificacao = NotificacaoUsuario(**{
                'id_aviso': novo_aviso.id_aviso,
                'id_usuario': user_id
            })
            db.session.add(notificacao)
        
        historico = HistoricoAvisos(**{
            'id_aviso': novo_aviso.id_aviso,
            'acao': 'CRIADO_AUTOMATICAMENTE',
            'detalhes': f'Notificação automática: {titulo}',
            'usuario_acao': None
        })
        db.session.add(historico)
        
        db.session.commit()
        
        return novo_aviso.id_aviso
        
    except Exception as e:
        db.session.rollback()
        return None

def check_stock_levels():
    from app.models import Insumos, TipoUsuario, Usuarios
    
    try:
        low_stock_items = Insumos.query.filter(Insumos.quantidade <= 10).all()
        
        if low_stock_items:
            items_text = '\n'.join([f"- {item.nome}: {item.quantidade} unidades" for item in low_stock_items])
            
            admins_and_managers = Usuarios.query.filter(
                Usuarios.is_ativo == True,
                Usuarios.tipo_usuario.in_([TipoUsuario.ADMIN, TipoUsuario.GERENTE])
            ).all()
            
            destinatarios = [user.id_usuario for user in admins_and_managers]
            
            create_automatic_notification(
                titulo="Alerta: Estoque Baixo",
                conteudo=f"Os seguintes insumos estão com estoque crítico:\n\n{items_text}\n\nVerifique a necessidade de reposição urgente.",
                categoria="Estoque",
                prioridade="ALTA",
                destinatarios=destinatarios
            )
            
        return len(low_stock_items)
        
    except Exception as e:
        return 0

def notify_maintenance_due():
    from app.models import TipoUsuario, Usuarios
    
    try:
        operadores = Usuarios.query.filter(
            Usuarios.is_ativo == True,
            Usuarios.tipo_usuario == TipoUsuario.OPERADOR
        ).all()
        
        destinatarios = [user.id_usuario for user in operadores]
        
        create_automatic_notification(
            titulo="Lembrete: Manutenção Semanal",
            conteudo="Lembrete para realizar as atividades de manutenção semanal:\n\n"
                     "- Verificar sistema de alimentação\n"
                     "- Limpar bebedouros\n"
                     "- Verificar sistema de ventilação\n"
                     "- Inspeção geral das instalações\n\n"
                     "Registre todas as atividades realizadas no sistema.",
            categoria="Manutenção",
            prioridade="NORMAL",
            destinatarios=destinatarios
        )
        
        return True
        
    except Exception as e:
        return False

def notify_report_due():
    from app.models import TipoUsuario, Usuarios
    
    try:
        today = date.today()
        
        if today.day == 1:
            gerentes_admins = Usuarios.query.filter(
                Usuarios.is_ativo == True,
                Usuarios.tipo_usuario.in_([TipoUsuario.ADMIN, TipoUsuario.GERENTE])
            ).all()
            
            destinatarios = [user.id_usuario for user in gerentes_admins]
            
            create_automatic_notification(
                titulo="Lembrete: Relatório Mensal",
                conteudo="É hora de gerar os relatórios mensais de produção:\n\n"
                         "- Relatório de produção de ovos\n"
                         "- Relatório de consumo de ração\n"
                         "- Relatório de mortalidade\n"
                         "- Relatório financeiro\n\n"
                         "Prazo: até o 5º dia útil do mês.",
                categoria="Relatórios",
                prioridade="ALTA",
                destinatarios=destinatarios
            )
            
            return True
            
        return False
        
    except Exception as e:
        return False

def calculate_age_in_weeks(birth_date):
    if not birth_date:
        return 0
    
    today = date.today()
    age_days = (today - birth_date).days
    return age_days // 7

def is_valid_date_range(start_date, end_date):
    if not start_date or not end_date:
        return False
    return start_date <= end_date

def format_currency(value):
    if value is None:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def sanitize_filename(filename):
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, '_', filename)

def generate_report_filename(report_type, date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    safe_type = sanitize_filename(report_type)
    return f"relatorio_{safe_type}_{date_str}.pdf"

def get_current_week_range():
    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    return start_week, end_week

def get_current_month_range():
    today = date.today()
    start_month = today.replace(day=1)
    if today.month == 12:
        end_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    return start_month, end_month