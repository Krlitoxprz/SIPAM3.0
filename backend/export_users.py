import app.models.user, app.models.convocatoria, app.models.postulacion, app.models.practica, app.models.presupuesto
from app.db.database import SessionLocal
from app.models.user import User, RolEnum

db = SessionLocal()
users = db.query(User).order_by(User.rol, User.apellidos).all()

grupos = {
    RolEnum.jefe_programa: [],
    RolEnum.decano: [],
    RolEnum.admin: [],
    RolEnum.profesor: [],
    RolEnum.estudiante: [],
}
for u in users:
    grupos[u.rol].append(u)
db.close()

print(f"jefe_programa:{len(grupos[RolEnum.jefe_programa])}")
print(f"decano:{len(grupos[RolEnum.decano])}")
print(f"admin:{len(grupos[RolEnum.admin])}")
print(f"profesor:{len(grupos[RolEnum.profesor])}")
print(f"estudiante:{len(grupos[RolEnum.estudiante])}")
print("---")
for rol, lista in grupos.items():
    for u in lista:
        prom = f"{u.promedio:.2f}" if u.promedio is not None else "-"
        cred = f"{u.porcentaje_creditos:.1f}%" if u.porcentaje_creditos is not None else "-"
        activo = "SI" if u.is_active else "NO"
        print(f"{rol.value}||{u.codigo}||{u.nombres} {u.apellidos}||{u.email}||{u.cedula}||{activo}||{prom}||{cred}")
