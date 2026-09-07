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

excluir_grupo = {
    "name": "excluir_grupo",
    "description": (
        "Exclui permanentemente um grupo e todas as suas despesas. "
        "Use quando o usuário quiser deletar ou remover um grupo inteiro. "
        "Exemplos: 'exclua o grupo da viagem', 'delete esse grupo', 'remova o grupo'. "
        "ATENÇÃO: esta ação é irreversível — todas as despesas e participantes são perdidos."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": "ID único do grupo a ser excluído."
            }
        },
        "required": ["group_id"]
    }
}

remover_participante = {
    "name": "remover_participante",
    "description": (
        "Remove um participante de um grupo existente. "
        "Use quando o usuário quiser retirar alguém do grupo, por exemplo: "
        "'remova João do grupo', 'tire a Ana daqui'. "
        "ATENÇÃO: falha automaticamente se o participante tiver despesas registradas — "
        "nesse caso, oriente o usuário a remover ou editar as despesas antes. "
        "NÃO use para corrigir nomes — para isso use renomear_participante."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": "ID único do grupo."
            },
            "participant": {
                "type": "string",
                "description": "Nome exato do participante a ser removido."
            }
        },
        "required": ["group_id", "participant"]
    }
}

renomear_participante = {
    "name": "renomear_participante",
    "description": (
        "Renomeia um participante existente, atualizando seu nome em todas as despesas do grupo. "
        "Use para corrigir erros de digitação ou nomes incorretos, por exemplo: "
        "'corrija o nome de Gustao para Gustavo', 'o nome certo é Maria, não Mari'. "
        "Atualiza automaticamente paid_by e split_among em todas as despesas."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": "ID único do grupo."
            },
            "old_name": {
                "type": "string",
                "description": "Nome atual (incorreto) do participante."
            },
            "new_name": {
                "type": "string",
                "description": "Novo nome (correto) do participante."
            }
        },
        "required": ["group_id", "old_name", "new_name"]
    }
}

editar_despesa = {
    "name": "editar_despesa",
    "description": (
        "Edita uma despesa já registrada em um grupo. "
        "Use quando o usuário quiser corrigir valor, descrição, quem pagou ou como foi dividida. "
        "Exemplos: 'corrija o valor do jantar para R$250', 'a hospedagem foi paga por João, não por Ana', "
        "'edite a descrição da despesa X'. "
        "Apenas os campos fornecidos são alterados — os demais ficam inalterados. "
        "Use listar_despesas para obter o expense_id antes de editar."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": "ID único do grupo."
            },
            "expense_id": {
                "type": "string",
                "description": "ID único da despesa (obtido via listar_despesas)."
            },
            "description": {
                "type": "string",
                "description": "Nova descrição da despesa. Omita para não alterar."
            },
            "amount": {
                "type": "number",
                "description": "Novo valor da despesa. Deve ser maior que zero. Omita para não alterar."
            },
            "paid_by": {
                "type": "string",
                "description": "Nome do novo responsável pelo pagamento. Deve ser participante do grupo. Omita para não alterar."
            },
            "split_among": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Nova lista de quem divide a despesa. Todos devem ser participantes do grupo. Omita para não alterar."
            }
        },
        "required": ["group_id", "expense_id"]
    }
}

remover_despesa = {
    "name": "remover_despesa",
    "description": (
        "Remove uma despesa do grupo pelo seu ID. "
        "Use quando o usuário quiser deletar um lançamento duplicado ou incorreto. "
        "Exemplos: 'apague a despesa de gasolina', 'remova esse lançamento duplicado'. "
        "Use listar_despesas para obter o expense_id antes de remover."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": "ID único do grupo."
            },
            "expense_id": {
                "type": "string",
                "description": "ID único da despesa a ser removida (obtido via listar_despesas)."
            }
        },
        "required": ["group_id", "expense_id"]
    }
}

listar_grupos = {
    "name": "listar_grupos",
    "description": (
        "Lista todos os grupos de despesas existentes com seus participantes. "
        "Use quando o usuário quiser ver todos os grupos disponíveis, alternar entre grupos, "
        "ou quando precisar encontrar um group_id específico. "
        "Exemplos: 'quais grupos eu tenho?', 'mostre todos os grupos', 'lista os grupos'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {}
    }
}

obter_detalhes_grupo = {
    "name": "obter_detalhes_grupo",
    "description": (
        "Retorna informações completas de um grupo: nome, membros, número de despesas, "
        "total gasto e quantas operações podem ser desfeitas. "
        "Use antes de adicionar despesas para validar participantes, "
        "ou quando o usuário pedir detalhes de um grupo específico."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": "ID único do grupo."
            }
        },
        "required": ["group_id"]
    }
}

desfazer_operacao = {
    "name": "desfazer_operacao",
    "description": (
        "Desfaz a última operação realizada em um grupo, revertendo ao estado anterior. "
        "Use quando o usuário pedir para desfazer, corrigir ou reverter a última ação. "
        "Exemplos: 'desfaça isso', 'volte ao estado anterior', 'undo', 'errei, desfaz'. "
        "Funciona para: adicionar/remover/renomear participante, adicionar/editar/remover despesa. "
        "IMPORTANTE: o histórico é mantido apenas enquanto o servidor está rodando."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": "ID único do grupo cuja última operação deve ser desfeita."
            }
        },
        "required": ["group_id"]
    }
}

TOOLS: list[dict] = [
    criar_grupo,
    excluir_grupo,
    adicionar_participante,
    remover_participante,
    renomear_participante,
    adicionar_despesa,
    listar_despesas,
    editar_despesa,
    remover_despesa,
    calcular_saldos,
    otimizar_liquidacoes,
    listar_grupos,
    obter_detalhes_grupo,
    desfazer_operacao,
]