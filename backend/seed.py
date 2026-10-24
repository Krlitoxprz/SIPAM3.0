"""
SIPAM-USCO -- Seeder v3 basado en Extramuros ING-2026-12-marzo
Ejecutar: venv/Scripts/python seed_new.py
"""
import sys, os, random
from datetime import datetime, date, timedelta
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import SessionLocal, init_db, engine
from app.models.user import User, RolEnum
from app.models.convocatoria import Convocatoria, Asignatura, AsignaturaEstudiante, EstadoConvocatoriaEnum, TipoMonitoriaEnum
from app.models.postulacion import Postulacion, EstadoPostulacionEnum
from app.models.practica import TarifaViatico
from app.models.presupuesto import Presupuesto, ConfiguracionCalendario
from app.core.security import get_password_hash
from sqlalchemy import text

random.seed(42)
PASSWORD = "sipam2025"
PERIODO = "2026-1"
FACULTAD = "Facultad de Ingeniería"

# ── Jefes de programa ─────────────────────────────────────────────────────────
JEFES_DATA = [
    ("JEFE001","Carlos Hernando","Ospina Toro",        "carlos.ospina@usco.edu.co",   "76001001","Ingeniería Agroindustrial","Neiva"),
    ("JEFE002","Luis Alfredo",   "Rubio Duarte",       "luis.rubio@usco.edu.co",      "76001002","Ingeniería Agrícola",      "Neiva"),
    ("JEFE003","Patricia",       "Rodríguez López",    "patricia.rodriguez@usco.edu.co","76001003","Ingeniería Civil",        "Neiva"),
    ("JEFE004","Germán",         "Acosta Ortiz",       "german.acosta@usco.edu.co",   "76001004","Ingeniería de Petróleos",  "Neiva"),
    ("JEFE005","Andrés",         "Morales Rivera",     "andres.morales@usco.edu.co",  "76001005","Ingeniería de Software",   "Neiva"),
]

