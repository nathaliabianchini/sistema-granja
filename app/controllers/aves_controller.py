from flask import jsonify, g
from app.models import Aves, RacaAve, db
from datetime import date, datetime
from typing import Union, Optional

def register_poultry(id_lote: str, raca_ave: Union[str, RacaAve], data_nascimento: date, 
                     tempo_de_vida: int, media_peso: float, caracteristicas_geneticas: str,
                     tipo_alojamento: str, historico_vacinas: str,
                     observacoes: Optional[str] = None):
    try:
        required_fields = {
            'id_lote': id_lote,
            'raca_ave': raca_ave,
            'media_peso': media_peso,
            'tipo_alojamento': tipo_alojamento,
            'historico_vacinas': historico_vacinas
        }
        
        for field_name, field_value in required_fields.items():
            if not field_value:
                return jsonify({'error': f'Required field not filled: {field_name}'}), 400

        if isinstance(raca_ave, str):
            try:
                raca_ave = RacaAve(raca_ave)
            except ValueError:
                return jsonify({'error': f'Invalid breed: {raca_ave}. Valid values: {[r.value for r in RacaAve]}'}), 400

        new_poultry = Aves.create(
            id_lote=id_lote,
            raca_ave=raca_ave.value,  
            data_nascimento=data_nascimento,
            tempo_de_vida=tempo_de_vida,
            media_peso=media_peso,
            caracteristicas_geneticas=caracteristicas_geneticas,
            tipo_alojamento=tipo_alojamento,
            historico_vacinas=historico_vacinas,
            observacoes=observacoes
        )
        
        return jsonify({
            'message': 'Poultry registered successfully!',
            'id_ave': new_poultry.id_ave
        }), 201
        
    except Exception as error:
        return jsonify({'error': f'Internal error: {str(error)}'}), 500

def get_poultries(id_ave=None, raca=None, id_lote=None, data_nascimento=None, incluir_inativas=False):
    try:
        query = Aves.select()
        
        if not incluir_inativas:
            query = query.where(Aves.ativa == True)
        
        if id_ave:
            query = query.where(Aves.id_ave == id_ave)
        if raca:
            query = query.where(Aves.raca_ave == raca)
        if id_lote:
            query = query.where(Aves.id_lote == id_lote)
        if data_nascimento:
            query = query.where(Aves.data_nascimento == data_nascimento)
        
        poultries = list(query)
        
        return jsonify({'aves': [{
            'id_ave': ave.id_ave,
            'id_lote': ave.id_lote,
            'raca_ave': ave.raca_ave,
            'data_nascimento': ave.data_nascimento.isoformat() if ave.data_nascimento else None,
            'tempo_de_vida': ave.tempo_de_vida,
            'media_peso': ave.media_peso,
            'caracteristicas_geneticas': ave.caracteristicas_geneticas,
            'tipo_alojamento': ave.tipo_alojamento,
            'historico_vacinas': ave.historico_vacinas,
            'observacoes': ave.observacoes,
            'ativa': ave.ativa
        } for ave in poultries]})
    except Exception as error:
        return jsonify({'error': f'Internal error: {str(error)}'}), 500

def get_poultry(ave_id: int):
    try:
        ave = Aves.get_or_none(Aves.id_ave == ave_id)
        if not ave:
            return jsonify({'message': 'Poultry not found'}), 404
        
        return jsonify({
            'id_ave': ave.id_ave,
            'id_lote': ave.id_lote,
            'raca_ave': ave.raca_ave,
            'data_nascimento': ave.data_nascimento.isoformat() if ave.data_nascimento else None,
            'tempo_de_vida': ave.tempo_de_vida,
            'media_peso': ave.media_peso,
            'caracteristicas_geneticas': ave.caracteristicas_geneticas,
            'tipo_alojamento': ave.tipo_alojamento,
            'historico_vacinas': ave.historico_vacinas,
            'observacoes': ave.observacoes
        })
    except Exception as error:
        return jsonify({'error': f'Internal error: {str(error)}'}), 500

def update_poultry(ave_id: int, **kwargs):
    try:
        ave = Aves.get_or_none(Aves.id_ave == ave_id)
        if not ave:
            return jsonify({'message': 'Poultry not found'}), 404

        current_user = g.get('current_user')
        modificacoes = []
        
        updatable_fields = [
            'raca_ave', 'data_nascimento', 'tempo_de_vida', 'media_peso',
            'caracteristicas_geneticas', 'tipo_alojamento', 'historico_vacinas', 'observacoes'
        ]
        
        for field in updatable_fields:
            if field in kwargs and kwargs[field] is not None:
                old_value = getattr(ave, field)
                new_value = kwargs[field]
                
                if field == 'raca_ave' and isinstance(new_value, str):
                    try:
                        new_value = RacaAve(new_value).value
                    except ValueError:
                        return jsonify({'error': f'Invalid breed: {new_value}'}), 400
                
                if field == 'data_nascimento' and isinstance(new_value, str):
                    new_value = datetime.strptime(new_value, '%Y-%m-%d').date()
                
                if old_value != new_value:
                    modificacoes.append({
                        'campo': field,
                        'valor_anterior': str(old_value),
                        'valor_novo': str(new_value),
                        'usuario': current_user.nome if current_user else 'Sistema',
                        'data_hora': datetime.now().isoformat()
                    })
                    setattr(ave, field, new_value)
        
        if modificacoes:
            historico_modificacoes = f"\n--- Modificações em {datetime.now().strftime('%d/%m/%Y %H:%M')} por {current_user.nome if current_user else 'Sistema'} ---\n"
            for mod in modificacoes:
                historico_modificacoes += f"{mod['campo']}: {mod['valor_anterior']} → {mod['valor_novo']}\n"
            
            ave.observacoes = (ave.observacoes or '') + historico_modificacoes
            
            ave.save()
            return jsonify({
                'message': 'Poultry updated successfully!',
                'modifications': modificacoes
            }), 200
        else:
            return jsonify({'message': 'No modification detected'}), 200
            
    except Exception as error:
        return jsonify({'error': f'Internal error: {str(error)}'}), 500

def delete_poultry(ave_id: int, motivo_exclusao: str):
    try:
        ave = Aves.get_or_none(Aves.id_ave == ave_id)
        if not ave:
            return jsonify({'message': 'Poultry not found'}), 404
        
        if not ave.ativa:
            return jsonify({'message': 'Poultry already deleted'}), 400

        current_user = g.get('current_user')
        
        ave.ativa = False
        
        log_exclusao = f"\n--- EXCLUSÃO em {datetime.now().strftime('%d/%m/%Y %H:%M')} ---\n"
        log_exclusao += f"Motivo: {motivo_exclusao}\n"
        log_exclusao += f"Responsável: {current_user.nome if current_user else 'Sistema'}\n"
        log_exclusao += f"Status: Inativa (soft delete)\n"
        
        ave.observacoes = (ave.observacoes or '') + log_exclusao
        
        ave.save()
        
        return jsonify({
            'message': 'Poultry deleted successfully (soft delete)!',
            'motivo': motivo_exclusao,
            'data_exclusao': datetime.now().isoformat(),
            'excluido_por': current_user.nome if current_user else 'Sistema'
        }), 200
        
    except Exception as error:
        return jsonify({'error': f'Internal error: {str(error)}'}), 500