
# Carrega as configurações privadas do banco a partir do arquivo .env local.
from pathlib import Path
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
import os
import re
import hmac
from decimal import Decimal
import psycopg 

# Configura o Flask para servir a API e os arquivos do frontend.
load_dotenv(Path(__file__).parent / ".env")

PASTA_FRONTEND = Path(__file__).parent.parent / "cardápio.front"
app = Flask(__name__, static_folder=str(PASTA_FRONTEND), static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
TAXA_ENTREGA = Decimal("5.00")

# Abre uma conexão PostgreSQL usando variáveis de ambiente, sem senha fixa no código.
def conectar_banco():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "lancheria"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
    )


# Exige um token secreto para as rotas que consultam ou alteram dados administrativos.
def admin_required(funcao):
    @wraps(funcao)
    def verificar_token(*args, **kwargs):
        token_correto = os.getenv("ADMIN_TOKEN", "")
        token_enviado = request.headers.get("X-Admin-Token", "")
        if len(token_correto) < 32:
            return jsonify({"erro": "Configure um ADMIN_TOKEN forte no arquivo .env."}), 503
        if not hmac.compare_digest(token_enviado, token_correto):
            return jsonify({"erro": "Acesso administrativo não autorizado."}), 401
        return funcao(*args, **kwargs)
    return verificar_token


# Valida os dígitos do CPF no servidor para não depender somente do navegador.
def cpf_valido(cpf):
    numeros = re.sub(r"\D", "", str(cpf or ""))
    if len(numeros) != 11 or len(set(numeros)) == 1:
        return False

    soma = sum(int(numeros[indice]) * (10 - indice) for indice in range(9))
    primeiro = (soma * 10) % 11
    primeiro = 0 if primeiro == 10 else primeiro
    if primeiro != int(numeros[9]):
        return False

    soma = sum(int(numeros[indice]) * (11 - indice) for indice in range(10))
    segundo = (soma * 10) % 11
    segundo = 0 if segundo == 10 else segundo
    return segundo == int(numeros[10])


@app.route("/")
def inicio():
    # Entrega a página do cardápio para ela usar a mesma origem das chamadas à API.
    return send_from_directory(PASTA_FRONTEND, "index.html")


# Cadastra os dados de nome e telefone enviados pelo checkout.
@app.route("/clientes", methods=["POST"])
@admin_required
def adicionar_cliente():

    dados = request.json

    conexao = conectar_banco()

    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO clientes (nome, telefone)
        VALUES (%s, %s)
        RETURNING id, nome, telefone;
        """,
        (dados["nome"], dados["telefone"])
    )

    cliente = cursor.fetchone()

    conexao.commit()

    cursor.close()
    conexao.close()

    novo_cliente = {
        "id": cliente[0],
        "nome": cliente[1],
        "telefone": cliente[2]
    }

    return jsonify(novo_cliente)

# Lista os clientes para o checkout localizar alguém pelo telefone.
@app.route("/clientes")
@admin_required
def lista_clientes():

    conexao = conectar_banco()

    cursor = conexao.cursor()

    cursor.execute("SELECT id, nome, telefone FROM clientes;")

    clientes = cursor.fetchall()

    resultado = []

    for cliente in clientes:
        resultado.append({
            "id": cliente[0],
            "nome": cliente[1],
            "telefone": cliente[2]
        })

    cursor.close()
    conexao.close()

    return jsonify(resultado)


# Localiza só o cliente informado no checkout, sem enviar a lista inteira de telefones ao navegador.
@app.route("/clientes/buscar", methods=["POST"])
@admin_required
def buscar_cliente_por_telefone():
    dados = request.get_json(silent=True) or {}
    telefone = re.sub(r"\D", "", str(dados.get("telefone", "")))
    if len(telefone) < 10:
        return jsonify({"erro": "Informe um telefone válido"}), 400

    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nome, telefone
                FROM clientes
                WHERE regexp_replace(telefone, '[^0-9]', '', 'g') = %s
                LIMIT 2;
                """,
                (telefone,)
            )
            clientes_encontrados = cursor.fetchall()

    if not clientes_encontrados:
        return jsonify({"erro": "Cliente não encontrado"}), 404
    if len(clientes_encontrados) > 1:
        return jsonify({
            "erro": "Há mais de um cadastro com esse telefone. Corrija os clientes duplicados antes de continuar."
        }), 409

    cliente = clientes_encontrados[0]
    return jsonify({"id": cliente[0], "nome": cliente[1], "telefone": cliente[2]})

