from flask import Blueprint, render_template, request, Response
from app.models.database import Producao, Lote
from peewee import fn
from io import StringIO, BytesIO
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

producao_relatorio_bp = Blueprint('producao_relatorio', __name__)

@producao_relatorio_bp.route('/producao/relatorio', methods=['GET'])
def relatorio_producao():
    print('Acessando relatorio_producao')
    # Filtros
    inicio = request.args.get('inicio')
    fim = request.args.get('fim')
    lote_id = request.args.get('lote')
    agrupamento = request.args.get('agrupamento')

    print(f'Filtros recebidos: inicio={inicio}, fim={fim}, lote_id={lote_id}, agrupamento={agrupamento}')

    query = Producao.select()
    if inicio:
        query = query.where(Producao.data_coleta >= inicio)
    if fim:
        query = query.where(Producao.data_coleta <= fim)
    if lote_id:
        query = query.where(Producao.id_lote == lote_id)

    registros = list(query)
    print(f'Registros encontrados: {len(registros)}')

    # Indicadores de performance
    total_ovos = sum(r.quantidade_ovos for r in registros)
    ovos_danificados = sum(r.producao_nao_aproveitada for r in registros)
    aves_ativas = sum(r.quantidade_aves for r in registros)
    taxa_quebra = round((ovos_danificados / total_ovos) * 100, 2) if total_ovos else 0

    # Exportação CSV
    if request.args.get('export') == 'csv':
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['Data', 'Lote', 'Ovos', 'Ovos Danificados', 'Aves Ativas', 'Qualidade', 'Responsável'])
        for r in registros:
            writer.writerow([
                r.data_coleta,
                r.id_lote,
                r.quantidade_ovos,
                r.producao_nao_aproveitada,
                r.quantidade_aves,
                r.qualidade_producao,
                r.responsavel
            ])
        output = si.getvalue()
        return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=relatorio_producao.csv'})

    # Exportação PDF
    if request.args.get('export') == 'pdf':
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, 'Relatório de Produção de Ovos')
        y = 720
        for r in registros:
            p.drawString(100, y, f"{r.data_coleta} | Lote: {r.id_lote} | Ovos: {r.quantidade_ovos} | Danificados: {r.producao_nao_aproveitada} | Aves: {r.quantidade_aves}")
            y -= 20
            if y < 50:
                p.showPage()
                y = 750
        p.save()
        pdf = buffer.getvalue()
        buffer.close()
        return Response(pdf, mimetype='application/pdf', headers={'Content-Disposition': 'attachment;filename=relatorio_producao.pdf'})

    return render_template('producao/relatorio.html', registros=registros, total_ovos=total_ovos, ovos_danificados=ovos_danificados, aves_ativas=aves_ativas, taxa_quebra=taxa_quebra)
