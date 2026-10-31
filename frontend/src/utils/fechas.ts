/**
 * El backend guarda las fechas de negocio (inicio/fin de práctica, cierres de
 * convocatoria, vigencias) como datetimes naive con la hora local de Colombia.
 * `new Date('YYYY-MM-DD')` las parsea como UTC y en zona negativa las muestra
 * un día antes; estos helpers toman el día calendario almacenado tal cual.
 */
export function parseFechaLocal(iso: string | null | undefined): Date | null {
  if (!iso) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return null;
  return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
}

export function formatFecha(
  iso: string | null | undefined,
  opts?: Intl.DateTimeFormatOptions,
): string {
  const d = parseFechaLocal(iso);
  if (!d) return '—';
  return d.toLocaleDateString('es-CO', opts ?? { day: '2-digit', month: 'short', year: 'numeric' });
}

/** Hoy como 'YYYY-MM-DD' en hora local (no UTC) — para max/min de inputs date. */
export function hoyLocalISO(): string {
  const d = new Date();
  const mes = String(d.getMonth() + 1).padStart(2, '0');
  const dia = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${mes}-${dia}`;
}

/** Fecha+hora local 'YYYY-MM-DDTHH:MM' para inputs datetime-local. */
export function ahoraLocalISO(): string {
  const d = new Date();
  const mes = String(d.getMonth() + 1).padStart(2, '0');
  const dia = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${d.getFullYear()}-${mes}-${dia}T${h}:${min}`;
}

/** 'YYYY-MM-DDTHH:MM' local de hoy + n días — para min de inputs datetime-local. */
export function isoLocalDaysAhead(days: number): string {
  const d = new Date(Date.now() + days * 24 * 60 * 60 * 1000);
  const mes = String(d.getMonth() + 1).padStart(2, '0');
  const dia = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${d.getFullYear()}-${mes}-${dia}T${h}:${min}`;
}
