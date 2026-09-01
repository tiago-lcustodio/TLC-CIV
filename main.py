import pygame
from menu import MenuConfiguracao
from game import Jogo

LARGURA_INICIAL = 1100
ALTURA_INICIAL = 720


def criar_janela():
    return pygame.display.set_mode((LARGURA_INICIAL, ALTURA_INICIAL), pygame.RESIZABLE)


def main():
    pygame.init()
    pygame.display.set_caption('TLC CIV')
    tela = criar_janela()
    while True:
        configuracao = MenuConfiguracao(tela).executar()
        if configuracao is None:
            break
        if configuracao.get('carregar_save'):
            try:
                jogo = Jogo.carregar_salvo(tela, configuracao['carregar_save'])
            except Exception as exc:
                print(f'Falha ao carregar save: {exc}')
                continue
        else:
            jogo = Jogo(tela, configuracao)
        resultado = jogo.executar()
        if resultado != 'novo':
            break
    pygame.quit()


if __name__ == '__main__':
    main()
