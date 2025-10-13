from app import db
from models import vacinaType, VaccinationSchedule, vacinaBatch, VaccinationRecord
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
from sqlalchemy.exc import IntegrityError

class vacinaService:
    
    @staticmethod
    def create_vacina_type(data):
        """Criar novo tipo de vacina"""
        try:
            vacina_type = vacinaType(
                name=data['name'],
                description=data.get('description'),
                manufacturer=data.get('manufacturer'),
                recommended_age_days=data.get('recommended_age_days'),
                duration_immunity_days=data.get('duration_immunity_days'),
                application_method=data.get('application_method'),
                storage_temperature=data.get('storage_temperature')
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
        """Listar tipos de vacina"""
        query = vacinaType.query
        if active_only:
            query = query.filter(vacinaType.is_active == True)
        return query.order_by(vacinaType.name).all()
    
    @staticmethod
    def get_vacina_type(vacina_id):
        """Obter tipo de vacina por ID"""
        return vacinaType.query.get(vacina_id)
    
    @staticmethod
    def update_vacina_type(vacina_id, data):
        """Atualizar tipo de vacina"""
        try:
            vacina_type = vacinaType.query.get(vacina_id)
            if not vacina_type:
                return None, "Tipo de vacina não encontrado"
            
            for key, value in data.items():
                if hasattr(vacina_type, key):
                    setattr(vacina_type, key, value)
            
            vacina_type.updated_at = datetime.utcnow()
            db.session.commit()
            return vacina_type, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def delete_vacina_type(vacina_id):
        """Deletar tipo de vacina (soft delete)"""
        try:
            vacina_type = vacinaType.query.get(vacina_id)
            if not vacina_type:
                return False, "Tipo de vacina não encontrado"
            
            vacina_type.is_active = False
            vacina_type.updated_at = datetime.utcnow()
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def create_vaccination_schedule(data):
        """Criar agendamento de vacinação"""
        try:
            scheduled_date = data['scheduled_date']
            if isinstance(scheduled_date, str):
                scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
            
            schedule = VaccinationSchedule(
                vacina_type_id=data['vacina_type_id'],
                scheduled_date=scheduled_date,
                target_group=data.get('target_group'),
                estimated_quantity=data.get('estimated_quantity'),
                responsible_person=data.get('responsible_person'),
                notes=data.get('notes')
            )
            db.session.add(schedule)
            db.session.commit()
            return schedule, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def get_vaccination_schedules(start_date=None, end_date=None, status=None):
        """Listar agendamentos de vacinação"""
        query = VaccinationSchedule.query
        
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(VaccinationSchedule.scheduled_date >= start_date)
        
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(VaccinationSchedule.scheduled_date <= end_date)
        
        if status:
            query = query.filter(VaccinationSchedule.status == status)
        
        return query.order_by(VaccinationSchedule.scheduled_date).all()
    
    @staticmethod
    def create_vacina_batch(data):
        """Criar lote de vacina"""
        try:
            manufacturing_date = data.get('manufacturing_date')
            if manufacturing_date and isinstance(manufacturing_date, str):
                manufacturing_date = datetime.strptime(manufacturing_date, '%Y-%m-%d').date()
            
            expiry_date = data['expiry_date']
            if isinstance(expiry_date, str):
                expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            
            batch = vacinaBatch(
                vacina_type_id=data['vacina_type_id'],
                batch_number=data['batch_number'],
                manufacturing_date=manufacturing_date,
                expiry_date=expiry_date,
                quantity_received=data['quantity_received'],
                supplier=data.get('supplier'),
                purchase_price=data.get('purchase_price'),
                storage_location=data.get('storage_location')
            )
            db.session.add(batch)
            db.session.commit()
            return batch, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def get_vacina_batches(vacina_type_id=None, active_only=True, available_only=False):
        """Listar lotes de vacina"""
        query = vacinaBatch.query
        
        if vacina_type_id:
            query = query.filter(vacinaBatch.vacina_type_id == vacina_type_id)
        
        if active_only:
            query = query.filter(vacinaBatch.is_active == True)
        
        if available_only:
            query = query.filter(vacinaBatch.quantity_received > vacinaBatch.quantity_used)
            query = query.filter(vacinaBatch.expiry_date > date.today())
        
        return query.order_by(vacinaBatch.expiry_date).all()
    
    @staticmethod
    def create_vaccination_record(data):
        """Registrar aplicação de vacina"""
        try:
            batch = vacinaBatch.query.get(data['batch_id'])
            if not batch:
                return None, "Lote de vacina não encontrado"
            
            if batch.quantity_available < data['quantity_applied']:
                return None, "Quantidade insuficiente no lote"
            
            if batch.is_expired:
                return None, "Lote de vacina expirado"
            
            application_date = data.get('application_date', datetime.utcnow())
            if isinstance(application_date, str):
                application_date = datetime.fromisoformat(application_date.replace('Z', '+00:00'))
            
            record = VaccinationRecord(
                schedule_id=data.get('schedule_id'),
                vacina_type_id=data['vacina_type_id'],
                batch_id=data['batch_id'],
                application_date=application_date,
                quantity_applied=data['quantity_applied'],
                target_group=data.get('target_group'),
                responsible_person=data['responsible_person'],
                application_method=data.get('application_method'),
                observations=data.get('observations'),
                adverse_reactions=data.get('adverse_reactions'),
                temperature_at_application=data.get('temperature_at_application')
            )
            
            batch.quantity_used += data['quantity_applied']
            
            if data.get('schedule_id'):
                schedule = VaccinationSchedule.query.get(data['schedule_id'])
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
        """Listar registros de vacinação"""
        query = VaccinationRecord.query
        
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(VaccinationRecord.application_date >= start_date)
        
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(VaccinationRecord.application_date <= end_date)
        
        if vacina_type_id:
            query = query.filter(VaccinationRecord.vacina_type_id == vacina_type_id)
        
        if target_group:
            query = query.filter(VaccinationRecord.target_group.ilike(f'%{target_group}%'))
        
        return query.order_by(VaccinationRecord.application_date.desc()).all()
    
    @staticmethod
    def get_vaccination_coverage_report(start_date=None, end_date=None):
        """Gerar relatório de cobertura vacinal"""
        query = db.session.query(
            vacinaType.name,
            func.count(VaccinationRecord.id).label('total_applications'),
            func.sum(VaccinationRecord.quantity_applied).label('total_quantity'),
            func.count(func.distinct(VaccinationRecord.target_group)).label('groups_covered')
        ).join(VaccinationRecord).filter(vacinaType.is_active == True)
        
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(VaccinationRecord.application_date >= start_date)
        
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(VaccinationRecord.application_date <= end_date)
        
        query = query.group_by(vacinaType.id, vacinaType.name)
        
        results = query.all()
        
        report = []
        for result in results:
            report.append({
                'vacina_name': result.name,
                'total_applications': result.total_applications,
                'total_quantity': result.total_quantity,
                'groups_covered': result.groups_covered
            })
        
        return report
    
    @staticmethod
    def get_upcoming_vaccinations(days_ahead=30):
        """Obter vacinações programadas para os próximos dias"""
        end_date = date.today() + timedelta(days=days_ahead)
        
        return VaccinationSchedule.query.filter(
            and_(
                VaccinationSchedule.scheduled_date >= date.today(),
                VaccinationSchedule.scheduled_date <= end_date,
                VaccinationSchedule.status == 'scheduled'
            )
        ).order_by(VaccinationSchedule.scheduled_date).all()
    
    @staticmethod
    def get_expiring_batches(days_ahead=30):
        """Obter lotes que vão expirar nos próximos dias"""
        end_date = date.today() + timedelta(days=days_ahead)
        
        return vacinaBatch.query.filter(
            and_(
                vacinaBatch.expiry_date <= end_date,
                vacinaBatch.expiry_date >= date.today(),
                vacinaBatch.is_active == True,
                vacinaBatch.quantity_received > vacinaBatch.quantity_used
            )
        ).order_by(vacinaBatch.expiry_date).all()