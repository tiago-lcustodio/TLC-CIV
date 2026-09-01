import math
import random
import pygame

from world import Mundo, VIZINHOS_8
from entities import Unidade, Cidade
from players import Jogador
from modifiers import MotorModificadores
from ai import ControladorIA
from timeline import CalendarioJogo
from data import (
    CORES_JOGADOR, CIVILIZACOES, UNIDADES, CONSTRUCOES,
    RENDIMENTOS_BASE_CIDADE, REGRAS_ENTORNO_CIDADE, ICONES_RECURSOS, ICONES_TERRENO, MELHORIAS,
)

TAMANHO_TILE = 34
ALTURA_BARRA_MENU = 28
ALTURA_BARRA_STATUS = 30
ALTURA_BARRA_FERRAMENTAS = 44
TOPO_MAPA = ALTURA_BARRA_MENU + ALTURA_BARRA_STATUS + ALTURA_BARRA_FERRAMENTAS

CORES_TERRENO = {
    'Grama': (74, 154, 75),
    'Água Rasa': (69, 143, 205),
    'Água Profunda': (35, 77, 145),
    'Montanha': (128, 94, 70),
    'Deserto': (222, 196, 91),
    'Neve': (238, 241, 244),
}
COR_GRADE = (50, 55, 55)


