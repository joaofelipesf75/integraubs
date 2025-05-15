"""
SISTEMA INTEGRA UBS - Módulo de Relatórios
"""
import io
import csv
import re
from datetime import datetime, timedelta
from flask import render_template, flash, redirect, url_for, jsonify, request, Response, make_response
from flask_login import login_required, current_user
from app import db
from models import Medication, MedicationBatch, Prescription, User, Patient, MedicationDispensing, PrescriptionItem
from fpdf import FPDF

# Utilitários para formatação de texto
def abreviar_texto(texto, max_len=25, preservar_palavras=True):
    """
    Abrevia um texto longo para caber em relatórios
    
    Args:
        texto: Texto original a ser abreviado
        max_len: Comprimento máximo desejado
        preservar_palavras: Se True, corta em espaços para preservar palavras
        
    Returns:
        Texto abreviado com '...' se necessário
    """
    if texto is None:
        return ""
        
    texto = str(texto).strip()
    
    # Aplicar abreviações comuns para economizar espaço
    abreviacoes = {
        'COMPRIMIDO': 'COMP',
        'MILIGRAMA': 'MG',
        'CÁPSULA': 'CAP',
        'INJETÁVEL': 'INJ',
        'SOLUÇÃO': 'SOL',
        'SUSPENSÃO': 'SUSP',
        'FRASCO': 'FR',
        'AMPOLA': 'AMP',
        'XAROPE': 'XAR',
        'MILILITRO': 'ML',
        'MILIGRAMA/MILILITRO': 'MG/ML',
        'MICROGRAMA': 'MCG',
        'POMADA': 'POM',
        'BISNAGA': 'BIS',
        'UNIDADE': 'UN',
        'DISPOSITIVO': 'DISP',
    }
    
    # Aplicar abreviações (caso insensitivo)
    for palavra, abreviacao in abreviacoes.items():
        texto = texto.replace(palavra, abreviacao).replace(palavra.lower(), abreviacao.lower())
    
    # Se o texto já for curto o suficiente, retorna sem alterações
    if len(texto) <= max_len:
        return texto
        
    if preservar_palavras:
        # Tentar cortar na última palavra completa
        palavras = texto[:max_len-3].split()
        if palavras:
            # Remover a última palavra se estiver cortada
            texto_abreviado = ' '.join(palavras[:-1]) if len(' '.join(palavras)) > max_len-3 else ' '.join(palavras)
            return texto_abreviado + '...'
        else:
            # Se não tem espaços, corta o texto
            return texto[:max_len-3] + '...'
    else:
        # Corta exatamente no comprimento máximo
        return texto[:max_len-3] + '...'

def abreviar_nome_medicamento(nome, concentracao=None, forma=None, max_len=30):
    """
    Cria uma versão abreviada do nome do medicamento incluindo concentração
    
    Args:
        nome: Nome do medicamento
        concentracao: Concentração se disponível
        forma: Forma farmacêutica se disponível
        max_len: Comprimento máximo
        
    Returns:
        Nome abreviado com concentração
    """
    if not nome:
        return ""
        
    # Remover partes comuns que podem ser abreviadas
    nome = re.sub(r'comprimido[s]?', 'comp', nome, flags=re.IGNORECASE)
    nome = re.sub(r'cápsula[s]?', 'cap', nome, flags=re.IGNORECASE)
    nome = re.sub(r'suspensão', 'susp', nome, flags=re.IGNORECASE)
    nome = re.sub(r'solução', 'sol', nome, flags=re.IGNORECASE)
    nome = re.sub(r'injetável', 'inj', nome, flags=re.IGNORECASE)
    nome = re.sub(r'xarope', 'xar', nome, flags=re.IGNORECASE)
    
    # Composição do texto completo
    texto_completo = nome
    
    # Adicionar concentração se fornecida
    if concentracao:
        texto_completo += f" {concentracao}"
        
    # Adicionar forma se fornecida e ainda não estiver no nome
    if forma and forma.lower() not in nome.lower():
        texto_completo += f" ({forma})"
        
    # Abreviar se necessário
    return abreviar_texto(texto_completo, max_len)

