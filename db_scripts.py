"""
Scripts úteis para gerenciamento do banco de dados no Render
Execute estes comandos no Shell do Render ou durante a inicialização
"""
import os
import sys
from app import app, db
from models import User
from werkzeug.security import generate_password_hash


def create_tables():
    """Cria todas as tabelas no banco de dados"""
    with app.app_context():
        db.create_all()
        print("Tabelas criadas com sucesso!")


def reset_admin_password():
    """Redefine a senha do administrador para '1234'"""
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            admin.password_hash = generate_password_hash('1234')
            db.session.commit()
            print("Senha do administrador redefinida para '1234'")
        else:
            print("Usuário administrador não encontrado")


def create_default_users():
    """Cria os usuários padrão no sistema"""
    with app.app_context():
        default_users = [
            {'username': 'admin', 'nome': 'Administrador', 'role': 'admin'},
            {'username': 'medico', 'nome': 'Dr. Carlos Silva', 'role': 'medico'},
            {'username': 'enfermeiro', 'nome': 'Enfermeira Ana Paula', 'role': 'enfermeiro'},
            {'username': 'farmaceutico', 'nome': 'Paulo Santos', 'role': 'farmaceutico'},
            {'username': 'recepcionista', 'nome': 'Maria Oliveira', 'role': 'recepcionista'}
        ]
        
        for user_data in default_users:
            user = User.query.filter_by(username=user_data['username']).first()
            if not user:
                user = User(
                    username=user_data['username'],
                    nome=user_data['nome'],
                    email=f"{user_data['username']}@integrabs.local",
                    role=user_data['role'],
                    password_hash=generate_password_hash('1234'),
                    status='ativo'
                )
                db.session.add(user)
                print(f"Usuário {user_data['username']} criado")
        
        db.session.commit()
        print("Usuários padrão criados com sucesso!")


def check_database_connection():
    """Verifica a conexão com o banco de dados"""
    with app.app_context():
        try:
            # Tenta executar uma consulta simples
            User.query.first()
            print(f"Conexão bem-sucedida ao banco de dados: {db.engine.url}")
            print(f"Tipo de banco: {db.engine.name}")
            return True
        except Exception as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            return False


if __name__ == "__main__":
    # Execute comandos específicos conforme os argumentos da linha de comando
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "create_tables":
            create_tables()
        elif command == "reset_admin":
            reset_admin_password()
        elif command == "create_users":
            create_default_users()
        elif command == "check_connection":
            check_database_connection()
        else:
            print(f"Comando desconhecido: {command}")
    else:
        # Se nenhum comando for especificado, executa todos
        print("Verificando conexão com o banco de dados...")
        if check_database_connection():
            print("Criando tabelas...")
            create_tables()
            print("Criando usuários padrão...")
            create_default_users()
            print("Configuração concluída!")
        else:
            print("Falha na configuração do banco de dados.")