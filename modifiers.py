class MotorModificadores:
    """Aplica bônus/multas com escopo, duração e condição opcionais.

    Campos reconhecidos num modificador:
      atributo, operacao, valor, escopo, duracao, condicao, origem.
    Ausência de escopo significa compatibilidade universal com o sistema antigo.
    ``condicao`` pode ser bool ou callable(contexto)->bool.
    """

    @staticmethod
    def _ativo(mod, escopo=None, contexto=None):
        escopo_mod = mod.get('escopo')
        permitidos={None,'global',escopo}
        if escopo in ('cidade','unidade','tile'):
            permitidos.add('jogador')
        if escopo and escopo_mod not in permitidos:
            return False
        duracao = mod.get('duracao')
        if duracao is not None and int(duracao) <= 0:
            return False
        condicao = mod.get('condicao', True)
        if callable(condicao):
            try:
                return bool(condicao(contexto or {}))
            except Exception:
                return False
        return bool(condicao)

    @classmethod
    def filtrar(cls, modificadores, atributo=None, escopo=None, contexto=None):
        saida = []
        for mod in modificadores:
            if atributo is not None and mod.get('atributo') != atributo:
                continue
            if cls._ativo(mod, escopo, contexto):
                saida.append(mod)
        return saida

    @classmethod
    def aplicar(cls, valor_base, atributo, modificadores, escopo=None, contexto=None):
        valor = float(valor_base)
        percentuais = 0.0
        for mod in cls.filtrar(modificadores, atributo, escopo, contexto):
            op = mod.get('operacao', 'somar')
            quant = mod.get('valor', 0)
            if op == 'somar':
                valor += quant
            elif op == 'subtrair':
                valor -= quant
            elif op == 'percentual':
                percentuais += quant
            elif op == 'multiplicar':
                valor *= quant
        if percentuais:
            valor *= 1 + percentuais / 100.0
        return max(0, int(round(valor)))
