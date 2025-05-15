"""
SISTEMA INTEGRA UBS - Modelos de dados
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='usuario')  # admin, medico, enfermeiro, farmaceutico, recepcionista
    status = db.Column(db.String(20), nullable=False, default='ativo')  # ativo, inativo
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        # Inicializador genérico que aceita keywords arguments
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    # Relationships
    sent_messages = db.relationship('Message', backref='sender', foreign_keys='Message.sender_id', lazy='dynamic')
    received_messages = db.relationship('Message', backref='recipient', foreign_keys='Message.recipient_id', lazy='dynamic')
    
    def set_password(self, password):
        """Define a senha criptografada para o usuário"""
        try:
            self.password_hash = generate_password_hash(password)
            return True
        except Exception as e:
            print(f"Erro ao definir senha: {str(e)}")
            return False
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    data_nascimento = db.Column(db.Date, nullable=True)
    sexo = db.Column(db.String(10), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.String(200), nullable=True)
    sus_card = db.Column(db.String(20), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        # Inicializador genérico que aceita keywords arguments
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    # Relationships
    records = db.relationship('MedicalRecord', backref='patient', lazy='dynamic')
    prescriptions = db.relationship('Prescription', backref='patient', lazy='dynamic')
    
    def __repr__(self):
        return f'<Patient {self.nome}>'

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    complaint = db.Column(db.Text, nullable=True)
    diagnosis = db.Column(db.Text, nullable=True)
    treatment = db.Column(db.Text, nullable=True)
    observations = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        # Inicializador genérico que aceita keywords arguments
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    # Relationships
    doctor = db.relationship('User')
    
    def __repr__(self):
        return f'<MedicalRecord {self.id} - Patient {self.patient_id}>'

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    principio_ativo = db.Column(db.String(120), nullable=True)
    forma = db.Column(db.String(50), nullable=True)  # comprimido, líquido, injetável, etc.
    concentracao = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        # Inicializador genérico que aceita keywords arguments
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    # Relationships
    batches = db.relationship('MedicationBatch', backref='medication', lazy='dynamic')
    prescription_items = db.relationship('PrescriptionItem', backref='medication', lazy='dynamic')
    
    def __repr__(self):
        return f'<Medication {self.nome}>'
    
    def stock_total(self, preloaded_batches=None):
        """
        Retorna o estoque total do medicamento considerando todos os lotes
        
        Args:
            preloaded_batches: Lista opcional de lotes pré-carregados para evitar múltiplas consultas no banco
        """
        try:
            # Usar lotes pré-carregados se fornecidos para evitar múltiplas consultas
            lotes = preloaded_batches if preloaded_batches is not None else self.batches.all()
            return sum(batch.quantidade_atual for batch in lotes)
        except Exception:
            return 0
        
    def next_expiry_date(self, preloaded_batches=None):
        """
        Retorna a data de validade mais próxima entre os lotes com estoque disponível
        
        Args:
            preloaded_batches: Lista opcional de lotes pré-carregados para evitar múltiplas consultas no banco
        """
        try:
            # Usar lotes pré-carregados se fornecidos para evitar múltiplas consultas
            lotes = preloaded_batches if preloaded_batches is not None else self.batches.all()
            
            # Filtrar apenas lotes com estoque
            lotes_disponiveis = [batch for batch in lotes if batch.quantidade_atual > 0]
            
            if not lotes_disponiveis:
                return None
            
            # Calcular a data de validade mais próxima usando min() com uma expressão lambda
            return min(lotes_disponiveis, key=lambda batch: batch.validade).validade
        except Exception:
            return None

class MedicationBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    lote = db.Column(db.String(50), nullable=False)
    validade = db.Column(db.Date, nullable=False)
    quantidade_inicial = db.Column(db.Integer, nullable=False)
    quantidade_atual = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        # Inicializador genérico que aceita keywords arguments
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    # Relationships
    dispensings = db.relationship('MedicationDispensing', backref='batch', lazy='dynamic')
    
    def __repr__(self):
        return f'<MedicationBatch {self.lote} - Medication {self.medication_id}>'

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='pendente')  # pendente, dispensado, cancelado
    observacoes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        # Inicializador genérico que aceita keywords arguments
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    # Relationships
    doctor = db.relationship('User')
    items = db.relationship('PrescriptionItem', backref='prescription', lazy='dynamic')
    dispensings = db.relationship('MedicationDispensing', backref='prescription', lazy='dynamic')
    
    def __repr__(self):
        return f'<Prescription {self.id} - Patient {self.patient_id}>'

class PrescriptionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescription.id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    instrucoes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        # Inicializador genérico que aceita keywords arguments
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return f'<PrescriptionItem {self.id} - Prescription {self.prescription_id}>'

class MedicationDispensing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescription.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('medication_batch.id'), nullable=False)
    dispenser_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    quantidade = db.Column(db.Integer, nullable=False)
    observacoes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        # Inicializador genérico que aceita keywords arguments
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    # Relationships
    dispenser = db.relationship('User')
    
    def __repr__(self):
        return f'<MedicationDispensing {self.id} - Prescription {self.prescription_id}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        # Inicializador genérico que aceita keywords arguments
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __repr__(self):
        return f'<Message {self.id} - From {self.sender_id} to {self.recipient_id}>'
        
class ChatMensagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    usuario = db.relationship('User', backref='chat_mensagens')
    
    def __init__(self, **kwargs):
        # Inicializador genérico que aceita keywords arguments
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def hora_formatada(self):
        """Retorna a hora formatada da mensagem"""
        return self.created_at.strftime('%H:%M')
    
    def to_dict(self):
        """Converte a mensagem para dicionário para uso na API"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'nome_usuario': self.usuario.nome,
            'texto': self.texto,
            'hora_formatada': self.hora_formatada(),
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<ChatMensagem {self.id} de {self.usuario_id}>'
        
class ReceituarioModelo(db.Model):
    """Modelo para armazenar diferentes layouts de receituário médico"""
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    cabecalho = db.Column(db.Text, nullable=False, default="RECEITUÁRIO MÉDICO\nSISTEMA INTEGRA UBS")
    rodape = db.Column(db.Text, nullable=True)
    logotipo = db.Column(db.Text, nullable=True)  # Caminho ou código base64
    cor_primaria = db.Column(db.String(20), nullable=False, default="#0066cc")  # Azul UBS
    fonte_titulo = db.Column(db.String(50), nullable=False, default="Arial")
    tamanho_titulo = db.Column(db.Integer, nullable=False, default=16)
    fonte_corpo = db.Column(db.String(50), nullable=False, default="Arial")
    tamanho_corpo = db.Column(db.Integer, nullable=False, default=11)
    ativo = db.Column(db.Boolean, default=True)
    padrao = db.Column(db.Boolean, default=False)
    criado_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    usuario = db.relationship('User', backref='receituario_modelos', foreign_keys=[criado_por])
    
    def __init__(self, **kwargs):
        # Inicializador genérico que aceita keywords arguments
        for key, value in kwargs.items():
            setattr(self, key, value)
        
    def __repr__(self):
        return f'<ReceituarioModelo {self.id}: {self.nome}>'