import re
import random
import string
from datetime import datetime

def validate_password(password):
    """Valida se a senha atende aos critérios mínimos"""
    if len(password) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres"
    return True, "Senha válida"

def generate_matricula():
    """Gera uma matrícula única"""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"MAT{timestamp}{random_part}"

def validate_cpf(cpf):
    """Valida formato do CPF"""
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    if len(cpf) != 11:
        return False, "CPF deve ter 11 dígitos"
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False, "CPF inválido"
    
    return True, "CPF válido"

def log_user_activity(user_id, action, details=None):
    """Log de atividade do usuário"""
    # Por enquanto, apenas print. Você pode implementar log em banco depois
    print(f"User {user_id}: {action} - {details}")
    return True