# ── Profesores (cod,nom,ape,email,ced,prog,sede,tipo_docente,modalidad) ───────
PROFESORES_DATA = [
    # Agroindustrial — planta Neiva
    ("PROF001","Andrea Elinor",  "Lara Sánchez",       "andrea.lara@usco.edu.co",     "87650001","Ingeniería Agroindustrial","Neiva",   "planta",   "TCP"),
    ("PROF002","Andrés Felipe",  "Bahamon Monje",      "andres.bahamon@usco.edu.co",  "87650002","Ingeniería Agroindustrial","Neiva",   "planta",   "TCP"),
    ("PROF003","Angélica María", "Otero Paternina",    "angelica.otero@usco.edu.co",  "87650003","Ingeniería Agroindustrial","Neiva",   "ocasional","TCO"),
    ("PROF004","Beatriz Elena",  "Zapata Berruecos",   "beatriz.zapata@usco.edu.co",  "87650004","Ingeniería Agroindustrial","Neiva",   "planta",   "TCP"),
    ("PROF005","Eduardo",        "Pastrana Bonilla",   "eduardo.pastrana@usco.edu.co","87650005","Ingeniería Agroindustrial","Neiva",   "catedra",  "CAT"),
    ("PROF006","Jaime Daniel",   "Bustos Vanegas",     "jaime.bustos@usco.edu.co",    "87650006","Ingeniería Agroindustrial","Neiva",   "planta",   "TCP"),
    ("PROF007","Laura Nathalia", "Ochoa Ospitia",      "laura.ochoa@usco.edu.co",     "87650007","Ingeniería Agroindustrial","Neiva",   "planta",   "MTP"),
    ("PROF008","Natalia",        "Puentes",            "natalia.puentes@usco.edu.co", "87650008","Ingeniería Agroindustrial","Neiva",   "ocasional","TCO"),
    # Agrícola — mix de sedes
    ("PROF009","Arbey",          "Sánchez Rodríguez",  "arbey.sanchez@usco.edu.co",   "87650009","Ingeniería Agrícola","La Plata", "planta",   "TCP"),
    ("PROF010","Carlos Alberto", "Paloma",             "carlos.paloma@usco.edu.co",   "87650010","Ingeniería Agrícola","La Plata", "catedra",  "CAT"),
    ("PROF011","Damaris",        "Perdomo Medina",     "damaris.perdomo@usco.edu.co", "87650011","Ingeniería Agrícola","Pitalito", "planta",   "TCP"),
    ("PROF012","Daniel Felipe",  "Fernández Reyes",    "daniel.fernandez@usco.edu.co","87650012","Ingeniería Agrícola","Garzón",   "catedra",  "CAT"),
    ("PROF013","Dennis Milena",  "Villamil Ospina",    "dennis.villamil@usco.edu.co", "87650013","Ingeniería Agrícola","La Plata", "planta",   "MTP"),
    ("PROF014","Eddinson",       "Ortega Martínez",    "eddinson.ortega@usco.edu.co", "87650014","Ingeniería Agrícola","La Plata", "planta",   "TCP"),
    ("PROF015","Edinson",        "Mujica Rodríguez",   "edinson.mujica@usco.edu.co",  "87650015","Ingeniería Agrícola","Pitalito", "ocasional","TCO"),
    ("PROF016","Giovanni Andrés","Vargas Galván",      "giovanni.vargas@usco.edu.co", "87650016","Ingeniería Agrícola","Garzón",   "planta",   "TCP"),
    ("PROF017","Héctor Jair",    "Beltrán Vargas",     "hector.beltran@usco.edu.co",  "87650017","Ingeniería Agrícola","Garzón",   "planta",   "TCP"),
    ("PROF018","Jairo",          "Murcia Leal",        "jairo.murcia@usco.edu.co",    "87650018","Ingeniería Agrícola","Garzón",   "planta",   "MTP"),
    ("PROF019","Javier Eduardo", "Bonilla Perdomo",    "javier.bonilla@usco.edu.co",  "87650019","Ingeniería Agrícola","La Plata", "catedra",  "CAT"),
    ("PROF020","Jhon Jairo",     "Arévalo Hernández",  "jhon.arevalo@usco.edu.co",    "87650020","Ingeniería Agrícola","Neiva",    "planta",   "TCP"),
    ("PROF021","Jhon Jairo",     "Beltrán Díaz",       "jhon.beltran@usco.edu.co",    "87650021","Ingeniería Agrícola","Pitalito", "planta",   "TCP"),
    ("PROF022","Jhon Jairo",     "Vargas Hoyos",       "jhon.vargas@usco.edu.co",     "87650022","Ingeniería Agrícola","Garzón",   "ocasional","MTO"),
    ("PROF023","Johnny Mauricio","Gutiérrez Marroquín","johnny.gutierrez@usco.edu.co","87650023","Ingeniería Agrícola","Neiva",    "planta",   "TCP"),
    ("PROF024","José Daniel",    "Cardona Cárdenas",   "jose.cardona@usco.edu.co",    "87650024","Ingeniería Agrícola","Neiva",    "planta",   "TCP"),
    ("PROF025","Luisa Marcela",  "Cerquera Barrera",   "luisa.cerquera@usco.edu.co",  "87650025","Ingeniería Agrícola","Pitalito", "planta",   "MTP"),
    ("PROF026","Martha Lucía",   "Peña Quimbaya",      "martha.pena@usco.edu.co",     "87650026","Ingeniería Agrícola","Garzón",   "planta",   "TCP"),
    ("PROF027","Miguel Ángel",   "Díaz Herrera",       "miguel.diaz@usco.edu.co",     "87650027","Ingeniería Agrícola","Neiva",    "catedra",  "CAT"),
    ("PROF028","Miyer Javier",   "Valdés Ortiz",       "miyer.valdes@usco.edu.co",    "87650028","Ingeniería Agrícola","Garzón",   "planta",   "TCP"),
    ("PROF029","Nadia Brigitte", "Sanabria Méndez",    "nadia.sanabria@usco.edu.co",  "87650029","Ingeniería Agrícola","Neiva",    "planta",   "TCP"),
    ("PROF030","Oscar Eduardo",  "Gutiérrez Olaya",    "oscar.gutierrez@usco.edu.co", "87650030","Ingeniería Agrícola","La Plata", "planta",   "TCP"),
    ("PROF031","Oscar Fabián",   "Losada Gómez",       "oscar.losada@usco.edu.co",    "87650031","Ingeniería Agrícola","Garzón",   "catedra",  "CAT"),
    ("PROF032","Oscar Mauricio", "Barrera Bermeo",     "oscar.barrera@usco.edu.co",   "87650032","Ingeniería Agrícola","Garzón",   "planta",   "TCP"),
    ("PROF033","Silvia Cristina","Carrera Quintana",   "silvia.carrera@usco.edu.co",  "87650033","Ingeniería Agrícola","Garzón",   "planta",   "MTP"),
    ("PROF034","Victor Manuel",  "Martínez Castro",    "victor.martinez@usco.edu.co", "87650034","Ingeniería Agrícola","Pitalito", "ocasional","TCO"),
    ("PROF035","Wilmer Licerio", "Ladino Garzón",      "wilmer.ladino@usco.edu.co",   "87650035","Ingeniería Agrícola","Neiva",    "planta",   "TCP"),
    ("PROF036","Wilson Javier",  "Erazo Espinosa",     "wilson.erazo@usco.edu.co",    "87650036","Ingeniería Agrícola","Neiva",    "planta",   "TCP"),
    ("PROF037","Yanet Caridad",  "Apin Campos",        "yanet.apin@usco.edu.co",      "87650037","Ingeniería Agrícola","La Plata", "planta",   "TCP"),
    ("PROF038","Yaneth Liliana", "Ruíz Osorio",        "yaneth.ruiz@usco.edu.co",     "87650038","Ingeniería Agrícola","La Plata", "catedra",  "CAT"),
    ("PROF039","Yony Arley",     "Chavez Parra",       "yony.chavez@usco.edu.co",     "87650039","Ingeniería Agrícola","Pitalito", "planta",   "MTP"),
    # Civil
    ("PROF040","Isauro",         "Trujillo Vásquez",   "isauro.trujillo@usco.edu.co", "87650040","Ingeniería Civil","Neiva",       "planta",   "TCP"),
    ("PROF041","Jaime",          "Izquierdo Bautista", "jaime.izquierdo@usco.edu.co", "87650041","Ingeniería Civil","Neiva",       "planta",   "TCP"),
    ("PROF042","Mario German",   "Trujillo Vela",      "mario.trujillo@usco.edu.co",  "87650042","Ingeniería Civil","Neiva",       "ocasional","TCO"),
    # Petróleos
    ("PROF043","Ingrid Natalia", "Muñoz Quijano",      "ingrid.munoz@usco.edu.co",    "87650043","Ingeniería de Petróleos","Neiva",  "planta",   "TCP"),
    ("PROF044","Jorge Orlando",  "Mayorga Bautista",   "jorge.mayorga@usco.edu.co",   "87650044","Ingeniería de Petróleos","Neiva",  "planta",   "TCP"),
    ("PROF045","Roberto",        "Vargas Cuervo",      "roberto.vargas@usco.edu.co",  "87650045","Ingeniería de Petróleos","Neiva",  "planta",   "MTP"),
    # Software
    ("PROF046","Jorge Eliecer",  "Martínez Gaitán",    "jorge.martinez@usco.edu.co",  "87650046","Ingeniería de Software","Neiva",   "planta",   "TCP"),
    ("PROF047","Eurípides",      "Triana Tucuma",      "euripides.triana@usco.edu.co","87650047","Ingeniería de Software","Neiva",   "ocasional","TCO"),
]

