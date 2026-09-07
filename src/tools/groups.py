import uuid
from datetime import datetime, timezone

from src.storage import db
from src.models import Group

def _normalizar_participante(participant: str) -> str:
    return participant.strip().title()

def criar_grupo(name: str, participants: list[str]) -> dict:
    if len(participants) < 2:
        return {"error": "O novo grupo precisar ter no mínimo 2 participantes."}

    normalized_participants = [_normalizar_participante(nome) for nome in participants]

    if len(normalized_participants) != len(set(normalized_participants)):
        return {"error": "Participantes do grupo não podem ter o mesmo nome."}

    grupo = Group(id=str(uuid.uuid4()), name=name, participants=normalized_participants, expenses=[], created_at=datetime.now(timezone.utc).isoformat())
    db.save_group(grupo)

    return {"group_id": grupo.id, "name": grupo.name, "participants": grupo.participants, "message": "Grupo criado com sucesso!"}



def adicionar_participante(group_id: str, participant: str) -> dict:
    grupo = db.get_group(group_id)
    participante = _normalizar_participante(participant)

    if (grupo is None):
        return {"error": "Grupo não encontrado."}

    if (participante in grupo.participants):
        return {"error": f"Já existe um participante '{participante}' no grupo '{grupo.name}'."}

    grupo.participants.append(participante)
    db.save_group(grupo)

    return {"message": f"'{participante}' adicionado ao grupo '{grupo.name}'.", "participants": grupo.participants}
