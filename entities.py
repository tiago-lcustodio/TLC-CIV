import math

from data import UNIDADES, CONSTRUCOES, LIMITES_LEALDADE
from requirements import MotorRequisitos


class Unidade:
    def __init__(self, tipo, x, y, dono_id, entidade_id=None):
        dados = UNIDADES[tipo]
        self.tipo = tipo
        self.id = entidade_id
        self.x = x
        self.y = y
        self.dono_id = dono_id
        self.movimento_max = dados['movimento']
        self.movimento = float(self.movimento_max)
        self.rota = []
        self.selecionada = False
        self.fortificada = False
        self.melhorias_max = dados.get('melhorias_max', 0)
        self.melhorias_construidas = 0
        self.embarcada_em = None
        self.carga = []
        self.forca = dados.get('forca', 0)
        self.defesa = dados.get('defesa', 0)
        self.vida_max = dados.get('vida_max', 100)
        self.vida = self.vida_max
        self.alcance = dados.get('alcance', 1)
        self.classe = dados.get('classe', 'outro')
        self.experiencia = 0
        self.nivel = 1
        self.modificadores_temporarios = []

    @property
    def icone(self):
        return UNIDADES[self.tipo].get('icone', UNIDADES[self.tipo].get('sigla', '?'))

    @property
    def sigla(self):
        return UNIDADES[self.tipo].get('sigla', '??')

    @property
    def letra(self):
        return UNIDADES[self.tipo].get('letra', self.tipo[:1].upper())

    @property
    def marcador(self):
        return UNIDADES[self.tipo].get('marcador', self.letra)

    @property
    def dominio(self):
        return UNIDADES[self.tipo]['dominio']

    @property
    def capacidade_transporte(self):
        return UNIDADES[self.tipo].get('capacidade_transporte', 0)

    @property
    def transporta_dominios(self):
        return UNIDADES[self.tipo].get('transporta_dominios', [])

    @property
    def esta_embarcada(self):
        return self.embarcada_em is not None

    def pode_embarcar(self, unidade):
        return (
            self.capacidade_transporte > len(self.carga)
            and unidade.dominio in self.transporta_dominios
            and unidade.dono_id == self.dono_id
            and unidade is not self
            and not unidade.esta_embarcada
        )

    def embarcar(self, unidade):
        if not self.pode_embarcar(unidade):
            return False
        unidade.embarcada_em = self
        unidade.cancelar_rota()
        unidade.movimento = 0
        unidade.fortificada = False
        self.carga.append(unidade)
        return True

    def desembarcar(self, unidade, x, y):
        if unidade not in self.carga:
            return False
        self.carga.remove(unidade)
        unidade.embarcada_em = None
        unidade.x = x
        unidade.y = y
        unidade.movimento = 0
        unidade.fortificada = False
        return True

    def definir_rota(self, rota):
        self.rota = list(rota)
        if self.rota:
            self.fortificada = False

    def cancelar_rota(self):
        self.rota = []

    def _sincronizar_carga(self):
        for unidade in self.carga:
            unidade.x = self.x
            unidade.y = self.y

    def mover_um_passo(self, custo=1.0):
        custo = float(custo)
        if self.movimento + 1e-9 < custo or not self.rota or self.esta_embarcada:
            return False
        self.x, self.y = self.rota.pop(0)
        self.movimento = max(0.0, self.movimento - custo)
        self._sincronizar_carga()
        return True

    def mover_ate_esgotar(self, custo_func=None):
        passos = 0
        while self.movimento > 1e-9 and self.rota:
            destino = self.rota[0]
            custo = custo_func((self.x, self.y), destino) if custo_func else 1.0
            if self.movimento + 1e-9 < custo:
                break
            if not self.mover_um_passo(custo):
                break
            passos += 1
        return passos

    def novo_turno(self):
        if not self.esta_embarcada:
            self.movimento = float(self.movimento_max)
        self.cancelar_rota()

    def fortificar(self):
        if self.esta_embarcada:
            return
        self.fortificada = True
        self.movimento = 0
        self.cancelar_rota()

    def registrar_melhoria(self):
        if self.tipo != 'Trabalhador':
            return False
        self.melhorias_construidas += 1
        return self.melhorias_construidas >= self.melhorias_max

    @property
    def melhorias_restantes(self):
        if self.tipo != 'Trabalhador':
            return None
        return max(0, self.melhorias_max - self.melhorias_construidas)

    def adicionar_modificador_temporario(self, modificador):
        self.modificadores_temporarios.append(dict(modificador))

    def avancar_modificadores_temporarios(self):
        ativos=[]
        for mod in self.modificadores_temporarios:
            duracao=mod.get('duracao')
            if duracao is None:
                ativos.append(mod); continue
            duracao=int(duracao)-1
            if duracao>0:
                novo=dict(mod); novo['duracao']=duracao; ativos.append(novo)
        self.modificadores_temporarios=ativos


class AcampamentoBarbaro:
    def __init__(self, x, y, dono_id, entidade_id=None):
        self.id = entidade_id
        self.x = x
        self.y = y
        self.dono_id = dono_id
        self.ativo = True



