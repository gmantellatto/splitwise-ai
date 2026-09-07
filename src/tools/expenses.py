import uuid
from datetime import datetime, timezone
from typing import Optional

from src.storage import db
from src.storage.undo import save_state
from src.models import Expense


def _normalizar_participante(participant: str) -> str:
    return participant.strip().title()


# ── Adicionar / listar ───────────────────────────────────────────────────────

def adicionar_despesa(
    group_id: str,
    description: str,
    amount: float,
    paid_by: str,
    split_among: list[str]
) -> dict:
    grupo = db.get_group(group_id)
    if grupo is None:
        return {"error": "Grupo não encontrado."}

    if amount <= 0:
        return {"error": "Valor da despesa deve ser maior que zero."}

    paid_by = _normalizar_participante(paid_by)
    if paid_by not in grupo.participants:
        return {"error": f"Pagante '{paid_by}' não está presente no grupo."}

    if not split_among:
        return {"error": "A lista de participantes que dividirão a despesa não pode ser vazia."}

    split_among = [_normalizar_participante(nome) for nome in split_among]
    invalidos = [p for p in split_among if p not in grupo.participants]
    if invalidos:
        return {"error": f"Participantes não encontrados no grupo: {', '.join(invalidos)}."}

    save_state(grupo)

    despesa = Expense(
        id=str(uuid.uuid4()),
        description=description,
        amount=amount,
        paid_by=paid_by,
        split_among=split_among,
        created_at=datetime.now(timezone.utc).isoformat()
    )

    grupo.expenses.append(despesa)
    db.save_group(grupo)

    return {
        "expense_id": despesa.id,
        "description": description,
        "amount": amount,
        "paid_by": paid_by,
        "split_among": split_among,
        "message": "Despesa criada com sucesso!",
        "undo_available": True,
    }


def listar_despesas(group_id: str) -> dict:
    grupo = db.get_group(group_id)
    if grupo is None:
        return {"error": "Grupo não encontrado."}

    if not grupo.expenses:
        return {"message": f"O grupo '{grupo.name}' não possui despesas cadastradas."}

    total = sum(e.amount for e in grupo.expenses)
    return {
        "expenses": [e.model_dump() for e in grupo.expenses],
        "total": total,
        "message": f"{len(grupo.expenses)} despesa(s), total R$ {total:.2f}"
    }


# ── Editar / remover ─────────────────────────────────────────────────────────

def editar_despesa(
    group_id: str,
    expense_id: str,
    description: Optional[str] = None,
    amount: Optional[float] = None,
    paid_by: Optional[str] = None,
    split_among: Optional[list[str]] = None,
) -> dict:
    """
    Edita uma despesa já registrada. Apenas os campos enviados são alterados —
    os demais permanecem inalterados.
    """
    grupo = db.get_group(group_id)
    if grupo is None:
        return {"error": "Grupo não encontrado."}

    despesa = next((e for e in grupo.expenses if e.id == expense_id), None)
    if despesa is None:
        return {"error": f"Despesa '{expense_id}' não encontrada no grupo."}

    # Validações antes de salvar estado
    if amount is not None and amount <= 0:
        return {"error": "Valor da despesa deve ser maior que zero."}

    if paid_by is not None:
        paid_by = _normalizar_participante(paid_by)
        if paid_by not in grupo.participants:
            return {"error": f"Pagante '{paid_by}' não está presente no grupo."}

    if split_among is not None:
        if not split_among:
            return {"error": "A lista de participantes que dividirão a despesa não pode ser vazia."}
        split_among = [_normalizar_participante(nome) for nome in split_among]
        invalidos = [p for p in split_among if p not in grupo.participants]
        if invalidos:
            return {"error": f"Participantes não encontrados no grupo: {', '.join(invalidos)}."}

    save_state(grupo)

    # Aplica apenas os campos fornecidos
    campos_alterados = []
    if description is not None:
        despesa.description = description
        campos_alterados.append("descrição")
    if amount is not None:
        despesa.amount = amount
        campos_alterados.append("valor")
    if paid_by is not None:
        despesa.paid_by = paid_by
        campos_alterados.append("pagante")
    if split_among is not None:
        despesa.split_among = split_among
        campos_alterados.append("divisão")

    db.save_group(grupo)

    return {
        "expense_id": despesa.id,
        "description": despesa.description,
        "amount": despesa.amount,
        "paid_by": despesa.paid_by,
        "split_among": despesa.split_among,
        "fields_updated": campos_alterados,
        "message": f"Despesa atualizada: {', '.join(campos_alterados)}.",
        "undo_available": True,
    }


def remover_despesa(group_id: str, expense_id: str) -> dict:
    """Remove uma despesa do grupo pelo seu ID."""
    grupo = db.get_group(group_id)
    if grupo is None:
        return {"error": "Grupo não encontrado."}

    despesa = next((e for e in grupo.expenses if e.id == expense_id), None)
    if despesa is None:
        return {"error": f"Despesa '{expense_id}' não encontrada no grupo."}

    save_state(grupo)
    grupo.expenses = [e for e in grupo.expenses if e.id != expense_id]
    db.save_group(grupo)

    return {
        "message": f"Despesa '{despesa.description}' (R$ {despesa.amount:.2f}) removida com sucesso.",
        "undo_available": True,
    }