# ── Asignaturas (cod,nombre,cred,sem,prog,prof,caracter,caracteristica) ────────
ASIGNATURAS_DATA = [
    # ── Ingeniería Agroindustrial (índices 0-10) ─────────────────────────────
    ("IAGR-101","Almacenamiento de productos biológicos",                          3,4,"Ingeniería Agroindustrial","PROF006","teorico_practico","especifico"),
    ("IAGR-102","Control de calidad instrumental en alimentos",                    4,4,"Ingeniería Agroindustrial","PROF002","teorico_practico","especifico"),
    ("IAGR-103","Diseño de plantas agroindustriales",                              3,5,"Ingeniería Agroindustrial","PROF008","teorico_practico","especifico"),
    ("IAGR-104","Enología",                                                        2,6,"Ingeniería Agroindustrial","PROF005","teorico_practico","componente_flexible"),
    ("IAGR-105","Industrialización de productos no alimentarios",                  3,5,"Ingeniería Agroindustrial","PROF007","teorico_practico","especifico"),
    ("IAGR-106","Procesamiento transformación e inocuidad de productos piscícolas",3,4,"Ingeniería Agroindustrial","PROF003","teorico_practico","especifico"),
    ("IAGR-107","Procesos industriales cárnicos",                                  3,4,"Ingeniería Agroindustrial","PROF001","teorico_practico","especifico"),
    ("IAGR-108","Procesos industriales granos y semillas",                         3,4,"Ingeniería Agroindustrial","PROF006","teorico_practico","especifico"),
    ("IAGR-109","Producción pecuaria y acuícola",                                  3,3,"Ingeniería Agroindustrial","PROF004","teorico_practico","especifico"),
    ("IAGR-110","Sistemas productivos agrícolas",                                  3,3,"Ingeniería Agroindustrial","PROF002","teorico",         "especifico"),
    ("IAGR-111","Tecnología de café y cacao",                                      3,5,"Ingeniería Agroindustrial","PROF006","teorico_practico","especifico"),
    # ── Ingeniería Agrícola (índices 11-39) ──────────────────────────────────
    ("IAGC-101","Calidad de aguas",                                  3,5,"Ingeniería Agrícola","PROF037","teorico_practico","especifico"),
    ("IAGC-102","Construcciones rurales",                            3,4,"Ingeniería Agrícola","PROF036","teorico_practico","especifico"),
    ("IAGC-103","Desarrollo sostenible y medio ambiente",            3,4,"Ingeniería Agrícola","PROF026","teorico",         "facultad"),
    ("IAGC-104","Desarrollo y extensión rural",                      3,6,"Ingeniería Agrícola","PROF025","teorico",         "especifico"),
    ("IAGC-105","Drenajes agrícolas",                                4,5,"Ingeniería Agrícola","PROF030","teorico_practico","especifico"),
    ("IAGC-106","Ecología",                                          3,3,"Ingeniería Agrícola","PROF026","teorico",         "institucional"),
    ("IAGC-107","Elementos de máquinas",                             3,4,"Ingeniería Agrícola","PROF028","teorico_practico","especifico"),
    ("IAGC-108","Fertilidad y nutrición",                            4,5,"Ingeniería Agrícola","PROF023","teorico_practico","especifico"),
    ("IAGC-109","Física electromagnética",                           4,2,"Ingeniería Agrícola","PROF009","teorico_practico","institucional"),
    ("IAGC-110","Física mecánica",                                   4,1,"Ingeniería Agrícola","PROF010","teorico_practico","institucional"),
    ("IAGC-111","Fisiología vegetal",                                3,4,"Ingeniería Agrícola","PROF035","teorico_practico","especifico"),
    ("IAGC-112","Fuentes de potencia",                               4,5,"Ingeniería Agrícola","PROF028","teorico_practico","especifico"),
    ("IAGC-113","Hidráulica",                                        4,5,"Ingeniería Agrícola","PROF017","teorico_practico","especifico"),
    ("IAGC-114","Hidrología",                                        3,6,"Ingeniería Agrícola","PROF017","teorico_practico","especifico"),
    ("IAGC-115","Ingeniería de riegos I",                            4,5,"Ingeniería Agrícola","PROF030","teorico_practico","especifico"),
    ("IAGC-116","Ingeniería de riegos II",                           4,6,"Ingeniería Agrícola","PROF022","teorico_practico","especifico"),
    ("IAGC-117","Manejo de cultivos en invernadero",                 3,5,"Ingeniería Agrícola","PROF014","teorico_practico","especifico"),
    ("IAGC-118","Manejo y conservación de productos agropecuarios",  3,5,"Ingeniería Agrícola","PROF032","teorico_practico","especifico"),
    ("IAGC-119","Manejo y conservación de suelos",                   3,6,"Ingeniería Agrícola","PROF023","teorico_practico","especifico"),
    ("IAGC-120","Máquinas agrícolas",                                4,5,"Ingeniería Agrícola","PROF018","teorico_practico","especifico"),
    ("IAGC-121","Mecánica de fluidos",                               4,4,"Ingeniería Agrícola","PROF019","teorico_practico","facultad"),
    ("IAGC-122","Mecánica de suelos",                                3,4,"Ingeniería Agrícola","PROF031","teorico_practico","especifico"),
    ("IAGC-123","Pequeña irrigación",                                3,7,"Ingeniería Agrícola","PROF030","teorico_practico","especifico"),
    ("IAGC-124","Procesos agroindustriales en la acuicultura",       3,5,"Ingeniería Agrícola","PROF033","teorico_practico","especifico"),
    ("IAGC-125","Producción agrícola",                               3,4,"Ingeniería Agrícola","PROF029","teorico_practico","especifico"),
    ("IAGC-126","Saneamiento urbano y rural",                        3,6,"Ingeniería Agrícola","PROF015","teorico_practico","especifico"),
    ("IAGC-127","Secado de productos biológicos",                    3,6,"Ingeniería Agrícola","PROF032","teorico_practico","especifico"),
    ("IAGC-128","Suelos",                                            4,4,"Ingeniería Agrícola","PROF020","teorico_practico","especifico"),
    ("IAGC-129","Tecnología del café",                               3,6,"Ingeniería Agrícola","PROF038","teorico_practico","componente_flexible"),
    # ── Ingeniería Civil (índices 40-43) ──────────────────────────────────────
    ("ICIV-101","Estructuras hidráulicas",  3,6,"Ingeniería Civil","PROF041","teorico_practico","especifico"),
    ("ICIV-102","Geología para ingenieros", 3,4,"Ingeniería Civil","PROF040","teorico_practico","especifico"),
    ("ICIV-103","Hidráulica",               4,5,"Ingeniería Civil","PROF042","teorico_practico","facultad"),
    ("ICIV-104","Hidrología",               3,5,"Ingeniería Civil","PROF041","teorico_practico","especifico"),
    # ── Ingeniería de Petróleos (índices 44-48) ───────────────────────────────
    ("IPET-101","Geología estructural e introducción a la geotermia",3,6,"Ingeniería de Petróleos","PROF043","teorico_practico","especifico"),
    ("IPET-102","Geología General I",                                4,3,"Ingeniería de Petróleos","PROF045","teorico_practico","especifico"),
    ("IPET-103","Geología General II",                               4,4,"Ingeniería de Petróleos","PROF045","teorico_practico","especifico"),
    ("IPET-104","Sedimentología y geología del petróleo",            4,5,"Ingeniería de Petróleos","PROF043","teorico_practico","especifico"),
    ("IPET-105","Sistemas de información geográfica",                3,5,"Ingeniería de Petróleos","PROF044","teorico_practico","especifico"),
    # ── Ingeniería de Software (índices 49-50) ────────────────────────────────
    ("ISFW-101","Algoritmia I",  4,2,"Ingeniería de Software","PROF046","teorico_practico","especifico"),
    ("ISFW-102","Base de datos", 4,3,"Ingeniería de Software","PROF047","teorico_practico","especifico"),
]

