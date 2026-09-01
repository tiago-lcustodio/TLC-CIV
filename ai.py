import random


class ControladorIA:
    """IA inicial propositalmente simples e isolada do motor."""
    def __init__(self, jogador_id):
        self.jogador_id = jogador_id

    def jogar_turno(self, jogo, jogador):
        for unidade in list(jogador.unidades):
            if unidade.esta_embarcada:
                continue
            if unidade.tipo == 'Colono' and unidade.movimento > 0 and not jogo.cidade_em(unidade.x, unidade.y):
                if len(jogador.cidades) == 0:
                    jogo.fundar_cidade_cpu(jogador, unidade)
                    continue
            if unidade.movimento > 0:
                jogo.mover_unidade_aleatoria(unidade)

        for cidade in jogador.cidades:
            if cidade.producao_nome is None:
                opcoes = ['Guerreiro', 'Trabalhador']
                if cidade.populacao >= 2:
                    opcoes.append('Colono')
                if jogo.cidade_tem_agua_rasa_adjacente(cidade):
                    opcoes.append('Galé')
                taxa = jogo.rendimentos_cidade(cidade)['producao']
                cidade.iniciar_producao('unidade', jogo.random.choice(opcoes), jogador, taxa, jogo)
