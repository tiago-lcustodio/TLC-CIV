import pygame

from menu import MenuConfiguracao
from game import Jogo


LARGURA_INICIAL = 1100
ALTURA_INICIAL = 720
FPS = 60


def criar_janela():
    """Cria uma janela restaurada e redimensionável.

    O usuário pode maximizar normalmente pelo botão do sistema operacional.
    """
    return pygame.display.set_mode(
        (LARGURA_INICIAL, ALTURA_INICIAL),
        pygame.RESIZABLE,
    )


def main():
    pygame.init()
    pygame.display.set_caption("TLC CIV")

    tela = criar_janela()

    executando = True

    while executando:
        menu = MenuConfiguracao(tela)
        configuracao = menu.executar()

        if configuracao is None:
            break

        jogo = Jogo(tela, configuracao)
        resultado = jogo.executar()

        if resultado == "novo":
            continue

        executando = False

    pygame.quit()


if __name__ == "__main__":
    main()