# Asignatura indices por programa (para matrículas)
ASIG_IDX = {
    "Ingeniería Agroindustrial": list(range(0, 11)),
    "Ingeniería Agrícola":       list(range(11, 40)),
    "Ingeniería Civil":          list(range(40, 44)),
    "Ingeniería de Petróleos":   list(range(44, 49)),
    "Ingeniería de Software":    list(range(49, 51)),
}

# ── Estudiantes fijos (50 distribuidos 10 por programa) ──────────────────────
PROGRAMAS_EST = [
    "Ingeniería Agroindustrial","Ingeniería Agroindustrial",
    "Ingeniería Agroindustrial","Ingeniería Agroindustrial",
    "Ingeniería Agroindustrial","Ingeniería Agroindustrial",
    "Ingeniería Agroindustrial","Ingeniería Agroindustrial",
    "Ingeniería Agroindustrial","Ingeniería Agroindustrial",
    "Ingeniería Agrícola","Ingeniería Agrícola",
    "Ingeniería Agrícola","Ingeniería Agrícola",
    "Ingeniería Agrícola","Ingeniería Agrícola",
    "Ingeniería Agrícola","Ingeniería Agrícola",
    "Ingeniería Agrícola","Ingeniería Agrícola",
    "Ingeniería Civil","Ingeniería Civil",
    "Ingeniería Civil","Ingeniería Civil",
    "Ingeniería Civil","Ingeniería Civil",
    "Ingeniería Civil","Ingeniería Civil",
    "Ingeniería Civil","Ingeniería Civil",
    "Ingeniería de Petróleos","Ingeniería de Petróleos",
    "Ingeniería de Petróleos","Ingeniería de Petróleos",
    "Ingeniería de Petróleos","Ingeniería de Petróleos",
    "Ingeniería de Petróleos","Ingeniería de Petróleos",
    "Ingeniería de Petróleos","Ingeniería de Petróleos",
    "Ingeniería de Software","Ingeniería de Software",
    "Ingeniería de Software","Ingeniería de Software",
    "Ingeniería de Software","Ingeniería de Software",
    "Ingeniería de Software","Ingeniería de Software",
    "Ingeniería de Software","Ingeniería de Software",
]

