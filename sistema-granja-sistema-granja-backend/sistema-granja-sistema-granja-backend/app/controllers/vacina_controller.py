from flask import Blueprint, request, jsonify
from vacina_service import vacinaService
from datetime import datetime
import csv
from io import StringIO

vacina_bp = Blueprint('vacina', __name__)

@vacina_bp.route('/types', methods=['POST'])
def create_vacina_type():
    """Criar novo tipo de vacina"""
    try:
        data = request.get_json()

        if not data or 'name' not in data:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        
        vacina_type, error = vacinaService.create_vacina_type(data)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Tipo de vacina criado com sucesso',
            'data': vacina_type.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/types', methods=['GET'])
def get_vacina_types():
    """Listar tipos de vacina"""
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        vacina_types = vacinaService.get_vacina_types(active_only)
        
        return jsonify({
            'data': [vt.to_dict() for vt in vacina_types],
            'total': len(vacina_types)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/types/<int:vacina_id>', methods=['GET'])
def get_vacina_type(vacina_id):
    """Obter tipo de vacina específico"""
    try:
        vacina_type = vacinaService.get_vacina_type(vacina_id)
        
        if not vacina_type:
            return jsonify({'error': 'Tipo de vacina não encontrado'}), 404
        
        return jsonify({'data': vacina_type.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/types/<int:vacina_id>', methods=['PUT'])
def update_vacina_type(vacina_id):
    """Atualizar tipo de vacina"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        vacina_type, error = vacinaService.update_vacina_type(vacina_id, data)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Tipo de vacina atualizado com sucesso',
            'data': vacina_type.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/types/<int:vacina_id>', methods=['DELETE'])
def delete_vacina_type(vacina_id):
    """Deletar tipo de vacina"""
    try:
        success, error = vacinaService.delete_vacina_type(vacina_id)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({'message': 'Tipo de vacina removido com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/schedules', methods=['POST'])
def create_vaccination_schedule():
    """Criar agendamento de vacinação"""
    try:
        data = request.get_json()

        required_fields = ['vacina_type_id', 'scheduled_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} é obrigatório'}), 400
        
        schedule, error = vacinaService.create_vaccination_schedule(data)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Agendamento criado com sucesso',
            'data': schedule.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/schedules', methods=['GET'])
def get_vaccination_schedules():
    """Listar agendamentos de vacinação"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')
        
        schedules = vacinaService.get_vaccination_schedules(start_date, end_date, status)
        
        return jsonify({
            'data': [s.to_dict() for s in schedules],
            'total': len(schedules)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/schedules/upcoming', methods=['GET'])
def get_upcoming_vaccinations():
    """Obter vacinações programadas para os próximos dias"""
    try:
        days_ahead = int(request.args.get('days', 30))
        schedules = vacinaService.get_upcoming_vaccinations(days_ahead)
        
        return jsonify({
            'data': [s.to_dict() for s in schedules],
            'total': len(schedules)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/batches', methods=['POST'])
def create_vacina_batch():
    """Criar lote de vacina"""
    try:
        data = request.get_json()
    
        required_fields = ['vacina_type_id', 'batch_number', 'expiry_date', 'quantity_received']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} é obrigatório'}), 400
        
        batch, error = vacinaService.create_vacina_batch(data)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Lote criado com sucesso',
            'data': batch.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/batches', methods=['GET'])
def get_vacina_batches():
    """Listar lotes de vacina"""
    try:
        vacina_type_id = request.args.get('vacina_type_id', type=int)
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        available_only = request.args.get('available_only', 'false').lower() == 'true'
        
        batches = vacinaService.get_vacina_batches(vacina_type_id, active_only, available_only)
        
        return jsonify({
            'data': [b.to_dict() for b in batches],
            'total': len(batches)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/batches/expiring', methods=['GET'])
def get_expiring_batches():
    """Obter lotes que vão expirar"""
    try:
        days_ahead = int(request.args.get('days', 30))
        batches = vacinaService.get_expiring_batches(days_ahead)
        
        return jsonify({
            'data': [b.to_dict() for b in batches],
            'total': len(batches)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@vacina_bp.route('/records', methods=['POST'])
def create_vaccination_record():
    """Registrar aplicação de vacina"""
    try:
        data = request.get_json()
        
        required_fields = ['vacina_type_id', 'batch_id', 'quantity_applied', 'responsible_person']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} é obrigatório'}), 400
        
        record, error = vacinaService.create_vaccination_record(data)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Vacinação registrada com sucesso',
            'data': record.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/records', methods=['GET'])
def get_vaccination_records():
    """Listar registros de vacinação"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        vacina_type_id = request.args.get('vacina_type_id', type=int)
        target_group = request.args.get('target_group')
        
        records = vacinaService.get_vaccination_records(start_date, end_date, vacina_type_id, target_group)
        
        return jsonify({
            'data': [r.to_dict() for r in records],
            'total': len(records)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/reports/coverage', methods=['GET'])
def get_vaccination_coverage_report():
    """Relatório de cobertura vacinal"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        report = vacinaService.get_vaccination_coverage_report(start_date, end_date)
        
        return jsonify({
            'data': report,
            'generated_at': datetime.utcnow().isoformat(),
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """Dados para dashboard"""
    try:
        upcoming = vacinaService.get_upcoming_vaccinations(7)

        expiring = vacinaService.get_expiring_batches(30)
        
        from datetime import date, timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        coverage = vacinaService.get_vaccination_coverage_report(start_date.isoformat(), end_date.isoformat())
        
        return jsonify({
            'upcoming_vaccinations': [u.to_dict() for u in upcoming],
            'expiring_batches': [e.to_dict() for e in expiring],
            'coverage_report': coverage,
            'alerts': {
                'upcoming_count': len(upcoming),
                'expiring_count': len(expiring)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/export/types/csv', methods=['GET'])
def export_vacina_types_csv():
    """Exportar tipos de vacina para CSV"""
    try:
        vacina_types = vacinaService.get_vacina_types(active_only=False)
        
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'ID', 'Nome', 'Descrição', 'Fabricante', 'Idade Recomendada (dias)',
            'Duração Imunidade (dias)', 'Método Aplicação', 'Temperatura Armazenamento',
            'Ativo', 'Criado em', 'Atualizado em'
        ])

        for vt in vacina_types:
            writer.writerow([
                vt.id, vt.name, vt.description, vt.manufacturer,
                vt.recommended_age_days, vt.duration_immunity_days,
                vt.application_method, vt.storage_temperature,
                vt.is_active, vt.created_at, vt.updated_at
            ])
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=tipos_vacina_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacina_bp.route('/export/records/csv', methods=['GET'])
def export_vaccination_records_csv():
    """Exportar registros de vacinação para CSV"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        records = vacinaService.get_vaccination_records(start_date, end_date)
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'ID', 'Tipo Vacina', 'Lote', 'Data Aplicação', 'Quantidade',
            'Grupo Alvo', 'Responsável', 'Método Aplicação', 'Observações',
            'Reações Adversas', 'Temperatura'
        ])
        
        for record in records:
            writer.writerow([
                record.id, record.vacina_type.name if record.vacina_type else '',
                record.batch.batch_number if record.batch else '',
                record.application_date, record.quantity_applied,
                record.target_group, record.responsible_person,
                record.application_method, record.observations,
                record.adverse_reactions, record.temperature_at_application
            ])
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=registros_vacinacao_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500