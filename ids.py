class GeradorIDs:
    """Gerador simples de IDs estáveis e legíveis para saves e referências."""

    def __init__(self):
        self.contadores = {'P': 0, 'C': 0, 'U': 0}

    def novo(self, prefixo):
        self.contadores[prefixo] = self.contadores.get(prefixo, 0) + 1
        return f'{prefixo}{self.contadores[prefixo]:06d}'

    def observar(self, entidade_id):
        if not entidade_id or len(entidade_id) < 2:
            return
        prefixo = entidade_id[0]
        try:
            numero = int(entidade_id[1:])
        except ValueError:
            return
        self.contadores[prefixo] = max(self.contadores.get(prefixo, 0), numero)

    def exportar(self):
        return dict(self.contadores)

    def importar(self, dados):
        for prefixo, valor in (dados or {}).items():
            self.contadores[prefixo] = max(self.contadores.get(prefixo, 0), int(valor))
