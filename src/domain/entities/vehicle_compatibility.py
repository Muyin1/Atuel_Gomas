from dataclasses import dataclass


@dataclass
class VehicleCompatibility:
    brand: str            # Ej: Renault, Ford, Chevrolet, Fiat
    model: str            # Ej: Kangoo, Hilux, Gol Trend
    engine: str           # Ej: 1.6 16v K4M, 2.8 TDI
    years: str            # Ej: 2008-2018