class Jogo:
    def __init__(self, tela, configuracao):
        self.tela = tela
        self.configuracao = configuracao
        self.fonte = pygame.font.SysFont('arial', 16)
        self.fonte_pequena = pygame.font.SysFont('arial', 13)
        self.fonte_mini = pygame.font.SysFont('arial', 10, bold=True)
        self.fonte_negrito = pygame.font.SysFont('arial', 14, bold=True)
        self.fonte_grande = pygame.font.SysFont('arial', 25, bold=True)
        self.fonte_icone = pygame.font.SysFont('dejavusans', 20)
        self.fonte_icone_grande = pygame.font.SysFont('dejavusans', 23, bold=True)
        self.fonte_indicador = pygame.font.SysFont('dejavusans', 14, bold=True)

        self.mundo = Mundo(configuracao['largura_mapa'], configuracao['altura_mapa'], configuracao['percentuais'])
        self.turno = 1
        self.calendario = CalendarioJogo()
        self.offset_x = self.offset_y = 0
        self.velocidade_scroll = 42

        self.jogadores = []
        self.controladores_ia = {}
        self.unidades = []
        self.cidades = []
        self.unidade_selecionada = None
        self.cidade_modal = None
        self.modal = None
        self.menu_aberto = None
        self.campo_nome = ''
        self.mensagem = 'Selecione uma unidade e clique em um destino.'
        self.notificacoes = []
        self.notificacao_atual = None
        self.ajuda_contexto = None
        self.ultimo_clique_esquerdo_ms = -1000
        self.ultimo_clique_esquerdo_tile = None
        self.limite_duplo_clique_ms = 350

        self._criar_jogadores()
        self.jogador_humano = self.jogadores[0]
        self._criar_posicoes_iniciais()
        self._atualizar_layout()
        if self.jogador_humano.unidades:
            u = self.jogador_humano.unidades[0]
            self.centralizar_camera(u.x, u.y)
        self.atualizar_visibilidade_todos()

    # ---------- jogadores / setup ----------
    def _criar_jogadores(self):
        humano = Jogador(0, 'Jogador', self.configuracao['cor_jogador'], self.configuracao['civilizacao'], True, self.configuracao['dificuldade'])
        self.jogadores.append(humano)
        civs = [c for c in CIVILIZACOES if c != humano.civilizacao]
        cores = [c for c in CORES_JOGADOR if tuple(CORES_JOGADOR[c]) != tuple(humano.cor)]
        random.shuffle(civs); random.shuffle(cores)
        for i in range(self.configuracao.get('numero_cpus', 0)):
            cpu = Jogador(i + 1, f'CPU {i+1}', CORES_JOGADOR[cores[i % len(cores)]], civs[i % len(civs)], False, self.configuracao['dificuldade'])
            self.jogadores.append(cpu)
            self.controladores_ia[cpu.id] = ControladorIA(cpu.id)

    def _posicao_passavel_proxima(self, alvo_x, alvo_y, ocupadas):
        max_r = max(self.mundo.largura, self.mundo.altura)
        for r in range(max_r):
            for y in range(max(0, alvo_y-r), min(self.mundo.altura, alvo_y+r+1)):
                for x in range(max(0, alvo_x-r), min(self.mundo.largura, alvo_x+r+1)):
                    if (x, y) not in ocupadas and self.mundo.passavel(x, y):
                        return x, y
        return self.mundo.encontrar_posicao_inicial()

    def _criar_posicoes_iniciais(self):
        alvos = [
            (self.mundo.largura // 2, self.mundo.altura // 2),
            (self.mundo.largura // 5, self.mundo.altura // 5),
            (self.mundo.largura * 4 // 5, self.mundo.altura // 5),
            (self.mundo.largura // 2, self.mundo.altura * 4 // 5),
        ]
        ocupadas = set()
        for jogador, alvo in zip(self.jogadores, alvos):
            x, y = self._posicao_passavel_proxima(*alvo, ocupadas)
            ocupadas.add((x, y))
            self._adicionar_unidade(Unidade('Colono', x, y, jogador.id))

    def jogador_por_id(self, jogador_id):
        return next((j for j in self.jogadores if j.id == jogador_id), None)

    def _adicionar_unidade(self, unidade):
        if unidade not in self.unidades:
            self.unidades.append(unidade)
        jogador = self.jogador_por_id(unidade.dono_id)
        if jogador and unidade not in jogador.unidades:
            jogador.unidades.append(unidade)

    def _remover_unidade(self, unidade):
        # Se for transporte, desembarca/desvincula carga antes de remover.
        for carga in list(unidade.carga):
            carga.embarcada_em = None
            unidade.carga.remove(carga)
        if unidade.esta_embarcada and unidade.embarcada_em:
            transportador = unidade.embarcada_em
            if unidade in transportador.carga:
                transportador.carga.remove(unidade)
            unidade.embarcada_em = None
        if unidade in self.unidades:
            self.unidades.remove(unidade)
        jogador = self.jogador_por_id(unidade.dono_id)
        if jogador and unidade in jogador.unidades:
            jogador.unidades.remove(unidade)
        if self.unidade_selecionada is unidade:
            self.selecionar_unidade(None)

    def _adicionar_cidade(self, cidade):
        self.cidades.append(cidade)
        jogador = self.jogador_por_id(cidade.dono_id)
        if jogador and cidade not in jogador.cidades:
            jogador.cidades.append(cidade)
        self._inicializar_territorio_cidade(cidade)

    def _tile_controlado_por_outra_cidade(self, x, y, cidade_atual=None):
        for outra in self.cidades:
            if outra is cidade_atual:
                continue
            if (x, y) in outra.tiles_territorio:
                return outra
        return None

    def _candidatos_territorio(self, cidade):
        r = cidade.raio_territorio
        candidatos = []
        for y in range(cidade.y-r, cidade.y+r+1):
            for x in range(cidade.x-r, cidade.x+r+1):
                if self.mundo.dentro(x, y):
                    distancia = max(abs(x-cidade.x), abs(y-cidade.y))
                    candidatos.append((distancia, x, y))
        candidatos.sort()
        return candidatos

    def _inicializar_territorio_cidade(self, cidade):
        for _, x, y in self._candidatos_territorio(cidade):
            if self._tile_controlado_por_outra_cidade(x, y, cidade) is None:
                cidade.tiles_territorio.add((x, y))

    def _expandir_territorio_cidade(self, cidade):
        antes = len(cidade.tiles_territorio)
        for _, x, y in self._candidatos_territorio(cidade):
            if (x, y) in cidade.tiles_territorio:
                continue
            if self._tile_controlado_por_outra_cidade(x, y, cidade) is None:
                cidade.tiles_territorio.add((x, y))
        return len(cidade.tiles_territorio) - antes

    # ---------- layout ----------
    def _atualizar_layout(self):
        self.largura_tela, self.altura_tela = self.tela.get_size()
        self.viewport = pygame.Rect(0, TOPO_MAPA, max(100, self.largura_tela - 14), max(100, self.altura_tela - TOPO_MAPA - 14))
        self.rect_menu_jogo = pygame.Rect(10, 1, 72, 26)
        self.rect_menu_ajuda = pygame.Rect(88, 1, 72, 26)
        self.rect_novo = pygame.Rect(10, ALTURA_BARRA_MENU, 135, 30)
        self.rect_sair = pygame.Rect(10, ALTURA_BARRA_MENU + 30, 135, 30)
        self.rect_sobre = pygame.Rect(88, ALTURA_BARRA_MENU, 135, 30)

        y = ALTURA_BARRA_MENU + ALTURA_BARRA_STATUS + 5
        x = 8
        self.rect_proximo_turno = pygame.Rect(x, y, 112, 32); x += 118
        self.rect_politica = pygame.Rect(x, y, 72, 32); x += 78
        self.rect_tecnologia = pygame.Rect(x, y, 88, 32); x += 94
        self.rect_religiao = pygame.Rect(x, y, 76, 32); x += 82
        self.rect_economia = pygame.Rect(x, y, 78, 32); x += 84
        self.rect_diplomacia = pygame.Rect(x, y, 88, 32); x += 94
        self.rect_militar = pygame.Rect(x, y, 68, 32); x += 76
        self.x_acoes = x
        self.rect_fundar = pygame.Rect(x, y, 116, 32)
        self.rect_fazenda = pygame.Rect(x, y, 92, 32)
        self.rect_pasto = pygame.Rect(x + 98, y, 82, 32)
        self.limitar_camera()

    def centralizar_camera(self, x, y):
        self.offset_x = x * TAMANHO_TILE - self.viewport.width // 2
        self.offset_y = y * TAMANHO_TILE - self.viewport.height // 2
        self.limitar_camera()

    def limitar_camera(self):
        if not hasattr(self, 'viewport'): return
        lw, lh = self.mundo.largura*TAMANHO_TILE, self.mundo.altura*TAMANHO_TILE
        self.offset_x = max(0, min(self.offset_x, max(0, lw-self.viewport.width)))
        self.offset_y = max(0, min(self.offset_y, max(0, lh-self.viewport.height)))

    def tile_para_tela(self, x, y):
        return x*TAMANHO_TILE-self.offset_x, TOPO_MAPA+y*TAMANHO_TILE-self.offset_y

    def tela_para_tile(self, pos):
        if not self.viewport.collidepoint(pos): return None
        x = int((pos[0]+self.offset_x)//TAMANHO_TILE)
        y = int((pos[1]-TOPO_MAPA+self.offset_y)//TAMANHO_TILE)
        return (x, y) if self.mundo.dentro(x, y) else None

    # ---------- visão / território ----------
    def revelar_area(self, cx, cy, raio, destino):
        for y in range(cy-raio, cy+raio+1):
            for x in range(cx-raio, cx+raio+1):
                if self.mundo.dentro(x, y): destino.add((x, y))

    def atualizar_visibilidade_jogador(self, jogador):
        jogador.visivel = set()
        for u in jogador.unidades:
            if not u.esta_embarcada:
                self.revelar_area(u.x, u.y, 2, jogador.visivel)
        for c in jogador.cidades:
            self.revelar_area(c.x, c.y, 3, jogador.visivel)
            jogador.visivel.update(self.territorio_cidade(c))
        jogador.explorado.update(jogador.visivel)

    def atualizar_visibilidade_todos(self):
        for j in self.jogadores:
            self.atualizar_visibilidade_jogador(j)

    def territorio_cidade(self, cidade):
        if not cidade.tiles_territorio:
            self._inicializar_territorio_cidade(cidade)
        return set(cidade.tiles_territorio)

    def cidade_dona_tile(self, x, y, dono_id=None):
        for c in self.cidades:
            if dono_id is not None and c.dono_id != dono_id: continue
            if (x, y) in self.territorio_cidade(c): return c
        return None

    # ---------- busca ----------
    def unidade_em(self, x, y, dono_id=None, incluir_embarcadas=False):
        for u in reversed(self.unidades):
            if u.esta_embarcada and not incluir_embarcadas:
                continue
            if u.x == x and u.y == y and (dono_id is None or u.dono_id == dono_id):
                return u
        return None

    def unidades_em(self, x, y, dono_id=None):
        return [u for u in self.unidades if not u.esta_embarcada and u.x == x and u.y == y and (dono_id is None or u.dono_id == dono_id)]

    def cidade_em(self, x, y):
        return next((c for c in self.cidades if c.x == x and c.y == y), None)

    def selecionar_unidade(self, unidade):
        for u in self.unidades: u.selecionada = False
        self.unidade_selecionada = unidade
        if unidade:
            unidade.selecionada = True
            carga = f' | Carga {len(unidade.carga)}/{unidade.capacidade_transporte}' if unidade.capacidade_transporte else ''
            self.mensagem = f'{unidade.icone} {unidade.tipo} selecionado.{carga}'

    # ---------- economia / modificadores ----------
    def modificadores_entorno_cidade(self, cidade):
        contagem = {}
        for x, y in self.territorio_cidade(cidade):
            t = self.mundo.terreno(x, y)
            contagem[t] = contagem.get(t, 0) + 1
        mods, nomes = [], []
        for regra in REGRAS_ENTORNO_CIDADE:
            qtd = sum(contagem.get(t, 0) for t in regra['terrenos'])
            if qtd >= regra['minimo']:
                mods.extend(regra.get('modificadores', []))
                nomes.append(regra['nome'])
        return mods, nomes

    def modificadores_cidade(self, cidade):
        jogador = self.jogador_por_id(cidade.dono_id)
        mods = list(jogador.modificadores()) if jogador else []
        for nome in cidade.construcoes:
            mods.extend(CONSTRUCOES.get(nome, {}).get('modificadores', []))
        entorno, _ = self.modificadores_entorno_cidade(cidade)
        mods.extend(entorno)
        return mods

    def detalhamento_rendimentos_cidade(self, cidade):
        valores = dict(RENDIMENTOS_BASE_CIDADE)
        detalhes = []
        detalhes.append(('Base da cidade', dict(RENDIMENTOS_BASE_CIDADE)))

        # Somente o tile central é usado automaticamente. Os demais precisam de melhoria.
        central = self.mundo.rendimentos_base_tile(cidade.x, cidade.y)
        for recurso, q in central.items():
            valores[recurso] = valores.get(recurso, 0) + q
        detalhes.append((f'Tile central: {self.mundo.terreno(cidade.x, cidade.y)}', central))

        for tipo, x, y in cidade.melhorias:
            if (x, y) not in self.territorio_cidade(cidade):
                continue
            bonus, fontes = self.mundo.bonus_melhoria_tile(x, y)
            for recurso, q in bonus.items():
                valores[recurso] = valores.get(recurso, 0) + q
            variante = self.mundo.variante_em(x, y)
            rotulo = f'{tipo} ({x},{y})'
            if variante:
                ativada = tipo in variante.get('melhorias_ativadoras', [])
                rotulo += f' | {variante["nome"]}: ' + ('ATIVO' if ativada else 'não explorado')
            detalhes.append((rotulo, bonus))

        mods = self.modificadores_cidade(cidade)
        finais = {
            'alimento': MotorModificadores.aplicar(valores['alimento'], 'alimento_por_turno', mods),
            'producao': MotorModificadores.aplicar(valores['producao'], 'producao_por_turno', mods),
            'fe': MotorModificadores.aplicar(valores['fe'], 'fe_por_turno', mods),
            'ciencia': MotorModificadores.aplicar(valores['ciencia'], 'ciencia_por_turno', mods),
            'ouro': MotorModificadores.aplicar(valores['ouro'], 'ouro_por_turno', mods),
            'lealdade': valores.get('lealdade', 1),
            'felicidade': valores.get('felicidade', 0),
        }
        return finais, detalhes

    def rendimentos_cidade(self, cidade):
        return self.detalhamento_rendimentos_cidade(cidade)[0]

    def totais_civilizacao(self, jogador):
        # Produção é exibida como capacidade atual por turno; os demais são estoques.
        return {
            'alimento': sum(c.alimento for c in jogador.cidades),
            'producao': sum(self.rendimentos_cidade(c)['producao'] for c in jogador.cidades),
            'ouro': sum(c.ouro for c in jogador.cidades),
            'ciencia': sum(c.ciencia for c in jogador.cidades),
            'fe': sum(c.fe for c in jogador.cidades),
            'lealdade': sum(c.lealdade for c in jogador.cidades),
            'felicidade': sum(c.felicidade for c in jogador.cidades),
        }

    # ---------- movimento / transporte ----------
    def pode_fundar(self):
        u = self.unidade_selecionada
        return bool(u and u.dono_id == 0 and not u.esta_embarcada and u.tipo == 'Colono' and u.movimento > 0 and self.cidade_em(u.x, u.y) is None and self.cidade_dona_tile(u.x, u.y) is None)

    def trabalhador_pode_melhorar(self):
        u = self.unidade_selecionada
        return bool(u and u.dono_id == 0 and not u.esta_embarcada and u.tipo == 'Trabalhador' and u.movimento > 0 and self.cidade_dona_tile(u.x,u.y,0) and self.mundo.passavel(u.x,u.y) and self.mundo.melhoria_em(u.x,u.y) is None)

    def ordenar_movimento_unidade(self, unidade, destino):
        if unidade.movimento <= 0 or unidade.esta_embarcada:
            unidade.cancelar_rota(); return False
        rota = self.mundo.caminho((unidade.x, unidade.y), destino, unidade.dominio)
        if not rota and destino != (unidade.x, unidade.y): return False
        unidade.definir_rota(rota)
        unidade.mover_ate_esgotar()
        unidade.cancelar_rota()
        return True

    def ordenar_movimento(self, destino):
        u = self.unidade_selecionada
        if not u or u.dono_id != 0: return
        if u.movimento <= 0:
            u.cancelar_rota(); self.mensagem = 'Movimento esgotado. Passe o turno antes de dar nova ordem.'; return

        terreno_destino = self.mundo.terreno(*destino)
        if u.capacidade_transporte > 0 and u.carga and self.mundo.passavel(*destino):
            self.tentar_desembarcar(u, destino)
            return

        if self.ordenar_movimento_unidade(u, destino):
            self.atualizar_visibilidade_jogador(self.jogador_humano)
            self.mensagem = f'{u.tipo} moveu-se. Movimento: {u.movimento}/{u.movimento_max}.'
        else:
            if u.tipo == 'Galé' and terreno_destino == 'Água Profunda':
                self.mensagem = 'Galé só pode navegar em Água Rasa.'
            else:
                self.mensagem = 'Destino inválido para esta unidade.'

    def mover_unidade_aleatoria(self, unidade):
        candidatos = []
        for dx, dy in VIZINHOS_8:
            nx, ny = unidade.x+dx, unidade.y+dy
            if self.mundo.dentro(nx,ny) and self.mundo.passavel_para(nx,ny,unidade.dominio): candidatos.append((nx,ny))
        if candidatos: self.ordenar_movimento_unidade(unidade, random.choice(candidatos))

    def _adjacentes_passaveis(self, x, y, dominio):
        return [(x+dx,y+dy) for dx,dy in VIZINHOS_8 if self.mundo.dentro(x+dx,y+dy) and self.mundo.passavel_para(x+dx,y+dy,dominio)]

    def tentar_embarcar(self, unidade, transportador):
        if unidade.movimento <= 0:
            self.mensagem = 'Movimento esgotado. Passe o turno antes de embarcar.'; return
        if not transportador.pode_embarcar(unidade):
            self.mensagem = 'Essa unidade naval não pode embarcar esta unidade ou está sem espaço.'; return

        candidatos = self._adjacentes_passaveis(transportador.x, transportador.y, unidade.dominio)
        melhores = []
        for destino in candidatos:
            rota = self.mundo.caminho((unidade.x, unidade.y), destino, unidade.dominio)
            if destino == (unidade.x, unidade.y): rota = []
            if rota or destino == (unidade.x, unidade.y):
                melhores.append((len(rota), destino))
        if not melhores:
            self.mensagem = 'Não há acesso terrestre ao ponto de embarque.'; return
        _, destino = min(melhores, key=lambda item: item[0])
        if destino != (unidade.x, unidade.y):
            self.ordenar_movimento_unidade(unidade, destino)
        if (unidade.x, unidade.y) == destino and max(abs(unidade.x-transportador.x), abs(unidade.y-transportador.y)) == 1:
            if transportador.embarcar(unidade):
                self.selecionar_unidade(transportador)
                self.atualizar_visibilidade_jogador(self.jogador_humano)
                self.mensagem = f'{unidade.tipo} embarcou em {transportador.icone} {transportador.tipo}.'
                return
        self.mensagem = 'A unidade não conseguiu alcançar o ponto de embarque neste turno.'

    def tentar_desembarcar(self, transportador, destino_terra):
        if not transportador.carga:
            self.mensagem = 'O transporte não possui unidade embarcada.'; return
        if transportador.movimento <= 0:
            self.mensagem = 'Movimento esgotado. Passe o turno antes de desembarcar.'; return
        if not self.mundo.passavel(*destino_terra):
            self.mensagem = 'O desembarque exige um quadrado terrestre passável.'; return
        if self.unidade_em(*destino_terra) is not None:
            self.mensagem = 'O quadrado de desembarque está ocupado.'; return

        candidatos = self._adjacentes_passaveis(destino_terra[0], destino_terra[1], transportador.dominio)
        rotas = []
        for agua in candidatos:
            rota = self.mundo.caminho((transportador.x, transportador.y), agua, transportador.dominio)
            if agua == (transportador.x, transportador.y): rota = []
            if rota or agua == (transportador.x, transportador.y):
                rotas.append((len(rota), agua))
        if not rotas:
            self.mensagem = 'Não há Água Rasa acessível junto ao ponto de desembarque.'; return
        _, agua_alvo = min(rotas, key=lambda item:item[0])
        if agua_alvo != (transportador.x, transportador.y):
            self.ordenar_movimento_unidade(transportador, agua_alvo)
        if (transportador.x, transportador.y) != agua_alvo:
            self.mensagem = 'A embarcação não alcançou a costa neste turno.'; return

        unidade = transportador.carga[0]
        transportador.desembarcar(unidade, *destino_terra)
        transportador.movimento = 0
        self.selecionar_unidade(unidade)
        self.atualizar_visibilidade_jogador(self.jogador_humano)
        self.mensagem = f'{unidade.tipo} desembarcou. A embarcação encerrou o movimento do turno.'

    def mover_para_cidade_fortificar(self, cidade):
        u = self.unidade_selecionada
        if not u or u.dono_id != 0: return
        if cidade.dono_id != 0:
            self.mensagem = 'Combate/conquista ainda não implementado.'; return
        if u.dominio != 'terra':
            self.mensagem = 'Unidades navais não podem entrar em uma cidade terrestre.'; return
        if u.movimento <= 0:
            self.mensagem = 'Movimento esgotado. Passe o turno.'; return
        if self.ordenar_movimento_unidade(u,(cidade.x,cidade.y)) and (u.x,u.y)==(cidade.x,cidade.y):
            u.fortificar(); self.mensagem=f'{u.tipo} fortificado em {cidade.nome}.'
        else:
            self.mensagem='A unidade não alcançou a cidade neste turno.'
        self.atualizar_visibilidade_jogador(self.jogador_humano)

    # ---------- cidades / produção ----------
    def fundar_cidade(self):
        if self.pode_fundar(): self.modal='nome_cidade'; self.campo_nome=''

    def confirmar_fundacao(self):
        nome=self.campo_nome.strip(); u=self.unidade_selecionada
        if not nome or not u or u.tipo!='Colono' or u.movimento<=0: return
        c=Cidade(nome,u.x,u.y,u.dono_id); self._adicionar_cidade(c); self._remover_unidade(u)
        self.modal=None; self.atualizar_visibilidade_todos(); self.mensagem=f'Cidade {nome} fundada.'

    def fundar_cidade_cpu(self,jogador,unidade):
        nome=f'{jogador.civilizacao} {len(jogador.cidades)+1}'
        self._adicionar_cidade(Cidade(nome,unidade.x,unidade.y,jogador.id)); self._remover_unidade(unidade)

    def construir_melhoria(self,tipo):
        u=self.unidade_selecionada
        if not self.trabalhador_pode_melhorar(): self.mensagem='Trabalhador sem condições para construir melhoria.'; return
        c=self.cidade_dona_tile(u.x,u.y,0)
        if self.mundo.construir_melhoria(u.x,u.y,tipo):
            c.melhorias.append((tipo,u.x,u.y)); u.movimento=0
            if u.registrar_melhoria(): self._remover_unidade(u); self.mensagem=f'{tipo} construída. Trabalhador consumido após 3 melhorias.'
            else: self.mensagem=f'{tipo} construída. Restam {u.melhorias_restantes} melhorias.'

    def _tiles_adjacentes(self,c):
        return [(c.x+dx,c.y+dy) for dx,dy in VIZINHOS_8 if self.mundo.dentro(c.x+dx,c.y+dy)]

    def cidade_tem_agua_rasa_adjacente(self,c):
        return any(self.mundo.passavel_mar_raso(x,y) for x,y in self._tiles_adjacentes(c))

    # Compatibilidade com IA/código anterior.
    def cidade_tem_agua_adjacente(self,c):
        return self.cidade_tem_agua_rasa_adjacente(c)

    def _spawn(self,c,tipo):
        dom=UNIDADES[tipo]['dominio']
        for x,y in self._tiles_adjacentes(c):
            if self.unidade_em(x,y) is None and self.cidade_em(x,y) is None and self.mundo.passavel_para(x,y,dom): return x,y
        if dom=='terra' and self.unidade_em(c.x,c.y) is None: return c.x,c.y
        return None

    def iniciar_producao(self,categoria,nome):
        c=self.cidade_modal
        if not c or c.dono_id!=0: return
        if nome=='Galé' and not self.cidade_tem_agua_rasa_adjacente(c):
            self.mensagem='Galé exige Água Rasa adjacente à cidade.'; return
        taxa=self.rendimentos_cidade(c)['producao']
        ok,motivo=c.iniciar_producao(categoria,nome,self.jogador_humano,taxa)
        if ok:
            self.mensagem=(f'{c.nome} iniciou {nome}: {c.turnos_producao_total} turno(s) '
                           f'com {c.producao_por_turno_inicio} de Produção/turno.')
        else:
            self.mensagem=motivo

    def adicionar_notificacao(self,texto):
        self.notificacoes.append(texto)

    def _abrir_proxima_notificacao(self):
        if self.notificacoes and self.modal is None:
            self.notificacao_atual=self.notificacoes.pop(0)
            self.modal='aviso'

    def processar_cidades_jogador(self,jogador,notificar=False):
        mensagens=[]
        for c in list(jogador.cidades):
            r=self.rendimentos_cidade(c)
            cresceu, expansoes=c.adicionar_recursos(**r)
            if cresceu: mensagens.append(f'{c.nome} cresceu para {c.populacao}')
            if expansoes:
                novos=self._expandir_territorio_cidade(c)
                texto_exp=f'{c.nome} expandiu suas fronteiras para raio {c.raio_territorio} (+{novos} tiles).'
                mensagens.append(texto_exp)
                if notificar: self.adicionar_notificacao(texto_exp)
            resultado=c.avancar_producao()
            if resultado:
                categoria,nome=resultado
                if categoria=='unidade':
                    spawn=self._spawn(c,nome)
                    if spawn:
                        self._adicionar_unidade(Unidade(nome,*spawn,jogador.id))
                        texto=f'{c.nome} concluiu a unidade {UNIDADES[nome].get("icone","")} {nome}.'
                    else:
                        texto=f'{c.nome} concluiu {nome}, mas não há quadrado válido livre para posicioná-la.'
                else:
                    texto=f'{c.nome} concluiu a construção {nome}.'
                mensagens.append(texto)
                if notificar: self.adicionar_notificacao(texto)
        return mensagens

    def proximo_turno(self):
        mensagens=self.processar_cidades_jogador(self.jogador_humano,notificar=True)
        for cpu in self.jogadores[1:]:
            for u in cpu.unidades: u.novo_turno()
            self.controladores_ia[cpu.id].jogar_turno(self,cpu)
            mensagens.extend(self.processar_cidades_jogador(cpu,notificar=False))
            self.atualizar_visibilidade_jogador(cpu)
        self.turno += 1
        self.calendario.avancar()
        for u in self.jogador_humano.unidades: u.novo_turno()
        self.atualizar_visibilidade_todos()
        self.mensagem='; '.join(mensagens[:3]) if mensagens else f'Turno {self.turno} — {self.calendario.texto}.'
        self._abrir_proxima_notificacao()

    # ---------- interface ----------
    def botao(self,rect,texto,ativo=True,cor=None):
        cor=cor or ((77,83,92) if ativo else (58,61,66))
        pygame.draw.rect(self.tela,cor,rect,border_radius=4); pygame.draw.rect(self.tela,(28,30,33),rect,1,border_radius=4)
        surf=self.fonte_pequena.render(texto,True,(245,245,245) if ativo else (135,135,135)); self.tela.blit(surf,surf.get_rect(center=rect.center))

    def desenhar_interface(self):
        # Linha 1: menu.
        pygame.draw.rect(self.tela,(30,33,38),(0,0,self.largura_tela,ALTURA_BARRA_MENU))
        for rect,txt in ((self.rect_menu_jogo,'Jogo'),(self.rect_menu_ajuda,'Ajuda')):
            surf=self.fonte_pequena.render(txt,True,(235,235,235)); self.tela.blit(surf,surf.get_rect(center=rect.center))

        # Linha 2: status, turno/ano e recursos gerais.
        pygame.draw.rect(self.tela,(39,43,49),(0,ALTURA_BARRA_MENU,self.largura_tela,ALTURA_BARRA_STATUS))
        if self.unidade_selecionada:
            u=self.unidade_selecionada
            status=f'{u.icone} {u.tipo} | Mov {u.movimento}/{u.movimento_max}'
            if u.fortificada: status+=' | Defesa'
            if u.capacidade_transporte: status+=f' | Carga {len(u.carga)}/{u.capacidade_transporte}'
        else:
            status=f'{self.jogador_humano.civilizacao}'
        self.tela.blit(self.fonte_pequena.render(status,True,(230,230,230)),(10,ALTURA_BARRA_MENU+8))

        tempo=f'Turno {self.turno} | {self.calendario.texto}'
        self.tela.blit(self.fonte_pequena.render(tempo,True,(245,225,180)),(340,ALTURA_BARRA_MENU+8))
        t=self.totais_civilizacao(self.jogador_humano)
        recursos=(f'{ICONES_RECURSOS["alimento"]}{t["alimento"]}  {ICONES_RECURSOS["producao"]}{t["producao"]}  '
                  f'{ICONES_RECURSOS["ouro"]}{t["ouro"]}  {ICONES_RECURSOS["ciencia"]}{t["ciencia"]}  '
                  f'{ICONES_RECURSOS["fe"]}{t["fe"]}  {ICONES_RECURSOS["lealdade"]}{t["lealdade"]}  '
                  f'{ICONES_RECURSOS["felicidade"]}{t["felicidade"]}')
        surf=self.fonte_icone.render(recursos,True,(220,235,220)); self.tela.blit(surf,(self.largura_tela-surf.get_width()-12,ALTURA_BARRA_MENU+5))

        # Linha 3: ferramentas.
        pygame.draw.rect(self.tela,(48,53,60),(0,ALTURA_BARRA_MENU+ALTURA_BARRA_STATUS,self.largura_tela,ALTURA_BARRA_FERRAMENTAS))
        self.botao(self.rect_proximo_turno,'Próximo Turno',True,(57,102,69))
        for rect,txt in ((self.rect_politica,'Política'),(self.rect_tecnologia,'Tecnologia'),(self.rect_religiao,'Religião'),(self.rect_economia,'Economia'),(self.rect_diplomacia,'Diplomacia'),(self.rect_militar,'Militar')):
            self.botao(rect,txt)
        if self.pode_fundar(): self.botao(self.rect_fundar,'Fundar Cidade',True,(128,88,48))
        elif self.unidade_selecionada and self.unidade_selecionada.tipo=='Trabalhador':
            ativo=self.trabalhador_pode_melhorar(); self.botao(self.rect_fazenda,'Fazenda +1',ativo); self.botao(self.rect_pasto,'Pasto +1',ativo)

        if self.menu_aberto=='Jogo':
            pygame.draw.rect(self.tela,(49,53,60),(10,ALTURA_BARRA_MENU,135,60)); self._item_menu(self.rect_novo,'Novo'); self._item_menu(self.rect_sair,'Sair')
        elif self.menu_aberto=='Ajuda':
            pygame.draw.rect(self.tela,(49,53,60),self.rect_sobre); self._item_menu(self.rect_sobre,'Sobre')

    def _item_menu(self,r,t):
        self.tela.blit(self.fonte_pequena.render(t,True,(235,235,235)),(r.x+10,r.y+7))

    # ---------- desenho do mapa ----------
    def desenhar_mapa(self):
        j=self.jogador_humano
        self.tela.set_clip(self.viewport); pygame.draw.rect(self.tela,(4,4,6),self.viewport)
        x0=max(0,self.offset_x//TAMANHO_TILE); y0=max(0,self.offset_y//TAMANHO_TILE)
        x1=min(self.mundo.largura,(self.offset_x+self.viewport.width)//TAMANHO_TILE+2)
        y1=min(self.mundo.altura,(self.offset_y+self.viewport.height)//TAMANHO_TILE+2)
        territorios={}
        for c in self.cidades:
            dono=self.jogador_por_id(c.dono_id)
            for tile in self.territorio_cidade(c): territorios[tile]=dono.cor
        for y in range(y0,y1):
            for x in range(x0,x1):
                sx,sy=self.tile_para_tela(x,y); r=pygame.Rect(sx,sy,TAMANHO_TILE,TAMANHO_TILE)
                if (x,y) not in j.explorado:
                    pygame.draw.rect(self.tela,(3,3,5),r); continue
                cor=CORES_TERRENO[self.mundo.terreno(x,y)]
                if (x,y) not in j.visivel: cor=tuple(max(18,int(c*.36)) for c in cor)
                pygame.draw.rect(self.tela,cor,r); pygame.draw.rect(self.tela,COR_GRADE,r,1)
                if (x,y) in territorios: pygame.draw.rect(self.tela,territorios[(x,y)],r,2)
                if (x,y) in j.visivel:
                    simbolo_terreno=ICONES_TERRENO.get(self.mundo.terreno(x,y),'')
                    if simbolo_terreno:
                        ts=self.fonte_icone.render(simbolo_terreno,True,tuple(max(25,int(v*.62)) for v in cor))
                        self.tela.blit(ts,ts.get_rect(center=(sx+TAMANHO_TILE//2,sy+TAMANHO_TILE//2)))
                    variante=self.mundo.variante_em(x,y)
                    if variante and variante.get('icone'):
                        vs=self.fonte_icone.render(variante['icone'],True,(30,30,30))
                        self.tela.blit(vs,(sx+TAMANHO_TILE-vs.get_width()-2,sy+1))
                    mel=self.mundo.melhoria_em(x,y)
                    if mel:
                        mi=MELHORIAS.get(mel,{}).get('icone','•')
                        ms=self.fonte_icone.render(mi,True,(35,25,15)); self.tela.blit(ms,(sx+2,sy+TAMANHO_TILE-ms.get_height()+2))
        self.desenhar_cidades(); self.desenhar_unidades(); self.tela.set_clip(None)

    def desenhar_cidades(self):
        vis=self.jogador_humano.visivel
        for c in self.cidades:
            if (c.x,c.y) not in vis: continue
            dono=self.jogador_por_id(c.dono_id); sx,sy=self.tile_para_tela(c.x,c.y)
            pygame.draw.rect(self.tela,dono.cor,(sx+5,sy+5,TAMANHO_TILE-10,TAMANHO_TILE-10),border_radius=4)
            txt=self.fonte_icone_grande.render('♜',True,(255,255,255)); self.tela.blit(txt,txt.get_rect(center=(sx+17,sy+17)))
            nome=self.fonte_pequena.render(f'{c.nome} ({c.populacao})',True,(255,255,255)); fundo=pygame.Rect(sx-2,sy-18,nome.get_width()+8,18); pygame.draw.rect(self.tela,dono.cor,fundo,border_radius=3); self.tela.blit(nome,(fundo.x+4,fundo.y+1))

    def desenhar_unidades(self):
        vis=self.jogador_humano.visivel
        for u in self.unidades:
            if u.esta_embarcada or (u.x,u.y) not in vis: continue
            dono=self.jogador_por_id(u.dono_id); sx,sy=self.tile_para_tela(u.x,u.y); centro=(sx+17,sy+17)
            pygame.draw.circle(self.tela,dono.cor,centro,13); pygame.draw.circle(self.tela,(245,245,245),centro,13,2)
            if u is self.unidade_selecionada: pygame.draw.rect(self.tela,(255,235,70),(sx+1,sy+1,TAMANHO_TILE-2,TAMANHO_TILE-2),3)
            t=self.fonte_icone_grande.render(u.icone,True,(255,255,255)); self.tela.blit(t,t.get_rect(center=centro))
            letra=self.fonte_mini.render(u.letra,True,(255,255,255))
            lf=pygame.Rect(sx+TAMANHO_TILE-11,sy+1,10,10)
            pygame.draw.rect(self.tela,(25,25,25),lf,border_radius=2)
            self.tela.blit(letra,letra.get_rect(center=lf.center))
            if u.fortificada: self.tela.blit(self.fonte_mini.render('DF',True,(255,245,160)),(sx+1,sy+1))
            if u.capacidade_transporte and u.carga:
                self.tela.blit(self.fonte_mini.render(f'+{len(u.carga)}',True,(255,245,160)),(sx+1,sy+TAMANHO_TILE-11))

    def desenhar_barras_rolagem(self):
        lw,lh=self.mundo.largura*TAMANHO_TILE,self.mundo.altura*TAMANHO_TILE
        if lw>self.viewport.width:
            trilho=pygame.Rect(0,self.altura_tela-14,self.largura_tela-14,14); pygame.draw.rect(self.tela,(45,45,45),trilho); tam=max(30,int(trilho.width*self.viewport.width/lw)); maxo=lw-self.viewport.width; x=int(self.offset_x/maxo*(trilho.width-tam)) if maxo else 0; pygame.draw.rect(self.tela,(135,135,135),(x,trilho.y+2,tam,10),border_radius=3)
        if lh>self.viewport.height:
            trilho=pygame.Rect(self.largura_tela-14,TOPO_MAPA,14,self.altura_tela-TOPO_MAPA-14); pygame.draw.rect(self.tela,(45,45,45),trilho); tam=max(30,int(trilho.height*self.viewport.height/lh)); maxo=lh-self.viewport.height; y=trilho.y+(int(self.offset_y/maxo*(trilho.height-tam)) if maxo else 0); pygame.draw.rect(self.tela,(135,135,135),(trilho.x+2,y,10,tam),border_radius=3)

    # ---------- modais ----------
    def abrir_cidade(self,cidade):
        if cidade.dono_id!=0:
            self.mensagem=f'{cidade.nome} pertence a {self.jogador_por_id(cidade.dono_id).civilizacao}. Diplomacia/conquista virá depois.'; return
        self.selecionar_unidade(None); self.cidade_modal=cidade; self.modal='cidade'; self.menu_aberto=None

    def desenhar_modal_nome(self):
        caixa=pygame.Rect(self.largura_tela//2-230,self.altura_tela//2-105,460,210); pygame.draw.rect(self.tela,(50,54,61),caixa,border_radius=10)
        self.tela.blit(self.fonte_grande.render('Fundar Cidade',True,(245,245,245)),(caixa.x+30,caixa.y+25)); self.tela.blit(self.fonte.render('Digite o nome e pressione ENTER:',True,(220,220,220)),(caixa.x+30,caixa.y+70))
        self.rect_campo_nome=pygame.Rect(caixa.x+30,caixa.y+100,caixa.width-60,38); pygame.draw.rect(self.tela,(235,235,235),self.rect_campo_nome); self.tela.blit(self.fonte.render(self.campo_nome+'|',True,(30,30,30)),(self.rect_campo_nome.x+8,self.rect_campo_nome.y+8))
        self.rect_confirmar_nome=pygame.Rect(caixa.centerx-100,caixa.bottom-50,95,32); self.rect_cancelar_nome=pygame.Rect(caixa.centerx+5,caixa.bottom-50,95,32); self.botao(self.rect_confirmar_nome,'Fundar',bool(self.campo_nome.strip()),(57,102,69)); self.botao(self.rect_cancelar_nome,'Cancelar')

    def desenhar_modal_cidade(self):
        c=self.cidade_modal; largura=min(900,self.largura_tela-40); altura=min(590,self.altura_tela-40)
        caixa=pygame.Rect((self.largura_tela-largura)//2,(self.altura_tela-altura)//2,largura,altura); pygame.draw.rect(self.tela,(48,52,59),caixa,border_radius=10)
        self.rect_fechar_cidade=pygame.Rect(caixa.right-45,caixa.y+15,30,30); self.botao(self.rect_fechar_cidade,'X')
        self.tela.blit(self.fonte_grande.render(f'♜ {c.nome} — {self.jogador_humano.civilizacao}',True,(245,235,190)),(caixa.x+25,caixa.y+18))
        r, detalhes=self.detalhamento_rendimentos_cidade(c)
        limite=c.limite_proxima_populacao()
        prox_leal=c.proximo_limite_lealdade()
        self.tela.blit(self.fonte.render(
            f'População: {c.populacao} | próximo alimento: {limite} | território: raio {c.raio_territorio}',
            True,(220,220,220)),(caixa.x+25,caixa.y+55))

        recursos_cidade = [
            ('alimento', c.alimento, r['alimento']), ('producao', c.producao, r['producao']),
            ('ouro', c.ouro, r['ouro']), ('ciencia', c.ciencia, r['ciencia']),
            ('fe', c.fe, r['fe']), ('lealdade', c.lealdade, r['lealdade']),
            ('felicidade', c.felicidade, r['felicidade']),
        ]
        for i,(chave,estoque,ganho) in enumerate(recursos_cidade):
            ic=ICONES_RECURSOS[chave]
            if chave == 'producao':
                txt=f'{ic} Produção: +{ganho}/turno'
            else:
                txt=f'{ic} {chave.capitalize()}: {estoque}'
                if ganho:
                    txt += f' (+{ganho}/turno)'
            px=caixa.x+25+(i%4)*205
            py=caixa.y+82+(i//4)*25
            self.tela.blit(self.fonte_indicador.render(txt,True,(225,225,225)),(px,py))

        leal_txt=f'Próxima expansão por Lealdade: {prox_leal if prox_leal is not None else "máximo provisório"}'
        self.tela.blit(self.fonte_pequena.render(leal_txt,True,(205,190,225)),(caixa.x+25,caixa.y+134))
        _, efeitos = self.modificadores_entorno_cidade(c)
        entorno='Entorno: '+(', '.join(efeitos) if efeitos else 'sem bônus/multas gerais')
        self.tela.blit(self.fonte_pequena.render(entorno,True,(190,210,230)),(caixa.x+25,caixa.y+151))
        if c.producao_nome:
            prod=(f'Produção atual: {c.producao_nome} — {c.turnos_producao_restantes}/{c.turnos_producao_total} turno(s) restantes '
                  f'| custo {c.custo_producao_atual} | taxa fixada {c.producao_por_turno_inicio}/turno')
        else:
            prod='Produção atual: nenhuma'
        self.tela.blit(self.fonte_pequena.render(prod,True,(220,220,220)),(caixa.x+25,caixa.y+171))

        x=caixa.x+25; y=caixa.y+208; self.tela.blit(self.fonte_negrito.render('Construir Unidades',True,(240,240,240)),(x,y)); livre=c.producao_nome is None
        self.rect_producoes={}; yy=y+28
        for nome in ['Colono','Guerreiro','Trabalhador','Galé']:
            dados=UNIDADES[nome]; ativo=livre and self.jogador_humano.possui_tecnologia(dados.get('tecnologia'))
            if nome=='Colono': ativo=ativo and c.populacao>=dados.get('populacao_min',0)
            if nome=='Galé': ativo=ativo and self.cidade_tem_agua_rasa_adjacente(c)
            turnos=max(1,math.ceil(dados['custo_producao']/max(1,r['producao'])))
            rect=pygame.Rect(x,yy,270,32); self.rect_producoes[('unidade',nome)]=rect; self.botao(rect,f'{dados.get("icone","")} {nome} — {turnos} turno(s)',ativo); yy+=37
        yy+=8; self.tela.blit(self.fonte_negrito.render('Construir Construções',True,(240,240,240)),(x,yy)); yy+=27
        for nome in ['Templo','Muralha']:
            dados=CONSTRUCOES[nome]; ativo=livre and nome not in c.construcoes and self.jogador_humano.possui_tecnologia(dados.get('tecnologia')); turnos=max(1,math.ceil(dados['custo_producao']/max(1,r['producao']))); rect=pygame.Rect(x,yy,270,32); self.rect_producoes[('construcao',nome)]=rect; self.botao(rect,f'{nome} — {turnos} turno(s)',ativo); yy+=37

        dx=caixa.x+520; self.tela.blit(self.fonte_negrito.render('Construções existentes',True,(240,240,240)),(dx,y)); yy2=y+28
        for nome in c.construcoes or ['Nenhuma']:
            self.tela.blit(self.fonte.render(f'• {nome}',True,(220,220,220)),(dx,yy2)); yy2+=21
        yy2+=8
        self.tela.blit(self.fonte_negrito.render('O que gera bônus nesta cidade',True,(240,240,240)),(dx,yy2)); yy2+=25
        for rotulo, valores in detalhes:
            partes=[]
            for rec in ('alimento','producao','ouro','ciencia','fe','lealdade'):
                v=valores.get(rec,0)
                if v:
                    partes.append(f'{ICONES_RECURSOS[rec]}{v:+d}')
            linha=f'• {rotulo}' + (f'  [{" ".join(partes)}]' if partes else '')
            cor=(215,225,210) if 'ATIVO' in rotulo or 'Base' in rotulo or 'central' in rotulo else (180,180,180)
            self.tela.blit(self.fonte_pequena.render(linha,True,cor),(dx,yy2)); yy2+=18
            if yy2 > caixa.bottom-85: break
        yy2+=5
        self.tela.blit(self.fonte_negrito.render('Recursos ainda não explorados',True,(240,240,240)),(dx,yy2)); yy2+=23
        pendentes=0
        for tx,ty in sorted(self.territorio_cidade(c)):
            var=self.mundo.variante_em(tx,ty)
            if not var: continue
            mel=self.mundo.melhoria_em(tx,ty)
            ativo=mel in var.get('melhorias_ativadoras',[])
            if ativo: continue
            necessaria=', '.join(var.get('melhorias_ativadoras',[])) or 'tecnologia futura'
            linha=f'• {var["nome"]} ({tx},{ty}) — requer {necessaria}'
            self.tela.blit(self.fonte_pequena.render(linha,True,(180,180,180)),(dx,yy2)); yy2+=18; pendentes+=1
            if yy2 > caixa.bottom-25: break
        if not pendentes:
            self.tela.blit(self.fonte_pequena.render('• Nenhum.',True,(170,170,170)),(dx,yy2))

    def cidade_da_melhoria(self, x, y):
        for cidade in self.cidades:
            for _, mx, my in cidade.melhorias:
                if (mx, my) == (x, y):
                    return cidade
        return None

    def abrir_ajuda_unidade(self, unidade):
        self.ajuda_contexto = {'tipo': 'unidade', 'unidade': unidade}
        self.modal = 'ajuda'
        self.menu_aberto = None

    def abrir_ajuda_tile(self, x, y):
        self.ajuda_contexto = {'tipo': 'tile', 'x': x, 'y': y}
        self.modal = 'ajuda'
        self.menu_aberto = None

    def desenhar_modal_ajuda(self):
        ctx = self.ajuda_contexto or {}
        caixa = pygame.Rect(self.largura_tela//2-300, self.altura_tela//2-190, 600, 380)
        pygame.draw.rect(self.tela, (50,54,61), caixa, border_radius=10)
        pygame.draw.rect(self.tela, self.jogador_humano.cor, caixa, 2, border_radius=10)
        self.rect_fechar_ajuda = pygame.Rect(caixa.right-45, caixa.y+15, 30, 30)
        self.botao(self.rect_fechar_ajuda, 'X')

        if ctx.get('tipo') == 'unidade':
            u = ctx.get('unidade')
            if u not in self.unidades:
                self.modal = None
                return
            dono = self.jogador_por_id(u.dono_id)
            titulo = f'{u.icone} {u.tipo} ({u.letra})'
            self.tela.blit(self.fonte_grande.render(titulo, True, (245,235,190)), (caixa.x+25, caixa.y+22))
            linhas = [
                f'Civilização: {dono.civilizacao if dono else "Desconhecida"}',
                f'Jogador: {dono.nome if dono else u.dono_id}',
                f'Domínio: {u.dominio}',
                f'Movimento: {u.movimento}/{u.movimento_max}',
                f'Estado: {"Fortificada / defesa" if u.fortificada else "Ativa"}',
                f'Posição: ({u.x}, {u.y})',
            ]
            if u.tipo == 'Trabalhador':
                linhas.append(f'Melhorias restantes: {u.melhorias_restantes}')
            if u.capacidade_transporte:
                linhas.append(f'Capacidade de transporte: {len(u.carga)}/{u.capacidade_transporte}')
                if u.carga:
                    linhas.append('Carga: ' + ', '.join(c.tipo for c in u.carga))
            y = caixa.y + 78
            for linha in linhas:
                self.tela.blit(self.fonte.render(linha, True, (225,225,225)), (caixa.x+28, y))
                y += 27
            dados = UNIDADES.get(u.tipo, {})
            self.tela.blit(self.fonte_pequena.render(
                f'Custo-base: {dados.get("custo_producao", 0)} de Produção | Era: {dados.get("era", "-")}',
                True, (190,205,220)), (caixa.x+28, caixa.bottom-55))
            return

        x, y = ctx.get('x'), ctx.get('y')
        terreno = self.mundo.terreno(x, y)
        variante = self.mundo.variante_em(x, y)
        melhoria = self.mundo.melhoria_em(x, y)
        icone = ICONES_TERRENO.get(terreno, '')
        titulo = f'{icone} {terreno} — ({x}, {y})'
        self.tela.blit(self.fonte_grande.render(titulo, True, (245,235,190)), (caixa.x+25, caixa.y+22))
        base = self.mundo.rendimentos_base_tile(x, y)
        partes = [f'{ICONES_RECURSOS[k]} {k}: {v:+d}' for k, v in base.items() if v]
        linhas = [f'Rendimento natural do tile: {" | ".join(partes) if partes else "nenhum"}']

        if variante:
            ativadores = ', '.join(variante.get('melhorias_ativadoras', [])) or 'nenhuma melhoria'
            ativo = melhoria in variante.get('melhorias_ativadoras', [])
            linhas.append(f'Recurso: {variante.get("icone", "")} {variante["nome"]}')
            linhas.append(f'Ativação: requer {ativadores} — {"ATIVO" if ativo else "INATIVO"}')
            mods = variante.get('modificadores', {})
            if mods:
                linhas.append('Bônus potencial: ' + ', '.join(f'{k} {v:+d}' for k, v in mods.items()))
        else:
            linhas.append('Recurso especial: nenhum')

        if melhoria:
            cidade = self.cidade_da_melhoria(x, y)
            dono = self.jogador_por_id(cidade.dono_id) if cidade else None
            linhas.append(f'Melhoria: {MELHORIAS.get(melhoria,{}).get("icone","")} {melhoria}')
            linhas.append(f'Pertence à cidade: {cidade.nome if cidade else "não identificada"}')
            if dono:
                linhas.append(f'Civilização proprietária: {dono.civilizacao}')
            bonus, fontes = self.mundo.bonus_melhoria_tile(x, y)
            ativos = [f'{k} {v:+d}' for k, v in bonus.items() if v]
            linhas.append('Bônus efetivo da melhoria: ' + (', '.join(ativos) if ativos else 'nenhum'))
        else:
            dona = self.cidade_dona_tile(x, y)
            linhas.append(f'Território: {dona.nome if dona else "não controlado"}')

        yy = caixa.y + 78
        for linha in linhas:
            self.tela.blit(self.fonte.render(linha, True, (225,225,225)), (caixa.x+28, yy))
            yy += 27

    def desenhar_modal_generico(self,titulo,linhas):
        caixa=pygame.Rect(self.largura_tela//2-270,self.altura_tela//2-150,540,300); pygame.draw.rect(self.tela,(50,54,61),caixa,border_radius=10); self.tela.blit(self.fonte_grande.render(titulo,True,(245,235,190)),(caixa.x+25,caixa.y+25)); y=caixa.y+75
        for l in linhas: self.tela.blit(self.fonte.render(l,True,(220,220,220)),(caixa.x+25,y)); y+=28
        self.rect_fechar_generico=pygame.Rect(caixa.centerx-50,caixa.bottom-48,100,32); self.botao(self.rect_fechar_generico,'Fechar')

    def desenhar_modal_aviso(self):
        caixa=pygame.Rect(self.largura_tela//2-280,self.altura_tela//2-100,560,200); pygame.draw.rect(self.tela,(52,57,65),caixa,border_radius=10); pygame.draw.rect(self.tela,self.jogador_humano.cor,caixa,2,border_radius=10)
        self.tela.blit(self.fonte_grande.render('Aviso da civilização',True,(245,235,190)),(caixa.x+25,caixa.y+24))
        texto=self.notificacao_atual or ''
        self.tela.blit(self.fonte.render(texto,True,(230,230,230)),(caixa.x+25,caixa.y+80))
        self.rect_fechar_aviso=pygame.Rect(caixa.centerx-55,caixa.bottom-50,110,32); self.botao(self.rect_fechar_aviso,'Continuar',True,(57,102,69))

    # ---------- eventos ----------
    def tratar_click_mapa(self, pos, botao, duplo=False):
        tile = self.tela_para_tile(pos)
        if not tile:
            return
        x, y = tile
        if (x, y) not in self.jogador_humano.visivel:
            self.mensagem = 'Esse quadrado não está visível.'
            return

        cidade = self.cidade_em(x, y)
        unidades_todas = self.unidades_em(x, y)
        unidades_humanas = [u for u in unidades_todas if u.dono_id == self.jogador_humano.id]
        unidade = unidades_todas[-1] if unidades_todas else None

        if botao == 1 and duplo:
            if cidade is not None:
                self.abrir_cidade(cidade)
                return
            if unidade is not None:
                self.abrir_ajuda_unidade(unidade)
                return
            self.abrir_ajuda_tile(x, y)
            return

        if botao == 1:
            # Clique esquerdo apenas seleciona. Em cidade, prioriza guarnição fortificada.
            if cidade is not None:
                fortificadas = [u for u in unidades_humanas if u.fortificada]
                if fortificadas:
                    self.selecionar_unidade(fortificadas[-1])
                else:
                    self.selecionar_unidade(None)
                    self.mensagem = f'{cidade.nome}: nenhuma unidade fortificada. Duplo clique abre a cidade.'
                return
            if unidade is not None:
                self.selecionar_unidade(unidade)
                return
            return

        if botao != 3:
            return

        # Botão direito executa a ação da unidade previamente selecionada.
        sel = self.unidade_selecionada
        if sel is None:
            self.mensagem = 'Selecione uma unidade com o botão esquerdo antes de dar uma ordem.'
            return
        if sel.dono_id != self.jogador_humano.id:
            self.mensagem = 'Você não pode dar ordens a uma unidade de outra civilização.'
            return

        # Embarque: unidade terrestre selecionada + botão direito sobre transporte amigo.
        transportes = [u for u in unidades_humanas if u.capacidade_transporte > 0 and u is not sel]
        for transporte in reversed(transportes):
            if transporte.pode_embarcar(sel):
                self.tentar_embarcar(sel, transporte)
                return

        # Cidade amiga: ordem de movimento/fortificação.
        if cidade is not None:
            self.mover_para_cidade_fortificar(cidade)
            return

        # Movimento comum; para transportes com carga, terra é interpretada como desembarque.
        self.ordenar_movimento((x, y))

    def tratar_evento_modal(self,e):
        if self.modal=='nome_cidade':
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: self.modal=None
                elif e.key in (pygame.K_RETURN,pygame.K_KP_ENTER): self.confirmar_fundacao()
                elif e.key==pygame.K_BACKSPACE: self.campo_nome=self.campo_nome[:-1]
                elif e.unicode.isprintable() and len(self.campo_nome)<24: self.campo_nome+=e.unicode
            elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                if self.rect_confirmar_nome.collidepoint(e.pos) and self.campo_nome.strip(): self.confirmar_fundacao()
                elif self.rect_cancelar_nome.collidepoint(e.pos): self.modal=None
            return
        if self.modal=='cidade':
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: self.modal=None; self.cidade_modal=None
            elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                if self.rect_fechar_cidade.collidepoint(e.pos): self.modal=None; self.cidade_modal=None; return
                for chave,rect in self.rect_producoes.items():
                    if rect.collidepoint(e.pos): self.iniciar_producao(*chave); return
            return
        if self.modal=='ajuda':
            fechar=(e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE) or (e.type==pygame.MOUSEBUTTONDOWN and e.button==1 and self.rect_fechar_ajuda.collidepoint(e.pos))
            if fechar:
                self.modal=None; self.ajuda_contexto=None
            return
        if self.modal=='aviso':
            fechar=(e.type==pygame.KEYDOWN and e.key in (pygame.K_RETURN,pygame.K_KP_ENTER,pygame.K_ESCAPE)) or (e.type==pygame.MOUSEBUTTONDOWN and e.button==1 and self.rect_fechar_aviso.collidepoint(e.pos))
            if fechar:
                self.modal=None; self.notificacao_atual=None; self._abrir_proxima_notificacao()
            return
        if self.modal in ('sobre','politica','tecnologia','religiao','economia','diplomacia','militar'):
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: self.modal=None
            elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1 and self.rect_fechar_generico.collidepoint(e.pos): self.modal=None

    def mover_camera_teclado(self):
        if self.modal: return
        k=pygame.key.get_pressed()
        if k[pygame.K_LEFT] or k[pygame.K_a]: self.offset_x-=self.velocidade_scroll
        if k[pygame.K_RIGHT] or k[pygame.K_d]: self.offset_x+=self.velocidade_scroll
        if k[pygame.K_UP] or k[pygame.K_w]: self.offset_y-=self.velocidade_scroll
        if k[pygame.K_DOWN] or k[pygame.K_s]: self.offset_y+=self.velocidade_scroll
        self.limitar_camera()

    def executar(self):
        relogio=pygame.time.Clock()
        while True:
            for e in pygame.event.get():
                if e.type==pygame.QUIT: return 'sair'
                if e.type==pygame.VIDEORESIZE: self.tela=pygame.display.set_mode(e.size,pygame.RESIZABLE); self._atualizar_layout(); continue
                if self.modal: self.tratar_evento_modal(e); continue
                if e.type==pygame.MOUSEWHEEL: self.offset_y-=e.y*self.velocidade_scroll; self.limitar_camera()
                elif e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: self.menu_aberto=None; self.selecionar_unidade(None)
                elif e.type==pygame.MOUSEBUTTONDOWN:
                    pos=e.pos
                    if e.button==1 and self.rect_menu_jogo.collidepoint(pos): self.menu_aberto=None if self.menu_aberto=='Jogo' else 'Jogo'; continue
                    if e.button==1 and self.rect_menu_ajuda.collidepoint(pos): self.menu_aberto=None if self.menu_aberto=='Ajuda' else 'Ajuda'; continue
                    if self.menu_aberto=='Jogo' and e.button==1:
                        if self.rect_novo.collidepoint(pos): return 'novo'
                        if self.rect_sair.collidepoint(pos): return 'sair'
                        self.menu_aberto=None; continue
                    if self.menu_aberto=='Ajuda' and e.button==1:
                        if self.rect_sobre.collidepoint(pos): self.modal='sobre'
                        self.menu_aberto=None; continue
                    if e.button==1 and self.rect_proximo_turno.collidepoint(pos): self.proximo_turno(); continue
                    modal_botoes=[
                        (self.rect_politica,'politica'),(self.rect_tecnologia,'tecnologia'),(self.rect_religiao,'religiao'),
                        (self.rect_economia,'economia'),(self.rect_diplomacia,'diplomacia'),(self.rect_militar,'militar')]
                    abriu=False
                    if e.button==1:
                        for rect,nome in modal_botoes:
                            if rect.collidepoint(pos): self.modal=nome; abriu=True; break
                    if abriu: continue
                    if e.button==1 and self.pode_fundar() and self.rect_fundar.collidepoint(pos): self.fundar_cidade(); continue
                    if e.button==1 and self.unidade_selecionada and self.unidade_selecionada.tipo=='Trabalhador':
                        if self.rect_fazenda.collidepoint(pos): self.construir_melhoria('Fazenda'); continue
                        if self.rect_pasto.collidepoint(pos): self.construir_melhoria('Pasto'); continue

                    duplo=False
                    if e.button==1 and self.viewport.collidepoint(pos):
                        tile_clique=self.tela_para_tile(pos)
                        agora=pygame.time.get_ticks()
                        if (tile_clique is not None and tile_clique==self.ultimo_clique_esquerdo_tile
                                and agora-self.ultimo_clique_esquerdo_ms<=self.limite_duplo_clique_ms):
                            duplo=True
                            self.ultimo_clique_esquerdo_ms=-1000
                            self.ultimo_clique_esquerdo_tile=None
                        else:
                            self.ultimo_clique_esquerdo_ms=agora
                            self.ultimo_clique_esquerdo_tile=tile_clique
                    self.tratar_click_mapa(pos,e.button,duplo)

            self.mover_camera_teclado(); self.tela.fill((22,24,27)); self.desenhar_mapa(); self.desenhar_barras_rolagem(); self.desenhar_interface()
            msg=self.fonte_pequena.render(self.mensagem,True,(235,235,235)); fundo=pygame.Rect(8,self.altura_tela-38,min(msg.get_width()+16,self.largura_tela-30),24); pygame.draw.rect(self.tela,(35,38,43),fundo,border_radius=4); self.tela.blit(msg,(fundo.x+8,fundo.y+4))

            if self.modal=='nome_cidade': self.desenhar_modal_nome()
            elif self.modal=='cidade': self.desenhar_modal_cidade()
            elif self.modal=='aviso': self.desenhar_modal_aviso()
            elif self.modal=='ajuda': self.desenhar_modal_ajuda()
            elif self.modal=='sobre': self.desenhar_modal_generico('Sobre o TLC CIV 0.10',['Mouse: esquerdo seleciona, direito executa e duplo esquerdo abre detalhes.','Produção calculada em turnos pela capacidade da cidade no início da ordem.'])
            elif self.modal=='politica': self.desenhar_modal_generico('Política',['Estrutura reservada para políticas e modificadores.'])
            elif self.modal=='tecnologia': self.desenhar_modal_generico('Tecnologia',[f'Era atual: {self.jogador_humano.era}',f'Tecnologias: {", ".join(sorted(self.jogador_humano.tecnologias))}',f'Ciência total: {self.totais_civilizacao(self.jogador_humano)["ciencia"]}'])
            elif self.modal=='religiao': self.desenhar_modal_generico('Religião',['Menu reservado para crenças, religiões e efeitos de Fé.'])
            elif self.modal=='economia': self.desenhar_modal_generico('Economia',['Menu reservado para Ouro, comércio, manutenção e rotas comerciais.'])
            elif self.modal=='diplomacia': self.desenhar_modal_generico('Diplomacia',['Menu reservado para relações entre civilizações, acordos e guerras.'])
            elif self.modal=='militar': self.desenhar_modal_generico('Militar',['Menu reservado para forças armadas, exércitos e informações de combate.'])
            pygame.display.flip(); relogio.tick(60)