ESTUDIANTES_DATA = [
    ("20231150092","Mateo",     "Bermúdez Herrera",   "mateo.bermudez@usco.edu.co",    "1136279761",4.63,35.9),
    ("20191150166","Andrea",    "Bernal Ríos",        "andrea.bernal@usco.edu.co",     "1131159096",3.03,40.4),
    ("20191150005","Angela",    "Castillo Acosta",    "angela.castillo@usco.edu.co",   "1123020082",4.90,84.7),
    ("20231150033","Sara",      "Correa Vega",        "sara.correa@usco.edu.co",       "1103285188",4.05,47.8),
    ("20191150277","Fabian",    "Cruz Sánchez",       "fabian.cruz@usco.edu.co",       "1003961530",4.75,74.4),
    ("20221150080","Luisa",     "Cruz Trujillo",      "luisa.cruz@usco.edu.co",        "1050975320",3.26,19.1),
    ("20211150233","Vanessa",   "García Mendoza",     "vanessa.garcia@usco.edu.co",    "1076571007",4.26,66.1),
    ("20231150065","Edward",    "González Acosta",    "edward.gonzalez@usco.edu.co",   "1034464821",3.80,53.5),
    ("20201150260","Sebastián", "González Mora",      "sebastian.gonzalez@usco.edu.co","1071189194",4.76,76.7),
    ("20191150284","Monica",    "González Ramos",     "monica.gonzalez@usco.edu.co",   "1061770953",3.26,20.0),
    ("20191150059","Oscar",     "Herrera Cruz",       "oscar.herrera@usco.edu.co",     "1182995233",4.38,68.8),
    ("20231150220","Sofía",     "Herrera Muñoz",      "sofia.herrera@usco.edu.co",     "1156640927",3.56,84.8),
    ("20221150283","Andrés",    "Herrera Rivera",     "andres.herrera@usco.edu.co",    "1189426163",3.98,22.8),
    ("20231150217","Laura",     "Herrera Ríos",       "laura.herrera@usco.edu.co",     "1056854146",4.39,63.3),
    ("20191150292","Diana",     "Jiménez Ruiz",       "diana.jimenez@usco.edu.co",     "1066092929",4.05,58.4),
    ("20211150081","Isabella",  "Jiménez Álvarez",    "isabella.jimenez@usco.edu.co",  "1117624274",4.28,57.8),
    ("20191150154","Catalina",  "Lozano Ríos",        "catalina.lozano@usco.edu.co",   "1178077052",4.77,24.4),
    ("20211150021","Ricardo",   "Martínez Medina",    "ricardo.martinez@usco.edu.co",  "1096048684",4.23,61.7),
    ("20191150124","Diego",     "Medina Jiménez",     "diego.medina@usco.edu.co",      "1152298718",2.98,49.0),
    ("20221150041","Valentina", "Mora Ramírez",       "valentina.mora@usco.edu.co",    "1148187279",4.54,58.3),
    ("20191150161","María",     "Muñoz Mora",         "maria.munoz@usco.edu.co",       "1015345186",4.03,50.2),
    ("20221150209","Tatiana",   "Patiño Jiménez",     "tatiana.patino@usco.edu.co",    "1051112773",3.00,45.2),
    ("20201150236","Stephanie", "Patiño Morales",     "stephanie.patino@usco.edu.co",  "1093860718",4.52,76.0),
    ("20201150035","Jorge",     "Perdomo López",      "jorge.perdomo@usco.edu.co",     "1008432351",2.95,31.7),
    ("20231150102","Paola",     "Perdomo Ospina",     "paola.perdomo@usco.edu.co",     "1041027479",4.40,52.8),
    ("20201150167","Yessica",   "Pineda Cruz",        "yessica.pineda@usco.edu.co",    "1015015728",4.53,71.4),
    ("20231150019","Esteban",   "Pineda Flores",      "esteban.pineda@usco.edu.co",    "1099110661",3.96,45.1),
    ("20191150195","Luis",      "Pérez Morales",      "luis.perez@usco.edu.co",        "1074617971",4.13,40.5),
    ("20221150142","Felipe",    "Pérez Perdomo",      "felipe.perez@usco.edu.co",      "1011834450",3.50,24.2),
    ("20211150223","Jhon",      "Ramos Ramírez",      "jhon.ramos@usco.edu.co",        "1042455148",2.81,65.5),
    ("20231150080","Alejandro", "Ramírez Sánchez",    "alejandro.ramirez@usco.edu.co", "1073107917",4.07,65.2),
    ("20211150259","Juliana",   "Reyes Correa",       "juliana.reyes@usco.edu.co",     "1131139270",4.70,74.2),
    ("20221150013","Daniel",    "Rivera Gómez",       "daniel.rivera@usco.edu.co",     "1048146761",4.74,69.8),
    ("20201150084","Nicolás",   "Rivera Mora",        "nicolas.rivera@usco.edu.co",    "1124087031",3.37,79.8),
    ("20221150247","Ivan",      "Rivera Suárez",      "ivan.rivera@usco.edu.co",       "1057377352",4.70,26.5),
    ("20231150209","David",     "Romero Bernal",      "david.romero@usco.edu.co",      "1166607554",3.12,80.1),
    ("20211150056","Camila",    "Ruiz Bermúdez",      "camila.ruiz@usco.edu.co",       "1066748176",3.20,46.4),
    ("20221150074","Miguel",    "Ruiz Lozano",        "miguel.ruiz@usco.edu.co",       "1071103229",3.32,54.3),
    ("20191150109","Valeria",   "Ruiz Vargas",        "valeria.ruiz@usco.edu.co",      "1152251235",3.46,60.9),
    ("20191150261","Natalia",   "Ríos Rivera",        "natalia.rios@usco.edu.co",      "1021504757",2.94,19.8),
    ("20231150290","Kevin",     "Suárez Trujillo",    "kevin.suarez@usco.edu.co",      "1140333417",4.76,29.3),
    ("20201150082","Julián",    "Suárez Trujillo",    "julian.suarez@usco.edu.co",     "1188247930",3.60,17.7),
    ("20221150047","Cristian",  "Torres Ospina",      "cristian.torres@usco.edu.co",   "1012647705",3.12,26.2),
    ("20201150277","Alejandra", "Trujillo Quintero",  "alejandra.trujillo@usco.edu.co","1035517190",4.76,55.0),
    ("20201150136","Jessica",   "Valencia Castillo",  "jessica.valencia@usco.edu.co",  "1106242954",4.21,36.0),
    ("20221150192","Santiago",  "Valencia Medina",    "santiago.valencia@usco.edu.co", "1117601594",3.75,32.4),
    ("20211150237","Daniela",   "Vega Gómez",         "daniela.vega@usco.edu.co",      "1067056907",3.73,75.3),
    ("20221150028","Karen",     "Vega Suárez",        "karen.vega@usco.edu.co",        "1180754918",4.87,21.9),
    ("20201150036","Steven",    "Álvarez Aguilar",    "steven.alvarez@usco.edu.co",    "1012300889",3.28,35.3),
    ("20201150137","Camilo",    "Álvarez Romero",     "camilo.alvarez@usco.edu.co",    "1188393455",4.16,57.6),
]

