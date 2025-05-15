# Sistema Integra UBS - Implantação no Render

## Configuração para Implantação no Render

O Sistema Integra UBS foi adaptado para ser implantado no Render, usando um banco de dados PostgreSQL em vez do SQLite local.

### Arquivos de Configuração

1. **Procfile**: Define como o Render deve executar a aplicação.
2. **render.yaml**: Configuração completa dos serviços e banco de dados.
3. **requirements_render.txt**: Dependências necessárias para o projeto.

### Etapas para Implantação

1. Crie uma conta no [Render](https://render.com/) se ainda não tiver.

2. No painel do Render, selecione "New" e depois "Blueprint".

3. Conecte seu repositório do GitHub onde está o código do projeto.

4. O Render detectará automaticamente o arquivo `render.yaml` e configurará os serviços.

5. Confirme e aguarde a implantação.

### Variáveis de Ambiente

A configuração já define automaticamente as seguintes variáveis:

- `DATABASE_URL`: Configurada automaticamente pela configuração do Render.
- `SESSION_SECRET`: Gerada automaticamente para proteger sessões.

### Banco de Dados

Um banco de dados PostgreSQL será automaticamente criado e configurado.

O banco de dados local (SQLite) não é mais utilizado em produção, pois o Render apaga arquivos locais após cada implantação.

### Comandos Úteis

Se precisar executar migrações ou outros comandos, use o Shell do Render:

1. No painel do seu serviço web no Render, vá para a aba "Shell".
2. Execute comandos como:
   ```
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

### Desenvolvimento Local

Para desenvolvimento local, você ainda pode usar SQLite:

1. Execute a aplicação sem definir a variável `DATABASE_URL`
2. O aplicativo usará automaticamente SQLite conforme a configuração em `app.py`

### Testando a Conexão

Para verificar se a conexão com o PostgreSQL está funcionando, a aplicação registrará isso nos logs:
- "Usando banco de dados remoto PostgreSQL" quando estiver conectado ao PostgreSQL.
- "Variável DATABASE_URL não encontrada, usando SQLite local" quando estiver em modo de desenvolvimento.