# Atualiza nome e telefone de um cliente pelo ID do banco.
@app.route("/clientes/<int:id>", methods=["PUT"])
@admin_required
def atualizar_cliente(id):

    dados = request.json

    conexao = conectar_banco()

    cursor = conexao.cursor()

    cursor.execute(
        """
        UPDATE clientes
        SET nome = %s, telefone = %s
        WHERE id = %s
        RETURNING id, nome, telefone;
        """,
        (dados["nome"], dados["telefone"], id)
    )

    cliente = cursor.fetchone()

    if cliente is None:
        cursor.close()
        conexao.close()

        return jsonify({"erro": "Cliente não encontrado"}), 404

    conexao.commit()

    cursor.close()
    conexao.close()

    cliente_atualizado = {
        "id": cliente[0],
        "nome": cliente[1],
        "telefone": cliente[2]
    }

    return jsonify(cliente_atualizado)


# Exclui o cliente se não houver pedidos ligados a ele no banco.
@app.route("/clientes/<int:id>", methods=["DELETE"])
@admin_required
def deletar_cliente(id):

    conexao = conectar_banco()

    cursor = conexao.cursor()

    cursor.execute(
        """
        DELETE FROM clientes
        WHERE id = %s
        RETURNING id, nome, telefone;
        """,
        (id,)
    )

    cliente = cursor.fetchone()

    if cliente is None:
        cursor.close()
        conexao.close()

        return jsonify({"erro": "Cliente não encontrado"}), 404

    conexao.commit()

    cursor.close()
    conexao.close()

    return jsonify({
        "mensagem": "Cliente excluído com sucesso",
        "cliente": {
            "id": cliente[0],
            "nome": cliente[1],
            "telefone": cliente[2]
        }
    })


# Lista os produtos que o frontend apresenta no cardápio.
@app.route("/produtos")
def lista_produtos():

    conexao = conectar_banco()

    cursor = conexao.cursor()

    cursor.execute("SELECT id, nome, preco FROM produtos;")

    produtos = cursor.fetchall()

    resultado = []

    for produto in produtos:
        resultado.append({
            "id": produto[0],
            "nome": produto[1],
            "preco": float(produto[2])
        })

    cursor.close()
    conexao.close()

    return jsonify(resultado)