# Convocatorias: (titulo, asig_idx, prof_code, estado, tipo, sede, dias_cierre)
CONVOCATORIAS_CONFIG = [
    ("Monitoría Control de Calidad 2026-1",        1, "PROF002", EstadoConvocatoriaEnum.abierta,        TipoMonitoriaEnum.laboratorios,        "Neiva",   45),
    ("Monitoría Producción Pecuaria 2026-1",        8, "PROF004", EstadoConvocatoriaEnum.borrador,       TipoMonitoriaEnum.academica_cursos,    "Neiva",   60),
    ("Monitoría Fertilidad y Nutrición 2026-1",    18, "PROF023", EstadoConvocatoriaEnum.abierta,        TipoMonitoriaEnum.academica_cursos,    "Neiva",   40),
    ("Monitoría Suelos 2026-1",                    28, "PROF020", EstadoConvocatoriaEnum.en_evaluacion,  TipoMonitoriaEnum.academica_cursos,    "La Plata",-3),
    ("Monitoría Geología para Ingenieros 2026-1",  41, "PROF040", EstadoConvocatoriaEnum.abierta,        TipoMonitoriaEnum.academica_cursos,    "Neiva",   50),
    ("Monitoría Hidráulica Civil 2026-1",          42, "PROF042", EstadoConvocatoriaEnum.cerrada,        TipoMonitoriaEnum.laboratorios,        "Neiva",  -10),
    ("Monitoría Geología General I 2026-1",        45, "PROF045", EstadoConvocatoriaEnum.abierta,        TipoMonitoriaEnum.academica_cursos,    "Neiva",   55),
    ("Monitoría SIG 2026-1",                       48, "PROF044", EstadoConvocatoriaEnum.borrador,       TipoMonitoriaEnum.tic,                 "Neiva",   70),
    ("Monitoría Algoritmia I 2026-1",              49, "PROF046", EstadoConvocatoriaEnum.abierta,        TipoMonitoriaEnum.academica_cursos,    "Neiva",   45),
    ("Monitoría Base de Datos 2026-1",             50, "PROF047", EstadoConvocatoriaEnum.en_evaluacion,  TipoMonitoriaEnum.laboratorios,        "Neiva",  -5),
]


def _upsert_user(db, codigo, **kwargs):
    """Inserta usuario solo si no existe (por codigo). Retorna (usuario, creado)."""
    u = db.query(User).filter_by(codigo=codigo).first()
    if u:
        return u, False
    u = User(codigo=codigo, **kwargs)
    db.add(u)
    return u, True


