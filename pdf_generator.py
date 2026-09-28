import re
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12) # Fonte ligeiramente menor
        self.set_text_color(42, 52, 65)
        self.cell(0, 5, 'Enterprise Data & AI Intelligence Hub', 0, 1, 'C')
        
        self.set_draw_color(200, 200, 200)
        self.line(10, 15, 200, 15)
        self.ln(1.5) 

    def footer(self):
        self.set_y(-8) 
        self.set_font('Arial', 'I', 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, f'Página {self.page_no()}', 0, 0, 'C')

def limpar_sintaxe_e_encoding(texto):
    texto_strip = texto.strip()
    if re.match(r'^[-_]{3,}$', texto_strip):
        return ""
        
    texto = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)
    texto = re.sub(r'\*(.*?)\*', r'\1', texto)
    texto = re.sub(r'([a-zA-ZáéíóúãõçÁÉÍÓÚÃÕÇ])(\d\.)', r'\1 \2', texto) 
    
    texto = texto.replace("globais-Faturamento", "globais - Faturamento")
    texto = texto.replace("homeoffice", "home-office").replace("Homeoffice", "Home-office")
    texto = texto.replace("Hub USBC", "Hub USB-C").replace("Hub USB C", "Hub USB-C")
    texto = texto.replace("do 2024", "de 2024")
    
    texto = texto.replace('\xa0', ' ').replace('\u200b', '')
    texto = texto.replace('•', '-')
    texto = re.sub(r'[\u2010\u2011\u2012\u2013\u2014\u2015\u2212]', '-', texto)
    texto = texto.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    texto = texto.replace("Hub USB?C", "Hub USB-C").replace("cross?sell", "cross-sell")
    
    return texto.strip()

def gerar_pdf_executivo(relatorio_md, categoria, tom):
    pdf = PDF()
    pdf.add_page()
    
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=6) # Limite inferior ultra comprimido
    
    linhas = relatorio_md.split('\n')
    em_tabela = False
    larguras = []
    
    for linha in linhas:
        linha_limpa = limpar_sintaxe_e_encoding(linha)
        
        if not linha_limpa:
            if not em_tabela:
                pdf.ln(1)
            continue
            
        try:
            texto_final = linha_limpa.encode('latin-1', 'replace').decode('latin-1')
        except Exception:
            texto_final = linha_limpa
            
        if re.match(r'^#+\s', texto_final):
            pdf.ln(1)
            pdf.set_x(10)
            pdf.set_font("Arial", 'B', 10) # Título comprimido
            pdf.set_text_color(20, 30, 40)
            texto_titulo = re.sub(r'^#+\s', '', texto_final)
            pdf.multi_cell(190, 4.0, texto_titulo)
            pdf.ln(0.5)
            continue
            
        if '|' in texto_final and not texto_final.startswith('Nota'):
            celulas = [c.strip() for c in texto_final.split('|') if c.strip()]
            if not celulas or all(re.match(r'^[-:\s]+$', c) for c in celulas): continue
                
            if not em_tabela:
                pdf.set_font("Arial", 'B', 8) 
                pdf.set_fill_color(240, 240, 240)
                pdf.set_text_color(20, 30, 40)
                num_colunas = len(celulas)
                larguras = [190 / num_colunas] * num_colunas
                if num_colunas >= 4:
                    larguras[0] = 55 
                    sobra = 190 - 55
                    for i in range(1, num_colunas): larguras[i] = sobra / (num_colunas - 1)
                em_tabela = True
                is_header = True
            else:
                pdf.set_font("Arial", '', 8)
                pdf.set_text_color(40, 40, 40)
                is_header = False
            
            if pdf.get_y() > 280: pdf.add_page()
            pdf.set_x(10)
            
            altura_linha = 5.5 # Altura da tabela otimizada
            
            max_linhas = 1
            for i, celula in enumerate(celulas):
                if i >= len(larguras): break
                largura_texto = pdf.get_string_width(celula)
                linhas_estimadas = max(1, int((largura_texto / (larguras[i] - 2)) + 1))
                if linhas_estimadas > max_linhas: max_linhas = linhas_estimadas
            
            altura_total = max_linhas * altura_linha
            x_atual, y_atual = pdf.get_x(), pdf.get_y()
            
            for i, celula in enumerate(celulas):
                if i >= len(larguras): break
                largura = larguras[i]
                alinhamento = 'L' if i == 0 else 'R'
                
                pdf.rect(x_atual, y_atual, largura, altura_total, 'DF' if is_header else 'D')
                pdf.set_xy(x_atual, y_atual)
                pdf.multi_cell(largura, altura_linha, celula, border=0, align=alinhamento)
                
                x_atual += largura
                
            pdf.set_xy(10, y_atual + altura_total)
            continue
            
        if em_tabela:
            em_tabela = False
            pdf.ln(1)
            
        pdf.set_x(10)
        pdf.set_font("Arial", '', 8) # Fonte base reduzida para 8
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(190, 4.0, texto_final) # Entrelinha otimizada
        
    try:
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
    except AttributeError:
        pdf_bytes = bytes(pdf.output(dest='S'))
        
    return pdf_bytes