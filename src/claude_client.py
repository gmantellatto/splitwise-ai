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
from typing import Generator

from src.tools.definitions import TOOLS

# --- Dispatcher de tools ---
# Mapeia o nome da tool (string que Claude retorna) para a função Python.
# TODO: importe as funções de groups.py, expenses.py e settlements.py
#       e adicione cada uma no dicionário abaixo.
TOOL_DISPATCH: dict = {
    # "criar_grupo": criar_grupo,
    # "adicionar_participante": adicionar_participante,
    # ... complete com todas as 6 tools
}


def _select_model(message: str) -> str:
    """
    TODO: Implemente a seleção de modelo por intenção.

    Regra de negócio:
    - Se a mensagem mencionar "otimizar", "liquidar", "menos transferências",
      "eficiente" → use "claude-sonnet-4-5" (raciocínio mais pesado)
    - Caso contrário → use "claude-haiku-4-5" (mais rápido e barato)

    Conceito CCDV-F: decisão deliberada de modelo por custo/qualidade.
    Esta função representa o trade-off que a prova cobra.
    """
    # TODO: implemente aqui
    return "claude-haiku-4-5"  # padrão enquanto não implementa


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
    """
    Gera chunks de texto via SSE para o frontend.

    Fluxo:
    1. Chama Claude com streaming + tools
    2. Se Claude retornar tool_use → executa a tool, retorna resultado, chama novamente
    3. Faz yield de cada chunk de texto recebido
    4. Trata erros da API com retry onde apropriado

    TODO: Implemente esta função seguindo os passos abaixo.

    PASSO 1 — Montar as mensagens
    ─────────────────────────────
    Adicione a mensagem atual do usuário ao histórico.
    Se group_id existir, inclua no contexto:
      "Grupo ativo: {group_id}"

    PASSO 2 — Primeira chamada com streaming
    ─────────────────────────────────────────
    Use client.messages.stream(...) com:
      - model: _select_model(message)
      - max_tokens: 4096
      - system: SYSTEM_PROMPT
      - tools: TOOLS
      - messages: histórico montado

    Faça yield de cada chunk via stream.text_stream.

    PASSO 3 — Verificar stop_reason
    ────────────────────────────────
    Após o stream terminar, pegue a mensagem final:
      final = stream.get_final_message()

    Se final.stop_reason == "tool_use":
      → Entre no loop de tool use (PASSO 4)

    Se final.stop_reason == "max_tokens":
      → Faça yield de "\n\n⚠️ Resposta cortada (max_tokens atingido)."

    PASSO 4 — Loop de tool use
    ───────────────────────────
    Para cada bloco em final.content onde block.type == "tool_use":
      a) Faça yield de f"\n🔧 Executando: {block.name}...\n"
      b) Execute: result = _execute_tool(block.name, block.input)
      c) Monte a mensagem de retorno:
         messages.append({"role": "assistant", "content": final.content})
         messages.append({
           "role": "user",
           "content": [{
             "type": "tool_result",
             "tool_use_id": block.id,
             "content": result
           }]
         })

    Depois das tools, faça uma nova chamada (sem streaming desta vez, ou
    com streaming — sua escolha) e faça yield do texto final.

    PASSO 5 — Error handling
    ─────────────────────────
    Envolva tudo em try/except:

    except anthropic.RateLimitError:
      → yield mensagem de erro + aguarde 30s (não faça retry automático aqui,
        deixe o usuário saber o que aconteceu)

    except anthropic.BadRequestError as e:
      → yield f"Erro na requisição: {e}" (não tente retry — é problema no código)

    except anthropic.APIError as e:
      → yield f"Erro da API ({e.status_code}): tente novamente"
    """

    client = anthropic.Anthropic()

    # TODO: implemente os 5 passos descritos acima
    yield "claude_client.py ainda não implementado. Complete os TODOs!"
