# Machado Burger — Cardápio V2

Aplicação local de cardápio com Flask, PostgreSQL e envio de pedidos pelo WhatsApp. O catálogo e os pedidos são lidos e gravados no banco.

## Arquivos principais

- `backend/app.py`: rotas Flask, operações CRUD e conexão PostgreSQL.
- `backend/database.sql`: tabelas e catálogo inicial, sem repetir produtos já existentes.
- `backend/migrar_banco.py`: aplica a atualização do banco existente.
- `backend/migracoes/002_pedido_completo.sql`: campos adicionais e índices dos pedidos.
- `backend/.env.example`: modelo das configurações privadas.
- `cardápio.front/index.html`: estrutura do cardápio e formulário.
- `cardápio.front/style.css`: apresentação visual e adaptação para celular.
- `cardápio.front/script.js`: carrinho, validações, consulta à API e checkout.

## Preparar o ambiente

1. Instale PostgreSQL e crie o banco `lancheria`.
2. Abra o SQL Shell (psql), conecte ao banco `lancheria` e execute o conteúdo de `backend/database.sql` se o banco for novo. Para a instalação que já existe, rode uma vez `py migrar_banco.py` dentro da pasta `backend` para acrescentar os novos campos aos pedidos.
3. Mantenha `backend/.env` fora do Git, preencha a senha do PostgreSQL e configure `ADMIN_TOKEN` com um valor aleatório de pelo menos 32 caracteres. O `.env` está ignorado pelo Git; o OneDrive ainda pode sincronizá-lo.
4. No PowerShell, entre na pasta `backend` e instale as dependências:

```powershell
# Instala Flask, Psycopg e o carregador do arquivo .env.
py -m pip install -r requirements.txt
```

5. Inicie o servidor:

```powershell
# Inicia a aplicação Flask local.
py app.py
```

6. Abra `http://127.0.0.1:5000/` no navegador. Não abra o `index.html` diretamente pelo explorador de arquivos.

Para gerar um token administrativo aleatório no PowerShell:

```powershell
# Gera um token forte; copie o resultado para ADMIN_TOKEN no arquivo .env.
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Fluxo do pedido

O cliente escolhe os produtos, informa nome, telefone, CPF, tipo de recebimento e pagamento. O checkout procura o cliente pelo telefone, grava cliente (se necessário) e pedido/itens no PostgreSQL e abre uma mensagem preenchida para o número configurado em `script.js`. A pessoa ainda precisa confirmar o envio dentro do WhatsApp.

Para trocar o WhatsApp que recebe os pedidos, altere a constante `telefoneLancheria` em `cardápio.front/script.js`, usando código do país e DDD, sem `+`, espaços ou traços.

Cada pedido novo guarda uma cópia do nome e telefone do cliente, modalidade (retirada/entrega), endereço, CPF, forma de pagamento, taxa, total e os itens com nomes e preços aplicados. O telefone é normalizado para reconhecer o mesmo cliente mesmo se ele digitar espaços, parênteses ou hífen. A mensagem informa o ID do cliente, quantos pedidos ele já tinha e o número deste pedido na loja. Pedidos antigos continuam no banco; os detalhes que não eram armazenados anteriormente não podem ser reconstruídos, então os campos novos ficam vazios ou zerados neles. A busca e o cadastro do cliente acontecem dentro do backend, sem expor a lista de clientes ao navegador.

## Rotas da API

- `GET /clientes`, `POST /clientes`, `POST /clientes/buscar`, `PUT /clientes/<id>` e `DELETE /clientes/<id>`: rotas administrativas que exigem o cabeçalho `X-Admin-Token`.
- `GET /produtos`: lista pública usada pelo cardápio.
- `POST /produtos`, `PUT /produtos/<id>` e `DELETE /produtos/<id>`: rotas administrativas que exigem `X-Admin-Token`.
- `POST /pedidos`: salva o pedido e identifica o cliente pelo telefone informado no checkout.

O servidor Flask integrado é para desenvolvimento local e fica ligado somente ao notebook. Antes de publicar, configure HTTPS, servidor WSGI de produção, limitação de tentativas e proteção contra pedidos automatizados. As rotas administrativas exigem token e o navegador público não recebe a lista de clientes.
