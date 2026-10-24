"""Servicio de envío de correos electrónicos vía SMTP (SF-02)."""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_html(titulo: str, cuerpo: str, boton_texto: Optional[str] = None, boton_url: Optional[str] = None) -> str:
    boton_html = ""
    if boton_texto and boton_url:
        boton_html = f"""
        <div style="text-align:center;margin:28px 0">
          <a href="{boton_url}"
             style="background:#8D191D;color:#fff;padding:12px 28px;border-radius:8px;
                    text-decoration:none;font-weight:600;font-size:14px;display:inline-block">
            {boton_texto}
          </a>
        </div>"""
    return f"""
    <!DOCTYPE html><html><body style="margin:0;padding:0;background:#f5f5f5;font-family:sans-serif">
    <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:12px;
                box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden">
      <div style="background:#8D191D;padding:24px 32px">
        <h1 style="color:#fff;margin:0;font-size:20px">SIPAM · USCO</h1>
        <p style="color:#D8CEA3;margin:4px 0 0;font-size:13px">Sistema Integrado de Prácticas y Monitorías</p>
      </div>
      <div style="padding:32px">
        <h2 style="color:#1f2937;margin:0 0 16px;font-size:18px">{titulo}</h2>
        <div style="color:#4b5563;font-size:14px;line-height:1.6">{cuerpo}</div>
        {boton_html}
        <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0">
        <p style="color:#9ca3af;font-size:12px;margin:0">
          Este correo fue generado automáticamente por SIPAM-USCO.
          Si no reconoces esta acción, ignóralo.
        </p>
      </div>
    </div></body></html>"""


def send_email(
    to: str,
    subject: str,
    titulo: str,
    cuerpo: str,
    boton_texto: Optional[str] = None,
    boton_url: Optional[str] = None,
) -> bool:
    """Envía un correo HTML. Retorna True si fue exitoso."""
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning("SMTP no configurado — email no enviado a %s", to)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[SIPAM] {subject}"
        msg["From"] = f"SIPAM-USCO <{settings.SMTP_FROM or settings.SMTP_USER}>"
        msg["To"] = to
        html = _build_html(titulo, cuerpo, boton_texto, boton_url)
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASS:
                server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(msg["From"], [to], msg.as_string())
        logger.info("Email enviado a %s — %s", to, subject)
        return True
    except Exception as exc:
        logger.error("Error enviando email a %s: %s", to, exc)
        return False


def send_notification_email(to: str, titulo: str, mensaje: str) -> bool:
    return send_email(to, titulo, titulo, f"<p>{mensaje}</p>")


def send_password_reset_email(to: str, nombre: str, reset_url: str) -> bool:
    cuerpo = f"""
    <p>Hola <strong>{nombre}</strong>,</p>
    <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en SIPAM-USCO.</p>
    <p>Haz clic en el botón de abajo para crear una nueva contraseña.
       El enlace es válido por <strong>30 minutos</strong> y solo se puede usar una vez.</p>
    <p style="color:#6b7280;font-size:12px">Si no solicitaste este cambio, ignora este mensaje.</p>"""
    return send_email(
        to, "Restablece tu contraseña",
        "Restablecer contraseña",
        cuerpo,
        boton_texto="Crear nueva contraseña",
        boton_url=reset_url,
    )


def send_convocatoria_abierta_email(to: str, nombre: str, titulo_conv: str, fecha_cierre: str, url: str) -> bool:
    cuerpo = f"""
    <p>Hola <strong>{nombre}</strong>,</p>
    <p>Se ha abierto una nueva convocatoria de monitoría:</p>
    <p style="background:#fef2f2;border-left:4px solid #8D191D;padding:12px 16px;border-radius:4px">
      <strong>{titulo_conv}</strong><br>
      <span style="color:#6b7280;font-size:13px">Cierre de postulaciones: {fecha_cierre}</span>
    </p>
    <p>Ingresa a SIPAM para revisar los requisitos y postularte.</p>"""
    return send_email(
        to, f"Nueva convocatoria: {titulo_conv}",
        "Nueva convocatoria de monitoría",
        cuerpo,
        boton_texto="Ver convocatoria",
        boton_url=url,
    )
