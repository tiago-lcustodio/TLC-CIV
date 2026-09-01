import pygame


class MenuConfiguracao:
    def __init__(self, tela):
        self.tela = tela

        self.fonte_titulo = pygame.font.SysFont("arial", 40, bold=True)
        self.fonte = pygame.font.SysFont("arial", 22)
        self.fonte_pequena = pygame.font.SysFont("arial", 18)

        self.percentuais = {
            "Grama": 40,
            "Água": 30,
            "Montanha": 10,
            "Deserto": 10,
            "Neve": 10,
        }

        self.tamanhos = [36, 72, 144, 288]
        self.indice_tamanho = 0

        self.ordem_terrenos = [
            "Grama",
            "Água",
            "Montanha",
            "Deserto",
            "Neve",
        ]

    def ajustar_percentual(self, terreno, delta):
        valor_atual = self.percentuais[terreno]
        novo_valor = max(0, min(100, valor_atual + delta))
        diferenca = novo_valor - valor_atual

        if diferenca == 0:
            return

        outros = [t for t in self.ordem_terrenos if t != terreno]

        if diferenca > 0:
            restante = diferenca

            while restante > 0:
                alterou = False

                for outro in outros:
                    if restante <= 0:
                        break

                    if self.percentuais[outro] > 0:
                        self.percentuais[outro] -= 1
                        restante -= 1
                        alterou = True

                if not alterou:
                    return

            self.percentuais[terreno] = novo_valor

        else:
            quantidade = -diferenca
            self.percentuais[terreno] = novo_valor
            indice = 0

            while quantidade > 0:
                outro = outros[indice % len(outros)]

                if self.percentuais[outro] < 100:
                    self.percentuais[outro] += 1
                    quantidade -= 1

                indice += 1

    def desenhar_botao(self, retangulo, texto, cor=(70, 70, 70)):
        pygame.draw.rect(self.tela, cor, retangulo, border_radius=6)
        pygame.draw.rect(self.tela, (20, 20, 20), retangulo, 2, border_radius=6)

        superficie = self.fonte_pequena.render(texto, True, (255, 255, 255))
        self.tela.blit(superficie, superficie.get_rect(center=retangulo.center))

    def executar(self):
        relogio = pygame.time.Clock()

        while True:
            largura, altura = self.tela.get_size()
            self.tela.fill((35, 40, 48))

            titulo = self.fonte_titulo.render("TLC CIV", True, (240, 240, 240))
            subtitulo = self.fonte.render(
                "Configuração inicial do mundo",
                True,
                (200, 200, 200),
            )

            self.tela.blit(titulo, titulo.get_rect(center=(largura // 2, 55)))
            self.tela.blit(subtitulo, subtitulo.get_rect(center=(largura // 2, 98)))

            painel_largura = min(620, largura - 40)
            painel_x = (largura - painel_largura) // 2
            painel = pygame.Rect(painel_x, 135, painel_largura, min(500, altura - 175))

            pygame.draw.rect(self.tela, (45, 50, 58), painel, border_radius=10)
            pygame.draw.rect(self.tela, (75, 80, 88), painel, 1, border_radius=10)

            botoes_menos = {}
            botoes_mais = {}

            y = painel.y + 28
            texto_x = painel.x + 45
            botoes_x = painel.right - 155

            for terreno in self.ordem_terrenos:
                texto = self.fonte.render(
                    f"{terreno}: {self.percentuais[terreno]}%",
                    True,
                    (235, 235, 235),
                )
                self.tela.blit(texto, (texto_x, y + 6))

                menos = pygame.Rect(botoes_x, y, 42, 38)
                mais = pygame.Rect(botoes_x + 55, y, 42, 38)

                botoes_menos[terreno] = menos
                botoes_mais[terreno] = mais

                self.desenhar_botao(menos, "-")
                self.desenhar_botao(mais, "+")
                y += 52

            soma = sum(self.percentuais.values())
            total = self.fonte_pequena.render(
                f"Total: {soma}%",
                True,
                (120, 230, 140),
            )
            self.tela.blit(total, (texto_x, y + 2))

            y += 45
            tamanho = self.tamanhos[self.indice_tamanho]
            tamanho_texto = self.fonte.render(
                f"Mapa: {tamanho} x {tamanho}",
                True,
                (235, 235, 235),
            )
            self.tela.blit(tamanho_texto, (texto_x, y + 5))

            anterior = pygame.Rect(botoes_x, y, 42, 38)
            proximo = pygame.Rect(botoes_x + 55, y, 42, 38)
            self.desenhar_botao(anterior, "<")
            self.desenhar_botao(proximo, ">")

            iniciar = pygame.Rect(
                largura // 2 - 125,
                min(altura - 76, painel.bottom - 58),
                250,
                48,
            )
            self.desenhar_botao(iniciar, "INICIAR JOGO", (45, 115, 65))

            dica = self.fonte_pequena.render(
                "As porcentagens sempre permanecem em 100%.",
                True,
                (180, 180, 180),
            )
            self.tela.blit(dica, dica.get_rect(center=(largura // 2, iniciar.y - 22)))

            pygame.display.flip()

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return None

                if evento.type == pygame.VIDEORESIZE:
                    self.tela = pygame.display.set_mode(evento.size, pygame.RESIZABLE)

                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    pos = evento.pos

                    for terreno, botao in botoes_menos.items():
                        if botao.collidepoint(pos):
                            self.ajustar_percentual(terreno, -1)

                    for terreno, botao in botoes_mais.items():
                        if botao.collidepoint(pos):
                            self.ajustar_percentual(terreno, +1)

                    if anterior.collidepoint(pos):
                        self.indice_tamanho = (self.indice_tamanho - 1) % len(self.tamanhos)

                    if proximo.collidepoint(pos):
                        self.indice_tamanho = (self.indice_tamanho + 1) % len(self.tamanhos)

                    if iniciar.collidepoint(pos):
                        tamanho = self.tamanhos[self.indice_tamanho]
                        return {
                            "percentuais": self.percentuais.copy(),
                            "largura_mapa": tamanho,
                            "altura_mapa": tamanho,
                        }

            relogio.tick(60)
