"""
server.py — FastAPI: rotas HTTP e SSE.

Este arquivo está completo — infraestrutura que não é conceito da prova.
Leia e entenda o fluxo, mas não precisa modificar para começar.
"""

import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.models import ChatRequest
from src.claude_client import chat_stream
from src.storage import db

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
    # Histórico simplificado: em produção você armazenaria por sessão
    history: list[dict] = []

    def event_generator():
        try:
            for chunk in chat_stream(
                message=request.message,
                group_id=request.group_id,
                history=history
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=True)
