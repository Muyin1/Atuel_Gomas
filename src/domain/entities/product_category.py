from enum import Enum


class ProductCategory(str, Enum):
    MANGUERAS_AUTOMOTOR = "Mangueras de Radiador y Calefacción"
    MANGUERAS_INDUSTRIALES = "Mangueras Industriales e Hidráulicas"
    BURLETES_PERFILES = "Burletes y Perfiles de Goma"
    FUELLES_SUSPENSION = "Fuelles Semieje y Dirección"
    PISOS_PLANCHAS = "Pisos de Goma y Planchas Técnicas"
    ABRAZADERAS_ACCESORIOS = "Abrazaderas y Acoples"
