"""
SISTEMA INTEGRA UBS - Módulo de Gerenciamento de Receituários
"""
import io
import os
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, Response, make_response, jsonify
from flask_login import login_required, current_user
from app import db
from models import ReceituarioModelo, Prescription, Medication, Patient, User, PrescriptionItem
from fpdf import FPDF

def gerar_receituario_com_modelo(prescription_id, modelo_id=None):
    """
    Gera um receituário médico em formato PDF para a prescrição especificada
    utilizando um modelo personalizado
    
    Args:
        prescription_id: ID da prescrição a ser impressa
        modelo_id: ID do modelo a ser utilizado (opcional)
        
    Returns:
        PDF do receituário médico formatado
    """
    # Buscar a prescrição e seus itens
    prescription = Prescription.query.get_or_404(prescription_id)
    items = PrescriptionItem.query.filter_by(prescription_id=prescription_id).all()
    
    # Buscar informações relacionadas
    patient = Patient.query.get(prescription.patient_id)
    doctor = User.query.get(prescription.doctor_id)
    
    # Buscar o modelo solicitado ou o padrão se não for especificado
    if modelo_id:
        modelo = ReceituarioModelo.query.get(modelo_id)
        if not modelo or not modelo.ativo:
            modelo = ReceituarioModelo.query.filter_by(padrao=True, ativo=True).first()
    else:
        modelo = ReceituarioModelo.query.filter_by(padrao=True, ativo=True).first()
    
    # Se não encontrar nenhum modelo, usar configurações padrão
    if not modelo:
        modelo = ReceituarioModelo(
            nome="Modelo Padrão",
            cabecalho="RECEITUÁRIO MÉDICO\nSISTEMA INTEGRA UBS",
            cor_primaria="#0066cc",
            fonte_titulo="Arial",
            tamanho_titulo=16,
            fonte_corpo="Arial",
            tamanho_corpo=11
        )
    
    # Criar o PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Aplicar configurações do modelo
    pdf.set_font(modelo.fonte_titulo, 'B', modelo.tamanho_titulo)
    
    # Converter cor hex para RGB
    cor_rgb = hex_to_rgb(modelo.cor_primaria)
    pdf.set_text_color(cor_rgb[0], cor_rgb[1], cor_rgb[2])
    
    # Cabeçalho do receituário (com quebras de linha)
    cabecalho_linhas = modelo.cabecalho.split("\n")
    for linha in cabecalho_linhas:
        pdf.cell(0, 10, linha, 0, 1, 'C')
    
    # Linha separadora
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Informações do paciente
    pdf.set_font(modelo.fonte_titulo, 'B', modelo.tamanho_titulo - 4)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "IDENTIFICAÇÃO DO PACIENTE", 0, 1, 'L')
    
    pdf.set_font(modelo.fonte_corpo, '', modelo.tamanho_corpo)
    pdf.cell(40, 7, "Nome:", 0, 0, 'L')
    pdf.set_font(modelo.fonte_corpo, 'B', modelo.tamanho_corpo)
    pdf.cell(0, 7, patient.nome if patient else "NÃO IDENTIFICADO", 0, 1, 'L')
    
    pdf.set_font(modelo.fonte_corpo, '', modelo.tamanho_corpo)
    
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
    pdf.set_font(modelo.fonte_titulo, 'B', modelo.tamanho_titulo - 4)
    pdf.cell(0, 8, "MEDICAMENTOS PRESCRITOS", 0, 1, 'L')
    
    # Lista de medicamentos
    pdf.set_font(modelo.fonte_corpo, '', modelo.tamanho_corpo)
    
    if not items:
        pdf.cell(0, 10, "Nenhum medicamento prescrito", 0, 1, 'C')
    else:
        for i, item in enumerate(items):
            medication = Medication.query.get(item.medication_id)
            if not medication:
                continue
                
            # Número do item
            pdf.set_font(modelo.fonte_corpo, 'B', modelo.tamanho_corpo)
            pdf.cell(0, 10, f"{i+1}) {medication.nome}", 0, 1, 'L')
            
            # Concentração e forma
            if medication.concentracao or medication.forma:
                info = []
                if medication.concentracao:
                    info.append(medication.concentracao)
                if medication.forma:
                    info.append(medication.forma)
                
                pdf.set_font(modelo.fonte_corpo, 'I', modelo.tamanho_corpo - 1)
                pdf.cell(0, 6, ", ".join(info), 0, 1, 'L')
            
            # Quantidade e instruções de uso
            pdf.set_font(modelo.fonte_corpo, '', modelo.tamanho_corpo)
            pdf.cell(0, 8, f"Quantidade: {item.quantidade}", 0, 1, 'L')
            
            # Instruções com estilo diferente
            if item.instrucoes:
                pdf.set_font(modelo.fonte_corpo, '', modelo.tamanho_corpo - 1)
                pdf.multi_cell(0, 6, f"Instruções: {item.instrucoes}", 0, 'L')
            
            pdf.ln(3)  # Espaço entre medicamentos
    
    # Observações da prescrição
    if prescription.observacoes:
        pdf.ln(5)
        pdf.set_font(modelo.fonte_corpo, 'B', modelo.tamanho_corpo)
        pdf.cell(0, 8, "OBSERVAÇÕES:", 0, 1, 'L')
        pdf.set_font(modelo.fonte_corpo, '', modelo.tamanho_corpo - 1)
        pdf.multi_cell(0, 6, prescription.observacoes, 0, 'L')
    
    # Rodapé com assinatura do médico
    pdf.ln(20)
    pdf.line(65, pdf.get_y(), 145, pdf.get_y())
    pdf.set_font(modelo.fonte_corpo, 'B', modelo.tamanho_corpo - 1)
    pdf.ln(3)
    pdf.cell(0, 6, doctor.nome if doctor else "MÉDICO RESPONSÁVEL", 0, 1, 'C')
    
    if doctor:
        pdf.set_font(modelo.fonte_corpo, '', modelo.tamanho_corpo - 1)
        role_text = "Médico(a)" if doctor.role == 'medico' else doctor.role.capitalize()
        pdf.cell(0, 6, f"{role_text} - Sistema Integra UBS", 0, 1, 'C')
    
    # Rodapé personalizado do modelo
    if modelo.rodape:
        pdf.ln(10)
        pdf.set_font(modelo.fonte_corpo, 'I', modelo.tamanho_corpo - 2)
        pdf.set_text_color(128, 128, 128)  # Cinza
        pdf.multi_cell(0, 5, modelo.rodape, 0, 'C')
    
    # Gerar o PDF e retornar
    pdf_output = io.BytesIO()
    pdf_data = pdf.output(dest='S').encode('latin1')
    pdf_output.write(pdf_data)
    pdf_output.seek(0)
    
    return pdf_output

