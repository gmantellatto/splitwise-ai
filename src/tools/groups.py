import uuid
from datetime import datetime, timezone

from src.storage import db
from src.storage.undo import save_state, peek_depth
from src.models import Group


def _normalizar_participante(participant: str) -> str:
    return participant.strip().title()


# ── Criar / adicionar ────────────────────────────────────────────────────────

def criar_grupo(name: str, participants: list[str]) -> dict:
    if len(participants) < 2:
        return {"error": "O novo grupo precisa ter no mínimo 2 participantes."}

    normalized_participants = [_normalizar_participante(nome) for nome in participants]

    if len(normalized_participants) != len(set(normalized_participants)):
        return {"error": "Participantes do grupo não podem ter o mesmo nome."}

    grupo = Group(
        id=str(uuid.uuid4()),
        name=name,
        participants=normalized_participants,
        expenses=[],
        created_at=datetime.now(timezone.utc).isoformat()
    )
    db.save_group(grupo)

    return {
        "group_id": grupo.id,
        "name": grupo.name,
        "participants": grupo.participants,
        "message": "Grupo criado com sucesso!"
    }


def adicionar_participante(group_id: str, participant: str) -> dict:
    grupo = db.get_group(group_id)
    if grupo is None:
        return {"error": "Grupo não encontrado."}

    participante = _normalizar_participante(participant)
    if participante in grupo.participants:
        return {"error": f"Já existe um participante '{participante}' no grupo '{grupo.name}'."}

    save_state(grupo)
    grupo.participants.append(participante)
    db.save_group(grupo)

    return {
        "message": f"'{participante}' adicionado ao grupo '{grupo.name}'.",
        "participants": grupo.participants,
        "undo_available": True,
    }


# ── Remover / renomear participante ─────────────────────────────────────────

def remover_participante(group_id: str, participant: str) -> dict:
    """
    Remove um participante do grupo.
    Falha se o participante estiver em qualquer despesa registrada —
    o usuário deve remover ou editar as despesas antes.
    """
    grupo = db.get_group(group_id)
    if grupo is None:
        return {"error": "Grupo não encontrado."}

    participante = _normalizar_participante(participant)
    if participante not in grupo.participants:
        return {"error": f"Participante '{participante}' não encontrado no grupo '{grupo.name}'."}

    # Verifica se está envolvido em alguma despesa
    despesas_envolvidas = [
        e.description
        for e in grupo.expenses
        if e.paid_by == participante or participante in e.split_among
    ]
    if despesas_envolvidas:
        lista = ", ".join(f"'{d}'" for d in despesas_envolvidas)
        return {
            "error": (
                f"'{participante}' está envolvido em {len(despesas_envolvidas)} despesa(s): {lista}. "
                "Remova ou edite essas despesas antes de remover o participante."
            )
        }

    save_state(grupo)
    grupo.participants.remove(participante)
    db.save_group(grupo)

    return {
        "message": f"'{participante}' removido do grupo '{grupo.name}'.",
        "participants": grupo.participants,
        "undo_available": True,
    }


def renomear_participante(group_id: str, old_name: str, new_name: str) -> dict:
    """
    Renomeia um participante em todo o grupo (lista de membros + todas as despesas).
    Útil para corrigir erros de digitação.
    """
    grupo = db.get_group(group_id)
    if grupo is None:
        return {"error": "Grupo não encontrado."}

    antigo = _normalizar_participante(old_name)
    novo   = _normalizar_participante(new_name)

    if antigo not in grupo.participants:
        return {"error": f"Participante '{antigo}' não encontrado no grupo '{grupo.name}'."}

    if novo in grupo.participants:
        return {"error": f"Já existe um participante chamado '{novo}' no grupo '{grupo.name}'."}

    save_state(grupo)

    # Atualiza lista de membros
    idx = grupo.participants.index(antigo)
    grupo.participants[idx] = novo

    # Atualiza todas as despesas
    despesas_atualizadas = 0
    for expense in grupo.expenses:
        changed = False
        if expense.paid_by == antigo:
            expense.paid_by = novo
            changed = True
        if antigo in expense.split_among:
            expense.split_among = [novo if p == antigo else p for p in expense.split_among]
            changed = True
        if changed:
            despesas_atualizadas += 1

    db.save_group(grupo)

    return {
        "message": f"'{antigo}' renomeado para '{novo}' em {despesas_atualizadas} despesa(s).",
        "participants": grupo.participants,
        "undo_available": True,
    }


# ── Listar / detalhes ────────────────────────────────────────────────────────

def listar_grupos() -> dict:
    """Retorna todos os grupos existentes com seus participantes."""
    grupos = db.get_all_groups()
    if not grupos:
        return {"message": "Nenhum grupo cadastrado ainda.", "groups": []}

    return {
        "groups": [
            {
                "group_id": g.id,
                "name": g.name,
                "participants": g.participants,
                "total_expenses": len(g.expenses),
                "created_at": g.created_at,
            }
            for g in grupos.values()
        ],
        "total": len(grupos),
    }


def obter_detalhes_grupo(group_id: str) -> dict:
    """Retorna informações completas do grupo: membros, número de despesas e operações desfeitas disponíveis."""
    grupo = db.get_group(group_id)
    if grupo is None:
        return {"error": "Grupo não encontrado."}

    total_gasto = sum(e.amount for e in grupo.expenses)

    return {
        "group_id": grupo.id,
        "name": grupo.name,
        "participants": grupo.participants,
        "total_participants": len(grupo.participants),
        "total_expenses": len(grupo.expenses),
        "total_spent": round(total_gasto, 2),
        "created_at": grupo.created_at,
        "undo_depth": peek_depth(grupo.id),
    }
