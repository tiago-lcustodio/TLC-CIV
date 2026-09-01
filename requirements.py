from data import TECNOLOGIAS, POLITICAS, CIVILIZACOES, ERAS


class MotorRequisitos:
    """Verificador genérico de requisitos/desbloqueios.

    O conteúdo pode declarar uma lista ``requisitos``. Tipos já reconhecidos:
    tecnologia, era, civilizacao, populacao, construcao, terreno, costeira e
    recurso_global. Novos tipos podem ser acrescentados sem alterar as entidades.
    """

    @staticmethod
    def _requisitos_definicao(definicao):
        requisitos = list(definicao.get('requisitos', []))
        # Compatibilidade com o campo antigo ``tecnologia``.
        tecnologia = definicao.get('tecnologia')
        if tecnologia and not any(r.get('tipo') == 'tecnologia' and r.get('id') == tecnologia for r in requisitos):
            requisitos.append({'tipo': 'tecnologia', 'id': tecnologia})
        return requisitos

    @classmethod
    def verificar(cls, definicao, jogador, jogo=None, cidade=None, tile=None):
        for requisito in cls._requisitos_definicao(definicao):
            tipo = requisito.get('tipo')
            if tipo == 'tecnologia':
                if not jogador.possui_tecnologia(requisito.get('id')):
                    return False, f'Requer tecnologia: {requisito.get("id")}.'
            elif tipo == 'era':
                era = requisito.get('id') or requisito.get('valor')
                try:
                    if ERAS.index(jogador.era) < ERAS.index(era):
                        return False, f'Requer Era {era}.'
                except (ValueError, TypeError):
                    return False, f'Era requerida inválida: {era}.'
            elif tipo == 'civilizacao':
                civ = requisito.get('id') or requisito.get('valor')
                if jogador.civilizacao != civ:
                    return False, f'Exclusivo da civilização {civ}.'
            elif tipo == 'populacao':
                minimo = int(requisito.get('minimo', requisito.get('valor', 0)))
                if cidade is None or cidade.populacao < minimo:
                    return False, f'Requer população {minimo}.'
            elif tipo == 'construcao':
                nome = requisito.get('id') or requisito.get('valor')
                if cidade is None or nome not in cidade.construcoes:
                    return False, f'Requer construção: {nome}.'
            elif tipo == 'terreno':
                permitido = requisito.get('valores', [requisito.get('valor')])
                if jogo is None or tile is None or jogo.mundo.terreno(*tile) not in permitido:
                    return False, 'Terreno incompatível.'
            elif tipo == 'costeira':
                if not cidade or not jogo or not jogo.cidade_tem_agua_rasa_adjacente(cidade):
                    return False, 'Requer cidade costeira com Água Rasa adjacente.'
            elif tipo == 'recurso_global':
                recurso = requisito.get('recurso')
                minimo = requisito.get('minimo', 0)
                if getattr(jogador, recurso, 0) < minimo:
                    return False, f'Requer {minimo} de {recurso}.'
        return True, ''

    @staticmethod
    def desbloqueios_do_jogador(jogador):
        """Retorna IDs explicitamente desbloqueados por civ/tecnologias/políticas."""
        resultado = {'unidade': set(), 'construcao': set(), 'melhoria': set(), 'politica': set(), 'outro': set()}
        fontes = [CIVILIZACOES.get(jogador.civilizacao, {})]
        fontes.extend(TECNOLOGIAS.get(t, {}) for t in jogador.tecnologias)
        fontes.extend(POLITICAS.get(p, {}) for p in jogador.politicas)
        for fonte in fontes:
            for desbloqueio in fonte.get('desbloqueios', []):
                tipo = desbloqueio.get('tipo', 'outro')
                resultado.setdefault(tipo, set()).add(desbloqueio.get('id'))
            # Compatibilidade com listas antigas.
            for nome in fonte.get('desbloqueia_unidades', []):
                resultado['unidade'].add(nome)
            for nome in fonte.get('desbloqueia_construcoes', []):
                resultado['construcao'].add(nome)
        return resultado
