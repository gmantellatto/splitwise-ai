"""
server.py — FastAPI: rotas HTTP e SSE.

Este arquivo está completo — infraestrutura que não é conceito da prova.
Leia e entenda o fluxo, mas não precisa modificar para começar.
"""

import json
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.models import (
    ChatRequest,
    CreateGroupRequest, AddParticipantRequest, RenameParticipantRequest,
    AddExpenseRequest, EditExpenseRequest,
)
from src.claude_client import chat_stream
from src.storage import db
from src.tools.groups import (
    criar_grupo, excluir_grupo,
    adicionar_participante, remover_participante, renomear_participante,
)
from src.tools.expenses import adicionar_despesa, editar_despesa, remover_despesa
from src.tools.settlements import calcular_saldos, otimizar_liquidacoes
from src.tools.undo import desfazer_operacao

app = FastAPI(title="SplitWise Claude")

# Serve os arquivos estáticos do frontend
PUBLIC_DIR = Path(__file__).parent.parent / "public"
app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")


@app.get("/")
async def root():
    """Serve o HTML principal."""
    return FileResponse(PUBLIC_DIR / "index.html")


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Endpoint principal: recebe mensagem, retorna stream SSE.

    SSE (Server-Sent Events): protocolo unidirecional servidor→cliente.
    É o transporte certo para streaming da Claude API porque o cliente
    não precisa enviar dados durante a geração.

    Cada evento SSE tem o formato:
      data: <payload>\n\n
    """
    # session_id identifica a conversa — gerado pelo frontend e enviado em cada request.
    # Se não vier (ex: chamadas diretas à API), criamos um ID descartável.
    session_id = request.session_id or str(uuid.uuid4())

    def event_generator():
        try:
            for chunk in chat_stream(
                message=request.message,
                group_id=request.group_id,
                session_id=session_id,
            ):
                # Formato SSE: "data: <conteúdo>\n\n"
                payload = json.dumps({"text": chunk}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
        except Exception as e:
            error_payload = json.dumps({"error": str(e)})
            yield f"data: {error_payload}\n\n"
        finally:
            # Sinaliza fim do stream para o frontend
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Desativa buffer do nginx se houver
        }
    )


@app.get("/api/groups")
async def list_groups():
    """Lista todos os grupos — usado pelo frontend para popular o seletor."""
    groups = db.get_all_groups()
    return {
        "groups": [
            {"id": g.id, "name": g.name, "participants": g.participants}
            for g in groups.values()
        ]
    }


@app.get("/api/groups/{group_id}")
async def get_group(group_id: str):
    """Retorna detalhes de um grupo específico."""
    group = db.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    return group.model_dump()


# ── REST endpoints para a UI (chamam as tool functions diretamente) ──────────

def _ok(result: dict):
    """Levanta 400 se a tool retornou erro, caso contrário devolve o resultado."""
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/groups")
async def create_group(req: CreateGroupRequest):
    return _ok(criar_grupo(req.name, req.participants))


@app.delete("/api/groups/{group_id}")
async def delete_group(group_id: str):
    return _ok(excluir_grupo(group_id))


@app.post("/api/groups/{group_id}/participants")
async def add_participant(group_id: str, req: AddParticipantRequest):
    return _ok(adicionar_participante(group_id, req.participant))


@app.delete("/api/groups/{group_id}/participants/{participant}")
async def remove_participant(group_id: str, participant: str):
    return _ok(remover_participante(group_id, participant))


@app.patch("/api/groups/{group_id}/participants")
async def rename_participant(group_id: str, req: RenameParticipantRequest):
    return _ok(renomear_participante(group_id, req.old_name, req.new_name))


@app.post("/api/groups/{group_id}/expenses")
async def add_expense(group_id: str, req: AddExpenseRequest):
    return _ok(adicionar_despesa(group_id, req.description, req.amount, req.paid_by, req.split_among))


@app.patch("/api/groups/{group_id}/expenses/{expense_id}")
async def edit_expense(group_id: str, expense_id: str, req: EditExpenseRequest):
    return _ok(editar_despesa(group_id, expense_id, req.description, req.amount, req.paid_by, req.split_among))


@app.delete("/api/groups/{group_id}/expenses/{expense_id}")
async def delete_expense(group_id: str, expense_id: str):
    return _ok(remover_despesa(group_id, expense_id))


@app.get("/api/groups/{group_id}/balances")
async def get_balances(group_id: str):
    return _ok(calcular_saldos(group_id))


@app.get("/api/groups/{group_id}/optimized")
async def get_optimized(group_id: str):
    return _ok(otimizar_liquidacoes(group_id))


@app.post("/api/groups/{group_id}/undo")
async def undo_last(group_id: str):
    return _ok(desfazer_operacao(group_id))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=True)
