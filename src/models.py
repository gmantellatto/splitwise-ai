"""
models.py — Tipos compartilhados do projeto.

Pydantic garante que os dados persistidos em JSON sempre
batem com o que o código espera. Isso é "parsing defensivo"
— conceito recorrente no CCDV-F.
"""

from pydantic import BaseModel, Field
from typing import Optional


class Expense(BaseModel):
    id: str
    description: str
    amount: float
    paid_by: str                  # nome do participante que pagou
    split_among: list[str]        # quem divide a despesa
    created_at: str               # ISO 8601


class Group(BaseModel):
    id: str
    name: str
    participants: list[str]
    expenses: list[Expense] = Field(default_factory=list)
    created_at: str


class Database(BaseModel):
    groups: dict[str, Group] = Field(default_factory=dict)


# --- Modelos de request/response da API HTTP ---

class ChatRequest(BaseModel):
    message: str
    group_id: Optional[str] = None   # None quando ainda não há grupo ativo
    session_id: Optional[str] = None  # identifica a conversa; frontend gera um UUID


# --- Modelos para endpoints REST da UI ---

class CreateGroupRequest(BaseModel):
    name: str
    participants: list[str]

class AddParticipantRequest(BaseModel):
    participant: str

class RenameParticipantRequest(BaseModel):
    old_name: str
    new_name: str

class AddExpenseRequest(BaseModel):
    description: str
    amount: float
    paid_by: str
    split_among: list[str]

class EditExpenseRequest(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    paid_by: Optional[str] = None
    split_among: Optional[list[str]] = None