# Classe personalizada para gerar PDFs
class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Logo
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 102, 204)  # Azul UBS
        self.cell(0, 10, 'Sistema Integra UBS', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.set_text_color(128, 128, 128)  # Cinza
        self.cell(0, 10, f'Relatório gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
        self.ln(5)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)  # Cinza
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
        
    def add_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)
        
    def subtitle(self, subtitle):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(64, 64, 64)
        self.cell(0, 10, subtitle, 0, 1, 'L')
        self.ln(2)
        
    def table_header(self, headers, widths):
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(0, 102, 204)  # Azul UBS
        
        for i, header in enumerate(headers):
            self.cell(widths[i], 8, header, 1, 0, 'C', fill=True)
        self.ln()
        
    def table_row(self, data, widths, fill=False):
        self.set_font('Arial', '', 10)  # Fonte maior para melhor legibilidade
        self.set_text_color(0, 0, 0)
        
        if fill:
            self.set_fill_color(240, 240, 240)  # Cinza claro
        else:
            self.set_fill_color(255, 255, 255)  # Branco
            
        # Altura base da linha e valor mínimo
        line_height = 5
        min_row_height = 8
        row_height = 8
        
        # Processar os textos e dividir em múltiplas linhas se necessário
        processed_data = []
        all_lines = []
        total_lines = 1  # Inicialmente, pelo menos 1 linha
        
        # Determinar quantas linhas são necessárias no total
        for i, cell_data in enumerate(data):
            text = str(cell_data)
            processed_data.append(text)
            
            # Para colunas de texto longas (como nome e princípio ativo)
            # Calcular quantas linhas serão necessárias baseado na largura
            if i in [1, 2] and len(text) > 30:  # Colunas de nome e princípio ativo
                # Estimar quantos caracteres cabem por linha
                chars_per_line = int(widths[i] / 2)  # Aproximadamente 2 caracteres por mm
                if chars_per_line == 0:
                    chars_per_line = 1
                
                # Quantas linhas este texto vai ocupar?
                num_lines = int(len(text) / chars_per_line) + (1 if len(text) % chars_per_line > 0 else 0)
                if num_lines > total_lines:
                    total_lines = num_lines
        
        # Ajustar a altura da linha baseado no texto mais longo
        if total_lines > 1:
            row_height = min_row_height * total_lines
        
        # Desenhar as células com a altura calculada
        for i, text in enumerate(processed_data):
            # Alinhamento baseado no tipo de dado
            if text.replace(',', '').replace('.', '').isdigit():
                align = 'R'  # Números à direita
            elif widths[i] < 15:
                align = 'C'  # Células estreitas centralizadas
            else:
                align = 'L'  # Texto normal à esquerda
            
            # Para textos longos, podemos usar multi_cell em vez de cell
            if i in [1, 2] and len(text) > 30 and total_lines > 1:
                # Salvar posição atual
                x = self.get_x()
                y = self.get_y()
                
                # Desenhar célula com bordas
                self.rect(x, y, widths[i], row_height)
                
                # Desenhar texto com quebra de linha
                self.multi_cell(widths[i], min_row_height, text, 0, align, fill)
                
                # Restaurar posição para a próxima célula
                self.set_xy(x + widths[i], y)
            else:
                # Para textos curtos, usar cell normal
                self.cell(widths[i], row_height, text, 1, 0, align, fill=fill)
        
        # Avançar para a próxima linha
        self.ln(row_height)

