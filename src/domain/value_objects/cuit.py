from dataclasses import dataclass
import re


@dataclass(frozen=True)
class CUIT:
    value: str

    def __post_init__(self):
        clean = re.sub(r"[^\d]", "", self.value)
        if len(clean) != 11:
            raise ValueError("El CUIT debe contener 11 dígitos")
        object.__setattr__(self, "value", f"{clean[:2]}-{clean[2:10]}-{clean[10]}")