# Cadastra um produto e devolve o ID criado pelo PostgreSQL.
@app.route("/produtos", methods=["POST"])
@admin_required
def adicionar_produto():

    dados = request.json

    conexao = conectar_banco()

    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO produtos (nome, preco)
        VALUES (%s, %s)
        RETURNING id, nome, preco;
        """,
        (dados["nome"], dados["preco"])
    )

    produto = cursor.fetchone()

    conexao.commit()

    cursor.close()
    conexao.close()

    novo_produto = {
        "id": produto[0],
        "nome": produto[1],
        "preco": float(produto[2])
    }

    return jsonify(novo_produto), 201


# Atualiza o nome e o preço de um produto pelo ID.
@app.route("/produtos/<int:id>", methods=["PUT"])
@admin_required
def atualizar_produto(id):

    dados = request.json

    conexao = conectar_banco()

    cursor = conexao.cursor()

    cursor.execute(
        """
        UPDATE produtos
        SET nome = %s, preco = %s
        WHERE id = %s
        RETURNING id, nome, preco;
        """,
        (dados["nome"], dados["preco"], id)
    )

    produto = cursor.fetchone()

    if produto is None:
        cursor.close()
        conexao.close()

        return jsonify({"erro": "Produto não encontrado"}), 404

    conexao.commit()

    cursor.close()
    conexao.close()

    produto_atualizado = {
        "id": produto[0],
        "nome": produto[1],
        "preco": float(produto[2])
    }

    return jsonify(produto_atualizado)


# Exclui um produto se nenhum pedido já gravado depender dele.
@app.route("/produtos/<int:id>", methods=["DELETE"])
@admin_required
def deletar_produto(id):

    conexao = conectar_banco()

    cursor = conexao.cursor()

    cursor.execute(
        """
        DELETE FROM produtos
        WHERE id = %s
        RETURNING id, nome, preco;
        """,
        (id,)
    )

    produto = cursor.fetchone()

    if produto is None:
        cursor.close()
        conexao.close()

        return jsonify({"erro": "Produto não encontrado"}), 404

    conexao.commit()

    cursor.close()
    conexao.close()

    return jsonify({
        "mensagem": "Produto excluído com sucesso",
        "produto": {
            "id": produto[0],
            "nome": produto[1],
            "preco": float(produto[2])
        }
    })


# Grava todos os dados do checkout e os itens numa única transação, incluindo a contagem do cliente.
@app.route("/pedidos", methods=["POST"])
def criar_pedido():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({"erro": "Envie os dados do pedido em JSON."}), 400

    # Confere os dados que identificam o cliente pelo número do WhatsApp.
    cliente_nome = str(dados.get("cliente_nome", "")).strip()
    telefone_cliente = re.sub(r"\D", "", str(dados.get("cliente_telefone", "")))
    itens = dados.get("itens")
    if len(cliente_nome) < 2 or len(cliente_nome) > 120:
        return jsonify({"erro": "Informe o nome completo do cliente."}), 400
    if not 10 <= len(telefone_cliente) <= 15:
        return jsonify({"erro": "Informe um WhatsApp válido com DDD."}), 400
    if not isinstance(itens, list) or not itens:
        return jsonify({"erro": "Adicione pelo menos um produto ao pedido."}), 400

    # Confere os dados pessoais, a modalidade e o método de pagamento.
    tipo_pedido = dados.get("tipo_pedido")
    cpf = re.sub(r"\D", "", str(dados.get("cpf", "")))
    pagamento = dados.get("pagamento")
    tipo_maquina = dados.get("tipo_maquina") or None
    if tipo_pedido not in ("Retirada", "Entrega"):
        return jsonify({"erro": "Escolha retirada ou entrega."}), 400
    if not cpf_valido(cpf):
        return jsonify({"erro": "Informe um CPF válido."}), 400
    if pagamento not in ("Dinheiro", "Na máquina"):
        return jsonify({"erro": "Escolha uma forma de pagamento válida."}), 400
    if pagamento == "Na máquina" and tipo_maquina not in ("Débito", "Crédito", "Pix"):
        return jsonify({"erro": "Escolha débito, crédito ou Pix."}), 400
    if pagamento == "Dinheiro":
        tipo_maquina = None

    # Pedidos para retirada não guardam campos de endereço; entregas exigem o endereço completo.
    endereco = {
        campo: str(dados.get(campo, "")).strip() or None
        for campo in ("rua", "numero", "bairro", "cidade", "cep", "complemento")
    }
    if tipo_pedido == "Entrega":
        campos_endereco = ("rua", "numero", "bairro", "cidade", "cep")
        if any(not endereco[campo] for campo in campos_endereco):
            return jsonify({"erro": "Preencha todos os campos obrigatórios do endereço."}), 400
        if not re.fullmatch(r"\d{5}-?\d{3}", endereco["cep"]):
            return jsonify({"erro": "Informe um CEP válido."}), 400
    else:
        endereco = {campo: None for campo in endereco}

    # Valida quantidades e IDs para que o cliente não consiga gravar itens inválidos.
    for item in itens:
        if not isinstance(item, dict):
            return jsonify({"erro": "Há um item inválido no pedido."}), 400
        produto_id = item.get("produto_id")
        quantidade = item.get("quantidade")
        if (not isinstance(produto_id, int) or isinstance(produto_id, bool) or produto_id <= 0
                or not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade <= 0):
            return jsonify({"erro": "Cada item precisa ter produto e quantidade válidos."}), 400

    taxa_entrega = TAXA_ENTREGA if tipo_pedido == "Entrega" else Decimal("0.00")
    subtotal = Decimal("0.00")

    try:
        # O bloqueio por telefone evita criar dois clientes se chegarem pedidos ao mesmo tempo.
        with conectar_banco() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0));",
                    (telefone_cliente,)
                )
                cursor.execute(
                    """
                    SELECT id, nome, telefone
                    FROM clientes
                    WHERE regexp_replace(telefone, '[^0-9]', '', 'g') = %s
                    LIMIT 2
                    FOR UPDATE;
                    """,
                    (telefone_cliente,)
                )
                clientes_encontrados = cursor.fetchall()
                if len(clientes_encontrados) > 1:
                    return jsonify({
                        "erro": "Há cadastros duplicados com esse WhatsApp. Corrija os clientes antes de continuar."
                    }), 409

                # Reutiliza o cadastro existente ou cria um novo com o telefone normalizado.
                if clientes_encontrados:
                    cliente = clientes_encontrados[0]
                    cliente_id = cliente[0]
                    cursor.execute(
                        "UPDATE clientes SET nome = %s, telefone = %s WHERE id = %s;",
                        (cliente_nome, telefone_cliente, cliente_id)
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO clientes (nome, telefone)
                        VALUES (%s, %s)
                        RETURNING id, nome, telefone;
                        """,
                        (cliente_nome, telefone_cliente)
                    )
                    cliente = cursor.fetchone()
                    cliente_id = cliente[0]

                # Conta somente pedidos já finalizados antes do novo pedido.
                cursor.execute("SELECT COUNT(*) FROM pedidos WHERE cliente_id = %s;", (cliente_id,))
                pedidos_anteriores = cursor.fetchone()[0]
                numero_pedido_cliente = pedidos_anteriores + 1

                # Lê preços do banco e soma os valores reais usados no registro.
                produtos_pedido = []
                for item in itens:
                    cursor.execute("SELECT nome, preco FROM produtos WHERE id = %s;", (item["produto_id"],))
                    produto = cursor.fetchone()
                    if produto is None:
                        raise ValueError("Um dos produtos selecionados não existe mais no cardápio.")
                    nome_produto, preco_unitario = produto
                    quantidade = item["quantidade"]
                    subtotal += preco_unitario * quantidade
                    produtos_pedido.append((item["produto_id"], nome_produto, quantidade, preco_unitario))

                total = subtotal + taxa_entrega
                cursor.execute(
                    """
                    INSERT INTO pedidos (
                        cliente_id, cliente_nome, cliente_telefone, tipo_pedido,
                        rua, numero, bairro, cidade, cep, complemento, cpf,
                        pagamento, tipo_maquina, taxa_entrega, total
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        cliente_id, cliente_nome, telefone_cliente, tipo_pedido,
                        endereco["rua"], endereco["numero"], endereco["bairro"],
                        endereco["cidade"], endereco["cep"], endereco["complemento"],
                        cpf, pagamento, tipo_maquina, taxa_entrega, total
                    )
                )
                pedido_id = cursor.fetchone()[0]

                # Guarda quantidades e preços unitários como estavam no momento da compra.
                for produto_id, nome_produto, quantidade, preco_unitario in produtos_pedido:
                    cursor.execute(
                        """
                        INSERT INTO itens_pedido (pedido_id, produto_id, produto_nome, quantidade, preco_unitario)
                        VALUES (%s, %s, %s, %s, %s);
                        """,
                        (pedido_id, produto_id, nome_produto, quantidade, preco_unitario)
                    )

        # Devolve o número do pedido deste cliente para aparecer na mensagem do WhatsApp.
        return jsonify({
            "mensagem": "Pedido criado com sucesso",
            "pedido_id": pedido_id,
            "cliente_id": cliente_id,
            "telefone_cliente": telefone_cliente,
            "pedidos_anteriores": pedidos_anteriores,
            "numero_pedido_cliente": numero_pedido_cliente,
            "total_pedidos": numero_pedido_cliente,
            "subtotal": float(subtotal),
            "taxa_entrega": float(taxa_entrega),
            "total": float(total),
            "itens": [
                {
                    "produto_id": produto_id,
                    "nome": nome_produto,
                    "quantidade": quantidade,
                    "preco_unitario": float(preco_unitario),
                    "total_item": float(preco_unitario * quantidade)
                }
                for produto_id, nome_produto, quantidade, preco_unitario in produtos_pedido
            ]
        }), 201
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    except psycopg.Error:
        app.logger.exception("Falha ao salvar pedido no PostgreSQL")
        return jsonify({"erro": "Não foi possível salvar o pedido no banco de dados."}), 500

if __name__ == "__main__":
    # Mantém o servidor preso ao notebook e a depuração desligada por padrão.
    app.run(host="127.0.0.1", port=5000, debug=os.getenv("FLASK_DEBUG", "0") == "1")
