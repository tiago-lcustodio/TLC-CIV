from world import VIZINHOS_8


class ControladorIA:
    """IA civilizacional simples e isolada do motor.

    A partir da v0.21, o turno também pode ser consumido incrementalmente pelo
    Turn Manager. Cada ``yield`` devolve o controle ao loop do Pygame, evitando
    que dezenas de unidades/cidades sejam resolvidas dentro de um único frame.
    """
    def __init__(self, jogador_id):
        self.jogador_id = jogador_id

    def iterar_turno(self, jogo, jogador):
        unidades = list(jogador.unidades)
        total_unidades = len(unidades)
        for indice, unidade in enumerate(unidades, 1):
            if unidade.esta_embarcada:
                yield f'unidade {indice}/{total_unidades}: embarcada'
                continue
            if unidade.tipo == 'Colono' and unidade.movimento > 0 and not jogo.cidade_em(unidade.x, unidade.y):
                if len(jogador.cidades) == 0:
                    jogo.fundar_cidade_cpu(jogador, unidade)
                    yield f'unidade {indice}/{total_unidades}: fundou cidade'
                    continue
            if unidade.movimento > 0:
                jogo.mover_unidade_aleatoria(unidade)
            yield f'unidade {indice}/{total_unidades}: {unidade.tipo}'

        cidades = list(jogador.cidades)
        total_cidades = len(cidades)
        for indice, cidade in enumerate(cidades, 1):
            if cidade.producao_nome is None and not cidade.em_revolta:
                opcoes = ['Guerreiro', 'Trabalhador']
                if cidade.populacao >= 2:
                    opcoes.append('Colono')
                if jogo.cidade_tem_agua_rasa_adjacente(cidade):
                    opcoes.append('Galé')
                taxa = jogo.rendimentos_cidade(cidade)['producao']
                cidade.iniciar_producao('unidade', jogo.random.choice(opcoes), jogador, taxa, jogo)
            yield f'cidade {indice}/{total_cidades}: {cidade.nome}'

    def jogar_turno(self, jogo, jogador):
        # Compatibilidade com chamadas antigas/testes: consome o iterador inteiro.
        for _ in self.iterar_turno(jogo, jogador):
            pass


class ControladorBarbaro:
    """IA agressiva leve para bárbaros.

    Antes, cada Guerreiro calculava até oito caminhos completos por turno. Como
    os Guerreiros iniciais têm movimento curto, a v0.21 usa uma aproximação
    local: escolhe o vizinho passável que mais reduz a distância até o alvo.
    Isso elimina a principal fonte de microtravamentos sem mudar a intenção da IA.
    """
    def __init__(self, jogador_id):
        self.jogador_id = jogador_id

    def _alvos(self, jogo):
        alvos = []
        humano = jogo.jogador_humano
        alvos.extend((c.x, c.y) for c in humano.cidades)
        alvos.extend((u.x, u.y) for u in humano.unidades if not u.esta_embarcada)
        if not alvos:
            for outro in jogo.jogadores:
                if outro.tipo == 'barbaro':
                    continue
                alvos.extend((c.x, c.y) for c in outro.cidades)
                alvos.extend((u.x, u.y) for u in outro.unidades if not u.esta_embarcada)
        return alvos

    def _mover_em_direcao(self, jogo, unidade, alvo):
        distancia_atual = abs(alvo[0] - unidade.x) + abs(alvo[1] - unidade.y)
        candidatos = []
        for dx, dy in VIZINHOS_8:
            p = (unidade.x + dx, unidade.y + dy)
            if not jogo.mundo.dentro(*p) or not jogo.mundo.passavel_para(*p, unidade.dominio):
                continue
            ocupante = jogo.unidade_em(*p)
            if ocupante is not None and ocupante is not unidade:
                continue
            # Não entra diretamente em cidade/unidade-alvo antes de o combate existir.
            if p == alvo:
                continue
            nova_dist = abs(alvo[0] - p[0]) + abs(alvo[1] - p[1])
            custo = jogo.mundo.custo_movimento((unidade.x, unidade.y), p, unidade.dominio)
            candidatos.append((nova_dist, custo, jogo.random.random(), p))

        if not candidatos:
            jogo.mover_unidade_aleatoria(unidade)
            return

        candidatos.sort(key=lambda item: (item[0], item[1], item[2]))
        melhor = candidatos[0]
        # Se nenhuma opção melhora a distância, ainda escolhe a melhor disponível;
        # isso ajuda a contornar pequenas barreiras sem pathfinding global.
        destino = melhor[3]
        jogo.ordenar_movimento_unidade(unidade, destino)

    def iterar_turno(self, jogo, jogador):
        alvos = self._alvos(jogo)
        unidades = list(jogador.unidades)
        total = len(unidades)
        if not alvos:
            if total == 0:
                yield 'sem unidades ativas'
            return

        for indice, unidade in enumerate(unidades, 1):
            if unidade.movimento <= 0 or unidade.esta_embarcada:
                yield f'unidade {indice}/{total}: aguardando'
                continue
            alvo = min(alvos, key=lambda p: abs(p[0]-unidade.x) + abs(p[1]-unidade.y))
            self._mover_em_direcao(jogo, unidade, alvo)
            yield f'unidade {indice}/{total}: {unidade.tipo}'

    def jogar_turno(self, jogo, jogador):
        for _ in self.iterar_turno(jogo, jogador):
            pass
