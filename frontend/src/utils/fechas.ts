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

/** Convierte un ISO almacenado (naive=UTC, o aware) al string local
 *  'YYYY-MM-DDTHH:MM' que espera un input datetime-local. */
export function isoUTCToLocalInput(s: string): string {
  const aware = /Z$|[+-]\d{2}:?\d{2}$/.test(s) ? s : `${s}Z`;
  const d = new Date(aware);
  if (isNaN(d.getTime())) return s.slice(0, 16);
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

/** 'YYYY-MM-DDTHH:MM' en UTC de hoy + n días.
 *  Úsalo para `min`/`max` de inputs datetime-local cuando el backend interpreta
 *  valores naive como UTC (convención de crear_practica). */
export function isoUTCDaysAhead(days: number): string {
  return new Date(Date.now() + days * 24 * 60 * 60 * 1000).toISOString().slice(0, 16);
}
