"""
storage/undo.py — Undo stack em memória por grupo.

Cada operação modificadora salva o estado anterior do grupo
antes de fazer qualquer alteração. desfazer_operacao restaura
o último estado salvo.

Limites:
  - Máximo de 10 snapshots por grupo (evita crescimento ilimitado)
  - Reseta quando o servidor reinicia (memória, não disco)
"""

from src.models import Group

# Estrutura: { group_id: [estado_mais_antigo, ..., estado_mais_recente] }
_UNDO_STACK: dict[str, list[dict]] = {}

MAX_UNDO_DEPTH = 10


def save_state(group: Group) -> None:
    """Salva snapshot do grupo ANTES de modificá-lo."""
    stack = _UNDO_STACK.setdefault(group.id, [])
    stack.append(group.model_dump())
    if len(stack) > MAX_UNDO_DEPTH:
        stack.pop(0)  # descarta o mais antigo


def pop_state(group_id: str) -> dict | None:
    """
    Retira e retorna o snapshot mais recente do grupo.
    Retorna None se não há estado para desfazer.
    """
    stack = _UNDO_STACK.get(group_id, [])
    if not stack:
        return None
    return stack.pop()


def peek_depth(group_id: str) -> int:
    """Quantas operações ainda podem ser desfeitas."""
    return len(_UNDO_STACK.get(group_id, []))
