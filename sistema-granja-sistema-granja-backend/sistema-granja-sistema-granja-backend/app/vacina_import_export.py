import csv
import json
from io import StringIO, BytesIO
from datetime import datetime
from flask import Flask, request, jsonify, Blueprint
from models import vacinaType, VaccinationSchedule, vacinaBatch, VaccinationRecord
from vacina_service import vacinaService
from app import db

class vacinaImportExport:
    
    @staticmethod
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
            
            return output.getvalue()
            
        except Exception as e:
            raise Exception(f"Erro ao exportar tipos de vacina: {str(e)}")
    
    @staticmethod
    def import_vacina_types_csv(csv_content):
        """Importar tipos de vacina de CSV"""
        try:
            reader = csv.DictReader(StringIO(csv_content))
            imported_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    data = {
                        'name': row['Nome'],
                        'description': row.get('Descrição'),
                        'manufacturer': row.get('Fabricante'),
                        'recommended_age_days': int(row['Idade Recomendada (dias)']) if row.get('Idade Recomendada (dias)') else None,
                        'duration_immunity_days': int(row['Duração Imunidade (dias)']) if row.get('Duração Imunidade (dias)') else None,
                        'application_method': row.get('Método Aplicação'),
                        'storage_temperature': row.get('Temperatura Armazenamento')
                    }
                    
                    vacina_type, error = vacinaService.create_vacina_type(data)
                    if error:
                        errors.append(f"Linha {row_num}: {error}")
                    else:
                        imported_count += 1
                        
                except Exception as e:
                    errors.append(f"Linha {row_num}: {str(e)}")
            
            return {
                'imported_count': imported_count,
                'errors': errors
            }
            
        except Exception as e:
            raise Exception(f"Erro ao importar tipos de vacina: {str(e)}")
    
    @staticmethod
    def export_vaccination_records_csv(start_date=None, end_date=None):
        """Exportar registros de vacinação para CSV"""
        try:
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
            
            return output.getvalue()
            
        except Exception as e:
            raise Exception(f"Erro ao exportar registros: {str(e)}")
    
    @staticmethod
    def export_vaccination_schedules_csv(start_date=None, end_date=None):
        """Exportar agendamentos para CSV"""
        try:
            schedules = vacinaService.get_vaccination_schedules(start_date, end_date)
            
            output = StringIO()
            writer = csv.writer(output)

            writer.writerow([
                'ID', 'Tipo Vacina', 'Data Agendada', 'Grupo Alvo',
                'Quantidade Estimada', 'Responsável', 'Observações', 'Status'
            ])
            

            for schedule in schedules:
                writer.writerow([
                    schedule.id, schedule.vacina_type.name if schedule.vacina_type else '',
                    schedule.scheduled_date, schedule.target_group,
                    schedule.estimated_quantity, schedule.responsible_person,
                    schedule.notes, schedule.status
                ])
            
            return output.getvalue()
            
        except Exception as e:
            raise Exception(f"Erro ao exportar agendamentos: {str(e)}")
    
    @staticmethod
    def export_vacina_batches_csv():
        """Exportar lotes para CSV"""
        try:
            batches = vacinaService.get_vacina_batches(active_only=False)
            
            output = StringIO()
            writer = csv.writer(output)

            writer.writerow([
                'ID', 'Tipo Vacina', 'Número Lote', 'Data Fabricação',
                'Data Validade', 'Quantidade Recebida', 'Quantidade Usada',
                'Quantidade Disponível', 'Fornecedor', 'Preço Compra',
                'Local Armazenamento', 'Ativo', 'Expirado'
            ])
            
            for batch in batches:
                writer.writerow([
                    batch.id, batch.vacina_type.name if batch.vacina_type else '',
                    batch.batch_number, batch.manufacturing_date,
                    batch.expiry_date, batch.quantity_received,
                    batch.quantity_used, batch.quantity_available,
                    batch.supplier, batch.purchase_price,
                    batch.storage_location, batch.is_active, batch.is_expired
                ])
            
            return output.getvalue()
            
        except Exception as e:
            raise Exception(f"Erro ao exportar lotes: {str(e)}")

@vacinaType.route('/export/types/csv', methods=['GET'])
def export_vacina_types_csv():
    """Exportar tipos de vacina para CSV"""
    try:
        csv_content = vacinaImportExport.export_vacina_types_csv()
        
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=tipos_vacina_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacinaType.route('/import/types/csv', methods=['POST'])
def import_vacina_types_csv():
    """Importar tipos de vacina de CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Arquivo não fornecido'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        csv_content = file.read().decode('utf-8')
        result = vacinaImportExport.import_vacina_types_csv(csv_content)
        
        return jsonify({
            'message': f'{result["imported_count"]} tipos de vacina importados com sucesso',
            'imported_count': result['imported_count'],
            'errors': result['errors']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacinaType.route('/export/records/csv', methods=['GET'])
def export_vaccination_records_csv():
    """Exportar registros de vacinação para CSV"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        csv_content = vacinaImportExport.export_vaccination_records_csv(start_date, end_date)
        
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=registros_vacinacao_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacinaType.route('/export/schedules/csv', methods=['GET'])
def export_vaccination_schedules_csv():
    """Exportar agendamentos para CSV"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        csv_content = vacinaImportExport.export_vaccination_schedules_csv(start_date, end_date)
        
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=agendamentos_vacinacao_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vacinaType.route('/export/batches/csv', methods=['GET'])
def export_vacina_batches_csv():
    """Exportar lotes para CSV"""
    try:
        csv_content = vacinaImportExport.export_vacina_batches_csv()
        
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=lotes_vacina_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500