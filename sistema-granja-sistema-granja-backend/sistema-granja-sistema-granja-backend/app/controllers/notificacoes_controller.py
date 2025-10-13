from flask import request, jsonify, g
from app.models import Avisos, NotificacaoUsuario, HistoricoAvisos, Usuarios, db
from app.models import CategoriaNotificacao, PrioridadeNotificacao, StatusNotificacao
from app.utils import log_user_activity
from datetime import datetime
from sqlalchemy import or_

def create_notification():
    try:
        current_user = g.get('current_user')
        data = request.get_json()
        
        required_fields = ['titulo', 'conteudo', 'categoria', 'destinatarios']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Required field: {field}'}), 400
        
        if isinstance(data['categoria'], str):
            try:
                categoria = CategoriaNotificacao(data['categoria'])
            except ValueError:
                return jsonify({'error': f'Invalid category: {data["categoria"]}'}), 400
        else:
            categoria = data['categoria']
        
        prioridade = PrioridadeNotificacao.NORMAL
        if 'prioridade' in data:
            try:
                prioridade = PrioridadeNotificacao(data['prioridade'])
            except ValueError:
                return jsonify({'error': f'Invalid priority: {data["prioridade"]}'}), 400
        
        data_validade = None
        if 'data_validade' in data and data['data_validade']:
            data_validade = datetime.strptime(data['data_validade'], '%Y-%m-%d %H:%M:%S')
        
        novo_aviso = Avisos(**{
            'titulo': data['titulo'],
            'conteudo': data['conteudo'],
            'categoria': categoria,
            'prioridade': prioridade,
            'data_validade': data_validade,
            'criado_por': current_user.id_usuario
        })
        
        db.session.add(novo_aviso)
        db.session.flush()
        
        destinatarios_criados = []
        for user_id in data['destinatarios']:
            user = Usuarios.query.get(user_id)
            if user and user.is_ativo:
                notificacao = NotificacaoUsuario(**{
                    'id_aviso': novo_aviso.id_aviso,
                    'id_usuario': user_id
                })
                db.session.add(notificacao)
                destinatarios_criados.append(user.nome)
        
        historico = HistoricoAvisos(**{
            'id_aviso': novo_aviso.id_aviso,
            'acao': 'CRIADO',
            'detalhes': f'Aviso criado com título: {data["titulo"]}. Destinatários: {", ".join(destinatarios_criados)}',
            'usuario_acao': current_user.id_usuario
        })
        db.session.add(historico)
        
        db.session.commit()
        
        log_user_activity(
            current_user.id_usuario,
            'AVISO_CRIADO',
            f'Aviso criado: {data["titulo"]} para {len(destinatarios_criados)} usuários'
        )
        
        return jsonify({
            'message': 'Notification created successfully!',
            'id_aviso': novo_aviso.id_aviso,
            'destinatarios_notificados': len(destinatarios_criados)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

def get_notifications():
    try:
        current_user = g.get('current_user')
        
        id_aviso = request.args.get('id_aviso')
        categoria = request.args.get('categoria')
        prioridade = request.args.get('prioridade')
        data_criacao = request.args.get('data_criacao')
        criado_por = request.args.get('criado_por')
        conteudo = request.args.get('conteudo')
        apenas_ativos = request.args.get('apenas_ativos', 'true').lower() == 'true'
        
        query = Avisos.query
        
        if apenas_ativos:
            query = query.filter(Avisos.is_ativo == True)
        
        if id_aviso:
            query = query.filter(Avisos.id_aviso == id_aviso)
        if categoria:
            query = query.filter(Avisos.categoria == categoria)
        if prioridade:
            query = query.filter(Avisos.prioridade == prioridade)
        if data_criacao:
            data_filter = datetime.strptime(data_criacao, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Avisos.data_criacao) == data_filter)
        if criado_por:
            query = query.filter(Avisos.criado_por == criado_por)
        if conteudo:
            query = query.filter(or_(
                Avisos.titulo.ilike(f'%{conteudo}%'),
                Avisos.conteudo.ilike(f'%{conteudo}%')
            ))
        
        avisos = query.order_by(Avisos.data_criacao.desc()).all()
        
        log_user_activity(
            current_user.id_usuario,
            'AVISOS_CONSULTADOS',
            f'Consulta de avisos realizada com filtros aplicados'
        )
        
        return jsonify([{
            'id_aviso': aviso.id_aviso,
            'titulo': aviso.titulo,
            'conteudo': aviso.conteudo,
            'categoria': aviso.categoria.value,
            'prioridade': aviso.prioridade.value,
            'data_criacao': aviso.data_criacao.isoformat(),
            'data_validade': aviso.data_validade.isoformat() if aviso.data_validade else None,
            'criado_por': aviso.criador.nome if aviso.criador else 'Sistema',
            'is_ativo': aviso.is_ativo,
            'total_notificacoes': len(aviso.notificacoes)
        } for aviso in avisos]), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

def delete_notifications(aviso_id: str):
    try:
        current_user = g.get('current_user')
        aviso = Avisos.query.get(aviso_id)
        
        if not aviso:
            return jsonify({'error': 'Notification not found.'}), 404
        
        if not aviso.is_ativo:
            return jsonify({'error': 'Notification already deleted.'}), 400
        
        if aviso.criado_por != current_user.id_usuario and current_user.tipo_usuario.value != 'ADMIN':
            return jsonify({'error': 'Only the creator or ADMIN can delete this notification'}), 403
        
        aviso.is_ativo = False
        aviso.data_exclusao = datetime.utcnow()
        aviso.excluido_por = current_user.id_usuario
        
        for notificacao in aviso.notificacoes:
            if notificacao.status == StatusNotificacao.ATIVO:
                notificacao.status = StatusNotificacao.EXCLUIDA
        
        historico = HistoricoAvisos(**{
            'id_aviso': aviso_id,
            'acao': 'EXCLUIDO',
            'detalhes': f'Aviso excluído: {aviso.titulo}',
            'usuario_acao': current_user.id_usuario
        })
        db.session.add(historico)
        
        db.session.commit()
        
        log_user_activity(
            current_user.id_usuario,
            'AVISO_EXCLUIDO',
            f'Aviso excluído: {aviso.titulo}'
        )
        
        return jsonify({'message': 'Notification deleted successfully.'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

def get_user_notifications():
    try:
        current_user = g.get('current_user')
        
        categoria = request.args.get('categoria')
        prioridade = request.args.get('prioridade')
        status = request.args.get('status')
        apenas_nao_lidas = request.args.get('apenas_nao_lidas', 'false').lower() == 'true'
        
        query = NotificacaoUsuario.query.filter_by(id_usuario=current_user.id_usuario)
        
        if apenas_nao_lidas:
            query = query.filter(NotificacaoUsuario.status == StatusNotificacao.ATIVO)
        
        if status:
            query = query.filter(NotificacaoUsuario.status == status)
        
        if categoria or prioridade:
            query = query.join(Avisos)
            if categoria:
                query = query.filter(Avisos.categoria == categoria)
            if prioridade:
                query = query.filter(Avisos.prioridade == prioridade)
        
        notificacoes = query.order_by(NotificacaoUsuario.data_criacao.desc()).all()
        
        result = []
        for notif in notificacoes:
            if notif.aviso and notif.aviso.is_ativo:
                result.append({
                    'id_notificacao': notif.id_notificacao,
                    'aviso': {
                        'id_aviso': notif.aviso.id_aviso,
                        'titulo': notif.aviso.titulo,
                        'conteudo': notif.aviso.conteudo,
                        'categoria': notif.aviso.categoria.value,
                        'prioridade': notif.aviso.prioridade.value,
                        'data_criacao': notif.aviso.data_criacao.isoformat(),
                        'criado_por': notif.aviso.criador.nome if notif.aviso.criador else 'Sistema'
                    },
                    'status': notif.status.value,
                    'data_leitura': notif.data_leitura.isoformat() if notif.data_leitura else None,
                    'data_criacao': notif.data_criacao.isoformat()
                })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

def mark_notification_as_read(notification_id: str):
    try:
        current_user = g.get('current_user')
        notificacao = NotificacaoUsuario.query.filter_by(
            id_notificacao=notification_id,
            id_usuario=current_user.id_usuario
        ).first()
        
        if not notificacao:
            return jsonify({'error': 'Notification not found'}), 404
        
        if notificacao.status == StatusNotificacao.LIDA:
            return jsonify({'message': 'Notification already read.'}), 200
        
        notificacao.status = StatusNotificacao.LIDA
        notificacao.data_leitura = datetime.utcnow()
        
        db.session.commit()
        
        log_user_activity(
            current_user.id_usuario,
            'NOTIFICACAO_LIDA',
            f'Notificação marcada como lida: {notificacao.aviso.titulo if notificacao.aviso else "N/A"}'
        )
        
        return jsonify({'message': 'Notification marked as read.'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

def get_notifications_count():
    try:
        current_user = g.get('current_user')
        
        nao_lidas = NotificacaoUsuario.query.filter_by(
            id_usuario=current_user.id_usuario,
            status=StatusNotificacao.ATIVO
        ).count()
        
        por_categoria = {}
        for categoria in CategoriaNotificacao:
            count = NotificacaoUsuario.query.join(Avisos).filter(
                NotificacaoUsuario.id_usuario == current_user.id_usuario,
                NotificacaoUsuario.status == StatusNotificacao.ATIVO,
                Avisos.categoria == categoria,
                Avisos.is_ativo == True
            ).count()
            por_categoria[categoria.value] = count
        
        por_prioridade = {}
        for prioridade in PrioridadeNotificacao:
            count = NotificacaoUsuario.query.join(Avisos).filter(
                NotificacaoUsuario.id_usuario == current_user.id_usuario,
                NotificacaoUsuario.status == StatusNotificacao.ATIVO,
                Avisos.prioridade == prioridade,
                Avisos.is_ativo == True
            ).count()
            por_prioridade[prioridade.value] = count
        
        return jsonify({
            'total_nao_lidas': nao_lidas,
            'por_categoria': por_categoria,
            'por_prioridade': por_prioridade
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

def get_notification_history(aviso_id: str):
    try:
        current_user = g.get('current_user')
        
        aviso = Avisos.query.get(aviso_id)
        if not aviso:
            return jsonify({'error': 'Notification not found'}), 404
        
        historico = HistoricoAvisos.query.filter_by(id_aviso=aviso_id).order_by(
            HistoricoAvisos.data_acao.desc()
        ).all()
        
        log_user_activity(
            current_user.id_usuario,
            'HISTORICO_AVISO_CONSULTADO',
            f'Histórico consultado para aviso: {aviso.titulo}'
        )
        
        return jsonify([{
            'id_historico': hist.id_historico,
            'acao': hist.acao,
            'detalhes': hist.detalhes,
            'usuario': hist.usuario.nome if hist.usuario else 'Sistema',
            'data_acao': hist.data_acao.isoformat()
        } for hist in historico]), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

def get_notifications_grouped():
    try:
        current_user = g.get('current_user')
        
        query = NotificacaoUsuario.query.filter_by(
            id_usuario=current_user.id_usuario,
            status=StatusNotificacao.ATIVO
        ).join(Avisos).filter(Avisos.is_ativo == True)
        
        notificacoes = query.order_by(Avisos.prioridade.desc(), Avisos.data_criacao.desc()).all()
        
        agrupadas = {
            'CRITICA': [],
            'ALTA': [],
            'NORMAL': [],
            'BAIXA': []
        }
        
        for notif in notificacoes:
            if notif.aviso:
                prioridade_key = notif.aviso.prioridade.value.upper()
                if prioridade_key == 'CRÍTICA':
                    prioridade_key = 'CRITICA'
                
                agrupadas[prioridade_key].append({
                    'id_notificacao': notif.id_notificacao,
                    'aviso': {
                        'id_aviso': notif.aviso.id_aviso,
                        'titulo': notif.aviso.titulo,
                        'conteudo': notif.aviso.conteudo,
                        'categoria': notif.aviso.categoria.value,
                        'prioridade': notif.aviso.prioridade.value,
                        'data_criacao': notif.aviso.data_criacao.isoformat()
                    },
                    'data_criacao': notif.data_criacao.isoformat()
                })
        
        return jsonify(agrupadas), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500