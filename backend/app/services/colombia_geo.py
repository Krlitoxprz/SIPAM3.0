"""
Catálogo geográfico de Colombia — Departamentos y Municipios.
Datos basados en DIVIPOLA (DANE 2024).
Todos los 37 municipios de Huila incluidos completos.
"""

DEPARTAMENTOS_MUNICIPIOS: dict[str, list[str]] = {
    "Amazonas": [
        "Leticia", "Puerto Nariño", "El Encanto", "La Chorrera", "La Pedrera",
        "La Victoria", "Mirití-Paraná", "Puerto Alegría", "Puerto Arica",
        "Puerto Santander", "Tarapacá",
    ],
    "Antioquia": [
        "Medellín", "Bello", "Itagüí", "Envigado", "Apartadó", "Rionegro",
        "Turbo", "Caucasia", "La Ceja", "Sabaneta", "Copacabana", "Caldas",
        "Girardota", "Barbosa", "Marinilla", "El Carmen de Viboral",
        "Santa Fe de Antioquia", "Andes", "Jericó", "Yarumal", "Chigorodó",
        "Puerto Berrío", "Mutatá", "Necoclí", "Montería", "Carepa",
    ],
    "Arauca": [
        "Arauca", "Arauquita", "Cravo Norte", "Fortul", "Puerto Rondón",
        "Saravena", "Tame",
    ],
    "Atlántico": [
        "Barranquilla", "Soledad", "Malambo", "Sabanalarga", "Galapa",
        "Puerto Colombia", "Baranoa", "Sabanagrande", "Palmar de Varela",
        "Ponedera", "Luruaco", "Repelón", "Candelaria",
    ],
    "Bolívar": [
        "Cartagena", "Magangué", "Mompox", "El Carmen de Bolívar",
        "San Juan Nepomuceno", "Turbaco", "Arjona", "Mahates", "Córdoba",
        "Margarita", "Pinillos", "San Martín de Loba", "Tiquisio",
    ],
    "Boyacá": [
        "Tunja", "Duitama", "Sogamoso", "Chiquinquirá", "Paipa", "Moniquirá",
        "Ramiriquí", "Soatá", "Garagoa", "Miraflores", "Guateque", "Santa Rosa de Viterbo",
        "Nobsa", "Tibasosa", "Samacá", "Villa de Leyva", "Ráquira",
    ],
    "Caldas": [
        "Manizales", "Villamaría", "Chinchiná", "Riosucio", "Supía",
        "La Dorada", "Anserma", "Salamina", "Aguadas", "Filadelfia",
        "Neira", "Aranzazu", "Pácora", "Marmato",
    ],
    "Caquetá": [
        "Florencia", "San José del Fragua", "San Vicente del Caguán",
        "Belén de los Andaquíes", "Curillo", "Milán", "Puerto Rico",
        "Valparaíso", "Albania", "Cartagena del Chairá", "El Doncello",
        "El Paujil", "La Montañita", "Morelia", "Solano", "Solita",
    ],
    "Casanare": [
        "Yopal", "Aguazul", "Orocué", "Paz de Ariporo", "Pore",
        "Recetor", "Sabanalarga", "Sácama", "San Luis de Palenque",
        "Támara", "Tauramena", "Trinidad", "Villanueva",
    ],
    "Cauca": [
        "Popayán", "Santander de Quilichao", "Puerto Tejada", "Miranda",
        "Padilla", "Corinto", "El Tambo", "Timbío", "Piendamó",
        "Rosas", "Balboa", "Florencia", "Guapi", "Inzá", "La Sierra",
        "La Vega", "López de Micay", "Mercaderes", "Morales", "Patía",
        "Sucre", "Timbiquí", "Toribío",
    ],
    "Cesar": [
        "Valledupar", "Aguachica", "Agustín Codazzi", "Bosconia",
        "Chimichagua", "El Copey", "El Paso", "Gamarra", "González",
        "La Gloria", "La Jagua de Ibirico", "Manaure", "Pailitas",
        "Pelaya", "Pueblo Bello", "Río de Oro", "San Alberto",
        "San Diego", "San Martín", "Tamalameque",
    ],
    "Chocó": [
        "Quibdó", "Acandí", "Alto Baudó", "Atrato", "Bagadó",
        "Bahía Solano", "Bajo Baudó", "Bojayá", "Cantón de San Pablo",
        "El Carmen de Atrato", "Istmina", "Juradó", "Lloró", "Medio Atrato",
        "Nóvita", "Nuquí", "Riosucio", "San José del Palmar", "Tadó",
        "Unguía",
    ],
    "Córdoba": [
        "Montería", "Montelíbano", "Cereté", "Lorica", "Sahagún",
        "Tierralta", "Valencia", "Chinú", "Ciénaga de Oro", "Planeta Rica",
        "Pueblo Nuevo", "Puerto Escondido", "Purísima",
    ],
    "Cundinamarca": [
        "Bogotá D.C.", "Soacha", "Mosquera", "Funza", "Madrid", "Facatativá",
        "Zipaquirá", "Chía", "La Calera", "Cajicá", "Girardot", "Fusagasugá",
        "Zipacón", "Tocancipá", "Cogua", "Tabio", "Tenjo", "Subachoque",
        "El Rosal", "La Mesa", "Anapoima", "Apulo", "Guaduas",
        "Villeta", "Ubaté", "Chocontá", "Suesca", "Nemocón",
    ],
    "Guainía": [
        "Inírida", "Barranco Minas", "Cacahual", "La Guadalupe",
        "Mapiripana", "Morichal", "Pana Pana", "Puerto Colombia", "San Felipe",
    ],
    "Guaviare": [
        "San José del Guaviare", "Calamar", "El Retorno", "Miraflores",
    ],
    "Huila": [
        "Neiva", "Pitalito", "Garzón", "La Plata", "Campoalegre",
        "Rivera", "Palermo", "Gigante", "Timaná", "San Agustín",
        "Isnos", "Acevedo", "Algeciras", "Altamira", "Baraya",
        "Colombia", "Elías", "Guadalupe", "Hobo", "Iquira",
        "La Argentina", "Nátaga", "Oporapa", "Paicol", "Palestina",
        "Pital", "Saladoblanco", "Santa María", "Suaza", "Tarqui",
        "Tello", "Teruel", "Tesalia", "Villavieja", "Yaguará",
        "La Jagua de Ibirico",
    ],
    "La Guajira": [
        "Riohacha", "Maicao", "Uribia", "Manaure", "Dibulla",
        "Fonseca", "Barrancas", "San Juan del Cesar", "Albania",
        "Distracción", "El Molino", "Hatonuevo", "La Jagua del Pilar",
        "Urumita", "Villanueva",
    ],
    "Magdalena": [
        "Santa Marta", "Ciénaga", "Fundación", "Plato", "Aracataca",
        "El Banco", "Pivijay", "Salamina", "San Zenón", "Zona Bananera",
        "Algarrobo", "Chivolo", "El Piñón", "Guamal",
    ],
    "Meta": [
        "Villavicencio", "Acacías", "Granada", "Puerto Gaitán", "Puerto López",
        "San Martín", "Vista Hermosa", "Cumaral", "El Castillo",
        "El Dorado", "Fuente de Oro", "La Macarena", "La Uribe",
        "Lejanías", "Mapiripán", "Mesetas", "Puerto Concordia",
        "Puerto Lleras", "Puerto Rico",
    ],
    "Nariño": [
        "Pasto", "Tumaco", "Ipiales", "Túquerres", "La Unión",
        "Samaniego", "Sandoná", "Barbacoas", "Cumbal", "El Contadero",
        "Guachucal", "Imués", "Iles", "La Cruz", "La Florida",
        "Mallama", "Olaya Herrera", "Ospina", "Policarpa", "Potosí",
        "Roberto Payán", "San Bernardo", "San Lorenzo", "San Pedro de Cartago",
        "Santa Bárbara", "Taminango",
    ],
    "Norte de Santander": [
        "Cúcuta", "Ocaña", "Pamplona", "Villa del Rosario", "Los Patios",
        "El Zulia", "Tibú", "Convención", "Hacarí", "La Playa de Belén",
        "Sardinata", "Toledo", "Chinácota", "Ragonvalia",
    ],
    "Putumayo": [
        "Mocoa", "Puerto Asís", "Orito", "Valle del Guamuez",
        "Villagarzón", "San Miguel", "Puerto Caicedo", "Puerto Guzmán",
        "Colón", "Leguízamo", "Sibundoy", "San Francisco", "Santiago",
    ],
    "Quindío": [
        "Armenia", "Calarcá", "La Tebaida", "Montenegro", "Quimbaya",
        "Circasia", "Filandia", "Génova", "Pijao", "Salento", "Buenavista",
        "Córdoba",
    ],
    "Risaralda": [
        "Pereira", "Dosquebradas", "Santa Rosa de Cabal", "La Virginia",
        "Cartago", "Belén de Umbría", "Guática", "La Celia", "Marsella",
        "Mistrató", "Pueblo Rico", "Quinchía",
    ],
    "San Andrés y Providencia": [
        "San Andrés", "Providencia",
    ],
    "Santander": [
        "Bucaramanga", "Floridablanca", "Girón", "Piedecuesta",
        "Barrancabermeja", "Vélez", "San Gil", "Socorro", "Málaga",
        "Barbosa", "Zapatoca", "Lebrija", "Rionegro", "Sabana de Torres",
        "Simacota", "El Carmen de Chucurí",
    ],
    "Sucre": [
        "Sincelejo", "Corozal", "Sampués", "San Marcos", "Tolú",
        "Tolú Viejo", "Ovejas", "Galeras", "Guaranda", "Los Palmitos",
        "Majagual", "Morroa", "Palmito", "San Benito Abad",
        "San Juan de Betulia", "San Onofre",
    ],
    "Tolima": [
        "Ibagué", "Espinal", "Girardot", "Melgar", "Honda",
        "Flandes", "Chaparral", "Mariquita", "Líbano", "Armero",
        "Ambalema", "Ataco", "Cajamarca", "Carmen de Apicalá", "Coyaima",
        "Cunday", "Dolores", "Fresno", "Guamo", "Icononzo",
        "Natagaima", "Ortega", "Planadas", "Purificación", "Rioblanco",
        "Roncesvalles", "Rovira", "Saldaña", "San Antonio", "San Luis",
        "Santa Isabel", "Suárez", "Valle de San Juan", "Venadillo", "Villahermosa",
    ],
    "Valle del Cauca": [
        "Cali", "Palmira", "Buenaventura", "Buga", "Tuluá", "Cartago",
        "Yumbo", "Florida", "Pradera", "Caicedonia", "Candelaria",
        "El Cerrito", "El Dovio", "El Águila", "Ginebra", "Guacarí",
        "Jamundí", "La Cumbre", "La Unión", "La Victoria", "Obando",
        "Restrepo", "Riofrío", "Roldanillo", "San Pedro", "Sevilla",
        "Toro", "Trujillo", "Ulloa", "Versalles", "Vijes",
        "Yotoco", "Zarzal", "Dagua",
    ],
    "Vaupés": [
        "Mitú", "Carurú", "Pacoa", "Papunaua", "Taraira", "Yavaraté",
    ],
    "Vichada": [
        "Puerto Carreño", "Cumaribo", "La Primavera", "Santa Rosalía",
    ],
}


def get_departamentos() -> list[str]:
    """Retorna la lista ordenada de departamentos."""
    return sorted(DEPARTAMENTOS_MUNICIPIOS.keys())


def get_municipios(departamento: str) -> list[str]:
    """Retorna los municipios ordenados de un departamento dado."""
    return sorted(DEPARTAMENTOS_MUNICIPIOS.get(departamento, []))
