"""
storage/db.py — Persistência em arquivo JSON.

Camada simples de leitura/escrita. Toda tool que modifica
dados passa por aqui — centraliza o error handling de I/O.
"""

import json
from pathlib import Path
from src.models import Database, Group

DB_PATH = Path(__file__).parent.parent.parent / "data" / "groups.json"


def _load() -> Database:
    """Lê o arquivo JSON e retorna o modelo validado pelo Pydantic."""
    try:
        raw = DB_PATH.read_text(encoding="utf-8")
        return Database.model_validate_json(raw)
    except FileNotFoundError:
        return Database()
    except json.JSONDecodeError as e:
        # Arquivo corrompido — não silencia o erro
        raise RuntimeError(f"Arquivo de dados corrompido: {e}") from e


def _save(db: Database) -> None:
    """Persiste o modelo como JSON formatado."""
    DB_PATH.write_text(
        db.model_dump_json(indent=2),
        encoding="utf-8"
    )


def get_all_groups() -> dict[str, Group]:
    return _load().groups


def get_group(group_id: str) -> Group | None:
    return _load().groups.get(group_id)


def save_group(group: Group) -> None:
    db = _load()
    db.groups[group.id] = group
    _save(db)


def delete_group(group_id: str) -> bool:
    db = _load()
    if group_id not in db.groups:
        return False
    del db.groups[group_id]
    _save(db)
    return True
