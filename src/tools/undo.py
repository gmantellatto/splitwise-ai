"""
tools/undo.py — Tool para desfazer a última operação de um grupo.

Como funciona:
  Cada tool modificadora chama save_state(grupo) antes de alterar os dados.
  desfazer_operacao restaura o snapshot mais recente do stack.

Limitações esperadas pelo usuário:
  - Reseta quando o servidor reinicia (stack em memória)
  - Máximo de 10 desfazimentos por grupo
"""

from src.storage import db
from src.storage.undo import pop_state, peek_depth
from src.models import Group


def desfazer_operacao(group_id: str) -> dict:
    """
    Reverte o grupo ao estado anterior à última operação modificadora.
    Funciona para: adicionar/remover participante, renomear participante,
    adicionar/editar/remover despesa.
    """
    grupo_atual = db.get_group(group_id)
    if grupo_atual is None:
        return {"error": "Grupo não encontrado."}

    snapshot = pop_state(group_id)
    if snapshot is None:
        return {
            "error": (
                "Não há operações para desfazer neste grupo. "
                "O histórico é reiniciado quando o servidor é reiniciado."
            )
        }

    grupo_restaurado = Group.model_validate(snapshot)
    db.save_group(grupo_restaurado)

    restantes = peek_depth(group_id)

    return {
        "message": f"Última operação desfeita no grupo '{grupo_restaurado.name}'.",
        "group_name": grupo_restaurado.name,
        "participants": grupo_restaurado.participants,
        "total_expenses": len(grupo_restaurado.expenses),
        "undo_remaining": restantes,
    }
