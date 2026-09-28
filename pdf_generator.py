import io
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class PDFRelatorioExecutivo(SimpleDocTemplate):
    pass

def limpar_texto_portugues(texto):
    """
    Limpa e substitui caracteres especiais para garantir compatibilidade 
    com a fonte padrão do ReportLab, mantendo o padrão PT-BR.
    """
    if not isinstance(texto, str):
        return ""
    
    substituicoes = {
        '–': '-',
        '—': '-',
        '•': '-',
        '“': '"',
        '”': '"',
        '‘': "'",
        '’': "'",
        '\xa0': ' ',
        '■': '-',
        '€': 'R$',
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A',
        'é': 'e', 'ê': 'e', 'É': 'E', 'Ê': 'E',
        'í': 'i', 'Í': 'I',
        'ó': 'o', 'ô': 'o', 'õ': 'o', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O',
        'ú': 'u', 'Ú': 'U',
        'ç': 'c', 'Ç': 'C'
    }
    
    for k, v in substituicoes.items():
        texto = texto.replace(k, v)
        
    texto = texto.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
    return texto.encode('ascii', 'ignore').decode('ascii')

def gerar_pdf_executivo(relatorio_texto, categoria_selecionada, tom_relatorio):
    """
    Gera um relatório PDF executivo com design corporativo em Português do Brasil.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36, leftMargin=36,
        topMargin=36, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    estilo_titulo_principal = ParagraphStyle(
        'TituloPrincipal',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=4
    )
    
    estilo_sub = ParagraphStyle(
        'SubTitulo',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        textColor=colors.HexColor('#555555'),
        spaceAfter=10
    )
    
    estilo_h2 = ParagraphStyle(
        'SecaoTitulo',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=colors.HexColor('#1F4E78'),
        spaceBefore=10,
        spaceAfter=4
    )
    
    estilo_corpo = ParagraphStyle(
        'CorpoTexto',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=4
    )
    
    estilo_celula = ParagraphStyle(
        'CelulaTabela',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#222222')
    )
    
    estilo_celula_header = ParagraphStyle(
        'CelulaHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )

    story = []
    
    # Cabeçalho Corporativo em PT-BR
    story.append(Paragraph("Enterprise Data & AI Intelligence Hub", estilo_sub))
    story.append(Paragraph(limpar_texto_portugues(f"Relatorio Executivo: {tom_relatorio}"), estilo_titulo_principal))
    story.append(Paragraph(limpar_texto_portugues(f"<b>Escopo Analitico:</b> Categoria [{categoria_selecionada}]"), estilo_sub))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1F4E78'), spaceAfter=12))
    
    if not relatorio_texto:
        relatorio_texto = "Nenhum relatorio disponivel."
        
    linhas = relatorio_texto.split('\n')
    tabela_linhas_acumuladas = []
    
    def processar_tabela_acumulada(linhas_tab):
        if not linhas_tab:
            return
        dados_tabela = []
        for l in linhas_tab:
            cols = [Paragraph(limpar_texto_portugues(c.strip()), estilo_celula) for c in l.split('|') if c.strip() != '']
            if cols:
                dados_tabela.append(cols)
                
        if dados_tabela:
            for i, cell in enumerate(dados_tabela[0]):
                txt_original = dados_tabela[0][i].text
                dados_tabela[0][i] = Paragraph(f"<b>{txt_original}</b>", estilo_celula_header)
                
            t = Table(dados_tabela, hAlign='CENTER')
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F4F8')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D3D3D3'))
            ]))
            story.append(t)
            story.append(Spacer(1, 8))

    for linha in linhas:
        linha_str = linha.strip()
        
        if linha_str.startswith('|') and linha_str.endswith('|'):
            if '---' in linha_str:
                continue
            tabela_linhas_acumuladas.append(linha_str)
            continue
        else:
            if tabela_linhas_acumuladas:
                processar_tabela_acumulada(tabela_linhas_acumuladas)
                tabela_linhas_acumuladas = []
                
        if not linha_str:
            continue
            
        linha_limpa = limpar_texto_portugues(linha_str)
        
        if linha_limpa.startswith('#'):
            titulo = linha_limpa.replace('#', '').strip()
            story.append(Paragraph(titulo, estilo_h2))
        elif linha_limpa.startswith('>'):
            citacao = linha_limpa.replace('>', '').strip()
            story.append(Paragraph(f"<i>{citacao}</i>", estilo_corpo))
        else:
            formatado = linha_limpa.replace('**', '<b>', 1).replace('**', '</b>', 1).replace('*', '')
            story.append(Paragraph(formatado, estilo_corpo))
            
    if tabela_linhas_acumuladas:
        processar_tabela_acumulada(tabela_linhas_acumuladas)
        
    doc.build(story)
    return buffer.getvalue()