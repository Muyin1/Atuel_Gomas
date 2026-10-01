from enum import Enum


class ProductCategory(str, Enum):
    MANGUERAS_AUTOMOTOR = "Mangueras Automotor"
    MANGUERAS_INDUSTRIALES = "Mangueras Industriales e Hidráulicas"
    ABRAZADERAS_ACCESORIOS = "Abrazaderas y Acoples"
    ARTICULOS_PROTECCION_EPP = "Artículos de Protección y EPP"
    CORREAS_TRANSMISION = "Correas y Transmisión"
    PISOS_REVESTIMIENTOS = "Pisos y Revestimientos"
    FERRETERIA_INDUSTRIAL_AUTOPARTES = "Ferretería Industrial y Autopartes"
    ACCESORIOS_AUTOMOTOR = "Accesorios y Mantenimiento Automotor"

    # Aliases retrocompatibles para vistas y nombres legados
    PISOS_PLANCHAS = "Pisos y Revestimientos"
    BURLETES_PERFILES = "Burletes y Perfiles de Goma"
    FUELLES_SUSPENSION = "Fuelles Semieje y Dirección"
