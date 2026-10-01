from enum import Enum


class BusinessLine(str, Enum):
    AUTOPARTES = "AUTOPARTES"
    FERRETERIA = "FERRETERIA"
    AMBOS = "AMBOS"
