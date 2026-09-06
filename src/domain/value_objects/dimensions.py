from dataclasses import dataclass


@dataclass(frozen=True)
class Dimensions:
    inner_diameter_mm: float | None = None
    outer_diameter_mm: float | None = None
    length_mm: float | None = None
    thickness_mm: float | None = None

    def summary(self) -> str:
        parts = []
        if self.inner_diameter_mm:
            parts.append(f"Ø Int: {self.inner_diameter_mm}mm")
        if self.outer_diameter_mm:
            parts.append(f"Ø Ext: {self.outer_diameter_mm}mm")
        if self.thickness_mm:
            parts.append(f"Espesor: {self.thickness_mm}mm")
        if self.length_mm:
            parts.append(f"Largo: {self.length_mm}mm")
        return " | ".join(parts) if parts else "Medidas estándar / s/e"
