from flask import Blueprint, render_template, session, redirect, url_for, flash
from datetime import date, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    # Verificar se está logado
    if not session.get('user_logged_in'):
        return redirect(url_for('auth.login'))
    
    try:
        from app.models.database import Lote, Producao, Usuarios
        
        # 1. TOTAL DE LOTES
        total_lotes = Lote.select().count()
        
        # 2. TOTAL DE AVES
        total_aves = 0
        lotes = Lote.select()
        for lote in lotes:
            total_aves += lote.quantidade_inicial
        
        # 3. PRODUÇÃO HOJE
        hoje = date.today()
        
        producao_hoje = 0
        try:
            producoes_hoje = Producao.select().where(Producao.data_coleta == hoje)
            
            count_hoje = 0
            for producao in producoes_hoje:
                producao_hoje += producao.quantidade_ovos
                count_hoje += 1
            
        except Exception as e:
            producao_hoje = 0
        
        # 4. PRODUÇÃO DO MÊS
        inicio_mes = hoje.replace(day=1)
        
        producao_mes = 0
        try:
            producoes_mes = Producao.select().where(
                Producao.data_coleta >= inicio_mes,
                Producao.data_coleta <= hoje
            )
            
            count_mes = 0
            for producao in producoes_mes:
                producao_mes += producao.quantidade_ovos
                count_mes += 1
            
        except Exception as e:
            producao_mes = 0
        
        # 5. TOTAL DE USUÁRIOS
        total_usuarios = Usuarios.select().count()
        
        # 6. ÚLTIMAS PRODUÇÕES
        ultimas_producoes = []
        try:
            ultimas_producoes = list(
                Producao.select()
                .join(Lote)
                .order_by(Producao.data_coleta.desc())
                .limit(5)
            )
            
        except Exception as e:

            ultimas_producoes = []
        
        # DADOS PARA O TEMPLATE
        resumo = {
            'total_lotes': total_lotes,
            'total_aves': total_aves,
            'producao_hoje': producao_hoje,
            'producao_mes': producao_mes,
            'total_usuarios': total_usuarios,
            'ultimas_producoes': ultimas_producoes,
            'alertas': [],
        }
                
        return render_template('dashboard/index.html', resumo=resumo)
        
    except Exception as e:               
        resumo = {
            'total_lotes': 0,
            'total_aves': 0,
            'producao_hoje': 0,
            'producao_mes': 0,
            'total_usuarios': 1,
            'ultimas_producoes': [],
            'alertas': [],
        }
        
        flash('⚠️ Erro ao carregar dados do dashboard.', 'warning')
    
        return render_template('dashboard/index.html', resumo=resumo)