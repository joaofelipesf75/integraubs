"""
SISTEMA INTEGRA UBS - Configuração da aplicação
"""
import os
import logging
import webbrowser
from datetime import datetime
from flask import Flask, render_template, flash
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from threading import Timer

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Inicialização simplificada para evitar conflitos de metaclasse
db = SQLAlchemy()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "integra_ubs_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database - Adaptado para PostgreSQL no Render/Heroku
DATABASE_URL = os.environ.get("DATABASE_URL")

# Correção para URL do PostgreSQL (necessário para Heroku/Render)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configurar porta para o Heroku
PORT = int(os.environ.get("PORT", 5000))

if DATABASE_URL:
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.logger.info(f"Usando banco de dados remoto PostgreSQL")
else:
    # Fallback to SQLite (apenas para desenvolvimento local)
    app.logger.warning("Variável DATABASE_URL não encontrada, usando SQLite local (não recomendado para produção)")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sistema_ubs.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,  # Verifica conexão antes de usar
    "pool_recycle": 300,    # Recicla conexões a cada 5 minutos
    "max_overflow": 15,     # Máximo de conexões extras além do pool
    "pool_size": 5          # Tamanho do pool de conexões
}

# Initialize extensions
db.init_app(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Context processor para resolver erro de unread_messages
@app.context_processor
def inject_unread_messages():
    """Adiciona a variável unread_messages aos templates para evitar erro após login"""
    if current_user.is_authenticated:
        try:
            from models import Message
            unread_count = Message.query.filter_by(
                recipient_id=current_user.id, read=False
            ).count()
            return {'unread_messages': unread_count}
        except Exception as e:
            app.logger.error(f"Error counting unread messages: {e}")
            return {'unread_messages': 0}
    return {'unread_messages': 0}

# Context processor for date/time
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message='Página não encontrada'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message='Erro interno do servidor'), 500

