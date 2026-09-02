from data import CIVILIZACOES, DIFICULDADES, TECNOLOGIAS, POLITICAS


class Jogador:
    def __init__(self, jogador_id, nome, cor, civilizacao, humano=True, dificuldade='Padrão', uid=None,
                 tipo='civilizacao', lider_nome=None, lider_genero=None):
        self.id = jogador_id
        self.uid = uid or f'P{int(jogador_id)+1:06d}'
        self.nome = nome
        self.cor = tuple(cor)
        self.civilizacao = civilizacao
        self.humano = humano
        self.dificuldade = dificuldade
        self.tipo = tipo  # civilizacao | cidade_estado | barbaro
        self.lider_nome = lider_nome
        self.lider_genero = lider_genero

        self.unidades = []
        self.cidades = []
        self.tecnologias = {'Conhecimento Inicial'}
        self.politicas = set()
        self.era = 'Antiga'
        self.pesquisa_atual = None
        self.progresso_pesquisa = 0
        self.explorado = set()
        self.visivel = set()

        # Recursos globais: Ouro, Ciência e Fé pertencem ao império inteiro.
        self.ouro = 0
        self.ciencia = 0
        self.fe = 0

        self.capital_id = None
        self.modificadores_temporarios = []

        # Diplomacia. Contatos são UIDs conhecidos por este jogador.
        self.contatos_diplomaticos = set()
        self.humor_relacoes = {}

    def possui_tecnologia(self, nome):
        return nome is None or nome in self.tecnologias

    def desbloqueios(self):
        from requirements import MotorRequisitos
        return MotorRequisitos.desbloqueios_do_jogador(self)

    def adicionar_recursos_globais(self, ouro=0, ciencia=0, fe=0):
        self.ouro += ouro
        self.ciencia += ciencia
        self.fe += fe

    def gastar_recurso_global(self, recurso, valor):
        atual = getattr(self, recurso, 0)
        if atual < valor:
            return False
        setattr(self, recurso, atual - valor)
        return True

    def adicionar_modificador_temporario(self, modificador):
        mod = dict(modificador)
        self.modificadores_temporarios.append(mod)
        return mod

    def avancar_modificadores_temporarios(self):
        ativos = []
        for mod in self.modificadores_temporarios:
            duracao = mod.get('duracao')
            if duracao is None:
                ativos.append(mod)
                continue
            duracao = int(duracao) - 1
            if duracao > 0:
                novo = dict(mod); novo['duracao'] = duracao; ativos.append(novo)
        self.modificadores_temporarios = ativos

    def registrar_contato(self, outro_uid, humor_inicial=0):
        novo = outro_uid not in self.contatos_diplomaticos
        self.contatos_diplomaticos.add(outro_uid)
        self.humor_relacoes.setdefault(outro_uid, int(humor_inicial))
        return novo

    def humor_com(self, outro_uid):
        return int(self.humor_relacoes.get(outro_uid, 0))

    @staticmethod
    def texto_humor(valor):
        valor = int(valor)
        if valor <= -50: return 'Hostil'
        if valor <= -10: return 'Desconfiado'
        if valor < 10: return 'Neutro'
        if valor < 50: return 'Cordial'
        return 'Amigável'

    def modificadores(self):
        mods = []
        civ = CIVILIZACOES.get(self.civilizacao, {})
        mods.extend(civ.get('modificadores', []))
        for tecnologia in self.tecnologias:
            mods.extend(TECNOLOGIAS.get(tecnologia, {}).get('modificadores', []))
        for politica in self.politicas:
            mods.extend(POLITICAS.get(politica, {}).get('modificadores', []))
        mods.extend(self.modificadores_temporarios)

        if not self.humano and self.tipo == 'civilizacao':
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
                    mods.append({'atributo': atributo, 'operacao': 'percentual', 'valor': valor,
                                 'escopo': 'jogador', 'duracao': None})
        return mods
