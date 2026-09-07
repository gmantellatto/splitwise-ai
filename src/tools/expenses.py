import uuid
from datetime import datetime, timezone

from src.storage import db
from src.models import Expense

def _normalizar_participante(participant: str) -> str:
    return participant.strip().title()


def adicionar_despesa(
    group_id: str,
    description: str,
    amount: float,
    paid_by: str,
    split_among: list[str]
) -> dict:
    grupo = db.get_group(group_id)
    
    if (grupo is None):
        return {"error": "Grupo não encontrado."}

    if (amount <= 0):
        return {"error": "Valor da despesa deve ser maior que zero."}

    paid_by = _normalizar_participante(paid_by)

    if (paid_by not in grupo.participants):
        return {"error": "Pagante não está presente no grupo."}

    if (len(split_among) == 0):
        return {"error": "A lista de participantes que dividirão a despesa não pode ser vazia."}

    split_among = [_normalizar_participante(nome) for nome in split_among]

    if (not all(p in grupo.participants for p in split_among)):
        return {"error": "Todos os participantes da despesa devem estar presentar no grupo."}

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

    return  {
        "expense_id": despesa.id, 
        "description": description, 
        "amount": amount, 
        "paid_by": paid_by,
        "split_among": split_among,
        "message": "Despesa criada com sucesso!"
    }
        


def listar_despesas(group_id: str) -> dict:
    grupo = db.get_group(group_id)
        
    if (grupo is None):
        return {"error": "Grupo não encontrado."}

    if (len(grupo.expenses) == 0):
        return {"message": f"O grupo '{grupo.name}' não possui despesas cadastradas."}

    total = sum(e.amount for e in grupo.expenses)
    return {
        "expenses": [e.model_dump() for e in grupo.expenses],
        "total": total,
        "message": f"{len(grupo.expenses)} despesa(s), total R$ {total:.2f}"
    }
