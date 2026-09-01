class Unidade:
    ICONES = {
        "Settler": "S",
        "Warrior": "W",
    }

    def __init__(self, tipo, x, y):
        self.tipo = tipo
        self.x = x
        self.y = y
        self.movimento_max = 1
        self.movimento = self.movimento_max
        self.rota = []
        self.selecionada = False

    @property
    def icone(self):
        return self.ICONES.get(self.tipo, "U")

    def definir_rota(self, rota):
        self.rota = list(rota)

    def mover_um_passo(self):
        if self.movimento <= 0 or not self.rota:
            return False

        self.x, self.y = self.rota.pop(0)
        self.movimento -= 1
        return True

    def novo_turno(self):
        self.movimento = self.movimento_max


class Cidade:
    CUSTOS_UNIDADES = {
        "Settler": 3,
        "Warrior": 3,
    }

    CUSTOS_CONSTRUCOES = {
        "Templo": 5,
        "Muralha": 3,
    }

    def __init__(self, nome, x, y):
        self.nome = nome
        self.x = x
        self.y = y
        self.construcoes = []
        self.producao_tipo = None
        self.producao_nome = None
        self.turnos_restantes = 0

    def iniciar_producao(self, categoria, nome):
        if self.producao_nome is not None:
            return False

        if categoria == "unidade":
            custo = self.CUSTOS_UNIDADES.get(nome)
        else:
            custo = self.CUSTOS_CONSTRUCOES.get(nome)

        if custo is None:
            return False

        self.producao_tipo = categoria
        self.producao_nome = nome
        self.turnos_restantes = custo
        return True

    def avancar_turno(self):
        if self.producao_nome is None:
            return None

        self.turnos_restantes -= 1

        if self.turnos_restantes > 0:
            return None

        resultado = (self.producao_tipo, self.producao_nome)

        if self.producao_tipo == "construcao":
            if self.producao_nome not in self.construcoes:
                self.construcoes.append(self.producao_nome)

        self.producao_tipo = None
        self.producao_nome = None
        self.turnos_restantes = 0
        return resultado
