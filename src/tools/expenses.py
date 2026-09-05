"""
tools/expenses.py — Implementações das tools de despesa.

╔══════════════════════════════════════════════════════════════════╗
║  VOCÊ VAI ESCREVER ESTE ARQUIVO                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import uuid
from datetime import datetime, timezone

from src.storage import db
from src.models import Expense


def adicionar_despesa(
    group_id: str,
    description: str,
    amount: float,
    paid_by: str,
    split_among: list[str]
) -> dict:
    """
    TODO: Implemente esta função.

    Deve validar:
    - Grupo existe
    - amount > 0  (pegadinha: e se vier negativo? e se vier zero?)
    - paid_by está na lista de participantes do grupo
    - Todos em split_among estão na lista de participantes
    - split_among não pode ser vazio

    Deve criar um Expense com id único, salvar no grupo e retornar confirmação.

    Dica de error handling: retorne sempre {"error": "mensagem"} em vez de
    lançar exceção — Claude consegue ler o erro e informar o usuário.
    """
    # TODO: implemente aqui
    raise NotImplementedError("adicionar_despesa ainda não implementada")


def listar_despesas(group_id: str) -> dict:
    """
    TODO: Implemente esta função.

    Deve:
    - Retornar erro se grupo não existe
    - Retornar mensagem amigável se não há despesas
    - Retornar lista de despesas com total geral
    """
    # TODO: implemente aqui
    raise NotImplementedError("listar_despesas ainda não implementada")
