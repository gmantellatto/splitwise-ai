"""
claude_client.py — Núcleo da integração com a Claude API.

╔══════════════════════════════════════════════════════════════════╗
║  Conceitos CCDV-F praticados aqui:                              ║
║  ✓ Streaming (client.messages.stream)                           ║
║  ✓ Tool use — loop completo (detectar, despachar, retornar)     ║
║  ✓ Error handling — RateLimitError, APIError, max_tokens        ║
║  ✓ Model selection — Haiku vs Sonnet por intenção               ║
║  ✓ Generator para SSE (yield de chunks)                         ║
║  ✓ Histórico de conversa por sessão (multi-turn)                ║
╚══════════════════════════════════════════════════════════════════╝
"""

import json
import anthropic
import os
from typing import Generator
from dotenv import load_dotenv

from src.tools.definitions import TOOLS
from src.tools.groups import (
    criar_grupo, adicionar_participante,
    remover_participante, renomear_participante,
    listar_grupos, obter_detalhes_grupo,
)
from src.tools.expenses import adicionar_despesa, listar_despesas, editar_despesa, remover_despesa
from src.tools.settlements import calcular_saldos, otimizar_liquidacoes
from src.tools.undo import desfazer_operacao

load_dotenv()

# ── Histórico por sessão ────────────────────────────────────────────────────
# Chave: session_id (str)  →  Valor: lista de mensagens no formato da API
SESSION_HISTORY: dict[str, list[dict]] = {}

TOOL_DISPATCH = {
    "criar_grupo": criar_grupo,
    "adicionar_participante": adicionar_participante,
    "remover_participante": remover_participante,
    "renomear_participante": renomear_participante,
    "adicionar_despesa": adicionar_despesa,
    "listar_despesas": listar_despesas,
    "editar_despesa": editar_despesa,
    "remover_despesa": remover_despesa,
    "calcular_saldos": calcular_saldos,
    "otimizar_liquidacoes": otimizar_liquidacoes,
    "listar_grupos": listar_grupos,
    "obter_detalhes_grupo": obter_detalhes_grupo,
    "desfazer_operacao": desfazer_operacao,
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
        return json.dumps({"error": f"Parâmetros inválidos para '{tool_name}': {e}"})
    except Exception as e:
        return json.dumps({"error": f"Erro ao executar '{tool_name}': {e}"})


def chat_stream(
    message: str,
    group_id: str | None,
    session_id: str,
) -> Generator[str, None, None]:
    """
    Gera chunks de texto para o SSE.

    Melhorias implementadas:
    - Histórico persistido por session_id (multi-turn real)
    - Loop de tool use completo (suporta múltiplos ciclos)
    - Follow-up com streaming (não bloqueia mais o cliente)
    """
    token = os.environ["ANTHROPIC_AUTH_TOKEN"]
    url   = os.environ["ANTHROPIC_BASE_URL"]

    client = anthropic.Anthropic(
        api_key=token,
        base_url=url,
        default_headers={"Authorization": f"Bearer {token}"}
    )

    # ── Passo 1: recuperar / criar histórico da sessão ──────────────────────
    # SESSION_HISTORY[session_id] é a lista mutável real — não copiamos,
    # pois queremos que os appends abaixo persistam entre requisições.
    history = SESSION_HISTORY.setdefault(session_id, [])

    user_content = f"[Grupo ativo: {group_id}]\n\n{message}" if group_id else message
    history.append({"role": "user", "content": user_content})

    model = _select_model(message)

    # ── Error handling externo ──────────────────────────────────────────────
    try:
        # ── Passo 2: loop de tool use ───────────────────────────────────────
        # Repete enquanto Claude quiser chamar tools.
        # Em cada iteração usamos streaming para manter o feedback visual.
        while True:
            with client.messages.stream(
                model=model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=history,
            ) as stream:
                for text in stream.text_stream:
                    yield text
                final = stream.get_final_message()

            # ── Passo 3: tratar stop_reason ─────────────────────────────────
            if final.stop_reason == "max_tokens":
                yield "\n\n⚠️ Resposta cortada (max_tokens atingido)."
                # Salva o que chegou para o histórico não ficar inconsistente
                history.append({"role": "assistant", "content": final.content})
                break

            if final.stop_reason == "end_turn":
                # Resposta completa — persiste no histórico e encerra o loop
                history.append({"role": "assistant", "content": final.content})
                break

            if final.stop_reason == "tool_use":
                # Persiste a resposta do assistente (contém os blocos tool_use)
                history.append({"role": "assistant", "content": final.content})

                # Executa todas as tools solicitadas neste ciclo
                tool_results = []
                for block in final.content:
                    if block.type == "tool_use":
                        yield f"\n🔧 Executando: {block.name}...\n"
                        result = _execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                # Uma única mensagem user com todos os resultados — persiste e continua
                history.append({"role": "user", "content": tool_results})
                # O while repete: Claude agora processa os resultados com streaming

            else:
                # stop_reason inesperado — encerra sem travar
                history.append({"role": "assistant", "content": final.content})
                break

    except anthropic.RateLimitError:
        yield "\n⚠️ Limite de requisições atingido. Aguarde 30 segundos."
    except anthropic.BadRequestError as e:
        yield f"\n⚠️ Erro na requisição: {e}"
    except anthropic.APIError as e:
        yield f"\n⚠️ Erro da API ({e.status_code}): tente novamente."

