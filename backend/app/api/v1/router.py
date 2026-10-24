from fastapi import APIRouter
from app.api.v1.endpoints import auth, convocatorias, postulaciones, seleccion, practicas, presupuesto, reportes, notificaciones, monitor, transporte, busqueda, qr, perfil, geo, admin, ia, pdf_gen, iot_tracking, ocr, nlp_analysis

api_router = APIRouter()


@api_router.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "system": "SIPAM-USCO", "version": "1.0.0"}


api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(convocatorias.router, prefix="/convocatorias", tags=["Convocatorias"])
api_router.include_router(postulaciones.router, prefix="/postulaciones", tags=["Postulaciones"])
api_router.include_router(seleccion.router, prefix="/seleccion", tags=["Selección de Monitores"])
api_router.include_router(practicas.router, prefix="/practicas", tags=["Prácticas Extramuros"])
api_router.include_router(presupuesto.router, prefix="/presupuesto", tags=["Presupuesto"])
api_router.include_router(reportes.router, prefix="/reportes", tags=["Reportes"])
api_router.include_router(notificaciones.router, prefix="/notificaciones", tags=["Notificaciones"])
api_router.include_router(monitor.router, prefix="/monitor", tags=["Monitor"])
api_router.include_router(transporte.router, prefix="/transporte", tags=["Transporte"])
api_router.include_router(busqueda.router, prefix="/busqueda", tags=["Búsqueda Global"])
api_router.include_router(qr.router, prefix="/qr", tags=["Códigos QR"])
api_router.include_router(perfil.router, prefix="/perfil", tags=["Perfil de Usuario"])
api_router.include_router(geo.router, prefix="/geo", tags=["Geolocalización"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(ia.router, prefix="/ia", tags=["Inteligencia Artificial"])
api_router.include_router(pdf_gen.router, prefix="/pdf", tags=["PDF Generator"])

# Course Compliance Routers (CNN, IoT, Transformer)
api_router.include_router(iot_tracking.router, prefix="/iot", tags=["IoT GPS Tracking"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["CNN OCR"])
api_router.include_router(nlp_analysis.router, prefix="/nlp", tags=["Transformer NLP"])
