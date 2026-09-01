class MotorModificadores:
    """Aplica bônus/multas vindos de civilização, edifícios, entorno, tecnologias etc."""

    @staticmethod
    def aplicar(valor_base, atributo, modificadores):
        valor = float(valor_base)
        percentuais = 0.0
        for mod in modificadores:
            if mod.get('atributo') != atributo:
                continue
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