def hex_to_rgb(hex_color):
    """Converte cor hexadecimal para RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def register_receituario_routes(app):
    """Registra as rotas relacionadas a modelos de receituário"""
    
    @app.route('/prescricao/receituario/<int:prescription_id>')
    @login_required
    def receituario_medico(prescription_id):
        """Gera um receituário médico em PDF para a prescrição"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        # Verificar se foi solicitado um modelo específico
        modelo_id = request.args.get('modelo_id', type=int)
        
        try:
            # Gerar o PDF do receituário com o modelo solicitado
            pdf_output = gerar_receituario_com_modelo(prescription_id, modelo_id)
            
            # Buscar informações para o nome do arquivo
            prescription = Prescription.query.get_or_404(prescription_id)
            patient = Patient.query.get(prescription.patient_id)
            
            # Nome do arquivo: receituario_NOME-DO-PACIENTE_DATA.pdf
            data_formatada = prescription.date.strftime('%d-%m-%Y')
            nome_paciente = "".join(c for c in patient.nome if c.isalnum() or c.isspace()).replace(" ", "-") if patient else "paciente"
            
            filename = f"receituario_{nome_paciente}_{data_formatada}.pdf"
            
            # Retorna o PDF como resposta para download
            response = make_response(pdf_output.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
        except Exception as e:
            flash(f'Erro ao gerar receituário: {str(e)}', 'error')
            return redirect(url_for('ver_prescricao', id=prescription_id))
    
    @app.route('/receituarios')
    @login_required
    def receituarios():
        """Página de gerenciamento de modelos de receituário"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        modelos = ReceituarioModelo.query.all()
        return render_template('receituarios.html', modelos=modelos)
    
    @app.route('/receituario/novo', methods=['GET', 'POST'])
    @login_required
    def novo_receituario():
        """Criar novo modelo de receituário"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            # Obter dados do formulário
            nome = request.form.get('nome')
            descricao = request.form.get('descricao')
            cabecalho = request.form.get('cabecalho')
            rodape = request.form.get('rodape')
            cor_primaria = request.form.get('cor_primaria')
            fonte_titulo = request.form.get('fonte_titulo')
            tamanho_titulo = request.form.get('tamanho_titulo', type=int)
            fonte_corpo = request.form.get('fonte_corpo')
            tamanho_corpo = request.form.get('tamanho_corpo', type=int)
            padrao = request.form.get('padrao') == 'on'
            
            # Validações
            if not nome or not cabecalho:
                flash('Por favor, preencha os campos obrigatórios (nome e cabeçalho).', 'error')
                return render_template('receituario_form.html')
            
            # Se este modelo for definido como padrão, remover o status padrão dos outros
            if padrao:
                outros_padrao = ReceituarioModelo.query.filter_by(padrao=True).all()
                for outro in outros_padrao:
                    outro.padrao = False
                    db.session.add(outro)
            
            # Criar novo modelo
            modelo = ReceituarioModelo(
                nome=nome,
                descricao=descricao,
                cabecalho=cabecalho,
                rodape=rodape,
                cor_primaria=cor_primaria or '#0066cc',
                fonte_titulo=fonte_titulo or 'Arial',
                tamanho_titulo=tamanho_titulo or 16,
                fonte_corpo=fonte_corpo or 'Arial',
                tamanho_corpo=tamanho_corpo or 11,
                ativo=True,
                padrao=padrao,
                criado_por=current_user.id
            )
            
            db.session.add(modelo)
            db.session.commit()
            
            flash('Modelo de receituário criado com sucesso!', 'success')
            return redirect(url_for('receituarios'))
        
        # GET request - mostrar formulário
        return render_template('receituario_form.html')
    
    @app.route('/receituario/editar/<int:id>', methods=['GET', 'POST'])
    @login_required
    def editar_receituario(id):
        """Editar modelo de receituário existente"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        modelo = ReceituarioModelo.query.get_or_404(id)
        
        if request.method == 'POST':
            # Obter dados do formulário
            nome = request.form.get('nome')
            descricao = request.form.get('descricao')
            cabecalho = request.form.get('cabecalho')
            rodape = request.form.get('rodape')
            cor_primaria = request.form.get('cor_primaria')
            fonte_titulo = request.form.get('fonte_titulo')
            tamanho_titulo = request.form.get('tamanho_titulo', type=int)
            fonte_corpo = request.form.get('fonte_corpo')
            tamanho_corpo = request.form.get('tamanho_corpo', type=int)
            ativo = request.form.get('ativo') == 'on'
            padrao = request.form.get('padrao') == 'on'
            
            # Validações
            if not nome or not cabecalho:
                flash('Por favor, preencha os campos obrigatórios (nome e cabeçalho).', 'error')
                return render_template('receituario_form.html', modelo=modelo)
            
            # Se este modelo for definido como padrão, remover o status padrão dos outros
            if padrao:
                outros_padrao = ReceituarioModelo.query.filter_by(padrao=True).all()
                for outro in outros_padrao:
                    if outro.id != modelo.id:
                        outro.padrao = False
                        db.session.add(outro)
            
            # Atualizar dados do modelo
            modelo.nome = nome
            modelo.descricao = descricao
            modelo.cabecalho = cabecalho
            modelo.rodape = rodape
            modelo.cor_primaria = cor_primaria or '#0066cc'
            modelo.fonte_titulo = fonte_titulo or 'Arial'
            modelo.tamanho_titulo = tamanho_titulo or 16
            modelo.fonte_corpo = fonte_corpo or 'Arial'
            modelo.tamanho_corpo = tamanho_corpo or 11
            modelo.ativo = ativo
            modelo.padrao = padrao
            
            db.session.add(modelo)
            db.session.commit()
            
            flash('Modelo de receituário atualizado com sucesso!', 'success')
            return redirect(url_for('receituarios'))
        
        # GET request - mostrar formulário preenchido
        return render_template('receituario_form.html', modelo=modelo)
    
    @app.route('/receituario/excluir/<int:id>')
    @login_required
    def excluir_receituario(id):
        """Excluir modelo de receituário"""
        if current_user.role not in ['admin']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        modelo = ReceituarioModelo.query.get_or_404(id)
        
        # Não permitir excluir o modelo padrão
        if modelo.padrao:
            flash('Não é possível excluir o modelo padrão. Defina outro modelo como padrão primeiro.', 'error')
            return redirect(url_for('receituarios'))
        
        db.session.delete(modelo)
        db.session.commit()
        
        flash('Modelo de receituário excluído com sucesso!', 'success')
        return redirect(url_for('receituarios'))
    
    @app.route('/prescricao/selecionar_modelo/<int:prescription_id>')
    @login_required
    def selecionar_modelo_receituario(prescription_id):
        """Página para selecionar modelo de receituário"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        modelos = ReceituarioModelo.query.filter_by(ativo=True).all()
        prescription = Prescription.query.get_or_404(prescription_id)
        
        return render_template(
            'selecionar_modelo.html', 
            modelos=modelos, 
            prescription=prescription
        )