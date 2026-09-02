from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


ON_TURN_START = 'turn_start'
ON_TURN_END = 'turn_end'
ON_CITY_FOUNDED = 'city_founded'
ON_CITY_GROWTH = 'city_growth'
ON_BORDER_EXPANDED = 'border_expanded'
ON_UNIT_CREATED = 'unit_created'
ON_BUILDING_COMPLETED = 'building_completed'
ON_TECH_RESEARCHED = 'tech_researched'
ON_COMBAT_END = 'combat_end'
ON_RELIGION_FOUNDED = 'religion_founded'
ON_CITY_REVOLT = 'city_revolt'
ON_CITY_SECESSION = 'city_secession'
ON_FIRST_CONTACT = 'first_contact'


@dataclass
class EventoJogo:
    tipo: str
    turno: int
    dados: Dict[str, Any] = field(default_factory=dict)


class GerenciadorEventos:
    """Barramento leve de eventos do motor."""
    def __init__(self, limite_historico=200):
        self._ouvintes: Dict[str, List[Callable[[EventoJogo], None]]] = {}
        self.historico: List[EventoJogo] = []
        self.limite_historico = limite_historico

    def registrar(self, tipo: str, callback: Callable[[EventoJogo], None]):
        self._ouvintes.setdefault(tipo, []).append(callback)

    def remover(self, tipo: str, callback):
        if tipo in self._ouvintes and callback in self._ouvintes[tipo]:
            self._ouvintes[tipo].remove(callback)

    def emitir(self, tipo: str, turno: int, **dados):
        evento = EventoJogo(tipo=tipo, turno=turno, dados=dados)
        self.historico.append(evento)
        if len(self.historico) > self.limite_historico:
            self.historico = self.historico[-self.limite_historico:]
        for callback in list(self._ouvintes.get(tipo, [])):
            callback(evento)
        for callback in list(self._ouvintes.get('*', [])):
            callback(evento)
        return evento
