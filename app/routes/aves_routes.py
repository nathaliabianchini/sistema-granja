from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.forms.aves_forms import AvesForm
from app.controllers.aves_controller import register_poultry, get_poultries, get_poultry, update_poultry, delete_poultry
from datetime import datetime

aves_bp = Blueprint('aves', __name__, url_prefix='/aves')

@aves_bp.route('/')
def listar():
    if not session.get('user_logged_in'):
        flash('Acesso negado. Faça login primeiro.', 'danger')
        return redirect(url_for('auth.login'))
    
    try:
        response = get_poultries()
        
        if hasattr(response, 'get_json'):
            aves_data = response.get_json()
        else:
            aves_data = response
        
        if isinstance(aves_data, dict) and 'aves' in aves_data:
            aves = aves_data['aves']
        elif isinstance(aves_data, list):
            aves = aves_data
        else:
            aves = []
        
        return render_template('aves/listar.html', aves=aves)
        
    except Exception as e:
        flash(f'Erro ao carregar aves: {str(e)}', 'danger')
        return render_template('aves/listar.html', aves=[])

@aves_bp.route('/novo', methods=['GET', 'POST'])
def cadastrar():
    if not session.get('user_logged_in'):
        flash('Acesso negado. Faça login primeiro.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = AvesForm()
    
    if form.validate_on_submit():
        try:
            ave_data = {
                'id_lote': form.id_lote.data,
                'raca_ave': form.raca_ave.data,
                'data_nascimento': form.data_nascimento.data.strftime('%Y-%m-%d'),
                'tempo_de_vida': form.tempo_de_vida.data,
                'media_peso': float(form.media_peso.data),
                'caracteristicas_geneticas': form.caracteristicas_geneticas.data,
                'tipo_alojamento': form.tipo_alojamento.data,
                'historico_vacinas': form.historico_vacinas.data,
                'observacoes': form.observacoes.data or ''
            }
            
            response = register_poultry(**ave_data)
            
            if isinstance(response, tuple):
                actual_response, status_code = response
                
                if status_code == 201:
                    try:
                        if hasattr(actual_response, 'get_json'):
                            success_data = actual_response.get_json()
                            ave_id = success_data.get('id_ave', 'N/A')
                            flash(f'✅ Ave cadastrada com sucesso! ID: {ave_id}', 'success')
                        else:
                            flash('✅ Ave cadastrada com sucesso!', 'success')
                    except:
                        flash('✅ Ave cadastrada com sucesso!', 'success')
                    
                    return redirect(url_for('aves.listar'))
                else:
                    try:
                        if hasattr(actual_response, 'get_json'):
                            error_data = actual_response.get_json()
                            error_msg = error_data.get('error', 'Erro desconhecido')
                        else:
                            error_msg = "Erro ao processar resposta"
                    except:
                        error_msg = "Erro desconhecido"
                    
                    flash(f'❌ Erro ao cadastrar ave: {error_msg}', 'danger')
            else:
                if hasattr(response, 'status_code') and response.status_code == 201:
                    flash('✅ Ave cadastrada com sucesso!', 'success')
                    return redirect(url_for('aves.listar'))
                else:
                    flash('❌ Erro ao cadastrar ave.', 'danger')
                
        except Exception as e:
            flash(f'❌ Erro ao cadastrar ave: {str(e)}', 'danger')
    else:
        if form.errors:
            print("DEBUG - Erros de validação:", form.errors)
    
    return render_template('aves/cadastrar.html', form=form)

@aves_bp.route('/editar/<int:ave_id>', methods=['GET', 'POST'])
def editar(ave_id):
    if not session.get('user_logged_in'):
        flash('Acesso negado. Faça login primeiro.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        response = get_poultry(ave_id)
        
        if isinstance(response, tuple):
            actual_response, status_code = response
            if status_code != 200:
                flash('❌ Ave não encontrada.', 'danger')
                return redirect(url_for('aves.listar'))
            ave_data = actual_response.get_json()
        else:
            if hasattr(response, 'get_json'):
                ave_data = response.get_json()
            else:
                ave_data = response
                
        if not ave_data:
            flash('❌ Ave não encontrada.', 'danger')
            return redirect(url_for('aves.listar'))

    except Exception as e:
        flash(f'❌ Erro ao carregar ave: {str(e)}', 'danger')
        return redirect(url_for('aves.listar'))

    form = AvesForm()

    if form.validate_on_submit():
        try:
            update_data = {
                'id_lote': form.id_lote.data,
                'raca_ave': form.raca_ave.data,
                'data_nascimento': form.data_nascimento.data.strftime('%Y-%m-%d'),
                'tempo_de_vida': form.tempo_de_vida.data,
                'media_peso': float(form.media_peso.data),
                'caracteristicas_geneticas': form.caracteristicas_geneticas.data,
                'tipo_alojamento': form.tipo_alojamento.data,
                'historico_vacinas': form.historico_vacinas.data,
                'observacoes': form.observacoes.data or ''
            }

            response = update_poultry(ave_id, **update_data)
            
            if isinstance(response, tuple):
                actual_response, status_code = response
                if status_code == 200:
                    flash('✅ Ave atualizada com sucesso!', 'success')
                    return redirect(url_for('aves.listar'))
                else:
                    flash('❌ Erro ao atualizar ave.', 'danger')
            else:
                if hasattr(response, 'status_code') and response.status_code == 200:
                    flash('✅ Ave atualizada com sucesso!', 'success')
                    return redirect(url_for('aves.listar'))
                else:
                    flash('❌ Erro ao atualizar ave.', 'danger')

        except Exception as e:
            flash(f'❌ Erro ao atualizar ave: {str(e)}', 'danger')

    # Preencher formulário com dados atuais
    if request.method == 'GET':
        try:
            form.id_lote.data = ave_data.get('id_lote', '')
            form.raca_ave.data = ave_data.get('raca_ave', '')
            data_nasc = ave_data.get('data_nascimento')
            if data_nasc:
                if isinstance(data_nasc, str):
                    form.data_nascimento.data = datetime.strptime(data_nasc.split('T')[0], '%Y-%m-%d').date()
                else:
                    form.data_nascimento.data = data_nasc
                    
            form.tempo_de_vida.data = ave_data.get('tempo_de_vida', 0)
            form.media_peso.data = ave_data.get('media_peso', 0.0)
            form.caracteristicas_geneticas.data = ave_data.get('caracteristicas_geneticas', '')
            form.tipo_alojamento.data = ave_data.get('tipo_alojamento', '')
            form.historico_vacinas.data = ave_data.get('historico_vacinas', '')
            form.observacoes.data = ave_data.get('observacoes', '')
            
        except Exception as e:
            flash(f'⚠️ Erro ao carregar dados da ave: {str(e)}', 'warning')

    return render_template('aves/editar.html', form=form, ave=ave_data)

@aves_bp.route('/excluir/<int:ave_id>', methods=['POST'])
def excluir(ave_id):
    if not session.get('user_logged_in') or session.get('user_tipo') != 'administrador':
        flash('Acesso negado. Apenas administradores podem excluir aves.', 'danger')
        return redirect(url_for('aves.listar'))
    
    try:
        motivo = request.form.get('motivo', 'Exclusão via interface web')
        response = delete_poultry(ave_id, motivo)
        
        if isinstance(response, tuple):
            actual_response, status_code = response
            if status_code == 200:
                flash('✅ Ave excluída com sucesso!', 'success')
            else:
                flash('❌ Erro ao excluir ave.', 'danger')
        else:
            flash('❌ Erro ao excluir ave.', 'danger')
            
    except Exception as e:
        flash(f'❌ Erro ao excluir ave: {str(e)}', 'danger')
    
    return redirect(url_for('aves.listar'))