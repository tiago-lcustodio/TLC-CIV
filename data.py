CORES_JOGADOR = {
    'Azul': (55, 105, 205),
    'Vermelho': (190, 65, 65),
    'Verde': (65, 150, 85),
    'Roxo': (135, 75, 180),
    'Laranja': (220, 130, 45),
    'Ciano': (45, 165, 175),
}

DIFICULDADES = {
    'Fácil': {
        'cpu_bonus_producao_pct': 0, 'cpu_bonus_ciencia_pct': 0,
        'cpu_bonus_fe_pct': 0, 'cpu_bonus_alimento_pct': 0, 'cpu_bonus_ouro_pct': 0,
        'multiplicador_barbaros': 0.75,
    },
    'Padrão': {
        'cpu_bonus_producao_pct': 0, 'cpu_bonus_ciencia_pct': 0,
        'cpu_bonus_fe_pct': 0, 'cpu_bonus_alimento_pct': 0, 'cpu_bonus_ouro_pct': 0,
        'multiplicador_barbaros': 1.0,
    },
    'Difícil': {
        'cpu_bonus_producao_pct': 0, 'cpu_bonus_ciencia_pct': 0,
        'cpu_bonus_fe_pct': 0, 'cpu_bonus_alimento_pct': 0, 'cpu_bonus_ouro_pct': 0,
        'multiplicador_barbaros': 1.35,
    },
}

CIVILIZACOES = {
    'Romanos': {
        'nome': 'Romanos', 'descricao': 'Civilização base preparada para bônus e conteúdo exclusivo.',
        'unidade_especial': None, 'construcao_especial': None, 'modificadores': [], 'desbloqueios': [],
        'lideres_m': ['Marcus', 'Lucius', 'Gaius'], 'lideres_f': ['Livia', 'Julia', 'Claudia'],
        'cidades': ['Roma', 'Ravena', 'Pompeia', 'Óstia', 'Verona', 'Capua', 'Aquileia', 'Mediolano'],
        'saudacao': 'Roma reconhece sua presença. Que nossas fronteiras tragam ordem, prosperidade e respeito mútuo.',
    },
    'Egípcios': {
        'nome': 'Egípcios', 'descricao': 'Civilização base preparada para bônus e conteúdo exclusivo.',
        'unidade_especial': None, 'construcao_especial': None, 'modificadores': [], 'desbloqueios': [],
        'lideres_m': ['Amenhotep', 'Ramsés', 'Tutemés'], 'lideres_f': ['Nefertari', 'Hatshepsut', 'Cleópatra'],
        'cidades': ['Mênfis', 'Tebas', 'Alexandria', 'Heliópolis', 'Abidos', 'Elefantina', 'Saís', 'Edfu'],
        'saudacao': 'As margens do Nilo saúdam seu povo. Que o tempo julgue se seremos parceiros ou rivais.',
    },
    'Gregos': {
        'nome': 'Gregos', 'descricao': 'Civilização base preparada para bônus e conteúdo exclusivo.',
        'unidade_especial': None, 'construcao_especial': None, 'modificadores': [], 'desbloqueios': [],
        'lideres_m': ['Alexandros', 'Péricles', 'Leônidas'], 'lideres_f': ['Aspásia', 'Gorgo', 'Hipátia'],
        'cidades': ['Atenas', 'Corinto', 'Argos', 'Tebas', 'Mileto', 'Delfos', 'Rodes', 'Siracusa'],
        'saudacao': 'Os helenos lhe oferecem palavras antes de lanças. Que a razão conduza nosso primeiro encontro.',
    },
    'Persas': {
        'nome': 'Persas', 'descricao': 'Civilização base preparada para bônus e conteúdo exclusivo.',
        'unidade_especial': None, 'construcao_especial': None, 'modificadores': [], 'desbloqueios': [],
        'lideres_m': ['Ciro', 'Dario', 'Xerxes'], 'lideres_f': ['Atossa', 'Parysatis', 'Amestris'],
        'cidades': ['Persépolis', 'Susa', 'Pasárgada', 'Ecbátana', 'Sardes', 'Babilônia', 'Nínive', 'Bactra'],
        'saudacao': 'O Grande Reino observa sua civilização com interesse. Que nossas estradas conduzam a bons acordos.',
    },
    'Fenícios': {
        'nome': 'Fenícios', 'descricao': 'Civilização base preparada para bônus e conteúdo exclusivo.',
        'unidade_especial': None, 'construcao_especial': None, 'modificadores': [], 'desbloqueios': [],
        'lideres_m': ['Hiram', 'Mattã', 'Baal-Eser'], 'lideres_f': ['Elissa', 'Astarté', 'Batnoam'],
        'cidades': ['Tiro', 'Sídon', 'Biblos', 'Arados', 'Berito', 'Cartago', 'Útica', 'Gades'],
        'saudacao': 'Nossos mercadores já ouviram falar de seu povo. Talvez o mar leve riquezas entre nós.',
    },
    'Celtas': {
        'nome': 'Celtas', 'descricao': 'Civilização base preparada para bônus e conteúdo exclusivo.',
        'unidade_especial': None, 'construcao_especial': None, 'modificadores': [], 'desbloqueios': [],
        'lideres_m': ['Brennos', 'Vercingetórix', 'Catuvolco'], 'lideres_f': ['Boudica', 'Cartimandua', 'Chiomara'],
        'cidades': ['Bibracte', 'Avaricum', 'Gergóvia', 'Camuloduno', 'Lugduno', 'Lutetia', 'Segóvia', 'Nemetocena'],
        'saudacao': 'Seu povo entrou em nossas histórias. Mostre honra, e talvez nossos clãs caminhem em paz.',
    },
}

