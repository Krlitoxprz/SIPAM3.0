"""Genera INSERT SQL para la tabla practica_plantillas a partir del Excel parseado."""
import json

with open('docs/extramuros_data.json', encoding='utf-8') as f:
    data = json.load(f)

def esc(s):
    if s is None:
        return 'NULL'
    s = str(s).strip().replace("'", "''")
    return f"'{s}'"

def num(v):
    if v is None:
        return 'NULL'
    return str(v)

lines = []
for p in data:
    nombre = esc(p['nombre_practica'])
    programa = esc(p['programa'])
    sede = esc(p['sede'])
    asignatura = esc(p['asignatura'])
    caracter = esc(p['caracter_curso'])
    ruta = esc(p['ruta'])
    visitas = esc(p['visitas_fo16'])
    tipo_bus = esc(p['tipo_bus'])
    costo_ext = num(p['costo_bus_externo'])
    costo_tiq = num(p['costo_tiquetes'])
    viat_doc_dias = num(p['viat_docente_dias'])
    viat_doc_val = num(p['viat_docente_valor_dia'])

    sql = (
        f"INSERT INTO practica_plantillas "
        f"(nombre,programa,sede,asignatura,caracter_curso,ruta_texto,visitas_fo16,tipo_bus,"
        f"costo_bus_externo,costo_tiquetes,viat_docente_dias,viat_docente_valor_dia) "
        f"VALUES ({nombre},{programa},{sede},{asignatura},{caracter},{ruta},{visitas},{tipo_bus},"
        f"{costo_ext},{costo_tiq},{viat_doc_dias},{viat_doc_val})"
    )
    lines.append(sql)

print(f"-- {len(lines)} registros de practica_plantillas")
for l in lines:
    print(l)
