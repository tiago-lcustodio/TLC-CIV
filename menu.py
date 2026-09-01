import pygame
from data import CORES_JOGADOR, CIVILIZACOES, DIFICULDADES


class MenuConfiguracao:
    def __init__(self, tela):
        self.tela = tela
        self.fonte_titulo = pygame.font.SysFont('arial', 38, bold=True)
        self.fonte = pygame.font.SysFont('arial', 20)
        self.fonte_pequena = pygame.font.SysFont('arial', 16)
        self.percentuais = {'Grama': 40, 'Água': 30, 'Montanha': 10, 'Deserto': 10, 'Neve': 10}
        self.ordem_terrenos = list(self.percentuais)
        self.tamanhos = [36, 72, 144, 288]
        self.indice_tamanho = 0
        self.cores = list(CORES_JOGADOR); self.indice_cor = 0
        self.civilizacoes = list(CIVILIZACOES); self.indice_civ = 0
        self.dificuldades = list(DIFICULDADES); self.indice_dif = 0
        self.numero_cpus = 3

    def ajustar_percentual(self, terreno, delta):
        atual = self.percentuais[terreno]
        novo = max(0, min(100, atual + delta))
        dif = novo - atual
        if dif == 0: return
        outros = [t for t in self.ordem_terrenos if t != terreno]
        if dif > 0:
            restante = dif
            while restante > 0:
                alterou = False
                for outro in outros:
                    if restante <= 0: break
                    if self.percentuais[outro] > 0:
                        self.percentuais[outro] -= 1; restante -= 1; alterou = True
                if not alterou: return
            self.percentuais[terreno] = novo
        else:
            qtd = -dif; self.percentuais[terreno] = novo; i = 0
            while qtd > 0:
                outro = outros[i % len(outros)]
                if self.percentuais[outro] < 100:
                    self.percentuais[outro] += 1; qtd -= 1
                i += 1

    def botao(self, rect, texto, ativo=True, cor=None):
        cor = cor or ((72,77,86) if ativo else (55,58,63))
        pygame.draw.rect(self.tela, cor, rect, border_radius=5)
        pygame.draw.rect(self.tela, (25,25,25), rect, 1, border_radius=5)
        surf = self.fonte_pequena.render(texto, True, (245,245,245) if ativo else (135,135,135))
        self.tela.blit(surf, surf.get_rect(center=rect.center))

    def executar(self):
        relogio = pygame.time.Clock()
        while True:
            largura, altura = self.tela.get_size()
            self.tela.fill((34,38,45))
            titulo = self.fonte_titulo.render('TLC CIV 0.12', True, (240,240,240))
            self.tela.blit(titulo, titulo.get_rect(center=(largura//2,42)))
            painel = pygame.Rect(max(20,largura//2-370),78,min(740,largura-40),max(560,altura-120))
            pygame.draw.rect(self.tela,(46,51,59),painel,border_radius=10)
            pygame.draw.rect(self.tela,(82,87,96),painel,1,border_radius=10)
            x= painel.x+34; y=painel.y+22; botoes={}
            self.tela.blit(self.fonte.render('Configuração da civilização',True,(245,235,195)),(x,y)); y+=34
            linhas=[
                ('Civilização',self.civilizacoes[self.indice_civ],'civ'),
                ('Cor do jogador',self.cores[self.indice_cor],'cor'),
                ('Adversários CPU',str(self.numero_cpus),'cpu'),
                ('Dificuldade',self.dificuldades[self.indice_dif],'dif'),
                ('Tamanho do mapa',f'{self.tamanhos[self.indice_tamanho]} x {self.tamanhos[self.indice_tamanho]}','tam'),
            ]
            for rotulo,valor,chave in linhas:
                self.tela.blit(self.fonte_pequena.render(f'{rotulo}: {valor}',True,(230,230,230)),(x,y+8))
                menos=pygame.Rect(painel.right-135,y,42,34); mais=pygame.Rect(painel.right-82,y,42,34)
                self.botao(menos,'<'); self.botao(mais,'>'); botoes[chave]=(menos,mais)
                if chave=='cor': pygame.draw.rect(self.tela,CORES_JOGADOR[valor],(x+245,y+8,46,20),border_radius=3)
                y+=42
            y+=8; self.tela.blit(self.fonte.render('Distribuição do mundo',True,(245,235,195)),(x,y)); y+=32
            ter_botoes={}
            for terreno in self.ordem_terrenos:
                self.tela.blit(self.fonte_pequena.render(f'{terreno}: {self.percentuais[terreno]}%',True,(230,230,230)),(x,y+7))
                menos=pygame.Rect(painel.right-135,y,42,32); mais=pygame.Rect(painel.right-82,y,42,32)
                self.botao(menos,'-'); self.botao(mais,'+'); ter_botoes[terreno]=(menos,mais); y+=36
            iniciar=pygame.Rect(painel.centerx-125,painel.bottom-58,250,42); self.botao(iniciar,'INICIAR JOGO',True,(49,112,68))
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type==pygame.QUIT: return None
                if e.type==pygame.VIDEORESIZE: self.tela=pygame.display.set_mode(e.size,pygame.RESIZABLE)
                if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                    pos=e.pos
                    for terreno,(menos,mais) in ter_botoes.items():
                        if menos.collidepoint(pos): self.ajustar_percentual(terreno,-1)
                        elif mais.collidepoint(pos): self.ajustar_percentual(terreno,1)
                    for chave,(menos,mais) in botoes.items():
                        d=-1 if menos.collidepoint(pos) else (1 if mais.collidepoint(pos) else 0)
                        if not d: continue
                        if chave=='civ': self.indice_civ=(self.indice_civ+d)%len(self.civilizacoes)
                        elif chave=='cor': self.indice_cor=(self.indice_cor+d)%len(self.cores)
                        elif chave=='cpu': self.numero_cpus=max(0,min(3,self.numero_cpus+d))
                        elif chave=='dif': self.indice_dif=(self.indice_dif+d)%len(self.dificuldades)
                        elif chave=='tam': self.indice_tamanho=(self.indice_tamanho+d)%len(self.tamanhos)
                    if iniciar.collidepoint(pos):
                        tam=self.tamanhos[self.indice_tamanho]; nome_cor=self.cores[self.indice_cor]
                        return {'percentuais':self.percentuais.copy(),'largura_mapa':tam,'altura_mapa':tam,
                                'civilizacao':self.civilizacoes[self.indice_civ],'nome_cor_jogador':nome_cor,
                                'cor_jogador':CORES_JOGADOR[nome_cor],'numero_cpus':self.numero_cpus,
                                'dificuldade':self.dificuldades[self.indice_dif]}
            relogio.tick(60)