LIDERES_GENERICOS_M = ['Adrian', 'Dorian', 'Leon']
LIDERES_GENERICOS_F = ['Helena', 'Mira', 'Selene']

CIDADES_ESTADO = [
    'Esparta', 'Tiro', 'Samarcanda', 'Veneza', 'Genebra', 'Zanzibar',
    'Mohenjo-Daro', 'Ur', 'Jerusalém', 'Ragusa', 'Kabul', 'La Venta',
    'Nan Madol', 'Valeta', 'Fez', 'Cartum', 'Singapura', 'Hong Kong',
]

SAUDACOES_CIDADES_ESTADO = [
    'Saudações de {nome}. Somos uma cidade livre e observaremos com atenção suas escolhas.',
    '{nome} reconhece seus emissários. Comércio e amizade podem ser úteis a ambos.',
    'Os portões de {nome} estão abertos ao diálogo. Nossa independência, porém, é preciosa.',
]

CORES_CIDADE_ESTADO = [
    (155, 145, 75), (120, 145, 165), (150, 105, 145), (105, 155, 135),
    (165, 120, 85), (125, 125, 155),
]
COR_BARBAROS = (95, 55, 50)

DENSIDADES_CIDADES_ESTADO = {'Poucas': 1.5, 'Média': 3.0, 'Muitas': 5.0}
DENSIDADES_BARBAROS = {'Poucos': 1.0, 'Médio': 2.0, 'Muitos': 4.0}


ERAS = ['Antiga', 'Clássica', 'Medieval', 'Renascimento', 'Industrial', 'Moderna', 'Atômica', 'Informação']

# Ícones Unicode: permanecem independentes de sprites/PNG.
UNIDADES = {
    'Colono': {
        'nome': 'Colono', 'sigla': 'ST', 'letra': 'S', 'marcador': 'S+', 'icone': '⚑', 'movimento': 1, 'dominio': 'terra',
        'custo_producao': 14, 'tecnologia': None, 'era': 'Antiga',
        'requisitos': [{'tipo': 'populacao', 'minimo': 2}],
        'populacao_min': 2, 'consome_populacao': 1, 'melhorias_max': 0,
        'capacidade_transporte': 0,
        'forca': 0, 'defesa': 2, 'vida_max': 100, 'alcance': 0, 'classe': 'civil',
    },
    'Guerreiro': {
        'nome': 'Guerreiro', 'sigla': 'WA', 'letra': 'W', 'marcador': 'W*', 'icone': '⚔', 'movimento': 1, 'dominio': 'terra',
        'custo_producao': 12, 'tecnologia': None, 'era': 'Antiga',
        'requisitos': [],
        'populacao_min': 0, 'consome_populacao': 0, 'melhorias_max': 0,
        'capacidade_transporte': 0,
        'forca': 10, 'defesa': 8, 'vida_max': 100, 'alcance': 1, 'classe': 'corpo_a_corpo',
    },
    'Trabalhador': {
        'nome': 'Trabalhador', 'sigla': 'WK', 'letra': 'W', 'marcador': 'W#', 'icone': '⚒', 'movimento': 1, 'dominio': 'terra',
        'custo_producao': 10, 'tecnologia': None, 'era': 'Antiga',
        'requisitos': [],
        'populacao_min': 0, 'consome_populacao': 0, 'melhorias_max': 3,
        'capacidade_transporte': 0,
        'forca': 0, 'defesa': 3, 'vida_max': 100, 'alcance': 0, 'classe': 'civil',
    },
    'Galé': {
        'nome': 'Galé', 'sigla': 'GA', 'letra': 'G', 'marcador': 'G~', 'icone': '⛵', 'movimento': 3, 'dominio': 'mar_raso',
        'custo_producao': 16, 'tecnologia': None, 'era': 'Antiga',
        'requisitos': [{'tipo': 'costeira'}],
        'populacao_min': 0, 'consome_populacao': 0, 'melhorias_max': 0,
        'capacidade_transporte': 1,
        'forca': 8, 'defesa': 7, 'vida_max': 100, 'alcance': 1, 'classe': 'naval',
        'transporta_dominios': ['terra'],
    },
}

