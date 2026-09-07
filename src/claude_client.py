"""
claude_client.py — Núcleo da integração com a Claude API.

╔══════════════════════════════════════════════════════════════════╗
║  VOCÊ VAI ESCREVER ESTE ARQUIVO — É O MAIS IMPORTANTE           ║
║                                                                  ║
║  Conceitos CCDV-F praticados aqui:                              ║
║  ✓ Streaming (client.messages.stream)                           ║
║  ✓ Tool use — loop completo (detectar, despachar, retornar)     ║
║  ✓ Error handling — RateLimitError, APIError, max_tokens        ║
║  ✓ Model selection — Haiku vs Sonnet por intenção               ║
║  ✓ Generator para SSE (yield de chunks)                         ║
╚══════════════════════════════════════════════════════════════════╝
"""

import json
import time
import anthropic
import os
from typing import Generator
from dotenv import load_dotenv
from src.storage import db
from src.models import Group

from src.tools.definitions import TOOLS

from src.tools.groups import criar_grupo, adicionar_participante
from src.tools.expenses import adicionar_despesa, listar_despesas
from src.tools.settlements import calcular_saldos, otimizar_liquidacoes

load_dotenv()

TOOL_DISPATCH = {
    "criar_grupo": criar_grupo,
    "adicionar_participante": adicionar_participante,
    "adicionar_despesa": adicionar_despesa,
    "listar_despesas": listar_despesas,
    "calcular_saldos": calcular_saldos,
    "otimizar_liquidacoes": otimizar_liquidacoes,
}


def _select_model(message: str) -> str:
    modelo_raciocinio = ["sonnet", "opus", "fable"]

    if any(p in message.lower() for p in modelo_raciocinio):
        return os.environ["ANTHROPIC_DEFAULT_SONNET_MODEL"]
        
    return os.environ["ANTHROPIC_DEFAULT_HAIKU_MODEL"]


SYSTEM_PROMPT = """Você é um assistente amigável para divisão de despesas em grupo.
Ajude o usuário a gerenciar despesas, calcular quem deve para quem e sugerir
a forma mais eficiente de liquidar as dívidas.

Ao receber uma solicitação, use as tools disponíveis para executar as ações.
Sempre confirme o que foi feito e explique os resultados de forma clara.
Responda sempre em português brasileiro.
Quando valores financeiros forem mencionados, assuma que são em Reais (R$)."""


def _execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Executa uma tool pelo nome e retorna o resultado como string JSON.
    Este é o 'dispatch' — o coração do loop de tool use.
    """
    func = TOOL_DISPATCH.get(tool_name)
    if not func:
        return json.dumps({"error": f"Tool '{tool_name}' não encontrada."})

    try:
        result = func(**tool_input)
        return json.dumps(result, ensure_ascii=False)
    except TypeError as e:
        # Parâmetros errados — problema na definição do schema
        return json.dumps({"error": f"Parâmetros inválidos para '{tool_name}': {e}"})
    except Exception as e:
        # Erro inesperado na execução da tool
        return json.dumps({"error": f"Erro ao executar '{tool_name}': {e}"})


def chat_stream(
    message: str,
    group_id: str | None,
    history: list[dict]
) -> Generator[str, None, None]:

    token = os.environ["ANTHROPIC_AUTH_TOKEN"]
    url = os.environ["ANTHROPIC_BASE_URL"]

    client = anthropic.Anthropic(
        api_key=token,
        base_url=url,
        default_headers={"Authorization": f"Bearer {token}"}
    )

    # Passo 1 — Montar mensagens
    messages = list(history)
    user_content = f"[Grupo ativo: {group_id}]\n\n{message}" if group_id else message
    messages.append({"role": "user", "content": user_content})

    # Passo 5 - Erro Handling
    try:
        # Passo 2 — Primeira chamada com streaming
            with client.messages.stream(
                model=_select_model(message),
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages
            ) as stream:
                for text in stream.text_stream:
                    yield text
                final = stream.get_final_message()
        
            # Passo 3 — Verificar stop_reason
            if final.stop_reason == "max_tokens":
                yield "\n\n⚠️ Resposta cortada (max_tokens atingido)."
                return
        
            # Passo 4 — Loop de tool use
            if final.stop_reason == "tool_use":
        
                # Assistant entra uma única vez no histórico
                messages.append({"role": "assistant", "content": final.content})
        
                # Coleta todos os resultados das tools
                tool_results = []
                for block in final.content:
                    if block.type == "tool_use":
                        yield f"\n🔧 Executando: {block.name}...\n"
                        result = _execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })
        
                # Uma única mensagem user com todos os resultados
                messages.append({"role": "user", "content": tool_results})
        
                # Follow-up — Claude processa os resultados e responde
                follow_up = client.messages.create(
                    model=_select_model(message),
                    max_tokens=4096,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages
                )
                yield follow_up.content[0].text

    except anthropic.RateLimitError:
        yield "\n⚠️ Limite de requisições atingido. Aguarde 30 segundos."
    except anthropic.BadRequestError as e:
        yield f"\n⚠️ Erro na requisição: {e}"
    except anthropic.APIError as e:
        yield f"\n⚠️ Erro da API ({e.status_code}): tente novamente."
        


