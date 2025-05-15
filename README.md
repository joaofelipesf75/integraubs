# Sistema Integra UBS

Sistema integrado de gestão para Unidades Básicas de Saúde (UBS) desenvolvido para facilitar o gerenciamento de pacientes, medicamentos, prescrições e comunicação entre a equipe de saúde.

## Funcionalidades

- Gestão de usuários com diferentes níveis de acesso (admin, médico, enfermeiro, farmacêutico, recepcionista)
- Cadastro e gestão de pacientes
- Prontuários médicos eletrônicos
- Controle de estoque de medicamentos (com suporte para lotes e validades)
- Importação automática de medicamentos a partir das planilhas na inicialização
- Sistema de prescrição e dispensação de medicamentos
- Comunicação interna entre profissionais via chat rápido e sistema de mensagens
- Relatórios e estatísticas em tempo real

## Requisitos

- Python 3.10 ou superior
- PostgreSQL (recomendado para produção)
- Pacotes Python listados em requirements.txt

## Instalação

1. Clone o repositório:
```
git clone <URL-do-repositório>
cd sistema-integra-ubs
```

2. Instale as dependências:
```
pip install -r requirements.txt
```

3. Configure a variável de ambiente para o banco de dados:
```
export DATABASE_URL="postgresql://usuario:senha@localhost/nomedobanco"
```

4. Execute a aplicação:
```
gunicorn --bind 0.0.0.0:5000 main:app
```

## Acesso ao Sistema

Credenciais padrão para primeiro acesso:
- Usuário: admin
- Senha: 1234

## Estrutura do Projeto

- `app.py`: Configuração principal da aplicação Flask
- `main.py`: Ponto de entrada da aplicação
- `models.py`: Modelos de dados (SQLAlchemy)
- `routes.py`: Rotas da aplicação
- `relatorios.py`: Módulo de geração de relatórios
- `utils.py`: Funções utilitárias
- `importador.py`: Módulo para importação de medicamentos
- `static/`: Arquivos estáticos (CSS, JS, imagens)
- `templates/`: Templates HTML (Jinja2)

## Contato

Para mais informações ou suporte, entre em contato com a equipe de desenvolvimento.

---
© 2025 Sistema Integra UBS - Todos os direitos reservados