def reset_db():
    """Elimina TODOS los datos de prueba (excepto admin). Solo para desarrollo/reset."""
    tablas = [
        "firmas_consentimiento","rutas_practica","viaticos","pagos_viaticos",
        "movimientos_presupuestales","documentos_presupuesto","archivos_adjuntos",
        "evaluaciones_monitor","horas_monitor","postulaciones","convocatorias",
        "practicas","asignatura_estudiantes","asignaturas",
        "historial_estados","notificaciones","audit_logs",
        "configuracion_calendario","presupuestos","tarifas_viaticos",
        "password_reset_tokens","monitoria_plantillas","practica_plantillas",
        "precios_combustible","peajes_nacionales",
    ]
    with engine.connect() as conn:
        for t in tablas:
            try:
                conn.execute(text(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE"))
            except Exception:
                conn.rollback()
        try:
            conn.execute(text("DELETE FROM users WHERE codigo != 'Krlitoxprz'"))
            conn.commit()
        except Exception:
            conn.rollback()
    print("  OK  BD limpiada.")


def run(reset: bool = False):
    """
    Seeder idempotente: puede ejecutarse múltiples veces sin errores.
    Sin flags  → inserta solo lo que NO existe todavía.
    --reset    → limpia la BD y vuelve a poblar todo desde cero.
    """
    print("=" * 70)
    print("  SIPAM-USCO — Seeder v4 · Idempotente")
    print("=" * 70)

    print("\n[1/9] Inicializando BD...")
    init_db()
    if reset:
        print("  ⚠  Modo reset: limpiando todos los datos de prueba...")
        reset_db()

    db = SessionLocal()
    try:
        pw = get_password_hash(PASSWORD)
        nuevos = {"users": 0, "asig": 0, "mat": 0, "conv": 0, "post": 0}
        ya_mats = ya_posts = 0

        # ── [2/9] Administrativos ─────────────────────────────────────────────
        print("\n[2/9] Cuentas administrativas...")
        decano, c = _upsert_user(db, "DECANO001",
            nombres="Álvaro Ernesto", apellidos="Guzmán Rincón",
            email="alvaro.guzman@usco.edu.co", cedula="12791500",
            hashed_password=pw, rol=RolEnum.decano,
            programa="Decanatura Facultad de Ingeniería", sede="Neiva")
        nuevos["users"] += int(c)
        jefes_db = []
        for cod, nom, ape, email, ced, prog, sede in JEFES_DATA:
            u, c = _upsert_user(db, cod, nombres=nom, apellidos=ape, email=email,
                                cedula=ced, hashed_password=pw, rol=RolEnum.jefe_programa,
                                programa=prog, sede=sede)
            jefes_db.append(u)
            nuevos["users"] += int(c)
        db.flush()
        print(f"  ✓  DECANO001 + JEFE001–JEFE005 ({nuevos['users']} nuevos).")

        # ── [3/9] Profesores ──────────────────────────────────────────────────
        print("\n[3/9] Profesores...")
        prof_map = {}
        n_prof = 0
        for cod, nom, ape, email, ced, prog, sede, tipo_doc, modalidad_doc in PROFESORES_DATA:
            u, c = _upsert_user(db, cod, nombres=nom, apellidos=ape, email=email,
                                cedula=ced, hashed_password=pw, rol=RolEnum.profesor,
                                programa=prog, sede=sede,
                                tipo_docente=tipo_doc, modalidad_docente=modalidad_doc)
            prof_map[cod] = u
            n_prof += int(c)
        db.flush()
        nuevos["users"] += n_prof
        print(f"  ✓  {len(prof_map)} profesores ({n_prof} nuevos).")

        # ── [4/9] Asignaturas ─────────────────────────────────────────────────
        print("\n[4/9] Asignaturas...")
        asig_db = []
        for cod, nom, cred, sem, prog, pcod, caracter, caracteristica in ASIGNATURAS_DATA:
            a = db.query(Asignatura).filter_by(codigo=cod).first()
            if not a:
                a = Asignatura(codigo=cod, nombre=nom, creditos=cred,
                               semestre=sem, programa=prog, facultad=FACULTAD,
                               profesor_id=prof_map[pcod].id,
                               caracter_curso=caracter,
                               caracteristica_curso=caracteristica)
                db.add(a)
                nuevos["asig"] += 1
            asig_db.append(a)
        db.flush()
        print(f"  ✓  {len(asig_db)} asignaturas ({nuevos['asig']} nuevas).")

        # ── [5/9] Estudiantes ─────────────────────────────────────────────────
        print("\n[5/9] Estudiantes (50 fijos + 550 generados)...")
        est_db = []
        n_est = 0
        SEDES_AGRIC = ["Neiva","La Plata","Garzón","Pitalito","La Plata"]
        for i, (cod, nom, ape, email, ced, prom, pct) in enumerate(ESTUDIANTES_DATA):
            prog = PROGRAMAS_EST[i]
            sede_est = SEDES_AGRIC[i % len(SEDES_AGRIC)] if prog == "Ingeniería Agrícola" else "Neiva"
            u, c = _upsert_user(db, cod, nombres=nom, apellidos=ape, email=email,
                                cedula=ced, hashed_password=pw, rol=RolEnum.estudiante,
                                promedio=prom, porcentaje_creditos=pct,
                                programa=prog, sede=sede_est)
            est_db.append((u, prog))
            n_est += int(c)

        random.seed(42)  # reproducibilidad garantizada para generados
        _N = ["Alejandro","Brayan","Camila","Daniel","Edgar","Felipe","Gabriela",
              "Harold","Ivan","Jairo","Kevin","Leidy","Manuel","Nelson","Orlando",
              "Pablo","Rafael","Sergio","Tania","Ulises","Vanessa","Wilson",
              "Ximena","Yolanda","Zamira","Brenda","Cesar","Diana","Ever","Fredy",
              "Gilberto","Hernando","Ingrid","Javier","Karen","Lorena","Mario",
              "Nathalia","Omar","Patricia","Rodrigo","Sandra","Tatiana","Uriel"]
        _A = ["Aguilar","Barrera","Cárdenas","Delgado","Espinosa","Florez",
              "Guerrero","Henao","Ibáñez","Jaramillo","Ladino","Millán",
              "Naranjo","Ospina","Pardo","Quintana","Restrepo","Salazar",
              "Téllez","Uribe","Valderrama","Wilches","Ynfante","Zambrano",
              "Acosta","Buitrago","Cortés","Durán","Escobar","Fernández",
              "Gómez","Herrera","Jiménez","Lozano","Medina","Niño",
              "Ortega","Pineda","Quiroga","Ramos","Suárez","Torres","Vargas"]
        progs_ciclo = list(ASIG_IDX.keys())
        for i in range(550):
            prog = progs_ciclo[i // 110]
            anio = 2018 + (i % 8)
            nom_g = _N[i % len(_N)]
            ape_g = _A[i % len(_A)]
            num_g = 500 + i
            sede_g = SEDES_AGRIC[i % len(SEDES_AGRIC)] if prog == "Ingeniería Agrícola" else "Neiva"
            prom_g = round(random.uniform(2.5, 5.0), 2)   # avanzar estado random siempre
            pct_g  = round(random.uniform(10.0, 95.0), 1)
            cod_g  = f"{anio}1150{num_g:03d}"
            u_g, c = _upsert_user(db, cod_g,
                nombres=nom_g, apellidos=ape_g,
                email=f"{nom_g.lower()}.{ape_g.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}{num_g}@usco.edu.co",
                cedula=f"117{num_g+800000:07d}",
                hashed_password=pw, rol=RolEnum.estudiante,
                promedio=prom_g, porcentaje_creditos=pct_g,
                programa=prog, sede=sede_g,
            )
            est_db.append((u_g, prog))
            n_est += int(c)
        db.flush()
        nuevos["users"] += n_est
        print(f"  ✓  {len(est_db)} estudiantes ({n_est} nuevos).")

        # ── [6/9] Matrículas ──────────────────────────────────────────────────
        print("\n[6/9] Matrículas...")
        ya_mats = db.query(AsignaturaEstudiante).count()
        if ya_mats == 0:
            random.seed(42)
            MAT_MAX_POR_ASIG = 30
            asig_cupos = {ai: MAT_MAX_POR_ASIG for asig_list in ASIG_IDX.values() for ai in asig_list}
            for u, prog in est_db:
                idxs = ASIG_IDX.get(prog, [])
                disponibles = [ai for ai in idxs if asig_cupos.get(ai, 0) > 0]
                if not disponibles:
                    continue
                n = min(random.randint(4, 6), len(disponibles))
                sample = random.sample(disponibles, n)
                for ai in sample:
                    db.add(AsignaturaEstudiante(
                        asignatura_id=asig_db[ai].id,
                        estudiante_id=u.id,
                        periodo_academico=PERIODO,
                    ))
                    asig_cupos[ai] -= 1
                    nuevos["mat"] += 1
            db.flush()
            print(f"  ✓  {nuevos['mat']} matrículas creadas.")
        else:
            print(f"  ─  {ya_mats} matrículas ya existen, omitiendo.")

        # ── [7/9] Convocatorias ───────────────────────────────────────────────
        print("\n[7/9] Convocatorias...")
        conv_db = []
        fecha_base = datetime(2026, 2, 9)
        for titulo, ai, pcod, estado, tipo, sede, dias in CONVOCATORIAS_CONFIG:
            conv = db.query(Convocatoria).filter_by(titulo=titulo, periodo_academico=PERIODO).first()
            if not conv:
                fecha_fin = fecha_base + timedelta(days=dias)
                fecha_ini = fecha_fin - timedelta(days=30) if dias < 0 else fecha_base
                conv = Convocatoria(
                    titulo=titulo, asignatura_id=asig_db[ai].id,
                    profesor_id=prof_map[pcod].id,
                    tipo_monitoria=tipo, estado=estado, sede=sede,
                    periodo_academico=PERIODO,
                    fecha_inicio_postulacion=fecha_ini,
                    fecha_fin_postulacion=fecha_fin,
                    num_monitores_requeridos=2, horas_semana=8, horas_semestre=128,
                    promedio_minimo=3.5, creditos_minimo_pct=30.0,
                )
                db.add(conv)
                nuevos["conv"] += 1
            conv_db.append(conv)
        db.flush()
        print(f"  ✓  {len(conv_db)} convocatorias ({nuevos['conv']} nuevas).")

        # ── [8/9] Postulaciones de muestra ────────────────────────────────────
        print("\n[8/9] Postulaciones de muestra...")
        ya_posts = db.query(Postulacion).count()
        if ya_posts == 0:
            random.seed(42)
            aptos = [(u, p) for u, p in est_db
                     if (u.promedio or 0) >= 3.5 and (u.porcentaje_creditos or 0) >= 30.0]
            random.shuffle(aptos)
            for u, _ in aptos[:10]:
                db.add(Postulacion(
                    convocatoria_id=conv_db[8].id, estudiante_id=u.id,
                    estado=random.choice([EstadoPostulacionEnum.pendiente, EstadoPostulacionEnum.en_revision]),
                    nota_asignatura=round(random.uniform(3.0, 5.0), 2),
                    promedio_estudiante=u.promedio,
                    documentos_completos=random.choice([True, False]),
                    carta_motivacion="Deseo apoyar a mis compañeros en el aprendizaje de esta asignatura.",
                ))
                nuevos["post"] += 1
            db.flush()
            print(f"  ✓  {nuevos['post']} postulaciones creadas.")
        else:
            print(f"  ─  {ya_posts} postulaciones ya existen, omitiendo.")

        # ── [9/9] Presupuesto, tarifas, calendario ────────────────────────────
        print("\n[9/9] Presupuesto, tarifas y calendarios...")
        for periodo_p, monto, ejecutado, comprometido, desc in [
            ("2025-1", 40_000_000.0, 32_700_000.0,  0.0,         "Histórico 2025-1"),
            (PERIODO,  48_000_000.0,  5_200_000.0, 3_800_000.0, "Presupuesto asignado Vicerrectoría Académica 2026-1"),
        ]:
            if not db.query(Presupuesto).filter_by(periodo_academico=periodo_p).first():
                db.add(Presupuesto(periodo_academico=periodo_p,
                                   monto_total_asignado=monto, monto_ejecutado=ejecutado,
                                   monto_comprometido=comprometido, descripcion=desc))

        for desc_t, valor, desde in [
            ("Viático municipal (Huila)",         65_000.0,  date(2026,1,1)),
            ("Viático interdepartamental",        100_000.0, date(2026,1,1)),
            ("Viático zona rural",                 80_000.0, date(2026,1,1)),
            ("Transporte interno (bus/colectivo)", 16_000.0, date(2026,1,1)),
        ]:
            if not db.query(TarifaViatico).filter_by(descripcion=desc_t).first():
                db.add(TarifaViatico(descripcion=desc_t, valor_dia=valor,
                                     aplica_desde=desde, is_active=True))

        for periodo_c, s_ini, s_fin, f_ini, f_fin, activo in [
            ("2025-1", 3, 14, datetime(2025,1,27), datetime(2025,6,13,23,59), False),
            (PERIODO,  3, 14, datetime(2026,1,26), datetime(2026,6,12,23,59), True),
        ]:
            if not db.query(ConfiguracionCalendario).filter_by(periodo_academico=periodo_c).first():
                db.add(ConfiguracionCalendario(
                    periodo_academico=periodo_c, semana_inicio_solicitudes=s_ini,
                    semana_fin_solicitudes=s_fin, fecha_inicio_semestre=f_ini,
                    fecha_fin_semestre=f_fin, is_active=activo))

        db.commit()
        print("  ✓  Presupuesto, tarifas y calendarios listos.")

        from app.db.database import (_seed_plantillas, _seed_monitoria_plantillas,
                                      _seed_precios_combustible, _seed_peajes_nacionales)
        _seed_plantillas()
        _seed_monitoria_plantillas()
        _seed_precios_combustible()
        _seed_peajes_nacionales()
        print("  ✓  Plantillas, precios y peajes regenerados.")

        # ── Resumen ───────────────────────────────────────────────────────────
        total_nuevos = sum(nuevos.values())
        print("\n" + "=" * 70)
        print(f"  SEEDER COMPLETADO — {total_nuevos} registros nuevos insertados")
        print("=" * 70)
        print(f"\n  {'ROL':<22} {'CÓDIGO':<12} NOMBRE / PROGRAMA")
        print(f"  {'-'*70}")
        print(f"  {'Decano':<22} {'DECANO001':<12} Álvaro E. Guzmán Rincón")
        for cod, nom, ape, _, _, prog, _ in JEFES_DATA:
            print(f"  {'Jefe Programa':<22} {cod:<12} {nom} {ape} · {prog}")
        print(f"\n  Profesores  : PROF001–PROF047 ({len(prof_map)})")
        print(f"  Estudiantes : {len(est_db)} (50 fijos + 550 generados, 5 programas)")
        print(f"  Asignaturas : {len(asig_db)} | Convocatorias: {len(conv_db)}")
        print(f"  Matrículas  : {nuevos['mat'] or ya_mats} | Postulaciones: {nuevos['post'] or ya_posts}")
        print(f"\n  Contraseña universal de prueba : sipam2025")
        print(f"  Admin                          : Krlitoxprz / Sasuke24")

    except Exception as e:
        db.rollback()
        print(f"\n  ✗ ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    run(reset="--reset" in sys.argv)