class Cidade:
    # Crescimento linear e bem mais lento: Pop 2=90, Pop 3=180, Pop 4=270...
    LIMITES_POPULACAO = [90 * i for i in range(1, 51)]

    def __init__(self, nome, x, y, dono_id, entidade_id=None):
        self.id = entidade_id
        self.nome = nome
        self.x = x
        self.y = y
        self.dono_id = dono_id
        self.construcoes = []
        self.producao_tipo = None
        self.producao_nome = None
        self.custo_producao_atual = 0
        self.producao_por_turno_inicio = 0
        self.turnos_producao_total = 0
        self.turnos_producao_restantes = 0
        self.populacao = 1
        self.alimento = 0
        self.producao = 0
        self.fe = 0
        self.ciencia = 0
        self.ouro = 0
        self.lealdade = 0
        self.felicidade = 1
        self.em_revolta = False
        self.capital = False
        self.melhorias = []
        self.raio_territorio = 1
        self.tiles_territorio = set()
        self.limites_lealdade_atingidos = set()
        self.modificadores_temporarios = []

    def limite_proxima_populacao(self):
        i = self.populacao - 1
        return self.LIMITES_POPULACAO[i] if 0 <= i < len(self.LIMITES_POPULACAO) else None

    def proximo_limite_lealdade(self):
        for limite in LIMITES_LEALDADE:
            if limite not in self.limites_lealdade_atingidos:
                return limite
        return None

    def adicionar_recursos(self, alimento=0, producao=0, fe=0, ciencia=0, ouro=0, lealdade=0, felicidade=0):
        self.alimento += alimento
        self.producao += producao
        self.fe += fe
        self.ciencia += ciencia
        self.ouro += ouro
        self.lealdade += lealdade
        self.felicidade += felicidade

        cresceu = False
        while True:
            limite = self.limite_proxima_populacao()
            if limite is None or self.alimento < limite:
                break
            self.populacao += 1
            # Pressão urbana: a partir da População 7, cada novo nível custa 1 Felicidade.
            if self.populacao >= 7:
                self.felicidade -= 1
            cresceu = True

        expansoes = 0
        for limite in LIMITES_LEALDADE:
            if self.lealdade >= limite and limite not in self.limites_lealdade_atingidos:
                self.limites_lealdade_atingidos.add(limite)
                self.raio_territorio += 1
                expansoes += 1
        return cresceu, expansoes

    def adicionar_modificador_temporario(self, modificador):
        self.modificadores_temporarios.append(dict(modificador))

    def avancar_modificadores_temporarios(self):
        ativos=[]
        for mod in self.modificadores_temporarios:
            duracao=mod.get('duracao')
            if duracao is None:
                ativos.append(mod); continue
            duracao=int(duracao)-1
            if duracao>0:
                novo=dict(mod); novo['duracao']=duracao; ativos.append(novo)
        self.modificadores_temporarios=ativos

    def iniciar_producao(self, categoria, nome, jogador, producao_por_turno=1, jogo=None):
        if self.producao_nome is not None:
            return False, 'A cidade já possui uma produção em andamento.'
        if categoria == 'unidade':
            dados = UNIDADES.get(nome)
            if not dados:
                return False, 'Unidade inválida.'
            ok, motivo = MotorRequisitos.verificar(dados, jogador, jogo=jogo, cidade=self)
            if not ok:
                return False, motivo
            if self.populacao < dados.get('populacao_min', 0):
                return False, f'População insuficiente para produzir {nome}.'
            custo = dados['custo_producao']
            self.populacao -= dados.get('consome_populacao', 0)
        else:
            dados = CONSTRUCOES.get(nome)
            if not dados:
                return False, 'Construção inválida.'
            if nome in self.construcoes:
                return False, f'{nome} já existe na cidade.'
            ok, motivo = MotorRequisitos.verificar(dados, jogador, jogo=jogo, cidade=self)
            if not ok:
                return False, motivo
            custo = dados['custo_producao']

        taxa = max(1, int(producao_por_turno))
        turnos = max(1, int(math.ceil(custo / taxa)))
        self.producao_tipo = categoria
        self.producao_nome = nome
        self.custo_producao_atual = custo
        self.producao_por_turno_inicio = taxa
        self.turnos_producao_total = turnos
        self.turnos_producao_restantes = turnos
        return True, ''

    def avancar_producao(self):
        if self.producao_nome is None:
            return None
        self.turnos_producao_restantes -= 1
        if self.turnos_producao_restantes > 0:
            return None

        resultado = (self.producao_tipo, self.producao_nome)
        if self.producao_tipo == 'construcao' and self.producao_nome not in self.construcoes:
            self.construcoes.append(self.producao_nome)

        self.producao_tipo = None
        self.producao_nome = None
        self.custo_producao_atual = 0
        self.producao_por_turno_inicio = 0
        self.turnos_producao_total = 0
        self.turnos_producao_restantes = 0
        return resultado
