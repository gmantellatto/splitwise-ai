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


adicionar_participante = {
    "name": "adicionar_participante",

    "description": (
        "Adiciona um novo participante a um grupo já existente. "
        "Use quando o usuário quiser adicionar um participante a um grupo, por exemplo: "
        "'adicione Maria ao grupo de viagem', 'novo participante do grupo viagem: Maria', "
        "'Maria deve fazer parte do grupo do ano novo'. "
        "NÃO deve ser usado se o grupo não existe. — "
        "para isso use criar_grupo."
    ),

    "input_schema": {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": (
                    "ID único do grupo, retornado pela tool criar_grupo. "
                    "Use o group_id da resposta mais recente de criar_grupo ou listar_grupos."
                )
            },
            "participant": {
                "type": "string",
                "description": (
                    "Nome do novo participante que será incluído no grupo. "
                    "Inclua o próprio usuário se ele mencionou 'eu' ou 'comigo'."
                )
            }
        },
        "required": ["group_id", "participant"]
    }
}


adicionar_despesa = {
    "name": "adicionar_despesa",

    "description": (
        "Adiciona uma nova despesa a um grupo existente. "
        "Use quando o usuário quiser adicionar alguma despesa paga a um grupo já existente. Exemplo: "
        "'Adicione o jantar de ontem pago por mim ao grupo do trabalho. Valor total R$300,00. Além de mim, Maria e Paulo "
        "estavam presentes.' "
        "O responsável por pagar a despesa deve ser participante do grupo. "
        "Todos os participantes da despesa também devem ser participantes do grupo."
    ),

    "input_schema": {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": (
                  "ID único do grupo, retornado pela tool criar_grupo. "
                  "Use o group_id da resposta mais recente de criar_grupo ou listar_grupos."
                )
            },
            "description": {
                "type": "string",
                "description": (
                  "Descrição da despesa a ser incluída. Exemplos: 'Gasolina', 'Compras Mercado', 'Ingressos Cinema'."
                )
            },
            "amount": {
                "type": "number",
                "description": (
                  "Valor total da despesa. "
                  "O valor deve ser maior do que zero."
                )
            },
            "paid_by": {
                "type": "string",
                "description": (
                  "Responsável pelo pagamento da despesa. Quem efetuou o pagamento e gastou o valor. "
                  "Inclua o próprio usuário quando ele citar algo como 'eu', 'meu'."
                )
            },
            "split_among": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Lista com os nomes dos participantes da despesa. "
                    "Mínimo 1 pessoa. Exemplo: ['João']. "
                    "Inclua todos que participaram da despesa, incluindo quem pagou. "
                    "O fato de alguém ter pagado não o exclui de dividir o custo."
                    
                )
            }
        },
        "required": ["group_id", "description", "amount", "paid_by", "split_among"]
    }
}

listar_despesas = {
    "name": "listar_despesas",
    "description": (
        "Lista todas as despesas e gastos de um grupo. "
        "Use quando o usuário precisar saber tudo o que foi gasto naquele grupo fornecido. "
        "Deve listar apenas as despesas referentes ao grupo fornecido."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": (
                  "ID único do grupo, retornado pela tool criar_grupo. "
                  "Use o group_id da resposta mais recente de criar_grupo ou listar_grupos."
                )
            }
        },
        "required": ["group_id"]
    }
}

calcular_saldos = {
    "name": "calcular_saldos",
    "description": (
        "Calcula o saldo de todos os participantes de um grupo. "
        "Use quando precisar saber o quanto um ou todos os participantes do grupo devem / precisam receber. "
        "NÃO use quando o usuário pedir o jeito mais eficiente ou menos transferências — "
        "para isso use otimizar_liquidacoes."

    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": (
                  "ID único do grupo, retornado pela tool criar_grupo. "
                  "Use o group_id da resposta mais recente de criar_grupo ou listar_grupos."
                )
            }
        },
        "required": ["group_id"]
    }
}

otimizar_liquidacoes = {
    "name": "otimizar_liquidacoes",
    "description": (
        "Utiliza um algoritmo mais elaborado para calcular de forma otimizada as transferencias finais para quitar as dívidas. "
        "Use quando o usuário pedir o jeito mais eficiente de pagar as despesas ou para reduzir ao máximo o número de transferências. "
        "Deve utilizar o altoritmo pesado e considerar todas as despesas e seus participantes, a fim de solucionar o problema."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": (
                  "ID único do grupo, retornado pela tool criar_grupo. "
                  "Use o group_id da resposta mais recente de criar_grupo ou listar_grupos."
                )
            }
        },
        "required": ["group_id"]
    }
}

TOOLS: list[dict] = [
                        criar_grupo, 
                        adicionar_participante, 
                        adicionar_despesa, 
                        listar_despesas, 
                        calcular_saldos, 
                        otimizar_liquidacoes
                    ]