# Initialize database
with app.app_context():
    # Import models after db initialization to avoid circular imports
    from models import User, Medication, Patient, Prescription, MedicationBatch, ReceituarioModelo
    
    # Create all tables in the database if they don't exist
    db.create_all()
    
    # Create admin user if none exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            nome='Administrador',
            email='admin@integrabs.local',
            role='admin',
            password_hash=generate_password_hash('1234'),
            status='ativo'
        )
        db.session.add(admin)
        db.session.commit()
        app.logger.info("Admin user created successfully")
    else:
        # Ensure admin password is '1234'
        admin.password_hash = generate_password_hash('1234')
        db.session.commit()
        app.logger.info("Admin password updated")
    
    # Criar usuários adicionais para o sistema de mensagens
    test_users = [
        {'username': 'medico', 'nome': 'Dr. Carlos Silva', 'role': 'medico', 'password': '1234'},
        {'username': 'enfermeiro', 'nome': 'Enfermeira Ana Paula', 'role': 'enfermeiro', 'password': '1234'},
        {'username': 'farmaceutico', 'nome': 'Paulo Santos', 'role': 'farmaceutico', 'password': '1234'},
        {'username': 'recepcionista', 'nome': 'Maria Oliveira', 'role': 'recepcionista', 'password': '1234'}
    ]
    
    created_users = []
    for user_data in test_users:
        user = User.query.filter_by(username=user_data['username']).first()
        if not user:
            user = User(
                username=user_data['username'],
                nome=user_data['nome'],
                email=f"{user_data['username']}@integrabs.local",
                role=user_data['role'],
                password_hash=generate_password_hash(user_data['password']),
                status='ativo'
            )
            db.session.add(user)
            app.logger.info(f"User {user_data['username']} created successfully")
            created_users.append(True)
        else:
            # Atualizar senha para '1234'
            user.password_hash = generate_password_hash(user_data['password'])
            created_users.append(False)
    
    db.session.commit()
    
    # Criar mensagens de exemplo se os usuários foram criados agora
    if any(created_users):
        from models import Message, ChatMensagem
        
        # Criar mensagens de exemplo entre os usuários
        example_messages = [
            {
                'sender': 'medico',
                'recipient': 'enfermeiro',
                'subject': 'Paciente com prioridade',
                'body': 'Ana, por favor priorize o atendimento do paciente João Silva que está com pressão alta. Obrigado.'
            },
            {
                'sender': 'enfermeiro',
                'recipient': 'medico',
                'subject': 'Re: Paciente com prioridade',
                'body': 'Dr. Carlos, o paciente já foi atendido e está sob observação. Pressão estabilizada em 140/90.'
            },
            {
                'sender': 'farmaceutico',
                'recipient': 'medico',
                'subject': 'Medicamento em falta',
                'body': 'Dr. Carlos, gostaria de informar que estamos com o estoque de Dipirona em falta. Chegarão novas unidades na próxima semana.'
            },
            {
                'sender': 'recepcionista',
                'recipient': 'admin',
                'subject': 'Sistema funcionando bem',
                'body': 'Administrador, o novo sistema está muito bom! Estamos conseguindo organizar melhor os atendimentos.'
            },
            {
                'sender': 'admin',
                'recipient': 'medico',
                'subject': 'Bem-vindo ao Sistema Integra UBS',
                'body': 'Dr. Carlos, seja bem-vindo ao nosso novo sistema. Use esta plataforma para se comunicar com a equipe. Qualquer dúvida estou à disposição.'
            }
        ]
        
        for msg_data in example_messages:
            # Buscar IDs dos usuários
            sender = User.query.filter_by(username=msg_data['sender']).first()
            recipient = User.query.filter_by(username=msg_data['recipient']).first()
            
            if sender and recipient:
                # Verificar se a mensagem já existe
                existing_msg = Message.query.filter_by(
                    sender_id=sender.id,
                    recipient_id=recipient.id,
                    subject=msg_data['subject']
                ).first()
                
                if not existing_msg:
                    message = Message(
                        sender_id=sender.id,
                        recipient_id=recipient.id,
                        subject=msg_data['subject'],
                        body=msg_data['body'],
                        read=False
                    )
                    db.session.add(message)
        
        db.session.commit()
        app.logger.info("Example messages created successfully")
        
        # Criar mensagens de exemplo para o chat rápido
        if ChatMensagem.query.count() == 0:
            chat_messages = [
                {
                    'username': 'admin',
                    'text': 'Bem-vindos ao bate-papo rápido da equipe!'
                },
                {
                    'username': 'medico',
                    'text': 'Olá, equipe! Estou disponível no consultório 3 hoje.'
                },
                {
                    'username': 'enfermeiro',
                    'text': 'Dr. Carlos, temos alguns pacientes aguardando na recepção.'
                },
                {
                    'username': 'farmaceutico',
                    'text': 'Equipe, os medicamentos da campanha já chegaram. Podem encaminhar os pacientes.'
                },
                {
                    'username': 'medico',
                    'text': 'Obrigado pelo aviso, Paulo!'
                },
                {
                    'username': 'recepcionista',
                    'text': 'Informo que temos dois casos de emergência. Triagem já realizada.'
                }
            ]
            
            for chat_msg in chat_messages:
                user = User.query.filter_by(username=chat_msg['username']).first()
                if user:
                    # Criar a mensagem para o chat
                    chat_message = ChatMensagem(
                        usuario_id=user.id,
                        texto=chat_msg['text']
                    )
                    db.session.add(chat_message)
            
            db.session.commit()
            app.logger.info("Example chat messages created successfully")
        
    # Criar modelo padrão de receituário se não existir
    try:
        modelo_padrao = ReceituarioModelo.query.filter_by(padrao=True).first()
        if not modelo_padrao:
            modelo_padrao = ReceituarioModelo(
                nome="Modelo Padrão UBS",
                descricao="Modelo padrão para receituários médicos da UBS",
                cabecalho="RECEITUÁRIO MÉDICO\nSISTEMA INTEGRA UBS",
                rodape="Este receituário é válido por 30 dias conforme regulamentação.",
                cor_primaria="#0066cc",  # Azul UBS
                fonte_titulo="Arial",
                tamanho_titulo=16,
                fonte_corpo="Arial",
                tamanho_corpo=11,
                ativo=True,
                padrao=True,
                criado_por=1  # Admin
            )
            db.session.add(modelo_padrao)
            db.session.commit()
            app.logger.info("Modelo padrão de receituário criado com sucesso")
    except Exception as e:
        app.logger.error(f"Erro ao criar modelo padrão de receituário: {e}")
    
    # Importar medicamentos automaticamente na inicialização
    from importador import import_medications
    import_result = import_medications(db, Medication, MedicationBatch)
    app.logger.info(f"Automatic medication import completed: {import_result['medications_added']} medications and {import_result['batches_added']} batches added.")

# Import and register routes
from routes import register_routes
register_routes(app)

from relatorios import register_relatorios_route
register_relatorios_route(app)

# Registrar as rotas de gerenciamento de receituários
from receituario import register_receituario_routes
register_receituario_routes(app)

# Registrar as rotas de API do chat rápido
from chat_api import register_chat_api
register_chat_api(app)

# Registrar as rotas de API de pesquisa inteligente
from search_api import register_search_api
register_search_api(app)