CONSTRUCOES = {
    'Templo': {
        'nome': 'Templo', 'sigla': 'TP', 'custo_producao': 20,
        'tecnologia': None, 'era': 'Antiga', 'requisitos': [],
        'modificadores': [
            {'atributo': 'fe_por_turno', 'operacao': 'somar', 'valor': 1, 'escopo': 'cidade', 'duracao': None}
        ],
    },
    'Muralha': {
        'nome': 'Muralha', 'sigla': 'MU', 'custo_producao': 16,
        'tecnologia': None, 'era': 'Antiga', 'requisitos': [], 'modificadores': [],
    },
}

TECNOLOGIAS = {
    'Conhecimento Inicial': {
        'nome': 'Conhecimento Inicial', 'era': 'Antiga', 'pre_requisitos': [],
        'custo_ciencia': 0, 'desbloqueia_unidades': [],
        'desbloqueia_construcoes': [], 'desbloqueios': [], 'requisitos': [], 'modificadores': [],
    }
}

POLITICAS = {}

# Recursos que pertencem à civilização inteira, e não a uma cidade específica.
RECURSOS_GLOBAIS = ('ouro', 'ciencia', 'fe')
RECURSOS_LOCAIS_CIDADE = ('alimento', 'producao', 'lealdade', 'felicidade')

# Economia deliberadamente baixa no começo. Tecnologias e melhorias escalam depois.
RENDIMENTOS_BASE_CIDADE = {
    'alimento': 1,
    'producao': 1,
    'fe': 1,
    'ciencia': 1,
    'ouro': 1,
    'lealdade': 1,
    'felicidade': 0,
}

# O terreno sem melhoria contribui pouco. A cidade usa seu tile central e melhorias.
RENDIMENTOS_TERRENO = {
    'Grama': {'alimento': 1, 'producao': 0, 'ouro': 0, 'ciencia': 0, 'fe': 0},
    'Deserto': {'alimento': 0, 'producao': 0, 'ouro': 0, 'ciencia': 0, 'fe': 0},
    'Neve': {'alimento': 0, 'producao': 0, 'ouro': 0, 'ciencia': 0, 'fe': 0},
    'Montanha': {'alimento': 0, 'producao': 1, 'ouro': 0, 'ciencia': 0, 'fe': 0},
    'Água Rasa': {'alimento': 0, 'producao': 0, 'ouro': 1, 'ciencia': 0, 'fe': 0},
    'Água Profunda': {'alimento': 0, 'producao': 0, 'ouro': 0, 'ciencia': 0, 'fe': 0},
}

# Recursos especiais só dão seus bônus se o tile tiver uma melhoria compatível.
VARIANTES_TERRENO = {
    'Grama': [
        {'nome': None, 'peso': 68, 'icone': '', 'modificadores': {}, 'melhorias_ativadoras': []},
        {'nome': 'Solo Fértil', 'peso': 22, 'icone': '✿', 'modificadores': {'alimento': 1}, 'melhorias_ativadoras': ['Fazenda']},
        {'nome': 'Minério', 'peso': 10, 'icone': '◆', 'modificadores': {'producao': 1}, 'melhorias_ativadoras': ['Mina']},
    ],
    'Deserto': [
        {'nome': None, 'peso': 88, 'icone': '', 'modificadores': {}, 'melhorias_ativadoras': []},
        {'nome': 'Oásis', 'peso': 12, 'icone': '◉', 'modificadores': {'alimento': 1, 'ouro': 1}, 'melhorias_ativadoras': ['Fazenda']},
    ],
    'Neve': [
        {'nome': None, 'peso': 94, 'icone': '', 'modificadores': {}, 'melhorias_ativadoras': []},
        {'nome': 'Minério', 'peso': 6, 'icone': '◆', 'modificadores': {'producao': 1}, 'melhorias_ativadoras': ['Mina']},
    ],
    'Montanha': [
        {'nome': None, 'peso': 70, 'icone': '', 'modificadores': {}, 'melhorias_ativadoras': []},
        {'nome': 'Minério', 'peso': 30, 'icone': '◆', 'modificadores': {'producao': 1}, 'melhorias_ativadoras': ['Mina']},
    ],
    'Água Rasa': [
        {'nome': None, 'peso': 70, 'icone': '', 'modificadores': {}, 'melhorias_ativadoras': []},
        {'nome': 'Peixes', 'peso': 30, 'icone': '♓', 'modificadores': {'alimento': 1}, 'melhorias_ativadoras': ['Barco de Pesca']},
    ],
    'Água Profunda': [
        {'nome': None, 'peso': 88, 'icone': '', 'modificadores': {}, 'melhorias_ativadoras': []},
        {'nome': 'Cardume', 'peso': 12, 'icone': '♓', 'modificadores': {'alimento': 1, 'ouro': 1}, 'melhorias_ativadoras': ['Barco de Pesca']},
    ],
}

