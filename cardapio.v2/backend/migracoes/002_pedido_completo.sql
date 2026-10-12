-- Acrescenta aos pedidos existentes os dados do checkout sem apagar os registros antigos.
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS cliente_nome TEXT;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS cliente_telefone TEXT;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS tipo_pedido TEXT;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS rua TEXT;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS numero TEXT;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS bairro TEXT;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS cidade TEXT;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS cep TEXT;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS complemento TEXT;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS cpf TEXT;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS pagamento TEXT;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS tipo_maquina TEXT;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS taxa_entrega NUMERIC(10, 2) NOT NULL DEFAULT 0;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS total NUMERIC(10, 2) NOT NULL DEFAULT 0;
ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Salva o nome comercial do item para preservar o histórico se o catálogo mudar.
ALTER TABLE itens_pedido ADD COLUMN IF NOT EXISTS produto_nome TEXT;
UPDATE itens_pedido AS item
SET produto_nome = produto.nome
FROM produtos AS produto
WHERE item.produto_id = produto.id AND item.produto_nome IS NULL;

-- Acelera a identificação do cliente pelo telefone, ignorando pontuação e espaços.
CREATE INDEX IF NOT EXISTS idx_clientes_telefone_normalizado
ON clientes (regexp_replace(telefone, '[^0-9]', '', 'g'));

-- Acelera a contagem de pedidos já feitos por cada cliente.
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente_id ON pedidos (cliente_id);
