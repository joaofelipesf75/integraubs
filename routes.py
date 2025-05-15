"""
SISTEMA INTEGRA UBS - Rotas da aplicação
"""
import json
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from models import (
    User, Patient, MedicalRecord, Medication, MedicationBatch,
    Prescription, PrescriptionItem, MedicationDispensing, Message, ChatMensagem
)
from importador import get_medications_data, import_medications

def register_routes(app):
    """Registra todas as rotas da aplicação"""
    
    @app.route('/')
    def index():
        """Rota inicial que detecta ambiente Replit e serve página estática ou redireciona"""
        import os
        if os.environ.get("REPL_SLUG") is not None and os.environ.get("REPL_OWNER") is not None:
            # Ambiente Replit, usar página estática
            return redirect(url_for('serve_static_preview'))
        else:
            # Ambiente normal, redirecionar para login
            return redirect(url_for('login'))
        
    @app.route('/debug')
    def debug():
        """Versão extremamente simplificada para depuração"""
        # Contagens para o dashboard
        patients_count = Patient.query.count() 
        consultas_realizadas = 15
        consultas_mes = 42
        medicamentos_vencidos = 3
        
        # Dados para atividades recentes
        atividades_recentes = [
            {
                "icone": "user",
                "cor": "blue",
                "texto": "Maria Silva foi registrada como nova paciente",
                "tempo": "Hoje, 10:30"
            },
            {
                "icone": "stethoscope",
                "cor": "green",
                "texto": "Dr. João concluiu 5 consultas hoje",
                "tempo": "Hoje, 09:45"
            },
            {
                "icone": "pills",
                "cor": "red",
                "texto": "Estoque baixo de Dipirona (5 unidades restantes)",
                "tempo": "Ontem, 16:20"
            }
        ]
        
        return render_template(
            'debug.html',
            patients_count=patients_count,
            consultas_realizadas=consultas_realizadas,
            consultas_mes=consultas_mes,
            medicamentos_vencidos=medicamentos_vencidos,
            atividades_recentes=atividades_recentes
        )

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Página de login"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Por favor, preencha todos os campos', 'error')
                return render_template('login.html')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                if user.status != 'ativo':
                    flash('Sua conta está desativada. Entre em contato com o administrador.', 'error')
                    return render_template('login.html')
                
                login_user(user)
                flash(f'Bem-vindo, {user.nome}!', 'success')
                
                # Redirecionar para a página solicitada originalmente (se houver)
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('dashboard')
                return redirect(next_page)
            else:
                flash('Usuário ou senha inválidos', 'error')
        
        return render_template('login.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Dashboard principal"""
        from datetime import datetime, timedelta
        import calendar
        
        # Obter contagens reais do banco de dados
        patients_count = Patient.query.count()
        
        # Consultas realizadas (total)
        consultas_realizadas = MedicalRecord.query.count()
        
        # Consultas do mês atual
        hoje = datetime.now()
        primeiro_dia_mes = datetime(hoje.year, hoje.month, 1)
        _, ultimo_dia = calendar.monthrange(hoje.year, hoje.month)
        ultimo_dia_mes = datetime(hoje.year, hoje.month, ultimo_dia, 23, 59, 59)
        
        consultas_mes = MedicalRecord.query.filter(
            MedicalRecord.date >= primeiro_dia_mes,
            MedicalRecord.date <= ultimo_dia_mes
        ).count()
        
        # Medicamentos vencidos
        hoje = datetime.now().date()
        medicamentos_vencidos = MedicationBatch.query.filter(
            MedicationBatch.validade <= hoje,
            MedicationBatch.quantidade_atual > 0
        ).count()
        
        # Buscar atividades recentes reais
        # Últimas consultas (até 2)
        consultas_recentes = MedicalRecord.query.order_by(MedicalRecord.date.desc()).limit(2).all()
        
        # Medicamentos com estoque baixo para o resumo do sistema
        # Primeiro, vamos buscar todos os lotes com estoque baixo (30% ou menos da quantidade inicial)
        medicamentos_baixo_estoque_resumo = db.session.query(
            Medication.nome,
            MedicationBatch.quantidade_atual,
            MedicationBatch.quantidade_inicial,
            db.func.cast(MedicationBatch.quantidade_atual * 100 / MedicationBatch.quantidade_inicial, db.Integer).label('porcentagem')
        ).join(
            MedicationBatch, Medication.id == MedicationBatch.medication_id
        ).filter(
            MedicationBatch.quantidade_atual > 0,
            db.func.cast(MedicationBatch.quantidade_atual * 100 / MedicationBatch.quantidade_inicial, db.Integer) <= 30
        ).order_by('porcentagem').limit(3).all()
        
        # Se não encontramos medicamentos com estoque muito baixo, então buscamos os que tem menos de 50%
        if len(medicamentos_baixo_estoque_resumo) == 0:
            medicamentos_baixo_estoque_resumo = db.session.query(
                Medication.nome,
                MedicationBatch.quantidade_atual,
                MedicationBatch.quantidade_inicial,
                db.func.cast(MedicationBatch.quantidade_atual * 100 / MedicationBatch.quantidade_inicial, db.Integer).label('porcentagem')
            ).join(
                MedicationBatch, Medication.id == MedicationBatch.medication_id
            ).filter(
                MedicationBatch.quantidade_atual > 0,
                db.func.cast(MedicationBatch.quantidade_atual * 100 / MedicationBatch.quantidade_inicial, db.Integer) <= 50
            ).order_by('porcentagem').limit(3).all()
        
        # Usar a porcentagem já calculada na consulta SQL
        medicamentos_resumo = []
        for med in medicamentos_baixo_estoque_resumo:
            # Se temos o campo 'porcentagem' da consulta, usamos ele, senão calculamos
            if hasattr(med, 'porcentagem'):
                porcentagem = med.porcentagem
            else:
                porcentagem = int((med.quantidade_atual / med.quantidade_inicial) * 100)
                
            # Definir cor baseada na porcentagem
            if porcentagem < 30:
                cor = 'danger'  # Vermelho para estoque crítico
            else:
                cor = 'warning'  # Amarelo para estoque baixo
            
            # Adicionar o medicamento à lista de exibição
            medicamentos_resumo.append({
                'nome': med.nome.split()[0],  # Pegar apenas o primeiro nome
                'porcentagem': porcentagem,
                'cor': cor
            })
        
        # Medicamentos com estoque baixo para atividades recentes (máximo 1)
        medicamentos_baixo_estoque = MedicationBatch.query.filter(
            MedicationBatch.quantidade_atual <= 10,
            MedicationBatch.quantidade_atual > 0
        ).join(Medication).limit(1).all()
        
        # Criar lista de atividades reais baseada nos dados
        atividades_recentes = []
        
        # Adicionar consultas recentes
        for consulta in consultas_recentes:
            paciente = Patient.query.get(consulta.patient_id)
            medico = User.query.get(consulta.doctor_id)
            if paciente and medico:
                atividades_recentes.append({
                    "icone": "stethoscope",
                    "cor": "success",
                    "texto": f"Consulta de {paciente.nome} com {medico.nome}",
                    "tempo": consulta.date.strftime('%d/%m/%Y %H:%M')
                })
        
        # Adicionar medicamentos com estoque baixo
        for batch in medicamentos_baixo_estoque:
            medicamento = Medication.query.get(batch.medication_id)
            if medicamento:
                atividades_recentes.append({
                    "icone": "pills",
                    "cor": "danger",
                    "texto": f"Estoque baixo de {medicamento.nome} ({batch.quantidade_atual} unidades)",
                    "tempo": "Estoque crítico"
                })
        
        # Se não houver atividades recentes reais, adicionar mensagem informativa
        if len(atividades_recentes) == 0:
            atividades_recentes.append({
                "icone": "info-circle",
                "cor": "info",
                "texto": "Não há atividades recentes registradas no sistema",
                "tempo": "Sistema iniciado"
            })
        
        return render_template(
            'dashboard.html',
            patients_count=patients_count,
            consultas_realizadas=consultas_realizadas,
            consultas_mes=consultas_mes,
            medicamentos_vencidos=medicamentos_vencidos,
            atividades_recentes=atividades_recentes,
            medicamentos_resumo=medicamentos_resumo
        )
        
    @app.route('/preview')
    def preview():
        """Versão de preview do dashboard sem autenticação (apenas para desenvolvimento)"""
        # Contagens para o dashboard
        patients_count = Patient.query.count() 
        consultas_realizadas = 15
        consultas_mes = 42
        medicamentos_vencidos = 3
        
        # Dados para atividades recentes
        atividades_recentes = [
            {
                "icone": "user",
                "cor": "primary",
                "texto": "Maria Silva foi registrada como nova paciente",
                "tempo": "Hoje, 10:30"
            },
            {
                "icone": "stethoscope",
                "cor": "success",
                "texto": "Dr. João concluiu 5 consultas hoje",
                "tempo": "Hoje, 09:45"
            },
            {
                "icone": "pills",
                "cor": "danger",
                "texto": "Estoque baixo de Dipirona (5 unidades restantes)",
                "tempo": "Ontem, 16:20"
            }
        ]
        
        return render_template(
            'preview.html',
            patients_count=patients_count,
            consultas_realizadas=consultas_realizadas,
            consultas_mes=consultas_mes,
            medicamentos_vencidos=medicamentos_vencidos,
            atividades_recentes=atividades_recentes
        )
        
    @app.route('/replit-preview')
    def replit_preview():
        """Rota específica para o preview do Replit - extremamente simples e estática"""
        return send_from_directory('static', 'preview.html')
    
    @app.route('/simple')
    def simple_preview():
        """Versão ultra-simplificada do dashboard sem autenticação (apenas para desenvolvimento)"""
        # Contagens para o dashboard
        patients_count = Patient.query.count() 
        consultas_realizadas = 15
        consultas_mes = 42
        medicamentos_vencidos = 3
        
        # Dados para atividades recentes
        atividades_recentes = [
            {
                "icone": "user",
                "cor": "blue",
                "texto": "Maria Silva foi registrada como nova paciente",
                "tempo": "Hoje, 10:30"
            },
            {
                "icone": "stethoscope",
                "cor": "green",
                "texto": "Dr. João concluiu 5 consultas hoje",
                "tempo": "Hoje, 09:45"
            },
            {
                "icone": "pills",
                "cor": "red",
                "texto": "Estoque baixo de Dipirona (5 unidades restantes)",
                "tempo": "Ontem, 16:20"
            }
        ]
        
        return render_template(
            'simple_preview.html',
            patients_count=patients_count,
            consultas_realizadas=consultas_realizadas,
            consultas_mes=consultas_mes,
            medicamentos_vencidos=medicamentos_vencidos,
            atividades_recentes=atividades_recentes
        )

    @app.route('/logout')
    @login_required
    def logout():
        """Encerrar sessão"""
        logout_user()
        flash('Você saiu do sistema.', 'info')
        return redirect(url_for('login'))

    @app.route('/usuarios')
    @login_required
    def usuarios():
        """Página de usuários (apenas admin)"""
        if current_user.role != 'admin':
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        # Diagnóstico de detalhes do modelo User
        app.logger.info("Diagnóstico de modelo User")
        for role in ['admin', 'medico', 'enfermeiro', 'farmaceutico', 'recepcionista']:
            test_user = User.query.filter_by(role=role).first()
            if test_user:
                app.logger.info(f"Usuário role={role}, id={test_user.id}, atributos: {[attr for attr in dir(test_user) if not attr.startswith('_')]}")
        
        users = User.query.all()
        return render_template('users.html', users=users)

    @app.route('/usuario/novo', methods=['POST'])
    @login_required
    def novo_usuario():
        """Adicionar novo usuário (apenas admin)"""
        if current_user.role != 'admin':
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        app.logger.info("Iniciando criação de novo usuário")
        
        username = request.form.get('username')
        nome = request.form.get('nome')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        app.logger.info(f"Dados recebidos: username={username}, nome={nome}, email={email}, role={role}")
        
        # Validações
        if not username or not nome or not password or not role:
            flash('Por favor, preencha todos os campos obrigatórios', 'error')
            return redirect(url_for('usuarios'))
        
        # Verificar se o usuário já existe
        if User.query.filter_by(username=username).first():
            flash('Este nome de usuário já está em uso', 'error')
            return redirect(url_for('usuarios'))
        
        if email and User.query.filter_by(email=email).first():
            flash('Este email já está em uso', 'error')
            return redirect(url_for('usuarios'))
        
        # Criar novo usuário
        try:
            app.logger.info(f"Criando usuário: username={username}, nome={nome}, role={role}")
            
            # Ajusta o email para NULL se vazio (evita erro de unicidade)
            if email == '':
                email = None
                
            user = User(
                username=username,
                nome=nome,
                email=email,
                role=role,
                status='ativo'
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            app.logger.info(f"Usuário {username} criado com sucesso, ID: {user.id}")
            flash(f'Usuário {username} criado com sucesso', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Erro ao criar usuário: {str(e)}")
            flash(f'Erro ao criar usuário: {str(e)}', 'error')
        return redirect(url_for('usuarios'))

    @app.route('/usuario/excluir/<int:id>')
    @login_required
    def excluir_usuario(id):
        """Excluir usuário existente (apenas admin)"""
        if current_user.role != 'admin':
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        # Não permitir exclusão do próprio usuário
        if id == current_user.id:
            flash('Você não pode excluir seu próprio usuário.', 'error')
            return redirect(url_for('usuarios'))
        
        try:
            user = User.query.get_or_404(id)
            app.logger.info(f"Tentando excluir usuário ID: {id}, username: {user.username}")
            
            # Verificar se é o usuário admin original
            if user.username == 'admin':
                flash('O usuário administrador principal não pode ser excluído.', 'error')
                return redirect(url_for('usuarios'))
            
            username = user.username  # Guardar para a mensagem
            
            # Excluir todas as associações do usuário para evitar erros de integridade
            
            # 1. Mensagens de chat
            ChatMensagem.query.filter_by(usuario_id=id).delete()
            
            # 2. Mensagens do sistema (enviadas e recebidas)
            Message.query.filter_by(sender_id=id).delete()
            Message.query.filter_by(recipient_id=id).delete()
            
            # 3. Dispensações de medicamentos
            dispensacoes = MedicationDispensing.query.filter_by(dispenser_id=id).all()
            for dispensacao in dispensacoes:
                db.session.delete(dispensacao)
            
            # 4. Prescrições médicas
            prescricoes = Prescription.query.filter_by(doctor_id=id).all()
            for prescricao in prescricoes:
                # Excluir itens da prescrição
                PrescriptionItem.query.filter_by(prescription_id=prescricao.id).delete()
                # Excluir a prescrição
                db.session.delete(prescricao)
                
            # 5. Prontuários médicos
            MedicalRecord.query.filter_by(doctor_id=id).delete()
            
            # 6. Finalmente excluir o usuário
            db.session.delete(user)
            db.session.commit()
            
            flash(f'Usuário {username} excluído com sucesso', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Erro ao excluir usuário: {str(e)}")
            flash(f'Erro ao excluir usuário: {str(e)}', 'error')
        
        return redirect(url_for('usuarios'))
    
    @app.route('/usuario/editar/<int:id>', methods=['POST'])
    @login_required
    def editar_usuario(id):
        """Editar usuário existente (apenas admin)"""
        if current_user.role != 'admin':
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        app.logger.info(f"Tentando editar usuário ID: {id}")
        app.logger.info(f"Formulário recebido: {request.form}")
        
        user = User.query.get_or_404(id)
        app.logger.info(f"Usuário encontrado: {user.username}, {user.nome}, {user.role}")
    
        nome = request.form.get('nome')
        email = request.form.get('email')
        role = request.form.get('role')
        status = request.form.get('status')
        password = request.form.get('password')
        
        app.logger.info(f"Dados para atualização: nome={nome}, email={email}, role={role}, status={status}")
        
        # Validações
        if not nome or not role or not status:
            flash('Por favor, preencha todos os campos obrigatórios', 'error')
            return redirect(url_for('usuarios'))
        
        # Verificar email único
        if email and email != user.email and User.query.filter_by(email=email).first():
            flash('Este email já está em uso', 'error')
            return redirect(url_for('usuarios'))
        
        # Atualizar dados do usuário
        try:
            # Ajusta o email para NULL se vazio (evita erro de unicidade)
            if email == '':
                email = None
                
            app.logger.info(f"Atualizando usuário ID {id}: nome={nome}, email={email}, role={role}, status={status}")
            
            user.nome = nome
            user.email = email
            user.role = role
            user.status = status
            
            # Atualizar senha se fornecida
            if password:
                user.set_password(password)
                app.logger.info(f"Senha atualizada para o usuário ID {id}")
            
            db.session.commit()
            
            app.logger.info(f"Usuário {user.username} (ID: {id}) atualizado com sucesso")
            flash(f'Usuário {user.username} atualizado com sucesso', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Erro ao atualizar usuário ID {id}: {str(e)}")
            flash(f'Erro ao atualizar usuário: {str(e)}', 'error')
        return redirect(url_for('usuarios'))

    @app.route('/pacientes')
    @login_required
    def pacientes():
        """Página de pacientes"""
        if current_user.role not in ['admin', 'medico', 'enfermeiro', 'farmaceutico', 'recepcionista']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        patients = Patient.query.all()
        return render_template('pacientes.html', patients=patients)

    @app.route('/paciente/novo', methods=['POST'])
    @login_required
    def novo_paciente():
        """Adicionar novo paciente"""
        if current_user.role not in ['admin', 'medico', 'enfermeiro', 'farmaceutico', 'recepcionista']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        data_nascimento = request.form.get('data_nascimento')
        sexo = request.form.get('sexo')
        telefone = request.form.get('telefone')
        endereco = request.form.get('endereco')
        sus_card = request.form.get('sus_card')
        
        # Validações
        if not nome:
            flash('O nome do paciente é obrigatório', 'error')
            return redirect(url_for('pacientes'))
        
        # Verificar CPF único
        if cpf and Patient.query.filter_by(cpf=cpf).first():
            flash('Este CPF já está cadastrado', 'error')
            return redirect(url_for('pacientes'))
        
        # Verificar cartão SUS único
        if sus_card and Patient.query.filter_by(sus_card=sus_card).first():
            flash('Este número do cartão SUS já está cadastrado', 'error')
            return redirect(url_for('pacientes'))
        
        # Converter data_nascimento
        date_obj = None
        if data_nascimento:
            try:
                date_obj = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de nascimento inválida. Use o formato AAAA-MM-DD', 'error')
                return redirect(url_for('pacientes'))
        
        # Criar novo paciente
        patient = Patient(
            nome=nome,
            cpf=cpf,
            data_nascimento=date_obj,
            sexo=sexo,
            telefone=telefone,
            endereco=endereco,
            sus_card=sus_card
        )
        
        db.session.add(patient)
        db.session.commit()
        
        flash(f'Paciente {nome} cadastrado com sucesso', 'success')
        return redirect(url_for('pacientes'))

    @app.route('/paciente/editar/<int:id>', methods=['POST'])
    @login_required
    def editar_paciente(id):
        """Editar paciente existente"""
        if current_user.role not in ['admin', 'medico', 'enfermeiro', 'farmaceutico', 'recepcionista']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        patient = Patient.query.get_or_404(id)
        
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        data_nascimento = request.form.get('data_nascimento')
        sexo = request.form.get('sexo')
        telefone = request.form.get('telefone')
        endereco = request.form.get('endereco')
        sus_card = request.form.get('sus_card')
        
        # Validações
        if not nome:
            flash('O nome do paciente é obrigatório', 'error')
            return redirect(url_for('pacientes'))
        
        # Verificar CPF único
        if cpf and cpf != patient.cpf and Patient.query.filter_by(cpf=cpf).first():
            flash('Este CPF já está cadastrado', 'error')
            return redirect(url_for('pacientes'))
        
        # Verificar cartão SUS único
        if sus_card and sus_card != patient.sus_card and Patient.query.filter_by(sus_card=sus_card).first():
            flash('Este número do cartão SUS já está cadastrado', 'error')
            return redirect(url_for('pacientes'))
            
        # Converter data_nascimento
        date_obj = None
        if data_nascimento:
            try:
                date_obj = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de data inválido', 'error')
                return redirect(url_for('pacientes'))
        
        # Atualizar dados do paciente
        patient.nome = nome
        patient.cpf = cpf
        patient.data_nascimento = date_obj
        patient.sexo = sexo
        patient.telefone = telefone
        patient.endereco = endereco
        patient.sus_card = sus_card
        
        try:
            db.session.commit()
            flash(f'Paciente {nome} atualizado com sucesso', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Erro ao atualizar paciente: {str(e)}")
            flash(f'Erro ao atualizar paciente: {str(e)}', 'error')
        
        return redirect(url_for('pacientes'))
            
    @app.route('/paciente/excluir/<int:id>', methods=['POST'])
    @login_required
    def excluir_paciente(id):
        """Excluir paciente existente"""
        # Verificar permissões - apenas admin, médicos e enfermeiros podem excluir pacientes
        if current_user.role not in ['admin', 'medico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        try:
            patient = Patient.query.get_or_404(id)
            nome_paciente = patient.nome
            
            # 1. Excluir todas as prescrições relacionadas ao paciente
            prescricoes = Prescription.query.filter_by(patient_id=id).all()
            for prescricao in prescricoes:
                # Excluir dispensações relacionadas
                MedicationDispensing.query.filter_by(prescription_id=prescricao.id).delete()
                
                # Excluir itens da prescrição
                PrescriptionItem.query.filter_by(prescription_id=prescricao.id).delete()
                
                # Excluir a prescrição
                db.session.delete(prescricao)
            
            # 2. Excluir todos os registros médicos (prontuário)
            MedicalRecord.query.filter_by(patient_id=id).delete()
            
            # 3. Finalmente excluir o paciente
            db.session.delete(patient)
            db.session.commit()
            
            flash(f'Paciente {nome_paciente} excluído com sucesso', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Erro ao excluir paciente: {str(e)}")
            flash(f'Erro ao excluir paciente: {str(e)}', 'error')
        
        return redirect(url_for('pacientes'))
        
        # Converter data_nascimento
        date_obj = None
        if data_nascimento:
            try:
                date_obj = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de nascimento inválida. Use o formato AAAA-MM-DD', 'error')
                return redirect(url_for('pacientes'))
        
        # Atualizar dados do paciente
        patient.nome = nome
        patient.cpf = cpf
        patient.data_nascimento = date_obj
        patient.sexo = sexo
        patient.telefone = telefone
        patient.endereco = endereco
        patient.sus_card = sus_card
        
        db.session.commit()
        
        flash(f'Paciente {nome} atualizado com sucesso', 'success')
        return redirect(url_for('pacientes'))

    @app.route('/prontuario/<int:patient_id>')
    @login_required
    def prontuario(patient_id):
        """Visualizar prontuário de paciente"""
        if current_user.role not in ['admin', 'medico', 'enfermeiro', 'farmaceutico']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        patient = Patient.query.get_or_404(patient_id)
        records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.date.desc()).all()
        prescriptions = Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.date.desc()).all()
        
        return render_template('prontuario.html', patient=patient, records=records, prescriptions=prescriptions)

    @app.route('/prontuario/novo/<int:patient_id>', methods=['POST'])
    @login_required
    def novo_registro_prontuario(patient_id):
        """Adicionar novo registro ao prontuário"""
        if current_user.role not in ['admin', 'medico', 'enfermeiro', 'farmaceutico']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        patient = Patient.query.get_or_404(patient_id)
        
        complaint = request.form.get('complaint')
        diagnosis = request.form.get('diagnosis')
        treatment = request.form.get('treatment')
        observations = request.form.get('observations')
        
        # Criar novo registro
        record = MedicalRecord(
            patient_id=patient_id,
            doctor_id=current_user.id,
            complaint=complaint,
            diagnosis=diagnosis,
            treatment=treatment,
            observations=observations
        )
        
        db.session.add(record)
        db.session.commit()
        
        flash('Registro adicionado ao prontuário com sucesso', 'success')
        return redirect(url_for('prontuario', patient_id=patient_id))

    @app.route('/medicamentos')
    @login_required
    def medicamentos():
        """Página de estoque de medicamentos"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        try:
            # Carregar todos os medicamentos
            medications = Medication.query.all()
            
            # Carregar todos os lotes de uma vez (mais eficiente que várias consultas)
            from models import MedicationBatch
            all_batches = MedicationBatch.query.all()
            
            # Agrupar lotes por medicamento para acesso rápido
            batches_by_med = {}
            for batch in all_batches:
                if batch.medication_id not in batches_by_med:
                    batches_by_med[batch.medication_id] = []
                batches_by_med[batch.medication_id].append(batch)
            
            # Pré-processar dados de estoque e validade para cada medicamento
            medication_data = {}
            for med in medications:
                med_batches = batches_by_med.get(med.id, [])
                medication_data[med.id] = {
                    'stock': med.stock_total(preloaded_batches=med_batches),
                    'expiry': med.next_expiry_date(preloaded_batches=med_batches)
                }
            
            return render_template(
                'medicamentos.html', 
                medications=medications,
                medication_data=medication_data
            )
        except Exception as e:
            # Log do erro e página de fallback simples para evitar erro 500
            print(f"Erro ao carregar página de medicamentos: {str(e)}")
            return render_template(
                'medicamentos.html', 
                medications=Medication.query.all(),
                medication_data={}
            )
        
    @app.route('/medicamentos/importar')
    @login_required
    def importar_medicamentos():
        """Página que mostra os medicamentos importados automaticamente das planilhas"""
        if current_user.role not in ['admin', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        # Obter dados dos medicamentos para exibição
        medications_data = get_medications_data()
        
        # Verificar quantos medicamentos existem no banco
        medicamentos_no_banco = Medication.query.count()
        lotes_no_banco = MedicationBatch.query.count()
        
        return render_template('importar_medicamentos.html', 
                              medications=medications_data,
                              total_meds=len(medications_data),
                              medicamentos_no_banco=medicamentos_no_banco,
                              lotes_no_banco=lotes_no_banco)
    
    # Rota mantida para compatibilidade, mas não é mais necessária
    @app.route('/medicamentos/executar-importacao')
    @login_required
    def executar_importacao():
        """API para verificar o status da importação de medicamentos (que já ocorre automaticamente)"""
        if current_user.role not in ['admin', 'farmaceutico']:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Retornar informações sobre a importação automática
        return jsonify({
            'medications_added': 0,
            'batches_added': 0,
            'log': ['Os medicamentos já foram importados automaticamente na inicialização do sistema.']
        })

    @app.route('/medicamento/novo', methods=['POST'])
    @login_required
    def novo_medicamento():
        """Adicionar novo medicamento com lote inicial"""
        if current_user.role not in ['admin', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        # Dados do medicamento
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        principio_ativo = request.form.get('principio_ativo')
        forma = request.form.get('forma')
        concentracao = request.form.get('concentracao')
        
        # Dados do lote
        lote = request.form.get('lote')
        validade_str = request.form.get('validade')
        quantidade_str = request.form.get('quantidade')
        
        # Validações
        if not nome:
            flash('O nome do medicamento é obrigatório', 'error')
            return redirect(url_for('medicamentos'))
        
        if not lote or not validade_str or not quantidade_str:
            flash('As informações do lote são obrigatórias (número do lote, validade e quantidade)', 'error')
            return redirect(url_for('medicamentos'))
        
        try:
            quantidade = int(quantidade_str)
            if quantidade <= 0:
                raise ValueError("A quantidade deve ser maior que zero")
        except ValueError:
            flash('A quantidade deve ser um número válido maior que zero', 'error')
            return redirect(url_for('medicamentos'))
        
        try:
            # Converter a data de validade
            from datetime import datetime
            validade = datetime.strptime(validade_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de data inválido. Use o formato correto (YYYY-MM-DD)', 'error')
            return redirect(url_for('medicamentos'))
        
        try:
            # Criar novo medicamento
            medication = Medication(
                nome=nome,
                descricao=descricao,
                principio_ativo=principio_ativo,
                forma=forma,
                concentracao=concentracao
            )
            
            db.session.add(medication)
            db.session.flush()  # Obter o ID do medicamento sem fazer commit
            
            # Criar lote inicial
            batch = MedicationBatch(
                medication_id=medication.id,
                lote=lote,
                validade=validade,
                quantidade_inicial=quantidade,
                quantidade_atual=quantidade
            )
            
            db.session.add(batch)
            db.session.commit()
            
            flash(f'Medicamento {nome} cadastrado com sucesso com lote inicial', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar medicamento: {str(e)}', 'error')
            app.logger.error(f"Erro ao cadastrar medicamento: {str(e)}")
        
        return redirect(url_for('medicamentos'))

    @app.route('/medicamento/editar/<int:id>', methods=['POST'])
    @login_required
    def editar_medicamento(id):
        """Editar medicamento existente"""
        if current_user.role not in ['admin', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        medication = Medication.query.get_or_404(id)
        
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        principio_ativo = request.form.get('principio_ativo')
        forma = request.form.get('forma')
        concentracao = request.form.get('concentracao')
        
        # Validações
        if not nome:
            flash('O nome do medicamento é obrigatório', 'error')
            return redirect(url_for('medicamentos'))
        
        # Atualizar dados do medicamento
        medication.nome = nome
        medication.descricao = descricao
        medication.principio_ativo = principio_ativo
        medication.forma = forma
        medication.concentracao = concentracao
        
        db.session.commit()
        
        flash(f'Medicamento {nome} atualizado com sucesso', 'success')
        return redirect(url_for('medicamentos'))
        
    @app.route('/medicamento/excluir/<int:id>', methods=['POST'])
    @login_required
    def excluir_medicamento(id):
        """Excluir medicamento existente"""
        if current_user.role not in ['admin', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        medication = Medication.query.get_or_404(id)
        
        # Verificar se tem dispensações relacionadas
        dispensacoes = MedicationDispensing.query.join(MedicationBatch).filter(
            MedicationBatch.medication_id == id
        ).first()
        
        if dispensacoes:
            flash(f'Não é possível excluir o medicamento {medication.nome} pois existem dispensações registradas', 'error')
            return redirect(url_for('medicamentos'))
        
        # Excluir todos os lotes relacionados
        MedicationBatch.query.filter_by(medication_id=id).delete()
        
        # Excluir o medicamento
        nome_medicamento = medication.nome
        db.session.delete(medication)
        db.session.commit()
        
        flash(f'Medicamento {nome_medicamento} excluído com sucesso', 'success')
        return redirect(url_for('medicamentos'))
        
    @app.route('/medicamento/ajustar-estoque/<int:id>', methods=['POST'])
    @login_required
    def ajustar_estoque_medicamento(id):
        """Ajustar estoque de um medicamento"""
        if current_user.role not in ['admin', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        app.logger.info(f"Ajustando estoque do medicamento {id}")
        app.logger.info(f"Form data: {request.form}")
        
        medication = Medication.query.get_or_404(id)
        
        # Obter dados do formulário
        operacao = request.form.get('operacao')
        quantidade_str = request.form.get('quantidade')
        lote_id = request.form.get('lote')
        observacao = request.form.get('observacao')
        
        app.logger.info(f"Dados recebidos: operacao={operacao}, quantidade={quantidade_str}, lote_id={lote_id}")
        
        # Validações
        if not operacao or not quantidade_str:
            flash('Todos os campos obrigatórios devem ser preenchidos', 'error')
            return redirect(url_for('medicamentos'))
        
        try:
            quantidade = int(quantidade_str)
            if quantidade <= 0:
                raise ValueError("A quantidade deve ser maior que zero")
        except ValueError as e:
            flash(f'Valor inválido para quantidade: {str(e)}', 'error')
            return redirect(url_for('medicamentos'))
        
        # Processar de acordo com a operação
        if operacao == 'adicionar':
            if lote_id:  # Adicionar a um lote existente
                batch = MedicationBatch.query.get_or_404(lote_id)
                batch.quantidade_atual += quantidade
                db.session.commit()
                flash(f'Adicionadas {quantidade} unidades ao lote {batch.lote}', 'success')
            else:  # Criar novo lote
                # Verificar se foi fornecida uma data de validade e número de lote
                lote_numero = request.form.get('lote_numero')
                lote_validade_str = request.form.get('lote_validade')
                
                # Se não foi fornecido número do lote, criar um padrão
                if not lote_numero:
                    lote_numero = f"AJUSTE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Se foi fornecida data de validade, usar; senão, criar validade padrão (1 ano)
                if lote_validade_str:
                    try:
                        validade = datetime.strptime(lote_validade_str, '%Y-%m-%d').date()
                    except ValueError:
                        validade = (datetime.now() + timedelta(days=365)).date()
                else:
                    validade = (datetime.now() + timedelta(days=365)).date()
                
                app.logger.info(f"Criando novo lote: número={lote_numero}, validade={validade}")
                
                novo_lote = MedicationBatch(
                    medication_id=id,
                    lote=lote_numero,
                    validade=validade,
                    quantidade_inicial=quantidade,
                    quantidade_atual=quantidade
                )
                db.session.add(novo_lote)
                db.session.commit()
                flash(f'Criado novo lote com {quantidade} unidades', 'success')
                
        elif operacao == 'remover':
            # Obter todos os lotes com estoque disponível
            lotes_disponiveis = MedicationBatch.query.filter(
                MedicationBatch.medication_id == id,
                MedicationBatch.quantidade_atual > 0
            ).order_by(MedicationBatch.validade).all()
            
            if not lotes_disponiveis:
                flash('Não há estoque disponível para remoção', 'error')
                return redirect(url_for('medicamentos'))
                
            # Verificar se há estoque suficiente
            total_disponivel = sum(lote.quantidade_atual for lote in lotes_disponiveis)
            if total_disponivel < quantidade:
                flash(f'Estoque insuficiente. Disponível: {total_disponivel}, Solicitado: {quantidade}', 'error')
                return redirect(url_for('medicamentos'))
            
            # Remover do estoque, começando pelos lotes com validade mais próxima
            quantidade_restante = quantidade
            for lote in lotes_disponiveis:
                if quantidade_restante <= 0:
                    break
                    
                if lote.quantidade_atual <= quantidade_restante:
                    # Remove todo o estoque deste lote
                    quantidade_restante -= lote.quantidade_atual
                    lote.quantidade_atual = 0
                else:
                    # Remove parte do estoque deste lote
                    lote.quantidade_atual -= quantidade_restante
                    quantidade_restante = 0
            
            db.session.commit()
            flash(f'Removidas {quantidade} unidades do estoque de {medication.nome}', 'success')
            
        elif operacao == 'definir':
            # Abordagem: ajustar o último lote para refletir o novo valor total
            total_atual = medication.stock_total()
            
            if quantidade == total_atual:
                flash(f'O estoque já possui a quantidade informada ({quantidade} unidades)', 'info')
                return redirect(url_for('medicamentos'))
                
            # Se não tiver lotes, cria um
            if total_atual == 0:
                # Criar validade padrão (1 ano)
                validade = (datetime.now() + timedelta(days=365)).date()
                
                novo_lote = MedicationBatch(
                    medication_id=id,
                    lote=f"AJUSTE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    validade=validade,
                    quantidade_inicial=quantidade,
                    quantidade_atual=quantidade
                )
                db.session.add(novo_lote)
                db.session.commit()
                flash(f'Estoque definido para {quantidade} unidades', 'success')
            else:
                # Ajustar o último lote
                diferenca = quantidade - total_atual
                ultimo_lote = MedicationBatch.query.filter_by(
                    medication_id=id
                ).order_by(MedicationBatch.id.desc()).first()
                
                if not ultimo_lote:
                    flash('Erro ao encontrar lote para ajustar o estoque', 'error')
                    return redirect(url_for('medicamentos'))
                    
                novo_valor = ultimo_lote.quantidade_atual + diferenca
                if novo_valor < 0:
                    flash('Não é possível reduzir o estoque para o valor especificado', 'error')
                    return redirect(url_for('medicamentos'))
                    
                ultimo_lote.quantidade_atual = novo_valor
                db.session.commit()
                
                if diferenca > 0:
                    flash(f'Estoque aumentado em {diferenca} unidades', 'success')
                else:
                    flash(f'Estoque reduzido em {abs(diferenca)} unidades', 'success')
        
        return redirect(url_for('medicamentos'))

    @app.route('/medicamento/lotes/<int:medication_id>')
    @login_required
    def medicamento_lotes(medication_id):
        """Visualizar lotes de um medicamento"""
        if current_user.role not in ['admin', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        medication = Medication.query.get_or_404(medication_id)
        batches = MedicationBatch.query.filter_by(medication_id=medication_id).all()
        
        return render_template('medicamento_lotes.html', medication=medication, batches=batches)

    @app.route('/medicamento/lote/novo/<int:medication_id>', methods=['POST'])
    @login_required
    def novo_lote(medication_id):
        """Adicionar novo lote de medicamento"""
        if current_user.role not in ['admin', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        medication = Medication.query.get_or_404(medication_id)
        
        lote = request.form.get('lote')
        validade = request.form.get('validade')
        quantidade = request.form.get('quantidade')
        
        # Validações
        if not lote or not validade or not quantidade:
            flash('Todos os campos são obrigatórios', 'error')
            return redirect(url_for('medicamento_lotes', medication_id=medication_id))
        
        try:
            quantidade = int(quantidade)
            if quantidade <= 0:
                raise ValueError("Quantidade deve ser positiva")
        except ValueError:
            flash('Quantidade inválida. Informe um número inteiro positivo', 'error')
            return redirect(url_for('medicamento_lotes', medication_id=medication_id))
        
        # Converter validade
        date_obj = None
        try:
            date_obj = datetime.strptime(validade, '%Y-%m-%d').date()
        except ValueError:
            flash('Data de validade inválida. Use o formato AAAA-MM-DD', 'error')
            return redirect(url_for('medicamento_lotes', medication_id=medication_id))
        
        # Criar novo lote
        batch = MedicationBatch(
            medication_id=medication_id,
            lote=lote,
            validade=date_obj,
            quantidade_inicial=quantidade,
            quantidade_atual=quantidade
        )
        
        db.session.add(batch)
        db.session.commit()
        
        flash(f'Lote {lote} adicionado com sucesso', 'success')
        return redirect(url_for('medicamento_lotes', medication_id=medication_id))
        
    @app.route('/medicamento/lote/editar/<int:batch_id>', methods=['POST'])
    @login_required
    def editar_lote(batch_id):
        """Editar lote de medicamento"""
        app.logger.info(f"Editando lote {batch_id}")
        app.logger.info(f"Form data: {request.form}")
        
        if current_user.role not in ['admin', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        batch = MedicationBatch.query.get_or_404(batch_id)
        app.logger.info(f"Lote encontrado: {batch.lote}, quantidade atual: {batch.quantidade_atual}")
        
        # Obter dados do formulário
        lote = request.form.get('lote')
        validade_str = request.form.get('validade')
        quantidade_atual = request.form.get('quantidade_atual')
        app.logger.info(f"Dados recebidos: lote={lote}, validade={validade_str}, quantidade={quantidade_atual}")
        
        # Validações
        if not lote or not validade_str or not quantidade_atual:
            flash('Todos os campos são obrigatórios', 'error')
            return redirect(url_for('medicamento_lotes', medication_id=batch.medication_id))
        
        try:
            # Converter validade
            validade = datetime.strptime(validade_str, '%Y-%m-%d').date()
            quantidade_atual = int(quantidade_atual)
            
            if quantidade_atual < 0:
                raise ValueError("A quantidade não pode ser negativa")
                
        except ValueError as e:
            flash(f'Erro de validação: {str(e)}', 'error')
            return redirect(url_for('medicamento_lotes', medication_id=batch.medication_id))
        
        # Atualizar lote
        batch.lote = lote
        batch.validade = validade
        batch.quantidade_atual = quantidade_atual
        
        db.session.commit()
        
        flash(f'Lote {lote} atualizado com sucesso', 'success')
        return redirect(url_for('medicamento_lotes', medication_id=batch.medication_id))
        
    @app.route('/medicamento/lote/excluir/<int:batch_id>', methods=['POST'])
    @login_required
    def excluir_lote(batch_id):
        """Excluir lote de medicamento"""
        if current_user.role not in ['admin', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        batch = MedicationBatch.query.get_or_404(batch_id)
        medication_id = batch.medication_id
        
        # Verificar se há dispensações relacionadas a este lote
        if batch.dispensings.count() > 0:
            flash(f'Não é possível excluir o lote {batch.lote} pois existem dispensações registradas', 'error')
            return redirect(url_for('medicamento_lotes', medication_id=medication_id))
        
        # Excluir o lote
        lote_num = batch.lote
        db.session.delete(batch)
        db.session.commit()
        
        flash(f'Lote {lote_num} excluído com sucesso', 'success')
        return redirect(url_for('medicamento_lotes', medication_id=medication_id))

    @app.route('/farmacia')
    @login_required
    def farmacia():
        """Página de prescrições/farmácia"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        prescriptions = Prescription.query.order_by(Prescription.date.desc()).all()
        return render_template('farmacia.html', prescriptions=prescriptions)

    @app.route('/prescricao/nova', methods=['GET', 'POST'])
    @login_required
    def nova_prescricao():
        """Criar nova prescrição médica"""
        if current_user.role not in ['admin', 'medico', 'enfermeiro', 'farmaceutico']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            patient_id = request.form.get('patient_id')
            observacoes = request.form.get('observacoes')
            medication_ids = request.form.getlist('medication_id[]')
            quantidades = request.form.getlist('quantidade[]')
            instrucoes_lista = request.form.getlist('instrucoes[]')
            
            # Validações
            if not patient_id or not medication_ids:
                flash('Por favor, selecione um paciente e pelo menos um medicamento', 'error')
                patients = Patient.query.all()
                medications = Medication.query.all()
                return render_template('prescricao_form.html', patients=patients, medications=medications)
            
            # Criar prescrição
            prescription = Prescription(
                patient_id=patient_id,
                doctor_id=current_user.id,
                observacoes=observacoes,
                status='pendente'
            )
            
            db.session.add(prescription)
            db.session.commit()
            
            # Adicionar itens à prescrição
            for i in range(len(medication_ids)):
                if i < len(quantidades) and quantidades[i] and int(quantidades[i]) > 0:
                    instrucoes = instrucoes_lista[i] if i < len(instrucoes_lista) else ""
                    
                    item = PrescriptionItem(
                        prescription_id=prescription.id,
                        medication_id=medication_ids[i],
                        quantidade=quantidades[i],
                        instrucoes=instrucoes
                    )
                    
                    db.session.add(item)
            
            db.session.commit()
            
            flash('Prescrição criada com sucesso', 'success')
            return redirect(url_for('farmacia'))
        
        # GET request - mostrar formulário
        patients = Patient.query.all()
        medications = Medication.query.all()
        return render_template('prescricao_form.html', patients=patients, medications=medications)

    @app.route('/prescricao/ver/<int:id>')
    @login_required
    def ver_prescricao(id):
        """Visualizar detalhes de uma prescrição"""
        if current_user.role not in ['admin', 'medico', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        prescription = Prescription.query.get_or_404(id)
        items = PrescriptionItem.query.filter_by(prescription_id=id).all()
        dispensings = MedicationDispensing.query.filter_by(prescription_id=id).all()
        
        return render_template('prescricao_view.html', prescription=prescription, items=items, dispensings=dispensings)
        
    @app.route('/prescricao/editar/<int:id>', methods=['GET', 'POST'])
    @login_required
    def editar_prescricao(id):
        """Editar uma prescrição existente"""
        if current_user.role not in ['admin', 'medico', 'enfermeiro', 'farmaceutico']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        prescription = Prescription.query.get_or_404(id)
        
        # Buscar todos os itens atuais da prescrição
        items = PrescriptionItem.query.filter_by(prescription_id=id).all()
        
        # Verificar se já foram dispensados medicamentos
        dispensings = MedicationDispensing.query.filter_by(prescription_id=id).all()
        has_dispensing = len(dispensings) > 0
        
        if request.method == 'POST':
            # Atualizar observações da prescrição
            prescription.observacoes = request.form.get('observacoes', '')
            
            # Recuperar dados do formulário
            medication_ids = request.form.getlist('medication_id[]')
            quantidades = request.form.getlist('quantidade[]')
            instrucoes_lista = request.form.getlist('instrucoes[]')
            item_ids = request.form.getlist('item_id[]')  # Para itens existentes
            
            # Se a prescrição já tem dispensações, não permitimos excluir itens
            # mas permitimos adicionar novos ou alterar instruções
            
            # Primeiro, processar itens existentes
            for i, item_id in enumerate(item_ids):
                if item_id and i < len(medication_ids) and i < len(quantidades):
                    item = PrescriptionItem.query.get(item_id)
                    if item:
                        # Atualizar apenas instruções se já houver dispensação
                        if has_dispensing:
                            item.instrucoes = instrucoes_lista[i] if i < len(instrucoes_lista) else ""
                        else:
                            # Se não houver dispensação, podemos atualizar tudo
                            item.medication_id = medication_ids[i]
                            item.quantidade = quantidades[i]
                            item.instrucoes = instrucoes_lista[i] if i < len(instrucoes_lista) else ""
            
            # Adicionar novos itens (apenas aqueles que não têm item_id)
            for i in range(len(medication_ids)):
                # Verificar se este é um novo item (não tem item_id correspondente)
                if i >= len(item_ids) or not item_ids[i]:
                    if i < len(quantidades) and quantidades[i] and int(quantidades[i]) > 0:
                        instrucoes = instrucoes_lista[i] if i < len(instrucoes_lista) else ""
                        
                        item = PrescriptionItem(
                            prescription_id=prescription.id,
                            medication_id=medication_ids[i],
                            quantidade=quantidades[i],
                            instrucoes=instrucoes
                        )
                        
                        db.session.add(item)
            
            db.session.commit()
            flash('Prescrição atualizada com sucesso', 'success')
            return redirect(url_for('ver_prescricao', id=prescription.id))
            
        # GET request - mostrar formulário de edição
        patients = Patient.query.all()
        medications = Medication.query.all()
        
        return render_template(
            'prescricao_edit.html', 
            prescription=prescription, 
            items=items,
            patients=patients,
            medications=medications,
            has_dispensing=has_dispensing
        )
            
    @app.route('/prescricao/excluir/<int:id>')
    @login_required
    def excluir_prescricao(id):
        """Excluir uma prescrição"""
        if current_user.role not in ['admin', 'medico', 'enfermeiro', 'farmaceutico']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        prescription = Prescription.query.get_or_404(id)
        
        try:
            # Verificar se existem dispensações associadas
            dispensings = MedicationDispensing.query.filter_by(prescription_id=id).all()
            
            # Se tiver dispensações, devolver os medicamentos ao estoque
            for dispensing in dispensings:
                batch = dispensing.batch
                batch.quantidade_atual += dispensing.quantidade
                db.session.delete(dispensing)
            
            # Remover os itens da prescrição
            PrescriptionItem.query.filter_by(prescription_id=id).delete()
            
            # Remover a prescrição
            db.session.delete(prescription)
            db.session.commit()
            
            flash('Prescrição excluída com sucesso. Medicamentos retornados ao estoque.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir prescrição: {str(e)}', 'error')
        
        return redirect(url_for('farmacia'))

    @app.route('/dispensar/<int:prescription_id>', methods=['GET', 'POST'])
    @login_required
    def dispensar_medicamentos(prescription_id):
        """Dispensar medicamentos de uma prescrição"""
        if current_user.role not in ['admin', 'farmaceutico', 'enfermeiro']:
            flash('Acesso negado. Você não tem permissão para realizar esta ação.', 'error')
            return redirect(url_for('dashboard'))
        
        prescription = Prescription.query.get_or_404(prescription_id)
        
        if prescription.status == 'dispensado':
            flash('Esta prescrição já foi dispensada', 'warning')
            return redirect(url_for('farmacia'))
        
        if request.method == 'POST':
            batch_ids = request.form.getlist('batch_id[]')
            quantities = request.form.getlist('quantidade[]')
            
            if not batch_ids or len(batch_ids) != len(quantities):
                flash('Dados inválidos', 'error')
                return redirect(url_for('dispensar_medicamentos', prescription_id=prescription_id))
            
            # Validar IDs dos lotes
            for batch_id in batch_ids:
                if not batch_id or not batch_id.isdigit():
                    flash('Selecione um lote válido para cada medicamento', 'error')
                    return redirect(url_for('dispensar_medicamentos', prescription_id=prescription_id))
            
            success = True
            
            for i in range(len(batch_ids)):
                batch_id = int(batch_ids[i])  # Converter para inteiro com segurança
                quantidade = int(quantities[i])
                
                if quantidade <= 0:
                    continue
                
                batch = MedicationBatch.query.get(batch_id)  # Agora batch_id já é um inteiro
                
                if not batch or batch.quantidade_atual < quantidade:
                    flash(f'Estoque insuficiente para o lote selecionado: {batch.medication.nome if batch else "Unknown"}', 'error')
                    success = False
                    break
                
                # Registrar dispensação
                dispensing = MedicationDispensing(
                    prescription_id=prescription_id,
                    batch_id=batch_id,
                    dispenser_id=current_user.id,
                    quantidade=quantidade
                )
                
                # Atualizar estoque
                batch.quantidade_atual -= quantidade
                
                db.session.add(dispensing)
            
            if success:
                # Atualizar status da prescrição
                prescription.status = 'dispensado'
                db.session.commit()
                flash('Medicamentos dispensados com sucesso', 'success')
                return redirect(url_for('farmacia'))
            else:
                db.session.rollback()
            
        # GET request - mostrar formulário
        items = PrescriptionItem.query.filter_by(prescription_id=prescription_id).all()
        
        # Para cada item, buscar lotes disponíveis
        item_batches = []
        for item in items:
            medication = Medication.query.get(item.medication_id)
            batches = MedicationBatch.query.filter_by(medication_id=item.medication_id).filter(MedicationBatch.quantidade_atual > 0).all()
            item_batches.append({
                'item': item,
                'medication': medication,
                'batches': batches
            })
        
        return render_template('dispensar_form.html', prescription=prescription, item_batches=item_batches)

    @app.route('/mensagens')
    @login_required
    def mensagens():
        """Página de mensagens"""
        received = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.created_at.desc()).all()
        sent = Message.query.filter_by(sender_id=current_user.id).order_by(Message.created_at.desc()).all()
        users = User.query.filter(User.id != current_user.id).all()
        
        return render_template('mensagens.html', received=received, sent=sent, users=users)

    @app.route('/mensagem/enviar', methods=['POST'])
    @login_required
    def enviar_mensagem():
        """Enviar nova mensagem"""
        recipient_id = request.form.get('recipient_id')
        subject = request.form.get('subject')
        body = request.form.get('body')
        
        if not recipient_id or not subject or not body:
            flash('Por favor, preencha todos os campos', 'error')
            return redirect(url_for('mensagens'))
        
        recipient = User.query.get_or_404(recipient_id)
        
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            subject=subject,
            body=body,
            read=False
        )
        
        db.session.add(message)
        db.session.commit()
        
        flash(f'Mensagem enviada para {recipient.nome}', 'success')
        return redirect(url_for('mensagens'))

    @app.route('/mensagem/ler/<int:id>')
    @login_required
    def ler_mensagem(id):
        """Ler mensagem específica"""
        message = Message.query.get_or_404(id)
        
        if message.recipient_id != current_user.id and message.sender_id != current_user.id:
            flash('Acesso negado. Você não tem permissão para ler esta mensagem.', 'error')
            return redirect(url_for('mensagens'))
        
        # Marcar como lida se for o destinatário
        if message.recipient_id == current_user.id and not message.read:
            message.read = True
            db.session.commit()
        
        return render_template('mensagem_view.html', message=message)
        
    @app.route('/mensagem/editar/<int:id>', methods=['POST'])
    @login_required
    def editar_mensagem(id):
        """Editar mensagem enviada"""
        message = Message.query.get_or_404(id)
        
        # Verificar se o usuário é o remetente
        if message.sender_id != current_user.id:
            flash('Acesso negado. Você só pode editar suas próprias mensagens.', 'error')
            return redirect(url_for('mensagens'))
        
        subject = request.form.get('subject')
        body = request.form.get('body')
        
        if not subject or not body:
            flash('Por favor, preencha todos os campos', 'error')
            return redirect(url_for('mensagens'))
        
        message.subject = subject
        message.body = body
        
        db.session.commit()
        
        flash('Mensagem atualizada com sucesso', 'success')
        return redirect(url_for('mensagens'))
        
    @app.route('/mensagem/excluir/<int:id>')
    @login_required
    def excluir_mensagem(id):
        """Excluir mensagem enviada"""
        message = Message.query.get_or_404(id)
        
        # Verificar se o usuário é o remetente
        if message.sender_id != current_user.id:
            flash('Acesso negado. Você só pode excluir suas próprias mensagens.', 'error')
            return redirect(url_for('mensagens'))
        
        db.session.delete(message)
        db.session.commit()
        
        flash('Mensagem excluída com sucesso', 'success')
        return redirect(url_for('mensagens'))

    @app.route('/configuracoes')
    @login_required
    def configuracoes():
        """Página de configurações"""
        if current_user.role != 'admin':
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        
        return render_template('configuracoes.html')
        
    @app.route('/teste')
    @login_required
    def test_page():
        """Página de teste para depuração de JavaScript"""
        return render_template('test_page.html')