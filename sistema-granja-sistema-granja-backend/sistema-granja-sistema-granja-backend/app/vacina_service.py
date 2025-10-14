from app import db
from app.models import TipoVacina, AgendamentoVacinacao, LoteVacina, RegistroVacinacao
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_
from sqlalchemy.exc import IntegrityError


class vacinaService:
    @staticmethod
    def create_vacina_type(data):
        try:
            vacina_type = TipoVacina(
                nome=data['name'],
                descricao=data.get('description'),
                fabricante=data.get('manufacturer'),
                idade_recomendada_dias=data.get('recommended_age_days'),
                duracao_imunidade_dias=data.get('duration_immunity_days'),
                metodo_aplicacao=data.get('application_method'),
                temperatura_armazenamento=data.get('storage_temperature'),
                id_granja=data['id_granja']
            )
            db.session.add(vacina_type)
            db.session.commit()
            return vacina_type, None
        except IntegrityError:
            db.session.rollback()
            return None, "Tipo de vacina com este nome já existe"
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_vacina_types(active_only=True):
        query = TipoVacina.query
        if active_only:
            query = query.filter(TipoVacina.is_ativo == True)
        return query.order_by(TipoVacina.nome).all()

    @staticmethod
    def get_vacina_type(vacina_id):
        return TipoVacina.query.get(vacina_id)

    @staticmethod
    def update_vacina_type(vacina_id, data):
        try:
            vacina_type = TipoVacina.query.get(vacina_id)
            if not vacina_type:
                return None, "Tipo de vacina não encontrado"

            mapping = {
                'name': 'nome',
                'description': 'descricao',
                'manufacturer': 'fabricante',
                'recommended_age_days': 'idade_recomendada_dias',
                'duration_immunity_days': 'duracao_imunidade_dias',
                'application_method': 'metodo_aplicacao',
                'storage_temperature': 'temperatura_armazenamento',
                'is_active': 'is_ativo'
            }

            for key, value in data.items():
                attr = mapping.get(key, key)
                if hasattr(vacina_type, attr):
                    setattr(vacina_type, attr, value)

            vacina_type.updated_at = datetime.utcnow()
            db.session.commit()
            return vacina_type, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def delete_vacina_type(vacina_id):
        try:
            vacina_type = TipoVacina.query.get(vacina_id)
            if not vacina_type:
                return False, "Tipo de vacina não encontrado"

            vacina_type.is_ativo = False
            vacina_type.updated_at = datetime.utcnow()
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def create_vaccination_schedule(data):
        try:
            scheduled_date = data['scheduled_date']
            if isinstance(scheduled_date, str):
                scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()

            schedule = AgendamentoVacinacao(
                id_tipo_vacina=data['vacina_type_id'],
                data_agendada=scheduled_date,
                grupo_alvo=data.get('target_group'),
                quantidade_estimada=data.get('estimated_quantity'),
                responsavel=data.get('responsible_person'),
                observacoes=data.get('notes'),
                id_granja=data['id_granja']
            )
            db.session.add(schedule)
            db.session.commit()
            return schedule, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_vaccination_schedules(start_date=None, end_date=None, status=None):
        query = AgendamentoVacinacao.query

        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(AgendamentoVacinacao.data_agendada >= start_date)

        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(AgendamentoVacinacao.data_agendada <= end_date)

        if status:
            query = query.filter(AgendamentoVacinacao.status == status)

        return query.order_by(AgendamentoVacinacao.data_agendada).all()

    @staticmethod
    def create_vacina_batch(data):
        try:
            manufacturing_date = data.get('manufacturing_date')
            if manufacturing_date and isinstance(manufacturing_date, str):
                manufacturing_date = datetime.strptime(manufacturing_date, '%Y-%m-%d').date()

            expiry_date = data['expiry_date']
            if isinstance(expiry_date, str):
                expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()

            batch = LoteVacina(
                id_tipo_vacina=data['vacina_type_id'],
                numero_lote=data['batch_number'],
                data_fabricacao=manufacturing_date,
                data_validade=expiry_date,
                quantidade_recebida=data['quantity_received'],
                fornecedor=data.get('supplier'),
                preco_compra=data.get('purchase_price'),
                local_armazenamento=data.get('storage_location'),
                id_granja=data['id_granja']
            )
            db.session.add(batch)
            db.session.commit()
            return batch, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_vacina_batches(vacina_type_id=None, active_only=True, available_only=False):
        query = LoteVacina.query

        if vacina_type_id:
            query = query.filter(LoteVacina.id_tipo_vacina == vacina_type_id)

        if active_only:
            query = query.filter(LoteVacina.is_ativo == True)

        if available_only:
            query = query.filter(LoteVacina.quantidade_recebida > LoteVacina.quantidade_usada)
            query = query.filter(LoteVacina.data_validade > date.today())

        return query.order_by(LoteVacina.data_validade).all()

    @staticmethod
    def create_vaccination_record(data):
        try:
            batch = LoteVacina.query.get(data['batch_id'])
            if not batch:
                return None, "Lote de vacina não encontrado"

            quantity_applied = int(data['quantity_applied'])
            if batch.quantidade_disponivel < quantity_applied:
                return None, "Quantidade insuficiente no lote"

            if batch.is_expirado:
                return None, "Lote de vacina expirado"

            application_date = data.get('application_date', datetime.utcnow())
            if isinstance(application_date, str):
                application_date = datetime.fromisoformat(application_date.replace('Z', '+00:00'))

            record = RegistroVacinacao(
                id_agendamento=data.get('schedule_id'),
                id_tipo_vacina=data['vacina_type_id'],
                id_lote_vacina=data['batch_id'],
                data_aplicacao=application_date,
                quantidade_aplicada=quantity_applied,
                grupo_alvo=data.get('target_group'),
                responsavel=data['responsible_person'],
                metodo_aplicacao=data.get('application_method'),
                observacoes=data.get('observations'),
                reacoes_adversas=data.get('adverse_reactions'),
                temperatura_aplicacao=data.get('temperature_at_application'),
                id_granja=data.get('id_granja')
            )

            batch.quantidade_usada = batch.quantidade_usada + quantity_applied

            if data.get('schedule_id'):
                schedule = AgendamentoVacinacao.query.get(data['schedule_id'])
                if schedule:
                    schedule.status = 'completed'

            db.session.add(record)
            db.session.commit()
            return record, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_vaccination_records(start_date=None, end_date=None, vacina_type_id=None, target_group=None):
        query = RegistroVacinacao.query

        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(RegistroVacinacao.data_aplicacao >= start_date)

        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(RegistroVacinacao.data_aplicacao <= end_date)

        if vacina_type_id:
            query = query.filter(RegistroVacinacao.id_tipo_vacina == vacina_type_id)

        if target_group:
            query = query.filter(RegistroVacinacao.grupo_alvo.ilike(f'%{target_group}%'))

        return query.order_by(RegistroVacinacao.data_aplicacao.desc()).all()

    @staticmethod
    def get_vaccination_coverage_report(start_date=None, end_date=None):
        query = db.session.query(
            TipoVacina.nome,
            func.count(RegistroVacinacao.id_registro).label('total_applications'),
            func.sum(RegistroVacinacao.quantidade_aplicada).label('total_quantity'),
            func.count(func.distinct(RegistroVacinacao.grupo_alvo)).label('groups_covered')
        ).join(RegistroVacinacao).filter(TipoVacina.is_ativo == True)

        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(RegistroVacinacao.data_aplicacao >= start_date)

        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(RegistroVacinacao.data_aplicacao <= end_date)

        query = query.group_by(TipoVacina.id_tipo_vacina, TipoVacina.nome)

        results = query.all()

        report = []
        for result in results:
            report.append({
                'vacina_name': result.nome if hasattr(result, 'nome') else result[0],
                'total_applications': result.total_applications,
                'total_quantity': result.total_quantity,
                'groups_covered': result.groups_covered
            })

        return report

    @staticmethod
    def get_upcoming_vaccinations(days_ahead=30):
        end_date = date.today() + timedelta(days=days_ahead)

        return AgendamentoVacinacao.query.filter(
            and_(
                AgendamentoVacinacao.data_agendada >= date.today(),
                AgendamentoVacinacao.data_agendada <= end_date,
                AgendamentoVacinacao.status == 'agendado'
            )
        ).order_by(AgendamentoVacinacao.data_agendada).all()

    @staticmethod
    def get_expiring_batches(days_ahead=30):
        end_date = date.today() + timedelta(days=days_ahead)

        return LoteVacina.query.filter(
            and_(
                LoteVacina.data_validade <= end_date,
                LoteVacina.data_validade >= date.today(),
                LoteVacina.is_ativo == True,
                LoteVacina.quantidade_recebida > LoteVacina.quantidade_usada
            )
        ).order_by(LoteVacina.data_validade).all()