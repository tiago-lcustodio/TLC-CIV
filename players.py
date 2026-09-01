from data import CIVILIZACOES, DIFICULDADES, TECNOLOGIAS, POLITICAS


class Jogador:
    def __init__(self, jogador_id, nome, cor, civilizacao, humano=True, dificuldade='Padrão'):
        self.id = jogador_id
        self.nome = nome
        self.cor = tuple(cor)
        self.civilizacao = civilizacao
        self.humano = humano
        self.dificuldade = dificuldade

        self.unidades = []
        self.cidades = []
        self.tecnologias = {'Conhecimento Inicial'}
        self.politicas = set()
        self.era = 'Antiga'
        self.explorado = set()
        self.visivel = set()

    def possui_tecnologia(self, nome):
        return nome is None or nome in self.tecnologias

    def modificadores(self):
        mods = []
        civ = CIVILIZACOES.get(self.civilizacao, {})
        mods.extend(civ.get('modificadores', []))

        for tecnologia in self.tecnologias:
            mods.extend(TECNOLOGIAS.get(tecnologia, {}).get('modificadores', []))
        for politica in self.politicas:
            mods.extend(POLITICAS.get(politica, {}).get('modificadores', []))

        if not self.humano:
            dif = DIFICULDADES.get(self.dificuldade, {})
            mapa = {
                'cpu_bonus_producao_pct': 'producao_por_turno',
                'cpu_bonus_ciencia_pct': 'ciencia_por_turno',
                'cpu_bonus_fe_pct': 'fe_por_turno',
                'cpu_bonus_alimento_pct': 'alimento_por_turno',
                'cpu_bonus_ouro_pct': 'ouro_por_turno',
            }
            for chave, atributo in mapa.items():
                valor = dif.get(chave, 0)
                if valor:
                    mods.append({'atributo': atributo, 'operacao': 'percentual', 'valor': valor})
        return mods