# Melhorias terrestres atuais. Pesca fica preparada para tecnologia futura.
MELHORIAS = {
    'Fazenda': {'icone': '♨', 'bonus': {'alimento': 1}, 'requisitos': []},
    'Pasto': {'icone': '♧', 'bonus': {'alimento': 1}, 'requisitos': []},
    # Preparadas para tecnologias futuras; ainda não aparecem para o Trabalhador.
    'Mina': {'icone': '⛏', 'bonus': {'producao': 1}, 'requisitos': []},
    'Barco de Pesca': {'icone': '⚓', 'bonus': {'alimento': 1}, 'requisitos': []},
}

# Efeitos de composição do entorno: pequenos, para não inflar a economia.
REGRAS_ENTORNO_CIDADE = [
    {
        'nome': 'Terras cultiváveis',
        'terrenos': ['Grama'], 'minimo': 5,
        'modificadores': [
            {'atributo': 'alimento_por_turno', 'operacao': 'somar', 'valor': 1},
        ],
    },
    {
        'nome': 'Relevo produtivo',
        'terrenos': ['Montanha'], 'minimo': 3,
        'modificadores': [
            {'atributo': 'producao_por_turno', 'operacao': 'somar', 'valor': 1},
            {'atributo': 'alimento_por_turno', 'operacao': 'subtrair', 'valor': 1},
        ],
    },
    {
        'nome': 'Acesso costeiro',
        'terrenos': ['Água Rasa', 'Água Profunda'], 'minimo': 3,
        'modificadores': [
            {'atributo': 'ouro_por_turno', 'operacao': 'somar', 'valor': 1},
        ],
    },
]

ICONES_RECURSOS = {
    'alimento': '●',
    'producao': '⚙',
    'ouro': '¤',
    'ciencia': '✦',
    'fe': '✝',
    'lealdade': '♥',
    'felicidade': '☺',
}

LIMITES_LEALDADE = [50, 100, 200, 300, 500]

ICONES_TERRENO = {
    'Grama': '♣',
    'Deserto': '☼',
    'Neve': '✧',
    'Montanha': '▲',
    'Água Rasa': '≈',
    'Água Profunda': '≋',
}


# Infraestrutura de mapa. Estradas podem coexistir com melhorias como Fazenda/Pasto.
INFRAESTRUTURA = {
    'Estrada': {
        'nome': 'Estrada',
        'icone': '═',
        'custo_movimento': 0.5,
        'bonus_conexao_capital': {'ouro': 1, 'lealdade': 1},
    },
    'Rio': {
        'nome': 'Rio',
        'bonus_cidade_ribeirinha': {'alimento': 1},
        'bonus_fazenda_ribeirinha': {'alimento': 1},
    },
}

# Geração procedural de rios. Números provisórios e fáceis de balancear.
CONFIG_RIOS = {
    # Meta de rios em um mapa-base 36x36; cresce proporcionalmente ao lado equivalente do mapa.
    # Valores mais altos deixam a hidrografia claramente presente sem explodir nos mapas grandes.
    'densidades': {
        'Poucos': 5.0,
        'Médio': 10.0,
        'Alto': 18.0,
    },
    'comprimento_minimo': 5,
    'tentativas_por_rio': 40,
    # Bacias diferentes mantêm uma faixa de separação visual/hidrológica.
    'distancia_min_bacias': {'Poucos': 2, 'Médio': 1, 'Alto': 1},
    'max_afluentes_por_rio': 2,
    'terrenos_nascente': ['Grama'],
    'terrenos_percurso': ['Grama', 'Deserto', 'Neve'],
}
