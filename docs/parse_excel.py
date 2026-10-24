import openpyxl, json

wb = openpyxl.load_workbook(r'docs\Extramuros ING-2026-12-marzo.xlsx', data_only=True)
ws = wb.active

practicas = []
for row in ws.iter_rows(min_row=5, max_row=1002, min_col=1, max_col=41):
    vals = {}
    for cell in row:
        if cell.value is not None:
            vals[cell.column_letter] = cell.value
    if 'A' in vals and isinstance(vals.get('A'), (int, float)):
        practicas.append(vals)

def safe_float(v):
    try:
        return float(v) if v else None
    except:
        return None

def safe_str(v):
    return str(v).strip() if v else ''

result = []
for p in practicas:
    d = safe_str(p.get('D', ''))
    if not d:
        continue
    result.append({
        'no': int(p.get('A', 0)),
        'programa': safe_str(p.get('B', '')),
        'sede': safe_str(p.get('C', '')),
        'nombre_practica': d,
        'profesor': safe_str(p.get('E', '')),
        'vinculacion': safe_str(p.get('F', '')),
        'asignatura': safe_str(p.get('G', '')),
        'caracter_curso': safe_str(p.get('K', '')),
        'ruta': safe_str(p.get('L', '')),
        'visitas_fo16': safe_str(p.get('M', '')),
        'tipo_bus': safe_str(p.get('T', '')),
        'costo_tiquetes': safe_float(p.get('Y')),
        'costo_bus_externo': safe_float(p.get('Z')),
        'viat_conductor_dias': safe_float(p.get('AA')),
        'viat_conductor_valor_dia': safe_float(p.get('AB')),
        'viat_docente_dias': safe_float(p.get('AD')),
        'viat_docente_valor_dia': safe_float(p.get('AE')),
        'total': safe_float(p.get('AG')),
    })

with open('docs/extramuros_data.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'Total practicas: {len(result)}')
programas = sorted(set(p['programa'] for p in result))
print('Programas:')
for pg in programas:
    n = sum(1 for p in result if p['programa'] == pg)
    print(f'  {pg} ({n})')

print()
print('=== NOMBRES DE PRACTICAS UNICOS ===')
nombres = sorted(set(p['nombre_practica'] for p in result))
for nm in nombres:
    print(f'  - {nm}')

print()
print('=== SAMPLE RUTAS ===')
for p in result[:10]:
    print(f"  [{p['no']}] {p['nombre_practica']}")
    print(f"       Ruta: {p['ruta']}")
    print()
