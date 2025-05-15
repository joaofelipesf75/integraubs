# Sistema Integra UBS - Guia de Instalação

## Requisitos

- Python 3.8 ou superior
- PostgreSQL (para implantação em produção) ou SQLite (para uso local)
- Pip (gerenciador de pacotes Python)

## Instalação Local

1. **Clone ou descompacte o arquivo do projeto**
   ```
   unzip sistema_integra_ubs.zip
   cd sistema_integra_ubs
   ```

2. **Crie um ambiente virtual (recomendado)**
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Instale as dependências**
   ```
   pip install -r requirements.txt
   ```

4. **Configure o banco de dados**
   
   - SQLite (desenvolvimento local):
     Não é necessária configuração adicional. O SQLite será usado automaticamente.
   
   - PostgreSQL (produção):
     Crie um banco de dados PostgreSQL e defina a variável de ambiente:
     ```
     export DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco
     ```

5. **Execute a aplicação**
   ```
   python main.py
   ```
   A aplicação estará disponível em http://localhost:5000

## Implantação em Produção com Render

1. **Crie uma conta no Render** (https://render.com)

2. **Crie um novo serviço Web**
   - Conecte seu repositório Git ou faça upload do código
   - Selecione "Python" como ambiente
   - Configure o build command: `pip install -r requirements_render.txt`
   - Configure o start command: `sh start.sh`
   
   **Nota importante**: Se encontrar erro de conflito de metaclasse durante o deploy, verifique o arquivo ATUALIZACAO_DEPLOY.md para instruções detalhadas sobre como resolver.

3. **Configure o banco de dados**
   - Crie um novo banco de dados PostgreSQL no Render
   - As variáveis de ambiente serão configuradas automaticamente

4. **Configure outras variáveis de ambiente necessárias**
   - SESSION_SECRET: uma chave secreta para sessões Flask
   - FLASK_SECRET_KEY: uma chave secreta para o Flask

5. **Implante o aplicativo**
   - A implantação será iniciada automaticamente
   - O processo pode levar alguns minutos

## Usuários Padrão

Após a instalação, o sistema cria automaticamente os seguintes usuários:

- **Administrador**:
  - Usuário: admin
  - Senha: 1234

- **Médico**:
  - Usuário: medico
  - Senha: 1234

- **Farmacêutico**:
  - Usuário: farmaceutico
  - Senha: 1234

- **Enfermeiro**:
  - Usuário: enfermeiro
  - Senha: 1234

- **Recepcionista**:
  - Usuário: recepcionista
  - Senha: 1234

## Solução de Problemas

1. **Erro ao conectar ao banco de dados**
   - Verifique se a variável DATABASE_URL está configurada corretamente
   - Confirme se o banco de dados PostgreSQL está em execução
   - Verifique as credenciais de acesso

2. **Erro ao iniciar o servidor**
   - Certifique-se de que a porta 5000 não está sendo usada por outro processo
   - Verifique os logs de erro para mais detalhes

3. **Problema com dependências**
   - Execute `pip install -r requirements.txt` novamente
   - Verifique se todas as dependências foram instaladas corretamente