def gerar_receituario(prescription_id):
    """
    Gera um receituário médico em formato PDF para a prescrição especificada
    
    Args:
        prescription_id: ID da prescrição a ser impressa
        
    Returns:
        PDF do receituário médico formatado
    """
    # Buscar a prescrição e seus itens
    prescription = Prescription.query.get_or_404(prescription_id)
    items = PrescriptionItem.query.filter_by(prescription_id=prescription_id).all()
    
    # Buscar informações relacionadas
    patient = Patient.query.get(prescription.patient_id)
    doctor = User.query.get(prescription.doctor_id)
    
    # Criar o PDF
    pdf = PDF()
    pdf.add_page()
    
    # Cabeçalho do receituário
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 102, 204)  # Azul UBS
    pdf.cell(0, 10, "RECEITUÁRIO MÉDICO", 0, 1, 'C')
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "SISTEMA INTEGRA UBS", 0, 1, 'C')
    
    # Linha separadora
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Informações do paciente
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "IDENTIFICAÇÃO DO PACIENTE", 0, 1, 'L')
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(40, 7, "Nome:", 0, 0, 'L')
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 7, patient.nome if patient else "NÃO IDENTIFICADO", 0, 1, 'L')
    
    pdf.set_font('Arial', '', 11)
    
    # CPF e cartão SUS na mesma linha
    pdf.cell(40, 7, "CPF:", 0, 0, 'L')
    pdf.cell(60, 7, patient.cpf if patient and patient.cpf else "Não informado", 0, 0, 'L')
    
    pdf.cell(30, 7, "Cartão SUS:", 0, 0, 'L')
    pdf.cell(0, 7, patient.sus_card if patient and patient.sus_card else "Não informado", 0, 1, 'L')
    
    # Data de nascimento e data da prescrição
    data_nasc = patient.data_nascimento.strftime('%d/%m/%Y') if patient and patient.data_nascimento else "Não informada"
    pdf.cell(40, 7, "Data de Nascimento:", 0, 0, 'L')
    pdf.cell(60, 7, data_nasc, 0, 0, 'L')
    
    pdf.cell(30, 7, "Data da Receita:", 0, 0, 'L')
    pdf.cell(0, 7, prescription.date.strftime('%d/%m/%Y'), 0, 1, 'L')
    
    # Linha separadora
    pdf.line(10, pdf.get_y() + 3, 200, pdf.get_y() + 3)
    pdf.ln(8)
    
    # Título da prescrição
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, "MEDICAMENTOS PRESCRITOS", 0, 1, 'L')
    
    # Lista de medicamentos
    pdf.set_font('Arial', '', 11)
    
    if not items:
        pdf.cell(0, 10, "Nenhum medicamento prescrito", 0, 1, 'C')
    else:
        for i, item in enumerate(items):
            medication = Medication.query.get(item.medication_id)
            if not medication:
                continue
                
            # Número do item
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 10, f"{i+1}) {medication.nome}", 0, 1, 'L')
            
            # Concentração e forma
            if medication.concentracao or medication.forma:
                info = []
                if medication.concentracao:
                    info.append(medication.concentracao)
                if medication.forma:
                    info.append(medication.forma)
                
                pdf.set_font('Arial', 'I', 10)
                pdf.cell(0, 6, ", ".join(info), 0, 1, 'L')
            
            # Quantidade e instruções de uso
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 8, f"Quantidade: {item.quantidade}", 0, 1, 'L')
            
            # Instruções com estilo diferente
            if item.instrucoes:
                pdf.set_font('Arial', '', 10)
                pdf.multi_cell(0, 6, f"Instruções: {item.instrucoes}", 0, 'L')
            
            pdf.ln(3)  # Espaço entre medicamentos
    
    # Observações da prescrição
    if prescription.observacoes:
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, "OBSERVAÇÕES:", 0, 1, 'L')
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, prescription.observacoes, 0, 'L')
    
    # Rodapé com assinatura do médico
    pdf.ln(20)
    pdf.line(65, pdf.get_y(), 145, pdf.get_y())
    pdf.set_font('Arial', 'B', 10)
    pdf.ln(3)
    pdf.cell(0, 6, doctor.nome if doctor else "MÉDICO RESPONSÁVEL", 0, 1, 'C')
    
    if doctor:
        pdf.set_font('Arial', '', 9)
        role_text = "Médico(a)" if doctor.role == 'medico' else doctor.role.capitalize()
        pdf.cell(0, 6, f"{role_text} - Sistema Integra UBS", 0, 1, 'C')
    
    # Gerar o PDF e retornar
    pdf_output = io.BytesIO()
    pdf_data = pdf.output(dest='S').encode('latin1')
    pdf_output.write(pdf_data)
    pdf_output.seek(0)
    
    return pdf_output

