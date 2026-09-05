"""
tools/groups.py — Implementações das tools de grupo.

╔══════════════════════════════════════════════════════════════════╗
║  VOCÊ VAI ESCREVER ESTE ARQUIVO                                  ║
║                                                                  ║
║  Cada função aqui corresponde a uma tool definida em            ║
║  definitions.py. O nome da função deve bater com o "name"       ║
║  da tool — o dispatcher em claude_client.py usa esse nome       ║
║  para saber qual função chamar.                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import uuid
from datetime import datetime, timezone

from src.storage import db
from src.models import Group


def criar_grupo(name: str, participants: list[str]) -> dict:
    """
    TODO: Implemente esta função.

    Deve:
    1. Validar que há pelo menos 2 participantes (error handling!)
    2. Validar que não há participantes duplicados
    3. Criar um objeto Group com:
       - id: uuid4 como string
       - name: nome recebido
       - participants: lista recebida (nomes normalizados — strip + title case)
       - expenses: lista vazia
       - created_at: datetime.now(timezone.utc).isoformat()
    4. Salvar com db.save_group(group)
    5. Retornar dict com: group_id, name, participants, message de sucesso

    Dica: retorne sempre um dict — Claude vai receber esse dict
    como string e vai usá-lo para formatar a resposta ao usuário.
    """
    # TODO: implemente aqui
    raise NotImplementedError("criar_grupo ainda não implementada")


def adicionar_participante(group_id: str, participant: str) -> dict:
    """
    TODO: Implemente esta função.

    Deve:
    1. Buscar o grupo com db.get_group(group_id)
    2. Retornar erro se grupo não existir
    3. Retornar erro se participante já estiver no grupo
    4. Adicionar o participante (normalizado) à lista
    5. Salvar e retornar confirmação
    """
    # TODO: implemente aqui
    raise NotImplementedError("adicionar_participante ainda não implementada")
