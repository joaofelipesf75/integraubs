# Instruções para Deploy no Heroku

## Configuração inicial

1. **Crie uma conta no Heroku** (se ainda não tiver)
   - Acesse https://signup.heroku.com/ e siga as instruções

2. **Instale o Heroku CLI**
   - Siga as instruções em: https://devcenter.heroku.com/articles/heroku-cli

3. **Faça login no Heroku CLI**
   ```
   heroku login
   ```

## Criando a aplicação no Heroku

1. **Crie uma nova aplicação**
   ```
   heroku create nome-da-sua-app
   ```
   Substitua "nome-da-sua-app" pelo nome que deseja dar à sua aplicação.

2. **Adicione o banco de dados PostgreSQL**
   ```
   heroku addons:create heroku-postgresql:mini
   ```
   Isso criará um banco de dados PostgreSQL no plano mais básico.

## Configurando as variáveis de ambiente

1. **Configure a chave secreta**
   ```
   heroku config:set SESSION_SECRET=uma_chave_secreta_aleatoria
   ```

2. **Verifique se o DATABASE_URL foi configurado automaticamente**
   ```
   heroku config
   ```
   Você deve ver a variável DATABASE_URL já configurada pelo add-on do PostgreSQL.

## Fazendo o deploy

### Opção 1: Deploy via Git

1. **Inicialize um repositório Git (se ainda não existir)**
   ```
   git init
   git add .
   git commit -m "Pronto para deploy"
   ```

2. **Adicione o remote do Heroku**
   ```
   heroku git:remote -a nome-da-sua-app
   ```

3. **Faça o push para o Heroku**
   ```
   git push heroku main
   ```
   ou se estiver na branch master:
   ```
   git push heroku master
   ```

### Opção 2: Deploy via Heroku Dashboard

1. **Conecte sua conta GitHub ao Heroku**
   - No dashboard do Heroku, vá para a aba "Deploy"
   - Escolha "GitHub" como método de deploy
   - Conecte sua conta GitHub e selecione o repositório

2. **Configure o deploy automático (opcional)**
   - Ative "Automatic Deploys" para fazer deploy a cada push no GitHub

3. **Faça o deploy manual**
   - Clique em "Deploy Branch"

## Inicializando o banco de dados

1. **Execute as migrações e criação inicial**
   ```
   heroku run python db_scripts.py
   ```

2. **Verifique os logs**
   ```
   heroku logs --tail
   ```

## Acessando a aplicação

1. **Abra a aplicação no navegador**
   ```
   heroku open
   ```
   ou acesse https://nome-da-sua-app.herokuapp.com

## Solução de problemas comuns

1. **Erro H10 (App crashed)**
   - Verifique os logs com `heroku logs --tail`
   - Certifique-se de que o Procfile está configurado corretamente
   - Verifique se todas as dependências estão instaladas

2. **Erro com banco de dados**
   - Verifique se a variável DATABASE_URL está configurada
   - Teste a conexão com o banco de dados usando `heroku pg:info`

3. **Erros de porta**
   - O Heroku define a porta automaticamente via variável de ambiente PORT
   - Certifique-se de que sua aplicação está usando `os.environ.get("PORT", 5000)`

## Recursos adicionais

- [Documentação oficial do Heroku para Python](https://devcenter.heroku.com/categories/python-support)
- [Guia de deploy de aplicações Flask](https://devcenter.heroku.com/articles/getting-started-with-python)