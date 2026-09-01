import random
from collections import deque
from data import VARIANTES_TERRENO, RENDIMENTOS_TERRENO, MELHORIAS

PASSAVEIS_TERRA = {'Grama', 'Deserto', 'Neve'}
PASSAVEIS_MAR = {'Água Rasa', 'Água Profunda'}
PASSAVEIS_MAR_RASO = {'Água Rasa'}

VIZINHOS_8 = (
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1),
)


class Mundo:
    def __init__(self, largura, altura, percentuais, seed=None):
        self.largura = largura
        self.altura = altura
        self.percentuais = percentuais
        self.random = random.Random(seed)
        self.tiles = self.gerar_mapa()
        self._classificar_aguas()
        self.variantes = self._gerar_variantes()
        self.melhorias = {}

    def _campo_ruido(self, suavizacoes=5):
        campo = [[self.random.random() for _ in range(self.largura)] for _ in range(self.altura)]
        for _ in range(suavizacoes):
            novo = [[0.0] * self.largura for _ in range(self.altura)]
            for y in range(self.altura):
                for x in range(self.largura):
                    total = 0.0
                    qtd = 0
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            nx = (x + dx) % self.largura
                            ny = min(self.altura - 1, max(0, y + dy))
                            total += campo[ny][nx]
                            qtd += 1
                    novo[y][x] = total / qtd
            campo = novo
        return campo

    def gerar_mapa(self):
        total = self.largura * self.altura
        quotas = {}
        usados = 0
        for terreno in ['Água', 'Montanha', 'Deserto', 'Neve']:
            q = round(total * self.percentuais[terreno] / 100)
            quotas[terreno] = q
            usados += q
        quotas['Grama'] = max(0, total - usados)

        oceano = self._campo_ruido(7)
        montanha = self._campo_ruido(4)
        deserto = self._campo_ruido(5)
        neve = self._campo_ruido(3)
        mapa = [[None for _ in range(self.largura)] for _ in range(self.altura)]
        livres = {(x, y) for y in range(self.altura) for x in range(self.largura)}

        def escolher(quantidade, score):
            candidatos = sorted(livres, key=lambda p: score(*p), reverse=True)
            escolhidos = candidatos[:min(quantidade, len(candidatos))]
            for p in escolhidos:
                livres.remove(p)
            return escolhidos

        for x, y in escolher(quotas['Água'], lambda x, y: oceano[y][x]):
            mapa[y][x] = 'Água'

        def score_neve(x, y):
            lat = y / max(1, self.altura - 1)
            return abs(lat - .5) * 3.6 + neve[y][x] * .45
        for x, y in escolher(quotas['Neve'], score_neve):
            mapa[y][x] = 'Neve'

        def score_montanha(x, y):
            vals = []
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx = (x + dx) % self.largura
                ny = min(self.altura - 1, max(0, y + dy))
                vals.append(montanha[ny][nx])
            relevo = montanha[y][x]
            return relevo + abs(relevo - sum(vals)/len(vals)) * .7
        for x, y in escolher(quotas['Montanha'], score_montanha):
            mapa[y][x] = 'Montanha'

        def score_deserto(x, y):
            lat = y / max(1, self.altura - 1)
            d = abs(lat - .5)
            faixa = max(0.0, 1.0 - abs(d - .22) * 3.0)
            return deserto[y][x] * 1.2 + faixa * .7
        for x, y in escolher(quotas['Deserto'], score_deserto):
            mapa[y][x] = 'Deserto'

        for x, y in livres:
            mapa[y][x] = 'Grama'
        return mapa

    def _classificar_aguas(self):
        terra = []
        agua = []
        for y in range(self.altura):
            for x in range(self.largura):
                if self.tiles[y][x] == 'Água':
                    agua.append((x, y))
                else:
                    terra.append((x, y))

        fila = deque()
        dist = {}
        for x, y in terra:
            for dx, dy in VIZINHOS_8:
                nx, ny = x + dx, y + dy
                if self.dentro(nx, ny) and self.tiles[ny][nx] == 'Água' and (nx, ny) not in dist:
                    dist[(nx, ny)] = 1
                    fila.append((nx, ny))
        while fila:
            x, y = fila.popleft()
            d = dist[(x, y)]
            if d >= 2:
                continue
            for dx, dy in VIZINHOS_8:
                nx, ny = x + dx, y + dy
                if self.dentro(nx, ny) and self.tiles[ny][nx] == 'Água' and (nx, ny) not in dist:
                    dist[(nx, ny)] = d + 1
                    fila.append((nx, ny))

        for x, y in agua:
            self.tiles[y][x] = 'Água Rasa' if dist.get((x, y), 99) <= 2 else 'Água Profunda'

    def _gerar_variantes(self):
        variantes = {}
        for y in range(self.altura):
            for x in range(self.largura):
                terreno = self.tiles[y][x]
                opcoes = VARIANTES_TERRENO.get(terreno, [])
                if not opcoes:
                    continue
                total = sum(o['peso'] for o in opcoes)
                sorteio = self.random.uniform(0, total)
                acc = 0
                escolhido = opcoes[0]
                for opcao in opcoes:
                    acc += opcao['peso']
                    if sorteio <= acc:
                        escolhido = opcao
                        break
                if escolhido.get('nome'):
                    variantes[(x, y)] = escolhido
        return variantes

    def dentro(self, x, y):
        return 0 <= x < self.largura and 0 <= y < self.altura

    def terreno(self, x, y):
        return self.tiles[y][x] if self.dentro(x, y) else None

    def variante_em(self, x, y):
        return self.variantes.get((x, y))

    def melhoria_em(self, x, y):
        return self.melhorias.get((x, y))

    def rendimentos_base_tile(self, x, y):
        base = dict(RENDIMENTOS_TERRENO.get(self.terreno(x, y), {}))
        for recurso in ('alimento', 'producao', 'ouro', 'ciencia', 'fe'):
            base.setdefault(recurso, 0)
        return base

    def bonus_melhoria_tile(self, x, y):
        melhoria = self.melhoria_em(x, y)
        if not melhoria:
            return {'alimento': 0, 'producao': 0, 'ouro': 0, 'ciencia': 0, 'fe': 0}, []
        bonus = {r: 0 for r in ('alimento', 'producao', 'ouro', 'ciencia', 'fe')}
        fontes = []
        dados_melhoria = MELHORIAS.get(melhoria, {})
        for recurso, valor in dados_melhoria.get('bonus', {}).items():
            bonus[recurso] += valor
        if dados_melhoria.get('bonus'):
            fontes.append(f'{melhoria}: {dados_melhoria["bonus"]}')

        variante = self.variante_em(x, y)
        if variante and melhoria in variante.get('melhorias_ativadoras', []):
            for recurso, valor in variante.get('modificadores', {}).items():
                bonus[recurso] += valor
            fontes.append(f'{variante["nome"]} ativado por {melhoria}: {variante.get("modificadores", {})}')
        return bonus, fontes

    def passavel(self, x, y):
        return self.terreno(x, y) in PASSAVEIS_TERRA

    def passavel_mar(self, x, y):
        return self.terreno(x, y) in PASSAVEIS_MAR

    def passavel_mar_raso(self, x, y):
        return self.terreno(x, y) in PASSAVEIS_MAR_RASO

    def passavel_para(self, x, y, dominio='terra'):
        if dominio == 'mar':
            return self.passavel_mar(x, y)
        if dominio == 'mar_raso':
            return self.passavel_mar_raso(x, y)
        return self.passavel(x, y)

    def construir_melhoria(self, x, y, tipo):
        if not self.passavel(x, y) or (x, y) in self.melhorias:
            return False
        self.melhorias[(x, y)] = tipo
        return True

    def encontrar_posicao_inicial(self):
        cx, cy = self.largura // 2, self.altura // 2
        if self.passavel(cx, cy):
            return cx, cy
        fila = deque([(cx, cy)])
        vistos = {(cx, cy)}
        while fila:
            x, y = fila.popleft()
            for dx, dy in VIZINHOS_8:
                nx, ny = x + dx, y + dy
                if not self.dentro(nx, ny) or (nx, ny) in vistos:
                    continue
                if self.passavel(nx, ny):
                    return nx, ny
                vistos.add((nx, ny))
                fila.append((nx, ny))
        self.tiles[cy][cx] = 'Grama'
        return cx, cy

    def caminho(self, origem, destino, dominio='terra'):
        if origem == destino:
            return []
        if not self.passavel_para(destino[0], destino[1], dominio):
            return []
        fila = deque([origem])
        anteriores = {origem: None}
        while fila:
            atual = fila.popleft()
            if atual == destino:
                break
            x, y = atual
            for dx, dy in VIZINHOS_8:
                prox = (x + dx, y + dy)
                if prox in anteriores or not self.dentro(*prox) or not self.passavel_para(*prox, dominio):
                    continue
                anteriores[prox] = atual
                fila.append(prox)
        if destino not in anteriores:
            return []
        caminho = []
        atual = destino
        while atual != origem:
            caminho.append(atual)
            atual = anteriores[atual]
        caminho.reverse()
        return caminho
