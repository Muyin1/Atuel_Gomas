from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    amount: float
    currency: str = "ARS"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("El monto no puede ser negativo")

    def format_ars(self) -> str:
        return f"${self.amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
