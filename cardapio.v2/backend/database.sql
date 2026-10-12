-- Cria os clientes usados para identificar quem fez cada pedido.
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    telefone TEXT NOT NULL
);

-- Guarda o nome e o preço atual de cada item do cardápio.
CREATE TABLE IF NOT EXISTS produtos (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    preco NUMERIC(10, 2) NOT NULL CHECK (preco >= 0)
);

-- Registra cada pedido associado a um cliente.
CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    cliente_nome TEXT NOT NULL,
    cliente_telefone TEXT NOT NULL,
    tipo_pedido TEXT NOT NULL CHECK (tipo_pedido IN ('Retirada', 'Entrega')),
    rua TEXT,
    numero TEXT,
    bairro TEXT,
    cidade TEXT,
    cep TEXT,
    complemento TEXT,
    cpf TEXT NOT NULL,
    pagamento TEXT NOT NULL CHECK (pagamento IN ('Dinheiro', 'Na máquina')),
    tipo_maquina TEXT,
    taxa_entrega NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (taxa_entrega >= 0),
    total NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (total >= 0),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Guarda os produtos e quantidades comprados, com o preço aplicado no pedido.
CREATE TABLE IF NOT EXISTS itens_pedido (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    produto_id INTEGER NOT NULL REFERENCES produtos(id),
    produto_nome TEXT NOT NULL,
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario NUMERIC(10, 2) NOT NULL CHECK (preco_unitario >= 0)
);

-- Insere os produtos iniciais só quando o mesmo nome ainda não existe.
INSERT INTO produtos (nome, preco)
SELECT dados.nome, dados.preco
FROM (VALUES
    ('X-Burger', 25.90),
    ('X-Bacon', 18.00),
    ('X-Salada', 16.00),
    ('X-Tudo', 25.00),
    ('Batata Frita', 15.00),
    ('Batata Frita c/ Cheddar', 20.00),
    ('Coca-Cola 2l', 12.00),
    ('Coca-Cola 2l zero', 12.00),
    ('Coca-Cola 350ml', 5.00),
    ('Guaraná Antartica 2l', 12.00),
    ('Fruki guaraná 2L', 10.00),
    ('Fruki guaraná 350 ml', 4.00)
) AS dados(nome, preco)
WHERE NOT EXISTS (
    SELECT 1 FROM produtos AS existentes WHERE LOWER(existentes.nome) = LOWER(dados.nome)
);
