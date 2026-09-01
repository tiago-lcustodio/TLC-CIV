class CalendarioJogo:
    """Calendário provisório do TLC CIV.

    4000 a.C. até 1000 a.C.: 50 anos/turno
    1000 a.C. até 1000 d.C.: 25 anos/turno
    1000 d.C. até 1900 d.C.: 10 anos/turno
    após 1900: 1 ano/turno
    """

    def __init__(self):
        self.ano = -4000

    def avancar(self):
        if self.ano < -1000:
            self.ano = min(-1000, self.ano + 50)
        elif self.ano < 1000:
            if self.ano == -25:
                self.ano = 1
            elif self.ano == 1:
                self.ano = 25
            else:
                self.ano = min(1000, self.ano + 25)
        elif self.ano < 1900:
            self.ano = min(1900, self.ano + 10)
        else:
            self.ano += 1
        return self.ano

    @property
    def texto(self):
        if self.ano < 0:
            return f'{abs(self.ano)} a.C.'
        return f'{self.ano} d.C.'