def register_relatorios_route(app):
    """Registra as rotas relacionadas a relatórios"""
    
    # Rota de receituário movida para receituario.py
    
    @app.route('/relatorios')
    @login_required
    def relatorios():
        """Página de relatórios do sistema"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        # Dados para o relatório de estoque
        medications = Medication.query.all()
        medication_stock = []
        
        for med in medications:
            batches = MedicationBatch.query.filter_by(medication_id=med.id).all()
            total_stock = sum(batch.quantidade_atual for batch in batches)
            
            medication_stock.append({
                'id': med.id,
                'nome': med.nome,
                'principio_ativo': med.principio_ativo,
                'forma': med.forma,
                'concentracao': med.concentracao,
                'total_stock': total_stock,
                'batches': len(batches)
            })
        
        # Dados para o relatório de prescrições
        prescriptions = Prescription.query.all()
        prescription_count = len(prescriptions)
        pending_count = Prescription.query.filter_by(status='pendente').count()
        dispensed_count = Prescription.query.filter_by(status='dispensado').count()
        
        # Dados para gráficos
        prescription_data = {
            'labels': ['Pendentes', 'Dispensadas'],
            'values': [pending_count, dispensed_count]
        }
        
        # Obter dados de lotes vencidos e próximos do vencimento (30 dias)
        today = datetime.now().date()
        from datetime import timedelta
        thirty_days_later = today + timedelta(days=30)
        
        # Lotes vencidos com estoque disponível
        expired_batches = MedicationBatch.query.filter(
            MedicationBatch.validade < today,
            MedicationBatch.quantidade_atual > 0
        ).order_by(MedicationBatch.validade).all()
        
        # Lotes próximos do vencimento
        expiring_soon = MedicationBatch.query.filter(
            MedicationBatch.validade >= today,
            MedicationBatch.validade <= thirty_days_later,
            MedicationBatch.quantidade_atual > 0
        ).order_by(MedicationBatch.validade).all()
        
        # Combinar os dois conjuntos, marcando os vencidos
        expiring_meds = []
        
        # Primeiro os vencidos (com marcador de status)
        for batch in expired_batches:
            medication = Medication.query.get(batch.medication_id)
            if medication:
                days_expired = (today - batch.validade).days
                expiring_meds.append({
                    'medication': medication.nome,
                    'batch': batch.lote,
                    'expiry': batch.validade.strftime('%d/%m/%Y'),
                    'stock': batch.quantidade_atual,
                    'status': f"VENCIDO há {days_expired} dias",
                    'expired': True
                })
        
        # Depois os que vão vencer (com indicação de dias para vencer)
        for batch in expiring_soon:
            medication = Medication.query.get(batch.medication_id)
            if medication:
                days_to_expire = (batch.validade - today).days
                expiring_meds.append({
                    'medication': medication.nome,
                    'batch': batch.lote,
                    'expiry': batch.validade.strftime('%d/%m/%Y'),
                    'stock': batch.quantidade_atual,
                    'status': f"Vence em {days_to_expire} dias",
                    'expired': False,
                    'critical': days_to_expire <= 7
                })
        
        return render_template(
            'relatorios.html',
            medication_stock=medication_stock,
            prescription_count=prescription_count,
            pending_count=pending_count,
            dispensed_count=dispensed_count,
            prescription_data=prescription_data,
            expiring_meds=expiring_meds
        )
        
    @app.route('/api/relatorios/medicamentos')
    @login_required
    def api_relatorio_medicamentos():
        """API para dados de relatório de medicamentos"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico']:
            return jsonify({'error': 'Acesso negado'}), 403
        
        medications = Medication.query.all()
        data = []
        
        labels = []
        values = []
        
        for med in medications:
            total_stock = med.stock_total()
            if total_stock > 0:
                labels.append(med.nome)
                values.append(total_stock)
        
        return jsonify({
            'labels': labels,
            'values': values
        })
        
    @app.route('/api/relatorios/prescricoes')
    @login_required
    def api_relatorio_prescricoes():
        """API para dados de relatório de prescrições"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico']:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Dados para o gráfico de status de prescrições
        pending_count = Prescription.query.filter_by(status='pendente').count()
        dispensed_count = Prescription.query.filter_by(status='dispensado').count()
        canceled_count = Prescription.query.filter_by(status='cancelado').count()
        
        return jsonify({
            'labels': ['Pendentes', 'Dispensadas', 'Canceladas'],
            'values': [pending_count, dispensed_count, canceled_count]
        })
        
    @app.route('/relatorios/exportar/estoque')
    @login_required
    def exportar_estoque_medicamentos():
        """Exporta o relatório de estoque de medicamentos em formato PDF"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        # Busca todos os medicamentos e seus lotes
        medications = Medication.query.order_by(Medication.nome).all()
        
        # Calcula estatísticas
        total_medicamentos = len(medications)
        total_estoque = 0
        medicamentos_sem_estoque = 0
        
        for med in medications:
            batches = MedicationBatch.query.filter_by(medication_id=med.id).all()
            total_stock = sum(batch.quantidade_atual for batch in batches)
            total_estoque += total_stock
            if total_stock == 0:
                medicamentos_sem_estoque += 1
        
        # Cria o PDF com orientação paisagem para mais espaço horizontal
        pdf = PDF()
        pdf.add_page(orientation='L')  # L = Landscape (paisagem)
        
        # Título do relatório
        pdf.add_title("Relatório de Estoque de Medicamentos")
        pdf.subtitle(f"UBS - {datetime.now().strftime('%d/%m/%Y')}")
        
        # Informações gerais
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Total de Medicamentos: {len(medications)}", 0, 1)
        pdf.cell(0, 6, f"Estoque Total: {total_estoque} unidades", 0, 1)
        pdf.cell(0, 6, f"Medicamentos sem estoque: {medicamentos_sem_estoque}", 0, 1)
        pdf.ln(5)
        
        # Cabeçalho da tabela - Usar larguras bem generosas na orientação paisagem
        headers = ['ID', 'Nome', 'Princípio Ativo', 'Forma', 'Concentração', 'Estoque', 'Lotes']
        widths = [15, 80, 70, 25, 30, 20, 15]  # Larguras adaptadas para a página paisagem
        
        pdf.table_header(headers, widths)
        
        # Dados da tabela
        for i, med in enumerate(medications):
            batches = MedicationBatch.query.filter_by(medication_id=med.id).all()
            total_stock = sum(batch.quantidade_atual for batch in batches)
            
            # Usar valores originais sem abreviação
            row_data = [
                med.id,
                med.nome,
                med.principio_ativo or '-',
                med.forma or '-',
                med.concentracao or '-',
                total_stock,
                len(batches)
            ]
            
            pdf.table_row(row_data, widths, fill=(i % 2 == 0))
        
        # Gera o PDF em memória
        pdf_output = io.BytesIO()
        pdf_data = pdf.output(dest='S').encode('latin1')
        pdf_output.write(pdf_data)
        pdf_output.seek(0)
        
        # Retorna o PDF como resposta
        response = make_response(pdf_output.getvalue())
        response.headers.set('Content-Type', 'application/pdf')
        response.headers.set('Content-Disposition', 'attachment', filename='estoque_medicamentos.pdf')
        
        return response
    
    @app.route('/relatorios/exportar/vencimentos')
    @login_required
    def exportar_medicamentos_vencimento():
        """Exporta o relatório de medicamentos próximos do vencimento e já vencidos em formato PDF"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        # Datas de referência
        today = datetime.now().date()
        thirty_days_later = today + timedelta(days=30)
        
        # Busca lotes já vencidos com estoque disponível
        expired_batches = MedicationBatch.query.filter(
            MedicationBatch.validade < today,
            MedicationBatch.quantidade_atual > 0
        ).order_by(MedicationBatch.validade).all()
        
        # Busca lotes próximos do vencimento (30 dias)
        expiring_batches = MedicationBatch.query.filter(
            MedicationBatch.validade >= today,
            MedicationBatch.validade <= thirty_days_later,
            MedicationBatch.quantidade_atual > 0
        ).order_by(MedicationBatch.validade).all()
        
        # Cria o PDF com orientação paisagem para mais espaço
        pdf = PDF()
        pdf.add_page(orientation='L')  # L = Landscape (paisagem)
        
        # Título do relatório
        pdf.add_title("Relatório de Medicamentos Vencidos e a Vencer")
        pdf.subtitle(f"Data de referência: {today.strftime('%d/%m/%Y')}")
        
        # Informações gerais
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Total de Lotes Vencidos: {len(expired_batches)}", 0, 1)
        pdf.cell(0, 6, f"Total de Lotes a Vencer em 30 dias: {len(expiring_batches)}", 0, 1)
        
        if len(expired_batches) == 0 and len(expiring_batches) == 0:
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(0, 0, 128)  # Azul escuro
            pdf.cell(0, 10, "Não há medicamentos vencidos ou próximos do vencimento", 0, 1, 'C')
        else:
            # Cabeçalho da tabela - Usar larguras maiores para orientação paisagem
            pdf.ln(5)
            headers = ['Medicamento', 'Lote', 'Validade', 'Status', 'Estoque']
            widths = [110, 40, 35, 45, 25]  # Larguras bem maiores para página paisagem
            
            pdf.table_header(headers, widths)
            
            # SEÇÃO 1: Medicamentos já vencidos
            if expired_batches:
                for i, batch in enumerate(expired_batches):
                    medication = Medication.query.get(batch.medication_id)
                    
                    # Formatar dados
                    if medication:
                        med_nome = abreviar_nome_medicamento(
                            medication.nome, 
                            medication.concentracao, 
                            medication.forma, 
                            55
                        )
                    else:
                        med_nome = 'Medicamento desconhecido'
                    
                    dias_vencido = (today - batch.validade).days
                    status = f"VENCIDO há {dias_vencido} dias"
                    
                    row_data = [
                        med_nome,
                        batch.lote,
                        batch.validade.strftime('%d/%m/%Y') if batch.validade else 'N/A',
                        status,
                        batch.quantidade_atual
                    ]
                    
                    # Usar cor de destaque para vencidos (fundo rosa claro)
                    pdf.set_fill_color(255, 200, 200)  # Rosa claro
                    pdf.set_text_color(139, 0, 0)  # Vermelho escuro
                    pdf.table_row(row_data, widths, fill=True)
            
            # Restaurar configurações padrão para os próximos a vencer
            pdf.set_fill_color(240, 240, 240)  # Cinza claro para linhas alternadas
            
            # SEÇÃO 2: Medicamentos a vencer
            if expiring_batches:
                for i, batch in enumerate(expiring_batches):
                    medication = Medication.query.get(batch.medication_id)
                    
                    # Formatar dados
                    if medication:
                        med_nome = abreviar_nome_medicamento(
                            medication.nome, 
                            medication.concentracao, 
                            medication.forma, 
                            55
                        )
                    else:
                        med_nome = 'Medicamento desconhecido'
                    
                    dias_para_vencer = (batch.validade - today).days
                    status = f"Vence em {dias_para_vencer} dias"
                    
                    row_data = [
                        med_nome,
                        batch.lote,
                        batch.validade.strftime('%d/%m/%Y') if batch.validade else 'N/A',
                        status,
                        batch.quantidade_atual
                    ]
                    
                    # Destacar linhas com validades críticas (7 dias)
                    if dias_para_vencer <= 7:
                        pdf.set_text_color(255, 0, 0)  # Vermelho para validades críticas
                    else:
                        pdf.set_text_color(0, 0, 0)  # Preto para outros
                        
                    pdf.table_row(row_data, widths, fill=(i % 2 == 0))
        
        # Resumo no final do relatório
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 9)
        pdf.set_text_color(128, 128, 128)  # Cinza
        pdf.cell(0, 5, f"* Este relatório mostra medicamentos vencidos e que vencerão nos próximos 30 dias.", 0, 1)
        pdf.cell(0, 5, f"* Medicamentos em vermelho vencerão nos próximos 7 dias e requerem atenção.", 0, 1)
        pdf.cell(0, 5, f"* Medicamentos com fundo rosa já estão vencidos e devem ser descartados conforme protocolo.", 0, 1)
        
        # Gera o PDF em memória
        pdf_output = io.BytesIO()
        pdf_data = pdf.output(dest='S').encode('latin1')
        pdf_output.write(pdf_data)
        pdf_output.seek(0)
        
        # Retorna o PDF como resposta
        response = make_response(pdf_output.getvalue())
        response.headers.set('Content-Type', 'application/pdf')
        response.headers.set('Content-Disposition', 'attachment', filename='medicamentos_vencimento.pdf')
        
        return response
    
    @app.route('/relatorios/exportar/prescricoes')
    @login_required
    def exportar_prescricoes():
        """Exporta o relatório de prescrições em formato PDF"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        # Parâmetros opcionais para filtrar por data
        data_inicio = request.args.get('inicio')
        data_fim = request.args.get('fim')
        
        # Constrói a consulta base
        query = Prescription.query.order_by(Prescription.date.desc())
        
        # Aplica filtros de data se fornecidos
        filtro_aplicado = False
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                query = query.filter(Prescription.date >= data_inicio_dt)
                filtro_aplicado = True
            except:
                data_inicio = None
                
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                data_fim_dt = data_fim_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(Prescription.date <= data_fim_dt)
                filtro_aplicado = True
            except:
                data_fim = None
        
        # Executa a consulta
        prescriptions = query.all()
        
        # Cria o PDF
        pdf = PDF()
        pdf.add_page()
        
        # Título do relatório
        pdf.add_title("Relatório de Prescrições Médicas")
        
        # Subtítulo com período
        subtitulo = "Todas as prescrições"
        if filtro_aplicado:
            if data_inicio and data_fim:
                data_inicio_str = datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')
                data_fim_str = datetime.strptime(data_fim, '%Y-%m-%d').strftime('%d/%m/%Y')
                subtitulo = f"Período: {data_inicio_str} a {data_fim_str}"
            elif data_inicio:
                data_inicio_str = datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')
                subtitulo = f"A partir de {data_inicio_str}"
            elif data_fim:
                data_fim_str = datetime.strptime(data_fim, '%Y-%m-%d').strftime('%d/%m/%Y')
                subtitulo = f"Até {data_fim_str}"
        
        pdf.subtitle(subtitulo)
        
        # Informações gerais
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Total de Prescrições: {len(prescriptions)}", 0, 1)
        
        # Estatísticas
        pendentes = sum(1 for p in prescriptions if p.status == 'pendente')
        dispensadas = sum(1 for p in prescriptions if p.status == 'dispensado')
        canceladas = sum(1 for p in prescriptions if p.status == 'cancelado')
        
        pdf.cell(0, 6, f"Pendentes: {pendentes} | Dispensadas: {dispensadas} | Canceladas: {canceladas}", 0, 1)
        pdf.ln(5)
        
        if len(prescriptions) == 0:
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(0, 0, 128)  # Azul escuro
            pdf.cell(0, 10, "Não há prescrições para o período selecionado", 0, 1, 'C')
        else:
            # Cabeçalho da tabela
            headers = ['ID', 'Data', 'Paciente', 'Médico', 'Status', 'Medicamentos']
            widths = [10, 28, 38, 38, 20, 40]  # Larguras das colunas em mm ajustadas
            
            pdf.table_header(headers, widths)
            
            # Dados da tabela
            for i, prescription in enumerate(prescriptions):
                # Busca informações relacionadas
                patient = Patient.query.get(prescription.patient_id)
                doctor = User.query.get(prescription.doctor_id)
                
                # Formata a lista de medicamentos usando abreviações
                items = PrescriptionItem.query.filter_by(prescription_id=prescription.id).all()
                medicamentos = []
                for item in items:
                    med = Medication.query.get(item.medication_id)
                    if med:
                        # Usar abreviação para nomes de medicamentos
                        nome_abreviado = abreviar_nome_medicamento(med.nome, med.concentracao, None, 25)
                        medicamentos.append(f"{nome_abreviado} ({item.quantidade})")
                    else:
                        medicamentos.append(f"Med. ID {item.medication_id} ({item.quantidade})")
                
                # Limitar número de medicamentos mostrados se for muito extenso
                if len(medicamentos) > 3:
                    medicamentos_str = ", ".join(medicamentos[:2]) + f"... +{len(medicamentos)-2}"
                else:
                    medicamentos_str = ", ".join(medicamentos)
                
                # Cor do status
                status_text = prescription.status.capitalize()
                
                if prescription.status == 'pendente':
                    pdf.set_text_color(255, 140, 0)  # Laranja
                elif prescription.status == 'dispensado':
                    pdf.set_text_color(0, 128, 0)  # Verde
                elif prescription.status == 'cancelado':
                    pdf.set_text_color(255, 0, 0)  # Vermelho
                else:
                    pdf.set_text_color(0, 0, 0)  # Preto
                
                # Preparar dados usando função de abreviação
                patient_nome = abreviar_texto(patient.nome if patient else 'Desconhecido', 38)
                doctor_nome = abreviar_texto(doctor.nome if doctor else 'Desconhecido', 38)
                
                row_data = [
                    prescription.id,
                    prescription.date.strftime('%d/%m/%Y %H:%M') if prescription.date else 'N/A',
                    patient_nome,
                    doctor_nome,
                    status_text,
                    medicamentos_str
                ]
                
                pdf.table_row(row_data, widths, fill=(i % 2 == 0))
                pdf.set_text_color(0, 0, 0)  # Reset color
        
        # Resumo no final do relatório
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 9)
        pdf.set_text_color(128, 128, 128)  # Cinza
        pdf.cell(0, 5, "* Este relatório apresenta as prescrições ordenadas pela data mais recente", 0, 1)
        
        # Gera o PDF em memória
        pdf_output = io.BytesIO()
        pdf_data = pdf.output(dest='S').encode('latin1')
        pdf_output.write(pdf_data)
        pdf_output.seek(0)
        
        # Retorna o PDF como resposta
        response = make_response(pdf_output.getvalue())
        response.headers.set('Content-Type', 'application/pdf')
        response.headers.set('Content-Disposition', 'attachment', filename='prescricoes.pdf')
        
        return response
    
    @app.route('/relatorios/exportar/dispensacoes')
    @login_required
    def exportar_dispensacoes():
        """Exporta o relatório de dispensações de medicamentos em formato PDF"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        # Busca todas as dispensações ordenadas por data (mais recentes primeiro)
        dispensings = MedicationDispensing.query.order_by(MedicationDispensing.date.desc()).all()
        
        # Cria o PDF
        pdf = PDF()
        pdf.add_page()
        
        # Título do relatório
        pdf.add_title("Relatório de Dispensações de Medicamentos")
        pdf.subtitle(f"UBS - {datetime.now().strftime('%d/%m/%Y')}")
        
        # Informações gerais
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Total de Dispensações: {len(dispensings)}", 0, 1)
        
        # Calcula estatísticas
        total_unidades = sum(dispensing.quantidade for dispensing in dispensings)
        
        # Agrupamento por medicamento para estatísticas
        medicamentos_dispensados = {}
        for dispensing in dispensings:
            batch = MedicationBatch.query.get(dispensing.batch_id)
            if batch:
                medication = Medication.query.get(batch.medication_id)
                if medication:
                    med_nome = medication.nome
                    if med_nome not in medicamentos_dispensados:
                        medicamentos_dispensados[med_nome] = 0
                    medicamentos_dispensados[med_nome] += dispensing.quantidade
        
        # Top 3 medicamentos mais dispensados
        top_medicamentos = sorted(medicamentos_dispensados.items(), key=lambda x: x[1], reverse=True)[:3]
        
        pdf.cell(0, 6, f"Total de Unidades Dispensadas: {total_unidades}", 0, 1)
        if top_medicamentos:
            pdf.cell(0, 6, "Medicamentos mais dispensados:", 0, 1)
            for med, qtd in top_medicamentos:
                pdf.cell(0, 6, f"   - {med}: {qtd} unidades", 0, 1)
        
        pdf.ln(5)
        
        if len(dispensings) == 0:
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(0, 0, 128)  # Azul escuro
            pdf.cell(0, 10, "Não há dispensações registradas", 0, 1, 'C')
        else:
            # Cabeçalho da tabela
            headers = ['ID', 'Data', 'Medicamento', 'Lote', 'Qtd', 'Paciente', 'Dispensador']
            widths = [10, 28, 40, 18, 10, 35, 25]  # Larguras das colunas em mm ajustadas
            
            pdf.table_header(headers, widths)
            
            # Dados da tabela
            for i, dispensing in enumerate(dispensings):
                # Busca informações relacionadas
                batch = MedicationBatch.query.get(dispensing.batch_id)
                medication = Medication.query.get(batch.medication_id) if batch else None
                prescription = Prescription.query.get(dispensing.prescription_id)
                patient = Patient.query.get(prescription.patient_id) if prescription else None
                dispenser = User.query.get(dispensing.dispenser_id)
                
                # Prepara os dados da linha usando funções de abreviação
                if medication:
                    med_nome = abreviar_nome_medicamento(
                        medication.nome,
                        medication.concentracao,
                        medication.forma,
                        40
                    )
                else:
                    med_nome = 'Desconhecido'
                
                # Usar funções de abreviação para os nomes
                patient_nome = abreviar_texto(patient.nome if patient else 'Desconhecido', 35)
                dispenser_nome = abreviar_texto(dispenser.nome if dispenser else 'Desconhecido', 25)
                
                row_data = [
                    dispensing.id,
                    dispensing.date.strftime('%d/%m/%Y %H:%M') if dispensing.date else 'N/A',
                    med_nome,
                    batch.lote if batch else 'N/A',
                    dispensing.quantidade,
                    patient_nome,
                    dispenser_nome
                ]
                
                pdf.table_row(row_data, widths, fill=(i % 2 == 0))
                
                # Se houver observações, adiciona abaixo da linha
                if dispensing.observacoes:
                    pdf.set_font('Arial', 'I', 8)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(sum(widths), 5, f"Obs: {dispensing.observacoes}", 1, 1, 'L')
                    pdf.set_font('Arial', '', 10)
                    pdf.set_text_color(0, 0, 0)
        
        # Resumo no final do relatório
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 9)
        pdf.set_text_color(128, 128, 128)  # Cinza
        pdf.cell(0, 5, "* Este relatório apresenta as dispensações ordenadas da mais recente para a mais antiga", 0, 1)
        pdf.cell(0, 5, "* As estatísticas apresentadas podem auxiliar no controle de estoque e planejamento de compras", 0, 1)
        
        # Gera o PDF em memória
        pdf_output = io.BytesIO()
        pdf_data = pdf.output(dest='S').encode('latin1')
        pdf_output.write(pdf_data)
        pdf_output.seek(0)
        
        # Retorna o PDF como resposta
        response = make_response(pdf_output.getvalue())
        response.headers.set('Content-Type', 'application/pdf')
        response.headers.set('Content-Disposition', 'attachment', filename='dispensacoes_medicamentos.pdf')
        
        return response