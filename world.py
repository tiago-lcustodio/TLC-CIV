import random
from collections import deque


PASSAVEIS = {"Grama", "Deserto", "Neve"}


class Mundo:
    def __init__(self, largura, altura, percentuais, seed=None):
        self.largura = largura
        self.altura = altura
        self.percentuais = percentuais
        self.random = random.Random(seed)
        self.tiles = self.gerar_mapa()

    def _campo_ruido(self, suavizacoes=5):
        campo = [
            [self.random.random() for _ in range(self.largura)]
            for _ in range(self.altura)
        ]

        for _ in range(suavizacoes):
            novo = [[0.0] * self.largura for _ in range(self.altura)]

            for y in range(self.altura):
                for x in range(self.largura):
                    total = 0.0
                    quantidade = 0

                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            nx = (x + dx) % self.largura
                            ny = min(self.altura - 1, max(0, y + dy))
                            total += campo[ny][nx]
                            quantidade += 1

                    novo[y][x] = total / quantidade

            campo = novo

        return campo

    def gerar_mapa(self):
        total = self.largura * self.altura

        quotas = {}
        usados = 0
        ordem = ["Água", "Montanha", "Deserto", "Neve"]

        for terreno in ordem:
            quantidade = round(total * self.percentuais[terreno] / 100)
            quotas[terreno] = quantidade
            usados += quantidade

        quotas["Grama"] = max(0, total - usados)

        oceano = self._campo_ruido(7)
        montanha = self._campo_ruido(4)
        deserto = self._campo_ruido(5)
        neve = self._campo_ruido(3)

        mapa = [[None for _ in range(self.largura)] for _ in range(self.altura)]
        livres = {(x, y) for y in range(self.altura) for x in range(self.largura)}

        def escolher(quantidade, score_func):
            if quantidade <= 0 or not livres:
                return []

            candidatos = sorted(livres, key=lambda p: score_func(*p), reverse=True)
            escolhidos = candidatos[: min(quantidade, len(candidatos))]
            for p in escolhidos:
                livres.remove(p)
            return escolhidos

        # Oceanos: ruído muito suavizado gera grandes massas contínuas.
        agua = escolher(quotas["Água"], lambda x, y: oceano[y][x])
        for x, y in agua:
            mapa[y][x] = "Água"

        # Neve: forte preferência pelas latitudes polares, com pequenas irregularidades.
        def score_neve(x, y):
            if self.altura <= 1:
                polo = 1.0
            else:
                lat = y / (self.altura - 1)
                polo = abs(lat - 0.5) * 2.0
            return polo * 1.8 + neve[y][x] * 0.45

        celulas_neve = escolher(quotas["Neve"], score_neve)
        for x, y in celulas_neve:
            mapa[y][x] = "Neve"

        # Cordilheiras: campo de ruído intermediário. O bônus local cria faixas agrupadas.
        def score_montanha(x, y):
            vizinhos = []
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx = (x + dx) % self.largura
                ny = min(self.altura - 1, max(0, y + dy))
                vizinhos.append(montanha[ny][nx])
            relevo = montanha[y][x]
            contraste = abs(relevo - sum(vizinhos) / len(vizinhos))
            return relevo + contraste * 0.7

        celulas_montanha = escolher(quotas["Montanha"], score_montanha)
        for x, y in celulas_montanha:
            mapa[y][x] = "Montanha"

        # Desertos tendem às latitudes intermediárias/quentes e aparecem em blocos.
        def score_deserto(x, y):
            if self.altura <= 1:
                faixa = 1.0
            else:
                lat = y / (self.altura - 1)
                distancia_equador = abs(lat - 0.5)
                faixa = max(0.0, 1.0 - abs(distancia_equador - 0.22) * 3.0)
            return deserto[y][x] * 1.2 + faixa * 0.7

        celulas_deserto = escolher(quotas["Deserto"], score_deserto)
        for x, y in celulas_deserto:
            mapa[y][x] = "Deserto"

        for x, y in livres:
            mapa[y][x] = "Grama"

        return mapa

    def dentro(self, x, y):
        return 0 <= x < self.largura and 0 <= y < self.altura

    def terreno(self, x, y):
        if not self.dentro(x, y):
            return None
        return self.tiles[y][x]

    def passavel(self, x, y):
        return self.terreno(x, y) in PASSAVEIS

    def encontrar_posicao_inicial(self):
        cx = self.largura // 2
        cy = self.altura // 2

        if self.passavel(cx, cy):
            return cx, cy

        fila = deque([(cx, cy)])
        visitados = {(cx, cy)}

        while fila:
            x, y = fila.popleft()

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy

                if not self.dentro(nx, ny) or (nx, ny) in visitados:
                    continue

                if self.passavel(nx, ny):
                    return nx, ny

                visitados.add((nx, ny))
                fila.append((nx, ny))

        # Se a configuração gerou 100% de terreno impassável, cria uma
        # pequena exceção para que o jogo ainda possa começar.
        cx = self.largura // 2
        cy = self.altura // 2
        self.tiles[cy][cx] = "Grama"
        return cx, cy

    def caminho(self, origem, destino):
        if origem == destino:
            return []

        if not self.passavel(*destino):
            return []

        fila = deque([origem])
        anteriores = {origem: None}

        while fila:
            atual = fila.popleft()

            if atual == destino:
                break

            x, y = atual

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                prox = (x + dx, y + dy)

                if prox in anteriores:
                    continue

                if not self.dentro(*prox) or not self.passavel(*prox):
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
