"""
tools/definitions.py — Schemas das tools que Claude pode chamar.

╔══════════════════════════════════════════════════════════════════╗
║  VOCÊ VAI ESCREVER ESTE ARQUIVO                                  ║
║                                                                  ║
║  Conceito CCDV-F: a DESCRIÇÃO da tool é o que guia Claude       ║
║  a escolher a tool certa. Schema claro > lógica de roteamento.  ║
║                                                                  ║
║  Siga os TODO abaixo em ordem. Quando terminar cada tool,       ║
║  pergunte ao tutor para revisar antes de avançar.               ║
╚══════════════════════════════════════════════════════════════════╝

Referência de tipos de parâmetro:
  "type": "string"           → texto livre
  "type": "number"           → número (int ou float)
  "type": "array"            → lista; use "items": {"type": "string"}
  "enum": ["a", "b"]        → valor deve ser um dos listados
  "required": ["campo"]      → campos obrigatórios da tool
"""

# TODO 1: Defina a tool `criar_grupo`
# Deve receber: nome do grupo (string) e lista de participantes (array de strings)
# Dica de descrição: explique *quando* Claude deve chamar essa tool,
# não apenas o que ela faz.
criar_grupo = {
    "name": "criar_grupo",

    "description": (
        "Cria um novo grupo de divisão de despesas com uma lista de participantes. "
        "Use quando o usuário quiser iniciar um grupo novo, por exemplo: "
        "'cria um grupo para a viagem', 'novo grupo com João e Ana', "
        "'quero dividir despesas com meus amigos'. "
        "NÃO use para adicionar participantes a um grupo que já existe — "
        "para isso use adicionar_participante."
    ),

    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Nome do grupo. Exemplos: 'Viagem para Floripa', 'Apartamento 2024'."
            },
            "participants": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Lista com os nomes dos participantes do grupo. "
                    "Mínimo 2 pessoas. Exemplo: ['João', 'Ana', 'Pedro']. "
                    "Inclua o próprio usuário se ele mencionou 'eu' ou 'comigo'."
                )
            }
        },
        "required": ["name", "participants"]
    }
}


# TODO 2: Defina a tool `adicionar_participante`
# Deve receber: group_id (string) e nome do participante (string)


# TODO 3: Defina a tool `adicionar_despesa`
# Deve receber: group_id, descrição, valor (number), quem pagou (string),
# e entre quem dividir (array de strings — pode ser subconjunto do grupo)

# TODO 4: Defina a tool `listar_despesas`
# Deve receber apenas: group_id

# TODO 5: Defina a tool `calcular_saldos`
# Deve receber apenas: group_id

# TODO 6: Defina a tool `otimizar_liquidacoes`
# Deve receber apenas: group_id
# Dica: a descrição deve deixar claro que essa tool usa um algoritmo
# mais pesado — Claude deve preferi-la quando o usuário pede
# "menor número de transferências" ou "jeito mais eficiente de pagar"


# Quando terminar os TODOs, exporte a lista assim:
# TOOLS: list[dict] = [criar_grupo, adicionar_participante, ...]
#
# Exemplo de estrutura de uma tool completa para referência:
EXEMPLO_TOOL = {
    "name": "exemplo",
    "description": (
        "Descrição clara de quando usar essa tool. "
        "Quanto mais específica, melhor Claude vai selecioná-la."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "param_obrigatorio": {
                "type": "string",
                "description": "O que esse parâmetro representa."
            },
            "param_opcional": {
                "type": "number",
                "description": "Valor numérico. Padrão: 0 se não informado."
            }
        },
        "required": ["param_obrigatorio"]
    }
}

# Remova EXEMPLO_TOOL da lista final — é só referência.
TOOLS: list[dict] = []  # ← substitua [] pela sua lista de tools
