import pygame

from world import Mundo
from entities import Unidade, Cidade


TAMANHO_TILE = 34
ALTURA_BARRA_MENU = 32
ALTURA_BARRA_FERRAMENTAS = 50
TOPO_MAPA = ALTURA_BARRA_MENU + ALTURA_BARRA_FERRAMENTAS

CORES_TERRENO = {
    "Grama": (74, 154, 75),
    "Água": (55, 116, 190),
    "Montanha": (128, 94, 70),
    "Deserto": (222, 196, 91),
    "Neve": (238, 241, 244),
}

COR_GRADE = (50, 55, 55)


class Jogo:
    def __init__(self, tela, configuracao):
        self.tela = tela
        self.configuracao = configuracao

        self.fonte = pygame.font.SysFont("arial", 17)
        self.fonte_pequena = pygame.font.SysFont("arial", 15)
        self.fonte_negrito = pygame.font.SysFont("arial", 16, bold=True)
        self.fonte_grande = pygame.font.SysFont("arial", 26, bold=True)

        self.mundo = Mundo(
            configuracao["largura_mapa"],
            configuracao["altura_mapa"],
            configuracao["percentuais"],
        )

        self.offset_x = 0
        self.offset_y = 0
        self.velocidade_scroll = 42
        self.turno = 1

        self.unidades = []
        self.cidades = []
        self.unidade_selecionada = None

        inicio_x, inicio_y = self.mundo.encontrar_posicao_inicial()
        self.unidades.append(Unidade("Settler", inicio_x, inicio_y))

        self.menu_aberto = None
        self.modal = None
        self.cidade_modal = None
        self.campo_nome = ""
        self.mensagem = "Selecione o Settler e clique em um destino."

        self._atualizar_layout()
        self.centralizar_camera(inicio_x, inicio_y)

    def _atualizar_layout(self):
        self.largura_tela, self.altura_tela = self.tela.get_size()
        self.viewport = pygame.Rect(
            0,
            TOPO_MAPA,
            max(100, self.largura_tela - 14),
            max(100, self.altura_tela - TOPO_MAPA - 14),
        )

        # Retângulos interativos existem desde o primeiro frame e são
        # recalculados quando a janela é redimensionada/maximizada.
        self.rect_menu_jogo = pygame.Rect(10, 2, 72, 28)
        self.rect_menu_ajuda = pygame.Rect(88, 2, 72, 28)
        self.rect_next_turn = pygame.Rect(12, ALTURA_BARRA_MENU + 8, 118, 34)
        self.rect_fundar = pygame.Rect(140, ALTURA_BARRA_MENU + 8, 140, 34)
        self.rect_novo = pygame.Rect(10, ALTURA_BARRA_MENU, 135, 30)
        self.rect_sair = pygame.Rect(10, ALTURA_BARRA_MENU + 30, 135, 30)
        self.rect_sobre = pygame.Rect(88, ALTURA_BARRA_MENU, 135, 30)

        self.limitar_camera()

    def centralizar_camera(self, x, y):
        self.offset_x = x * TAMANHO_TILE - self.viewport.width // 2
        self.offset_y = y * TAMANHO_TILE - self.viewport.height // 2
        self.limitar_camera()

    def limitar_camera(self):
        if not hasattr(self, "viewport"):
            return

        largura_total = self.mundo.largura * TAMANHO_TILE
        altura_total = self.mundo.altura * TAMANHO_TILE

        self.offset_x = max(0, min(self.offset_x, max(0, largura_total - self.viewport.width)))
        self.offset_y = max(0, min(self.offset_y, max(0, altura_total - self.viewport.height)))

    def tile_para_tela(self, x, y):
        return (
            x * TAMANHO_TILE - self.offset_x,
            TOPO_MAPA + y * TAMANHO_TILE - self.offset_y,
        )

    def tela_para_tile(self, pos):
        mx, my = pos
        if not self.viewport.collidepoint(pos):
            return None

        x = int((mx + self.offset_x) // TAMANHO_TILE)
        y = int((my - TOPO_MAPA + self.offset_y) // TAMANHO_TILE)

        if self.mundo.dentro(x, y):
            return x, y
        return None

    def desenhar_botao(self, rect, texto, ativo=True, cor=None):
        if cor is None:
            cor = (77, 83, 92) if ativo else (58, 61, 66)

        pygame.draw.rect(self.tela, cor, rect, border_radius=4)
        pygame.draw.rect(self.tela, (28, 30, 33), rect, 1, border_radius=4)

        texto_cor = (245, 245, 245) if ativo else (135, 135, 135)
        surf = self.fonte_pequena.render(texto, True, texto_cor)
        self.tela.blit(surf, surf.get_rect(center=rect.center))

    def desenhar_interface(self):
        # Menu principal
        pygame.draw.rect(self.tela, (30, 33, 38), (0, 0, self.largura_tela, ALTURA_BARRA_MENU))
        pygame.draw.line(self.tela, (70, 70, 70), (0, ALTURA_BARRA_MENU - 1), (self.largura_tela, ALTURA_BARRA_MENU - 1))

        for rect, texto in ((self.rect_menu_jogo, "Jogo"), (self.rect_menu_ajuda, "Ajuda")):
            if self.menu_aberto == texto:
                pygame.draw.rect(self.tela, (65, 69, 76), rect)
            surf = self.fonte_pequena.render(texto, True, (230, 230, 230))
            self.tela.blit(surf, surf.get_rect(center=rect.center))

        # Barra de ferramentas
        pygame.draw.rect(
            self.tela,
            (48, 53, 60),
            (0, ALTURA_BARRA_MENU, self.largura_tela, ALTURA_BARRA_FERRAMENTAS),
        )

        pode_fundar = (
            self.unidade_selecionada is not None
            and self.unidade_selecionada.tipo == "Settler"
        )

        self.desenhar_botao(self.rect_next_turn, "NEXT TURN", True, (57, 102, 69))
        self.desenhar_botao(self.rect_fundar, "Fundar Cidade", pode_fundar)

        if self.unidade_selecionada:
            status = (
                f"{self.unidade_selecionada.tipo} | Movimento: "
                f"{self.unidade_selecionada.movimento}/{self.unidade_selecionada.movimento_max}"
            )
            if self.unidade_selecionada.rota:
                status += f" | Destino: {self.unidade_selecionada.rota[-1]}"
        else:
            status = f"Turno {self.turno} | Nenhuma unidade selecionada"

        surf = self.fonte_pequena.render(status, True, (225, 225, 225))
        self.tela.blit(surf, (300, ALTURA_BARRA_MENU + 17))

        # Dropdowns
        if self.menu_aberto == "Jogo":
            pygame.draw.rect(self.tela, (49, 53, 60), (10, ALTURA_BARRA_MENU, 135, 60))
            self._desenhar_item_menu(self.rect_novo, "Novo")
            self._desenhar_item_menu(self.rect_sair, "Sair")

        elif self.menu_aberto == "Ajuda":
            pygame.draw.rect(self.tela, (49, 53, 60), self.rect_sobre)
            self._desenhar_item_menu(self.rect_sobre, "Sobre")

    def _desenhar_item_menu(self, rect, texto):
        pygame.draw.rect(self.tela, (80, 84, 91), rect, 1)
        surf = self.fonte_pequena.render(texto, True, (235, 235, 235))
        self.tela.blit(surf, (rect.x + 10, rect.y + 7))

    def desenhar_mapa(self):
        self.tela.set_clip(self.viewport)
        pygame.draw.rect(self.tela, (15, 15, 15), self.viewport)

        x0 = max(0, self.offset_x // TAMANHO_TILE)
        y0 = max(0, self.offset_y // TAMANHO_TILE)
        x1 = min(self.mundo.largura, (self.offset_x + self.viewport.width) // TAMANHO_TILE + 2)
        y1 = min(self.mundo.altura, (self.offset_y + self.viewport.height) // TAMANHO_TILE + 2)

        for y in range(y0, y1):
            for x in range(x0, x1):
                terreno = self.mundo.tiles[y][x]
                sx, sy = self.tile_para_tela(x, y)
                rect = pygame.Rect(sx, sy, TAMANHO_TILE, TAMANHO_TILE)
                pygame.draw.rect(self.tela, CORES_TERRENO[terreno], rect)
                pygame.draw.rect(self.tela, COR_GRADE, rect, 1)

        self.desenhar_cidades()
        self.desenhar_unidades()

        self.tela.set_clip(None)

    def desenhar_cidades(self):
        for cidade in self.cidades:
            sx, sy = self.tile_para_tela(cidade.x, cidade.y)
            centro = (sx + TAMANHO_TILE // 2, sy + TAMANHO_TILE // 2)

            pygame.draw.rect(
                self.tela,
                (165, 60, 55),
                (sx + 6, sy + 6, TAMANHO_TILE - 12, TAMANHO_TILE - 12),
                border_radius=4,
            )
            pygame.draw.rect(
                self.tela,
                (245, 220, 165),
                (sx + 6, sy + 6, TAMANHO_TILE - 12, TAMANHO_TILE - 12),
                2,
                border_radius=4,
            )

            c = self.fonte_negrito.render("C", True, (255, 255, 255))
            self.tela.blit(c, c.get_rect(center=centro))

            # Pequenos marcadores das construções já concluídas.
            marcadores = ""
            if "Templo" in cidade.construcoes:
                marcadores += "T"
            if "Muralha" in cidade.construcoes:
                marcadores += "M"
            if marcadores:
                marca = pygame.font.SysFont("arial", 10, bold=True).render(
                    marcadores, True, (255, 240, 170)
                )
                self.tela.blit(marca, (sx + 2, sy + TAMANHO_TILE - 12))

            nome = self.fonte_pequena.render(cidade.nome, True, (20, 20, 20))
            fundo = pygame.Rect(sx - 2, sy - 18, nome.get_width() + 8, 18)
            pygame.draw.rect(self.tela, (245, 235, 205), fundo, border_radius=3)
            self.tela.blit(nome, (fundo.x + 4, fundo.y + 1))

    def desenhar_unidades(self):
        for unidade in self.unidades:
            sx, sy = self.tile_para_tela(unidade.x, unidade.y)
            centro = (sx + TAMANHO_TILE // 2, sy + TAMANHO_TILE // 2)

            cor = (55, 65, 160) if unidade.tipo == "Settler" else (150, 55, 55)
            pygame.draw.circle(self.tela, cor, centro, 12)
            pygame.draw.circle(self.tela, (245, 245, 245), centro, 12, 2)

            if unidade is self.unidade_selecionada:
                pygame.draw.rect(
                    self.tela,
                    (255, 235, 70),
                    (sx + 1, sy + 1, TAMANHO_TILE - 2, TAMANHO_TILE - 2),
                    3,
                )

            letra = self.fonte_negrito.render(unidade.icone, True, (255, 255, 255))
            self.tela.blit(letra, letra.get_rect(center=centro))

    def desenhar_barras_rolagem(self):
        largura_total = self.mundo.largura * TAMANHO_TILE
        altura_total = self.mundo.altura * TAMANHO_TILE

        if largura_total > self.viewport.width:
            trilho = pygame.Rect(0, self.altura_tela - 14, self.largura_tela - 14, 14)
            pygame.draw.rect(self.tela, (45, 45, 45), trilho)
            tamanho = max(30, int(trilho.width * self.viewport.width / largura_total))
            max_offset = largura_total - self.viewport.width
            x = int((self.offset_x / max_offset) * (trilho.width - tamanho)) if max_offset else 0
            pygame.draw.rect(self.tela, (135, 135, 135), (x, trilho.y + 2, tamanho, 10), border_radius=3)

        if altura_total > self.viewport.height:
            trilho = pygame.Rect(self.largura_tela - 14, TOPO_MAPA, 14, self.altura_tela - TOPO_MAPA - 14)
            pygame.draw.rect(self.tela, (45, 45, 45), trilho)
            tamanho = max(30, int(trilho.height * self.viewport.height / altura_total))
            max_offset = altura_total - self.viewport.height
            y = trilho.y + (int((self.offset_y / max_offset) * (trilho.height - tamanho)) if max_offset else 0)
            pygame.draw.rect(self.tela, (135, 135, 135), (trilho.x + 2, y, 10, tamanho), border_radius=3)

    def unidade_em(self, x, y):
        for unidade in reversed(self.unidades):
            if unidade.x == x and unidade.y == y:
                return unidade
        return None

    def cidade_em(self, x, y):
        for cidade in self.cidades:
            if cidade.x == x and cidade.y == y:
                return cidade
        return None

    def selecionar_unidade(self, unidade):
        for u in self.unidades:
            u.selecionada = False
        self.unidade_selecionada = unidade
        if unidade:
            unidade.selecionada = True
            self.mensagem = f"{unidade.tipo} selecionado."

    def ordenar_movimento(self, destino):
        unidade = self.unidade_selecionada
        if unidade is None:
            return

        rota = self.mundo.caminho((unidade.x, unidade.y), destino)

        if not rota and destino != (unidade.x, unidade.y):
            self.mensagem = "Não existe rota terrestre até esse quadrado."
            return

        unidade.definir_rota(rota)

        if unidade.movimento > 0:
            unidade.mover_um_passo()

        if unidade.rota:
            self.mensagem = "Movimento esgotado. Clique NEXT TURN para continuar."
        else:
            self.mensagem = "Unidade chegou ao destino."

    def fundar_cidade(self):
        unidade = self.unidade_selecionada

        if unidade is None or unidade.tipo != "Settler":
            self.mensagem = "Selecione um Settler para fundar uma cidade."
            return

        if self.cidade_em(unidade.x, unidade.y):
            self.mensagem = "Já existe uma cidade neste quadrado."
            return

        self.modal = "nome_cidade"
        self.campo_nome = ""

    def confirmar_fundacao(self):
        nome = self.campo_nome.strip()
        if not nome:
            return

        unidade = self.unidade_selecionada
        if unidade is None or unidade.tipo != "Settler":
            self.modal = None
            return

        cidade = Cidade(nome, unidade.x, unidade.y)
        self.cidades.append(cidade)
        self.unidades.remove(unidade)
        self.selecionar_unidade(None)
        self.modal = None
        self.mensagem = f"Cidade {nome} fundada!"

    def _posicao_spawn_cidade(self, cidade):
        # Prioriza quadrados adjacentes para manter o tile da cidade clicável.
        candidatos = [
            (cidade.x + 1, cidade.y),
            (cidade.x - 1, cidade.y),
            (cidade.x, cidade.y + 1),
            (cidade.x, cidade.y - 1),
            (cidade.x + 1, cidade.y + 1),
            (cidade.x - 1, cidade.y + 1),
            (cidade.x + 1, cidade.y - 1),
            (cidade.x - 1, cidade.y - 1),
        ]

        for x, y in candidatos:
            if (
                self.mundo.dentro(x, y)
                and self.mundo.passavel(x, y)
                and self.unidade_em(x, y) is None
                and self.cidade_em(x, y) is None
            ):
                return x, y

        return cidade.x, cidade.y

    def proximo_turno(self):
        self.turno += 1

        for unidade in self.unidades:
            unidade.novo_turno()
            if unidade.rota:
                unidade.mover_um_passo()

        concluidos = []

        for cidade in self.cidades:
            resultado = cidade.avancar_turno()
            if resultado:
                concluidos.append((cidade, resultado))

        for cidade, (categoria, nome) in concluidos:
            if categoria == "unidade":
                spawn_x, spawn_y = self._posicao_spawn_cidade(cidade)
                self.unidades.append(Unidade(nome, spawn_x, spawn_y))
                self.mensagem = f"{cidade.nome} concluiu a unidade {nome}."
            else:
                self.mensagem = f"{cidade.nome} concluiu {nome}."

        if not concluidos:
            self.mensagem = f"Turno {self.turno}."

    def abrir_cidade(self, cidade):
        self.cidade_modal = cidade
        self.modal = "cidade"
        self.menu_aberto = None

    def iniciar_producao(self, categoria, nome):
        cidade = self.cidade_modal
        if cidade is None:
            return

        if cidade.producao_nome is not None:
            self.mensagem = "A cidade já possui uma produção em andamento."
            return

        if categoria == "construcao" and nome in cidade.construcoes:
            self.mensagem = f"{nome} já existe em {cidade.nome}."
            return

        if cidade.iniciar_producao(categoria, nome):
            self.mensagem = f"{cidade.nome} começou a produzir {nome}."

    def desenhar_modal_nome(self):
        overlay = pygame.Surface((self.largura_tela, self.altura_tela), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 135))
        self.tela.blit(overlay, (0, 0))

        caixa = pygame.Rect(self.largura_tela // 2 - 230, self.altura_tela // 2 - 105, 460, 210)
        pygame.draw.rect(self.tela, (50, 54, 61), caixa, border_radius=10)
        pygame.draw.rect(self.tela, (120, 125, 135), caixa, 1, border_radius=10)

        titulo = self.fonte_grande.render("Fundar Cidade", True, (245, 245, 245))
        self.tela.blit(titulo, titulo.get_rect(center=(caixa.centerx, caixa.y + 35)))

        instrucao = self.fonte.render("Digite o nome da cidade:", True, (220, 220, 220))
        self.tela.blit(instrucao, (caixa.x + 30, caixa.y + 70))

        self.rect_campo_nome = pygame.Rect(caixa.x + 30, caixa.y + 98, caixa.width - 60, 38)
        pygame.draw.rect(self.tela, (235, 235, 235), self.rect_campo_nome, border_radius=4)

        texto = self.fonte.render(self.campo_nome + "|", True, (30, 30, 30))
        self.tela.blit(texto, (self.rect_campo_nome.x + 8, self.rect_campo_nome.y + 8))

        self.rect_confirmar_nome = pygame.Rect(caixa.centerx - 100, caixa.bottom - 55, 95, 34)
        self.rect_cancelar_nome = pygame.Rect(caixa.centerx + 5, caixa.bottom - 55, 95, 34)
        self.desenhar_botao(self.rect_confirmar_nome, "Fundar", bool(self.campo_nome.strip()), (57, 102, 69))
        self.desenhar_botao(self.rect_cancelar_nome, "Cancelar")

    def desenhar_modal_cidade(self):
        cidade = self.cidade_modal
        if cidade is None:
            return

        overlay = pygame.Surface((self.largura_tela, self.altura_tela), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 125))
        self.tela.blit(overlay, (0, 0))

        largura = min(760, self.largura_tela - 60)
        altura = min(480, self.altura_tela - 70)
        caixa = pygame.Rect((self.largura_tela - largura) // 2, (self.altura_tela - altura) // 2, largura, altura)
        pygame.draw.rect(self.tela, (48, 52, 59), caixa, border_radius=10)
        pygame.draw.rect(self.tela, (125, 130, 140), caixa, 1, border_radius=10)

        titulo = self.fonte_grande.render(cidade.nome, True, (245, 235, 190))
        self.tela.blit(titulo, (caixa.x + 25, caixa.y + 20))

        self.rect_fechar_cidade = pygame.Rect(caixa.right - 45, caixa.y + 15, 30, 30)
        self.desenhar_botao(self.rect_fechar_cidade, "X")

        if cidade.producao_nome:
            prod = f"Produção atual: {cidade.producao_nome} ({cidade.turnos_restantes} turno(s))"
        else:
            prod = "Produção atual: nenhuma"

        prod_surf = self.fonte.render(prod, True, (220, 220, 220))
        self.tela.blit(prod_surf, (caixa.x + 25, caixa.y + 62))

        esquerda_x = caixa.x + 25
        topo = caixa.y + 110

        unidade_titulo = self.fonte_negrito.render("Construir Unidades", True, (240, 240, 240))
        self.tela.blit(unidade_titulo, (esquerda_x, topo))

        self.rect_prod_settler = pygame.Rect(esquerda_x, topo + 32, 210, 38)
        self.rect_prod_warrior = pygame.Rect(esquerda_x, topo + 78, 210, 38)
        livre = cidade.producao_nome is None
        self.desenhar_botao(self.rect_prod_settler, "Settler - 3 turnos", livre)
        self.desenhar_botao(self.rect_prod_warrior, "Warrior - 3 turnos", livre)

        constr_titulo = self.fonte_negrito.render("Construir Construções", True, (240, 240, 240))
        self.tela.blit(constr_titulo, (esquerda_x, topo + 145))

        self.rect_prod_templo = pygame.Rect(esquerda_x, topo + 177, 210, 38)
        self.rect_prod_muralha = pygame.Rect(esquerda_x, topo + 223, 210, 38)

        self.desenhar_botao(
            self.rect_prod_templo,
            "Templo - 5 turnos",
            livre and "Templo" not in cidade.construcoes,
        )
        self.desenhar_botao(
            self.rect_prod_muralha,
            "Muralha - 3 turnos",
            livre and "Muralha" not in cidade.construcoes,
        )

        divisoria_x = caixa.x + int(largura * 0.58)
        pygame.draw.line(self.tela, (95, 100, 108), (divisoria_x, topo), (divisoria_x, caixa.bottom - 30), 1)

        painel_titulo = self.fonte_negrito.render("Construções existentes", True, (240, 240, 240))
        self.tela.blit(painel_titulo, (divisoria_x + 25, topo))

        if cidade.construcoes:
            y = topo + 38
            for construcao in cidade.construcoes:
                linha = self.fonte.render(f"• {construcao}", True, (220, 220, 220))
                self.tela.blit(linha, (divisoria_x + 25, y))
                y += 30
        else:
            vazio = self.fonte.render("Nenhuma construção.", True, (170, 170, 170))
            self.tela.blit(vazio, (divisoria_x + 25, topo + 38))

    def desenhar_modal_sobre(self):
        overlay = pygame.Surface((self.largura_tela, self.altura_tela), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.tela.blit(overlay, (0, 0))

        caixa = pygame.Rect(self.largura_tela // 2 - 210, self.altura_tela // 2 - 100, 420, 200)
        pygame.draw.rect(self.tela, (50, 54, 61), caixa, border_radius=10)
        pygame.draw.rect(self.tela, (120, 125, 135), caixa, 1, border_radius=10)

        titulo = self.fonte_grande.render("TLC CIV", True, (245, 235, 190))
        self.tela.blit(titulo, titulo.get_rect(center=(caixa.centerx, caixa.y + 40)))

        linhas = [
            "Protótipo em Pygame inspirado em jogos 4X.",
            "Versão inicial: mapa, unidades, cidades e produção.",
        ]

        y = caixa.y + 80
        for linha in linhas:
            surf = self.fonte.render(linha, True, (220, 220, 220))
            self.tela.blit(surf, surf.get_rect(center=(caixa.centerx, y)))
            y += 28

        self.rect_fechar_sobre = pygame.Rect(caixa.centerx - 50, caixa.bottom - 48, 100, 32)
        self.desenhar_botao(self.rect_fechar_sobre, "Fechar")

    def mover_camera_teclado(self):
        if self.modal is not None:
            return

        teclas = pygame.key.get_pressed()

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            self.offset_x -= self.velocidade_scroll
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            self.offset_x += self.velocidade_scroll
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            self.offset_y -= self.velocidade_scroll
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            self.offset_y += self.velocidade_scroll

        self.limitar_camera()

    def tratar_click_mapa(self, pos):
        tile = self.tela_para_tile(pos)
        if tile is None:
            return

        x, y = tile
        unidade = self.unidade_em(x, y)
        cidade = self.cidade_em(x, y)

        if unidade is not None:
            self.selecionar_unidade(unidade)
            return

        if self.unidade_selecionada is not None:
            self.ordenar_movimento((x, y))
            return

        if cidade is not None:
            self.abrir_cidade(cidade)

    def tratar_evento_modal(self, evento):
        if self.modal == "nome_cidade":
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.modal = None
                elif evento.key == pygame.K_RETURN:
                    self.confirmar_fundacao()
                elif evento.key == pygame.K_BACKSPACE:
                    self.campo_nome = self.campo_nome[:-1]
                elif evento.unicode.isprintable() and len(self.campo_nome) < 24:
                    self.campo_nome += evento.unicode

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.rect_confirmar_nome.collidepoint(evento.pos) and self.campo_nome.strip():
                    self.confirmar_fundacao()
                elif self.rect_cancelar_nome.collidepoint(evento.pos):
                    self.modal = None
            return True

        if self.modal == "cidade":
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.modal = None
                self.cidade_modal = None

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                pos = evento.pos
                cidade = self.cidade_modal

                if self.rect_fechar_cidade.collidepoint(pos):
                    self.modal = None
                    self.cidade_modal = None
                elif self.rect_prod_settler.collidepoint(pos) and cidade.producao_nome is None:
                    self.iniciar_producao("unidade", "Settler")
                elif self.rect_prod_warrior.collidepoint(pos) and cidade.producao_nome is None:
                    self.iniciar_producao("unidade", "Warrior")
                elif (
                    self.rect_prod_templo.collidepoint(pos)
                    and cidade.producao_nome is None
                    and "Templo" not in cidade.construcoes
                ):
                    self.iniciar_producao("construcao", "Templo")
                elif (
                    self.rect_prod_muralha.collidepoint(pos)
                    and cidade.producao_nome is None
                    and "Muralha" not in cidade.construcoes
                ):
                    self.iniciar_producao("construcao", "Muralha")
            return True

        if self.modal == "sobre":
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.modal = None
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.rect_fechar_sobre.collidepoint(evento.pos):
                    self.modal = None
            return True

        return False

    def executar(self):
        relogio = pygame.time.Clock()

        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return "sair"

                if evento.type == pygame.VIDEORESIZE:
                    self.tela = pygame.display.set_mode(evento.size, pygame.RESIZABLE)
                    self._atualizar_layout()
                    continue

                if self.modal is not None:
                    self.tratar_evento_modal(evento)
                    continue

                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    if self.menu_aberto:
                        self.menu_aberto = None
                    else:
                        self.selecionar_unidade(None)

                elif evento.type == pygame.MOUSEWHEEL:
                    self.offset_y -= evento.y * self.velocidade_scroll
                    self.limitar_camera()

                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    pos = evento.pos

                    if self.rect_menu_jogo.collidepoint(pos):
                        self.menu_aberto = None if self.menu_aberto == "Jogo" else "Jogo"
                        continue

                    if self.rect_menu_ajuda.collidepoint(pos):
                        self.menu_aberto = None if self.menu_aberto == "Ajuda" else "Ajuda"
                        continue

                    if self.menu_aberto == "Jogo":
                        if self.rect_novo.collidepoint(pos):
                            return "novo"
                        if self.rect_sair.collidepoint(pos):
                            return "sair"
                        self.menu_aberto = None
                        continue

                    if self.menu_aberto == "Ajuda":
                        if self.rect_sobre.collidepoint(pos):
                            self.modal = "sobre"
                        self.menu_aberto = None
                        continue

                    if self.rect_next_turn.collidepoint(pos):
                        self.proximo_turno()
                        continue

                    if self.rect_fundar.collidepoint(pos):
                        self.fundar_cidade()
                        continue

                    self.tratar_click_mapa(pos)

            self.mover_camera_teclado()

            self.tela.fill((22, 24, 27))
            self.desenhar_mapa()
            self.desenhar_barras_rolagem()
            self.desenhar_interface()

            mensagem = self.fonte_pequena.render(self.mensagem, True, (235, 235, 235))
            fundo = pygame.Rect(8, self.altura_tela - 38, min(mensagem.get_width() + 16, self.largura_tela - 30), 24)
            pygame.draw.rect(self.tela, (35, 38, 43), fundo, border_radius=4)
            self.tela.blit(mensagem, (fundo.x + 8, fundo.y + 4))

            if self.modal == "nome_cidade":
                self.desenhar_modal_nome()
            elif self.modal == "cidade":
                self.desenhar_modal_cidade()
            elif self.modal == "sobre":
                self.desenhar_modal_sobre()

            pygame.display.flip()
            relogio.tick(60)
