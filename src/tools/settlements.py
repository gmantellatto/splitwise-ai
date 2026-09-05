"""
tools/settlements.py — Algoritmo de simplificação de dívidas (min-cash-flow).

Este arquivo é implementado pelo tutor — o algoritmo de grafo
não é conceito do CCDV-F. O que importa é como a tool é
definida e como o resultado é retornado para Claude.
"""

from src.storage import db


def otimizar_liquidacoes(group_id: str) -> dict:
    """
    Calcula o conjunto mínimo de transações para liquidar todas as dívidas.

    Algoritmo: min-cash-flow
    1. Calcula o saldo líquido de cada participante (quanto recebe - quanto deve)
    2. Resolve recursivamente emparelhando o maior credor com o maior devedor
    """
    group = db.get_group(group_id)
    if not group:
        return {"error": f"Grupo '{group_id}' não encontrado."}

    if not group.expenses:
        return {"transactions": [], "message": "Nenhuma despesa registrada ainda."}

    # Passo 1: calcular saldo líquido de cada participante
    balances: dict[str, float] = {p: 0.0 for p in group.participants}

    for expense in group.expenses:
        share = expense.amount / len(expense.split_among)
        balances[expense.paid_by] += expense.amount
        for person in expense.split_among:
            balances[person] -= share

    # Arredondar para evitar floating point noise
    balances = {k: round(v, 2) for k, v in balances.items()}

    # Passo 2: min-cash-flow recursivo
    transactions = []

    def settle(bal: dict[str, float]) -> None:
        creditors = sorted(
            [(p, v) for p, v in bal.items() if v > 0.001],
            key=lambda x: -x[1]
        )
        debtors = sorted(
            [(p, v) for p, v in bal.items() if v < -0.001],
            key=lambda x: x[1]
        )

        if not creditors or not debtors:
            return

        creditor, credit = creditors[0]
        debtor, debt = debtors[0]

        amount = round(min(credit, -debt), 2)
        transactions.append({
            "from": debtor,
            "to": creditor,
            "amount": amount
        })

        bal[creditor] = round(credit - amount, 2)
        bal[debtor] = round(debt + amount, 2)
        settle(bal)

    settle(dict(balances))

    return {
        "transactions": transactions,
        "total_transactions": len(transactions),
        "balances": balances
    }


def calcular_saldos(group_id: str) -> dict:
    """Retorna o saldo líquido de cada participante sem otimizar."""
    group = db.get_group(group_id)
    if not group:
        return {"error": f"Grupo '{group_id}' não encontrado."}

    balances: dict[str, float] = {p: 0.0 for p in group.participants}

    for expense in group.expenses:
        if not expense.split_among:
            continue
        share = expense.amount / len(expense.split_among)
        balances[expense.paid_by] = round(balances[expense.paid_by] + expense.amount, 2)
        for person in expense.split_among:
            balances[person] = round(balances[person] - share, 2)

    summary = []
    for person, balance in balances.items():
        if balance > 0:
            status = f"deve receber R$ {balance:.2f}"
        elif balance < 0:
            status = f"deve pagar R$ {abs(balance):.2f}"
        else:
            status = "está quite"
        summary.append({"participant": person, "balance": balance, "status": status})

    return {"balances": summary}
