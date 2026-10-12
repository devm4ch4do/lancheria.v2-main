"""Aplica a migração aditiva que armazena os dados completos dos pedidos."""

from pathlib import Path

from app import conectar_banco


# Localiza o arquivo SQL ao lado deste script para que o comando funcione dentro de backend.
ARQUIVO_MIGRACAO = Path(__file__).parent / "migracoes" / "002_pedido_completo.sql"


# Executa a migração como uma transação; se houver erro, o PostgreSQL desfaz as alterações.
def main():
    sql = ARQUIVO_MIGRACAO.read_text(encoding="utf-8")
    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            # Executa cada comando separado para funcionar com o protocolo padrão do Psycopg.
            for comando in sql.split(";"):
                if comando.strip():
                    cursor.execute(comando)
    print("Migração concluída. Os campos novos dos pedidos já estão disponíveis.")


# Só aplica alterações ao banco quando o usuário executa este arquivo diretamente.
if __name__ == "__main__":
    main()
