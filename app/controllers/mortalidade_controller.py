from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from app.forms.mortalidade_forms import MortalidadeForm
from app.models.database import RelatoriosMortalidade, Aves, Lote, Setor, Usuarios
import datetime

mortalidade_bp = Blueprint('mortalidade', __name__)

@mortalidade_bp.route('/mortalidade/registrar', methods=['GET', 'POST'])
def registrar_mortalidade():
	form = MortalidadeForm(request.form)
	form.set_choices()
	if request.method == 'POST' and form.validate():
		evento = RelatoriosMortalidade.create(
			data_hora_evento=form.data_hora_evento.data,
			ave=form.ave.data,
			lote=form.lote.data,
			setor=form.setor.data,
			motivo_obito=form.motivo_obito.data,
			categoria_motivo=form.categoria_motivo.data,
			descricao_adicional=form.descricao_adicional.data,
			funcionario=form.funcionario.data,
			data_registro=datetime.datetime.now()
		)
		flash('Evento de mortalidade registrado com sucesso!', 'success')
		return redirect(url_for('mortalidade.registrar_mortalidade'))
	return render_template('mortalidade/registrar.html', form=form)

@mortalidade_bp.route('/mortalidade/relatorio', methods=['GET'])
def relatorio_mortalidade():
	# Filtros
	periodo_inicio = request.args.get('inicio')
	periodo_fim = request.args.get('fim')
	lote_id = request.args.get('lote')
	setor_id = request.args.get('setor')
	raca = request.args.get('raca')
	motivo = request.args.get('motivo')

	query = RelatoriosMortalidade.select().join(Aves).switch(RelatoriosMortalidade)
	if periodo_inicio:
		query = query.where(RelatoriosMortalidade.data_hora_evento >= periodo_inicio)
	if periodo_fim:
		query = query.where(RelatoriosMortalidade.data_hora_evento <= periodo_fim)
	if lote_id:
		query = query.where(RelatoriosMortalidade.lote == lote_id)
	if setor_id:
		query = query.where(RelatoriosMortalidade.setor == setor_id)
	if raca:
		query = query.where(Aves.raca_ave == raca)
	if motivo:
		query = query.where(RelatoriosMortalidade.categoria_motivo == motivo)

	registros = list(query)

	# Cálculo de totais e porcentagem
	total_mortes = len(registros)
	total_aves_lote = None
	porcentagem_mortalidade = None
	if lote_id:
		lote = Lote.get_or_none(Lote.id_lote == lote_id)
		if lote:
			total_aves_lote = lote.quantidade_inicial
			if total_aves_lote:
				porcentagem_mortalidade = round((total_mortes / total_aves_lote) * 100, 2)

	# Exportação CSV
	if request.args.get('export') == 'csv':
		import csv
		from io import StringIO
		si = StringIO()
		writer = csv.writer(si)
		writer.writerow(['Data/Hora', 'Ave', 'Lote', 'Setor', 'Motivo', 'Categoria', 'Funcionário'])
		for r in registros:
			writer.writerow([
				r.data_hora_evento,
				r.ave.id_ave,
				r.lote.numero_lote,
				r.setor.descricao_setor,
				r.motivo_obito,
				r.categoria_motivo,
				r.funcionario.nome
			])
		output = si.getvalue()
		return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=relatorio_mortalidade.csv'})

	# Exportação PDF
	if request.args.get('export') == 'pdf':
		from io import BytesIO
		from reportlab.lib.pagesizes import letter
		from reportlab.pdfgen import canvas
		buffer = BytesIO()
		p = canvas.Canvas(buffer, pagesize=letter)
		p.drawString(100, 750, 'Relatório de Mortalidade')
		y = 720
		for r in registros:
			p.drawString(100, y, f"{r.data_hora_evento} | Ave: {r.ave.id_ave} | Lote: {r.lote.numero_lote} | Setor: {r.setor.descricao_setor} | Motivo: {r.motivo_obito}")
			y -= 20
			if y < 50:
				p.showPage()
				y = 750
		p.save()
		pdf = buffer.getvalue()
		buffer.close()
		return Response(pdf, mimetype='application/pdf', headers={'Content-Disposition': 'attachment;filename=relatorio_mortalidade.pdf'})

	return render_template('mortalidade/relatorio.html', registros=registros, total_mortes=total_mortes, porcentagem_mortalidade=porcentagem_mortalidade)
