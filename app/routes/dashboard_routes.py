from flask import Blueprint, render_template, session, redirect, url_for, flash
from datetime import date, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    # Verificar se está logado
    if not session.get('user_logged_in'):
        return redirect(url_for('auth.login'))
    
    try:
        # BUSCAR DADOS REAIS DO BANCO
        from app.models.database import Lote, Producao, Usuarios
        
        # 1. TOTAL DE LOTES
        total_lotes = Lote.select().count()
        print(f"DEBUG: Total de lotes: {total_lotes}")
        
        # 2. TOTAL DE AVES
        total_aves = 0
        lotes = Lote.select()
        for lote in lotes:
            total_aves += lote.quantidade_inicial
        print(f"DEBUG: Total de aves: {total_aves}")
        
        # 3. PRODUÇÃO HOJE - COM DEBUG
        hoje = date.today()
        print(f"DEBUG: Data de hoje: {hoje}")
        
        producao_hoje = 0
        try:
            producoes_hoje = Producao.select().where(Producao.data_coleta == hoje)
            print(f"DEBUG: Query producoes_hoje executada")
            
            count_hoje = 0
            for producao in producoes_hoje:
                producao_hoje += producao.quantidade_ovos
                count_hoje += 1
                print(f"DEBUG: Produção hoje - ID: {producao.id_producao}, Data: {producao.data_coleta}, Ovos: {producao.quantidade_ovos}")
            
            print(f"DEBUG: Total de registros hoje: {count_hoje}")
            print(f"DEBUG: Total de ovos hoje: {producao_hoje}")
            
        except Exception as e:
            print(f"DEBUG: Erro ao buscar produção hoje: {e}")
            producao_hoje = 0
        
        # 4. PRODUÇÃO DO MÊS - COM DEBUG
        inicio_mes = hoje.replace(day=1)
        print(f"DEBUG: Início do mês: {inicio_mes}")
        
        producao_mes = 0
        try:
            producoes_mes = Producao.select().where(
                Producao.data_coleta >= inicio_mes,
                Producao.data_coleta <= hoje
            )
            print(f"DEBUG: Query producoes_mes executada")
            
            count_mes = 0
            for producao in producoes_mes:
                producao_mes += producao.quantidade_ovos
                count_mes += 1
                print(f"DEBUG: Produção mês - ID: {producao.id_producao}, Data: {producao.data_coleta}, Ovos: {producao.quantidade_ovos}")
            
            print(f"DEBUG: Total de registros no mês: {count_mes}")
            print(f"DEBUG: Total de ovos no mês: {producao_mes}")
            
        except Exception as e:
            print(f"DEBUG: Erro ao buscar produção do mês: {e}")
            producao_mes = 0
        
        # 5. TOTAL DE USUÁRIOS
        total_usuarios = Usuarios.select().count()
        print(f"DEBUG: Total de usuários: {total_usuarios}")
        
        # 6. ÚLTIMAS PRODUÇÕES - COM DEBUG
        ultimas_producoes = []
        try:
            ultimas_producoes = list(
                Producao.select()
                .join(Lote)
                .order_by(Producao.data_coleta.desc())
                .limit(5)
            )
            print(f"DEBUG: Últimas produções encontradas: {len(ultimas_producoes)}")
            
        except Exception as e:
            print(f"DEBUG: Erro ao buscar últimas produções: {e}")
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
        
        print(f"DEBUG: Resumo final: {resumo}")
        
        return render_template('dashboard/index.html', resumo=resumo)
        
    except Exception as e:
        # Se der erro, usar dados básicos
        print(f"DEBUG: ERRO GERAL ao buscar dados: {e}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        
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
''
@dashboard_bp.route('/criar-lote-teste')
def criar_lote_teste():
    try:
        from app.models.database import db, Lote
        from datetime import date
        
        html = "<h1>🔧 CRIANDO LOTE DE TESTE</h1>"
        
        # Verificar se já existe lote
        total_lotes = Lote.select().count()
        html += f"<p>Lotes existentes: {total_lotes}</p>"
        
        if total_lotes == 0:
            # Criar lote de teste
            lote_teste = Lote.create(
                numero_lote="LOTE001",
                data_entrada=date.today(),
                quantidade_inicial=1000,
                idade_inicial=120,  # 120 dias
                raca="Rhode Island",
                fornecedor="Fornecedor Teste",
                observacoes="Lote criado para teste",
                ativo=True
            )
            html += f"<p>✅ Lote criado: {lote_teste.numero_lote} (ID: {lote_teste.id_lote})</p>"
        else:
            html += "<p>✅ Já existem lotes cadastrados</p>"
        
        # Listar lotes
        lotes = list(Lote.select())
        html += "<h2>Lotes no sistema:</h2><ul>"
        for lote in lotes:
            html += f"<li>{lote.numero_lote} - {lote.quantidade_inicial} aves</li>"
        html += "</ul>"
        
        html += "<br><p><a href='/dashboard'>🔗 Voltar ao Dashboard</a></p>"
        
        return html
        
    except Exception as e:
        return f"<h1>❌ ERRO:</h1><p>{e}</p>"

@dashboard_bp.route('/recrear-tabela-producao')
def recrear_tabela_producao():
    try:
        from app.models.database import db, Producao, Lote
        from datetime import date
        
        html = "<h1>🔧 RECRIANDO TABELA PRODUÇÃO</h1>"
        
        # Conectar ao banco
        if db.is_closed():
            db.connect()
        html += "<p>✅ Conectado ao banco</p>"
        
        # DELETAR tabela antiga
        db.drop_tables([Producao], safe=True)
        html += "<p>🗑️ Tabela antiga removida</p>"
        
        # CRIAR tabela nova
        db.create_tables([Producao], safe=True)
        html += "<p>✅ Nova tabela criada</p>"
        
        # Verificar se existem lotes para criar produção de teste
        lotes = list(Lote.select().limit(1))
        
        if lotes:
            # Criar produção de teste
            producao_teste = Producao.create(
                data_coleta=date.today(),
                quantidade_ovos=150,
                lote=lotes[0],
                observacoes="Produção de teste",
                responsavel="Sistema"
            )
            html += f"<p>✅ Produção de teste criada (ID: {producao_teste.id_producao})</p>"
        else:
            html += "<p>⚠️ Nenhum lote encontrado - não foi possível criar produção de teste</p>"
        
        # Testar contagem
        total = Producao.select().count()
        html += f"<p>✅ Total de produções: {total}</p>"
        
        html += "<br><p><a href='/dashboard'>🔗 Voltar ao Dashboard</a></p>"
        
        return html
        
    except Exception as e:
        import traceback
        return f"""
        <h1>❌ ERRO AO RECRIAR TABELA</h1>
        <p><strong>Erro:</strong> {e}</p>
        <pre>{traceback.format_exc()}</pre>
        """

@dashboard_bp.route('/debug/producoes')
def debug_producoes():
    try:
        from app.models.database import Producao, Lote
        from datetime import date
        
        html = "<h1>🔍 DEBUG - PRODUÇÕES</h1>"
        
        # Verificar todas as produções
        todas_producoes = list(Producao.select().order_by(Producao.data_coleta.desc()))
        
        html += f"<h2>Total de produções no banco: {len(todas_producoes)}</h2>"
        
        if todas_producoes:
            html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
            html += "<tr><th>ID</th><th>Data</th><th>Quantidade</th><th>Lote</th><th>Responsável</th></tr>"
            
            for prod in todas_producoes:
                html += f"<tr>"
                html += f"<td>{prod.id_producao}</td>"
                html += f"<td>{prod.data_coleta}</td>"
                html += f"<td>{prod.quantidade_ovos}</td>"
                html += f"<td>{prod.lote.numero_lote}</td>"
                html += f"<td>{prod.responsavel}</td>"
                html += f"</tr>"
            html += "</table>"
        else:
            html += "<p style='color: red;'><strong>NENHUMA PRODUÇÃO ENCONTRADA!</strong></p>"
        
        # Verificar data de hoje
        hoje = date.today()
        html += f"<h2>Data de hoje: {hoje}</h2>"
        
        # Verificar produções de hoje
        producoes_hoje = list(Producao.select().where(Producao.data_coleta == hoje))
        html += f"<h2>Produções de hoje: {len(producoes_hoje)}</h2>"
        
        html += "<br><a href='/dashboard'>🔗 Voltar ao Dashboard</a>"
        
        return html
        
    except Exception as e:
        return f"<h1>❌ ERRO</h1><p>{e}</p>"
    
        return render_template('dashboard/index.html', resumo=resumo)