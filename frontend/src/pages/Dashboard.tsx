import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, ClipboardList, MapPin, DollarSign, TrendingUp, CheckCircle, Clock, Loader2, ArrowRight, AlertTriangle, ShieldCheck, Users, UserCheck, UserX, Activity, Database, GraduationCap, Briefcase, Settings } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend, RadialBarChart, RadialBar } from 'recharts';
import { useAuthContext } from '../context/AuthContext';
import { convocatoriasService, postulacionesService, practicasService, presupuestoService, configuracionService, usuariosService, reportesService } from '../services/api';
import type { Presupuesto, User as UserType } from '../types';

function formatCOP(v: number) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v);
}

interface Stats {
  convocatorias: number;
  postulaciones: number;
  practicas: number;
  presupuesto: Presupuesto | null;
  periodoActivo: string;
  convByEstado: { estado: string; total: number }[];
}

interface AdminStats {
  totalUsuarios: number;
  activos: number;
  inactivos: number;
  porRol: { rol: string; label: string; total: number; color: string }[];
  totalConvocatorias: number;
  totalPracticas: number;
  pracByEstado: { estado: string; label: string; total: number; color: string }[];
  monitoriasByEstado: { estado: string; total: number }[];
  pracActivas: number;
  pracEnEjecucion: number;
  pracFinalizadas: number;
  periodoActivo: string;
  auditLog: { id: number; usuario: string; codigo: string; accion: string; detalle: string; created_at: string | null }[];
}

interface MateriaItem {
  id: number; codigo: string; nombre: string; semestre: number; creditos: number;
  total_estudiantes: number;
  estudiantes: { id: number; codigo: string; nombre: string; promedio: number | null; apto_monitoria: boolean }[];
}

function StatCard({ label, value, icon, color }: { label: string; value: string | number; icon: React.ReactNode; color: string }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex items-center gap-4">
      <div className={`${color} text-white rounded-xl p-3 shrink-0`}>{icon}</div>
      <div>
        <p className="text-2xl font-bold text-gray-800">{value}</p>
        <p className="text-xs text-gray-500 mt-0.5 leading-tight">{label}</p>
      </div>
    </div>
  );
}

const ROL_META: Record<string, { label: string; color: string; barColor: string }> = {
  admin:              { label: 'Admin',          color: 'bg-purple-100 text-purple-700',            barColor: '#7C3AED' },
  estudiante:         { label: 'Estudiantes',    color: 'bg-blue-100 text-blue-700',               barColor: '#3B82F6' },
  profesor:           { label: 'Profesores',     color: 'bg-indigo-100 text-indigo-700',           barColor: '#6366F1' },
  jefe_programa:      { label: 'Jefe Prog.',     color: 'bg-usco-vinotinto/10 text-usco-vinotinto', barColor: '#8D191D' },
  decano:             { label: 'Decano',          color: 'bg-rose-100 text-rose-700',               barColor: '#E11D48' },
};

const ESTADO_PRACTICA_META: Record<string, { label: string; color: string }> = {
  borrador:             { label: 'Borrador',            color: '#9CA3AF' },
  solicitada:           { label: 'Solicitada',          color: '#3B82F6' },
  pendiente_quorum:     { label: 'Pend. Quórum',        color: '#F59E0B' },
  aprobada_curriculo:   { label: 'Aprobada Comité',     color: '#06B6D4' },
  aprobada_facultad:    { label: 'Avalada Facultad',    color: '#8B5CF6' },
  aprobado_transporte:  { label: 'Aprob. Vicerrect.',   color: '#6366F1' },
  en_ejecucion:         { label: 'En Ejecución',        color: '#10B981' },
  finalizada:           { label: 'Finalizada',          color: '#059669' },
  rechazada:            { label: 'Rechazada',           color: '#EF4444' },
};

const ACCION_LABEL: Record<string, string> = {
  login_exitoso: 'Inicio de sesión', login_fallido: 'Login fallido',
  activar_usuario: 'Usuario activado', desactivar_usuario: 'Usuario desactivado',
  reset_password: 'Contraseña restablecida',
};

export function Dashboard() {
  const { user } = useAuthContext();
  const [stats, setStats] = useState<Stats>({ convocatorias: 0, postulaciones: 0, practicas: 0, presupuesto: null, periodoActivo: '', convByEstado: [] });
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null);
  const [misMaterias, setMisMaterias] = useState<MateriaItem[]>([]);
  const [expandedMat, setExpandedMat] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    async function cargar() {
      setLoading(true);
      try {
        // ── Admin: carga completa del sistema ──────────────────────────────
        if (user!.rol === 'admin') {
          const [usrR, convR, pracR, auditR] = await Promise.allSettled([
            usuariosService.getAll(),
            convocatoriasService.getAll(),
            practicasService.getAll(),
            reportesService.getAuditLog(12),
          ]);
          let periodoActivo = '';
          try { const calR = await configuracionService.getPeriodoActivo(); periodoActivo = (calR.data as { periodo_academico: string }).periodo_academico; } catch { /* sin periodo */ }

          const usuarios: UserType[] = usrR.status === 'fulfilled' ? usrR.value.data : [];
          const activos  = usuarios.filter(u => u.is_active).length;
          const rolMap: Record<string, number> = {};
          usuarios.forEach(u => { rolMap[u.rol] = (rolMap[u.rol] ?? 0) + 1; });
          const porRol = Object.entries(rolMap).map(([rol, total]) => ({
            rol, total,
            label: ROL_META[rol]?.label ?? rol,
            color: ROL_META[rol]?.color ?? 'bg-gray-100 text-gray-600',
          })).sort((a, b) => b.total - a.total);

          const convs = convR.status === 'fulfilled' ? convR.value.data : [];
          const pracs = pracR.status === 'fulfilled' ? pracR.value.data : [];
          const logs  = auditR.status === 'fulfilled' ? auditR.value.data : [];

          const pracByEstado = Object.entries(
            (pracs as { estado: string }[]).reduce((acc: Record<string, number>, p) => {
              acc[p.estado] = (acc[p.estado] ?? 0) + 1; return acc;
            }, {})
          ).map(([estado, total]) => ({
            estado, total,
            label: ESTADO_PRACTICA_META[estado]?.label ?? estado,
            color: ESTADO_PRACTICA_META[estado]?.color ?? '#9CA3AF',
          })).sort((a, b) => b.total - a.total);

          const monitoriasByEstado = Object.entries(
            (convs as { estado: string }[]).reduce((acc: Record<string, number>, c) => {
              acc[c.estado] = (acc[c.estado] ?? 0) + 1; return acc;
            }, {})
          ).map(([estado, total]) => ({ estado, total }));

          const pracActivas = (pracs as { estado: string }[]).filter(p =>
            !['borrador','rechazada','finalizada'].includes(p.estado)).length;
          const pracEnEjecucion = (pracs as { estado: string }[]).filter(p => p.estado === 'en_ejecucion').length;
          const pracFinalizadas = (pracs as { estado: string }[]).filter(p => p.estado === 'finalizada').length;

          setAdminStats({
            totalUsuarios: usuarios.length,
            activos,
            inactivos: usuarios.length - activos,
            porRol,
            totalConvocatorias: (convs as unknown[]).length,
            totalPracticas: (pracs as unknown[]).length,
            pracByEstado,
            monitoriasByEstado,
            pracActivas,
            pracEnEjecucion,
            pracFinalizadas,
            periodoActivo,
            auditLog: (logs as { id: number; usuario: string; codigo: string; accion: string; detalle: string; created_at: string | null }[]),
          });
          return;
        }

        // ── Otros roles ────────────────────────────────────────────────────
        const [convR, pracR] = await Promise.all([
          convocatoriasService.getAll(),
          practicasService.getAll(),
        ]);
        let postCount = 0;
        let presupuesto: Presupuesto | null = null;
        let periodoActivo = '';

        if (user!.rol === 'estudiante') {
          const postR = await postulacionesService.getMias();
          postCount = postR.data.length;
        }
        if (user!.rol === 'profesor') {
          try { const r = await convocatoriasService.getMisMaterias(); setMisMaterias(r.data); } catch { /* silencioso */ }
        }
        if (['jefe_programa', 'decano', 'admin'].includes(user!.rol)) {
          try {
            const presR = await presupuestoService.getActual();
            presupuesto = presR.data;
            periodoActivo = presR.data.periodo_academico;
          } catch { presupuesto = null; }
        }
        if (!periodoActivo) {
          try {
            const calR = await configuracionService.getPeriodoActivo();
            periodoActivo = (calR.data as { periodo_academico: string }).periodo_academico;
          } catch { /* sin periodo activo */ }
        }

        const estadoMap: Record<string, number> = {};
        (convR.data as { estado: string }[]).forEach(c => {
          estadoMap[c.estado] = (estadoMap[c.estado] ?? 0) + 1;
        });
        const convByEstado = Object.entries(estadoMap).map(([estado, total]) => ({ estado, total }));

        setStats({
          convocatorias: convR.data.length,
          postulaciones: postCount,
          practicas: pracR.data.length,
          presupuesto,
          periodoActivo,
          convByEstado,
        });
      } catch { /* silencioso */ }
      finally { setLoading(false); }
    }
    cargar();
  }, [user]);

  if (!user) return null;

  const rolTitles: Record<string, { title: string; subtitle: string }> = {
    admin: { title: 'Panel de Administración', subtitle: 'Visión completa del sistema SIPAM — gestión de usuarios y actividad.' },
    estudiante: { title: 'Mi Panel', subtitle: 'Consulta convocatorias abiertas y el estado de tus postulaciones.' },
    profesor: { title: 'Panel del Profesor', subtitle: 'Gestiona convocatorias de monitoría y registra rutas de prácticas.' },
    jefe_programa: { title: 'Panel — Jefe de Programa', subtitle: 'Abre convocatorias, aprueba solicitudes y visualiza el presupuesto.' },
    decano: { title: 'Panel — Decano de Facultad', subtitle: 'Supervisa, imprime formularios FO-14/FO-15 y envía a consejo académico.' },
  };

  const { title, subtitle } = rolTitles[user.rol] ?? { title: 'Dashboard', subtitle: '' };
  const p = stats.presupuesto;

  // ── ADMIN DASHBOARD ────────────────────────────────────────────────────────
  if (user.rol === 'admin') {
    const a = adminStats;
    const fmtDate = (iso: string | null) => {
      if (!iso) return '—';
      const d = new Date(iso);
      return d.toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: '2-digit' }) + ' '
           + d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
    };
    return (
      <div className="space-y-6">
        {/* Cabecera */}
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <div className="bg-purple-100 rounded-xl p-2">
                <ShieldCheck size={22} className="text-purple-700" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-800">Panel de Administración</h1>
                <p className="text-sm text-gray-500">SIPAM-USCO · Superusuario: <span className="font-semibold text-purple-700">{user.codigo}</span></p>
              </div>
            </div>
          </div>
          <Link to="/usuarios"
            className="flex items-center gap-2 bg-usco-vinotinto text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-usco-vinotinto/90 transition-colors">
            <Users size={16} /> Gestionar usuarios
          </Link>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 size={28} className="animate-spin text-usco-vinotinto" />
          </div>
        ) : (
          <>
            {/* KPI Row — Usuarios */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
              {[
                { label: 'Usuarios totales',   value: a?.totalUsuarios ?? 0, icon: <Users size={20} />,     color: 'bg-usco-vinotinto' },
                { label: 'Cuentas activas',    value: a?.activos ?? 0,       icon: <UserCheck size={20} />, color: 'bg-emerald-600' },
                { label: 'Cuentas inactivas',  value: a?.inactivos ?? 0,     icon: <UserX size={20} />,    color: a?.inactivos ? 'bg-red-500' : 'bg-gray-400' },
                { label: 'Estudiantes',        value: a?.porRol.find(r => r.rol === 'estudiante')?.total ?? 0, icon: <GraduationCap size={20} />, color: 'bg-blue-500' },
                { label: 'Profesores',         value: a?.porRol.find(r => r.rol === 'profesor')?.total ?? 0,   icon: <Briefcase size={20} />,     color: 'bg-indigo-500' },
              ].map(item => (
                <div key={item.label} className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex items-center gap-3">
                  <div className={`${item.color} text-white rounded-lg p-2 shrink-0`}>{item.icon}</div>
                  <div className="min-w-0">
                    <p className="text-xl font-bold text-gray-800">{item.value}</p>
                    <p className="text-xs text-gray-400 leading-tight">{item.label}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* KPI Row — Académico */}
            <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {[
                { label: 'Monitorías (convoc.)', value: a?.totalConvocatorias ?? 0,  icon: <BookOpen size={20} />,       color: 'bg-amber-500',   to: '/convocatorias' },
                { label: 'Prácticas totales',    value: a?.totalPracticas ?? 0,      icon: <MapPin size={20} />,         color: 'bg-usco-gris',   to: '/practicas' },
                { label: 'Prácticas activas',    value: a?.pracActivas ?? 0,         icon: <Activity size={20} />,       color: 'bg-cyan-600',    to: '/practicas' },
                { label: 'En ejecución',         value: a?.pracEnEjecucion ?? 0,     icon: <CheckCircle size={20} />,    color: 'bg-emerald-600', to: '/practicas' },
                { label: 'Finalizadas',          value: a?.pracFinalizadas ?? 0,     icon: <ClipboardList size={20} />,  color: 'bg-indigo-500',  to: '/practicas' },
              ].map(item => (
                <Link key={item.label} to={item.to} className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex items-center gap-3 hover:shadow-md transition-shadow">
                  <div className={`${item.color} text-white rounded-lg p-2 shrink-0`}>{item.icon}</div>
                  <div className="min-w-0">
                    <p className="text-xl font-bold text-gray-800">{item.value}</p>
                    <p className="text-xs text-gray-400 leading-tight">{item.label}</p>
                  </div>
                </Link>
              ))}
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* Usuarios por rol */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-4">Distribucón de usuarios por rol</h2>
                {a?.porRol && a.porRol.length > 0 ? (
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={a.porRol} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                      <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                      <Tooltip formatter={(v: unknown) => [`${v} usuarios`, 'Total']} />
                      <Bar dataKey="total" radius={[4, 4, 0, 0]} label={{ position: 'top', fontSize: 11 }}>
                        {a.porRol.map((entry) => (
                          <Cell key={entry.rol} fill={ROL_META[entry.rol]?.barColor ?? '#8D191D'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : <p className="text-sm text-gray-400 text-center py-10">Sin datos</p>}
              </div>

              {/* Activos vs Inactivos */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-4">Cuentas activas vs inactivas</h2>
                {a && a.totalUsuarios > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={150}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Activas', value: a.activos },
                            { name: 'Inactivas', value: a.inactivos },
                          ]}
                          dataKey="value" cx="50%" cy="50%" outerRadius={65} innerRadius={35}
                        >
                          <Cell fill="#10B981" />
                          <Cell fill="#EF4444" />
                        </Pie>
                        <Tooltip formatter={(v: unknown) => [`${v} cuentas`]} />
                        <Legend iconSize={10} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="flex justify-center gap-6 mt-2">
                      <div className="text-center">
                        <p className="text-xl font-bold text-emerald-600">{a.activos > 0 ? ((a.activos / a.totalUsuarios) * 100).toFixed(0) : 0}%</p>
                        <p className="text-xs text-gray-400">activas</p>
                      </div>
                      <div className="text-center">
                        <p className="text-xl font-bold text-gray-400">{a.inactivos > 0 ? ((a.inactivos / a.totalUsuarios) * 100).toFixed(0) : 0}%</p>
                        <p className="text-xs text-gray-400">inactivas</p>
                      </div>
                    </div>
                  </>
                ) : <p className="text-sm text-gray-400 text-center py-10">Sin datos</p>}
              </div>
            </div>

            {/* Prácticas & Monitorías Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* Prácticas por estado */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <MapPin size={16} className="text-usco-gris" />
                    <h2 className="text-sm font-semibold text-gray-700">Prácticas extramuros por estado</h2>
                  </div>
                  <Link to="/practicas" className="text-xs text-usco-vinotinto hover:underline font-medium">Ver todas →</Link>
                </div>
                {a?.pracByEstado && a.pracByEstado.length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={180}>
                      <BarChart data={a.pracByEstado} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                        <XAxis dataKey="label" tick={{ fontSize: 10 }} />
                        <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                        <Tooltip formatter={(v: unknown) => [`${v} práctica(s)`, 'Total']} />
                        <Bar dataKey="total" radius={[4, 4, 0, 0]} label={{ position: 'top', fontSize: 10 }}>
                          {a.pracByEstado.map(entry => (
                            <Cell key={entry.estado} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {a.pracByEstado.map(e => (
                        <span key={e.estado} className="flex items-center gap-1 text-[10px] text-gray-500">
                          <span className="w-2 h-2 rounded-full inline-block shrink-0" style={{ background: e.color }} />
                          {e.label}: <strong className="text-gray-700">{e.total}</strong>
                        </span>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center py-10 text-gray-300">
                    <MapPin size={28} className="mb-2" />
                    <p className="text-sm">Sin prácticas registradas</p>
                  </div>
                )}
              </div>

              {/* Monitorías por estado */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <BookOpen size={16} className="text-amber-500" />
                    <h2 className="text-sm font-semibold text-gray-700">Convocatorias de monitoría por estado</h2>
                  </div>
                  <Link to="/convocatorias" className="text-xs text-usco-vinotinto hover:underline font-medium">Ver todas →</Link>
                </div>
                {a?.monitoriasByEstado && a.monitoriasByEstado.length > 0 ? (
                  <ResponsiveContainer width="100%" height={210}>
                    <BarChart data={a.monitoriasByEstado} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                      <XAxis dataKey="estado" tick={{ fontSize: 10 }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                      <Tooltip formatter={(v: unknown) => [`${v} convocatoria(s)`, 'Total']} />
                      <Bar dataKey="total" radius={[4, 4, 0, 0]} label={{ position: 'top', fontSize: 10 }}>
                        {a.monitoriasByEstado.map((_, i) => (
                          <Cell key={i} fill={['#8D191D','#F59E0B','#10B981','#6366F1','#EF4444'][i % 5]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex flex-col items-center justify-center py-10 text-gray-300">
                    <BookOpen size={28} className="mb-2" />
                    <p className="text-sm">Sin convocatorias registradas</p>
                  </div>
                )}
              </div>
            </div>

            {/* Data Row: Audit Log + Estado del Sistema */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              {/* Audit Log */}
              <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Activity size={16} className="text-usco-vinotinto" />
                  <h2 className="text-sm font-semibold text-gray-700">Actividad Reciente del Sistema</h2>
                </div>
                {a?.auditLog && a.auditLog.length > 0 ? (
                  <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                    {a.auditLog.map(log => (
                      <div key={log.id} className="flex items-start gap-3 py-2 border-b border-gray-50 last:border-0">
                        <div className={`rounded-full w-2 h-2 mt-1.5 shrink-0 ${
                          log.accion.includes('fallido') ? 'bg-red-400' :
                          log.accion.includes('login') ? 'bg-emerald-400' :
                          log.accion.includes('desactivar') ? 'bg-orange-400' : 'bg-blue-400'
                        }`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <p className="text-xs font-semibold text-gray-700 truncate">
                              {ACCION_LABEL[log.accion] ?? log.accion}
                              {' '}<span className="font-normal text-gray-400">— {log.usuario}</span>
                              {log.codigo !== '—' && <span className="font-mono text-[10px] text-gray-300 ml-1">({log.codigo})</span>}
                            </p>
                            <span className="text-[10px] text-gray-300 shrink-0">{fmtDate(log.created_at)}</span>
                          </div>
                          {log.detalle && (
                            <p className="text-[11px] text-gray-400 mt-0.5 truncate">{log.detalle}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-10 text-gray-300">
                    <Activity size={28} className="mb-2" />
                    <p className="text-sm">Sin actividad registrada</p>
                  </div>
                )}
              </div>

              {/* Estado del Sistema */}
              <div className="space-y-4">
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Database size={16} className="text-usco-gris" />
                    <h2 className="text-sm font-semibold text-gray-700">Estado del Sistema</h2>
                  </div>
                  <div className="space-y-3">
                    {[
                      { label: 'SIPAM-USCO',       value: 'v1.0 — Activo',                         dot: 'bg-emerald-500' },
                      { label: 'Período activo',   value: a?.periodoActivo || '—',                  dot: a?.periodoActivo ? 'bg-emerald-500' : 'bg-gray-300' },
                      { label: 'Convocatorias',    value: String(a?.totalConvocatorias ?? 0),        dot: 'bg-blue-400' },
                      { label: 'Prácticas',       value: String(a?.totalPracticas ?? 0),            dot: 'bg-amber-400' },
                      { label: 'Usuarios totales', value: String(a?.totalUsuarios ?? 0),             dot: 'bg-usco-vinotinto' },
                      { label: 'Activos',          value: String(a?.activos ?? 0),                   dot: 'bg-emerald-500' },
                    ].map(row => (
                      <div key={row.label} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full shrink-0 ${row.dot}`} />
                          <span className="text-gray-500">{row.label}</span>
                        </div>
                        <span className="font-semibold text-gray-700">{row.value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-purple-50 rounded-xl border border-purple-100 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Settings size={14} className="text-purple-600" />
                    <p className="text-xs font-bold text-purple-700 uppercase tracking-wide">Acciones rápidas</p>
                  </div>
                  <div className="space-y-2">
                    {[
                      { to: '/usuarios',        label: 'Gestionar usuarios',       icon: <Users size={13} /> },
                      { to: '/practicas',       label: 'Ver prácticas',            icon: <MapPin size={13} /> },
                      { to: '/convocatorias',   label: 'Ver monitorías',           icon: <BookOpen size={13} /> },
                      { to: '/admin',           label: 'Panel de administración',  icon: <Database size={13} /> },
                      { to: '/perfil',          label: 'Mi perfil admin',          icon: <ShieldCheck size={13} /> },
                    ].map(item => (
                      <Link key={item.label} to={item.to}
                        className="flex items-center gap-2 text-xs font-medium text-purple-600 hover:text-purple-800 hover:underline py-0.5">
                        {item.icon} {item.label}
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    );
  }
  // ── FIN ADMIN DASHBOARD ────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">{title}</h1>
        <p className="text-gray-500 mt-1">{subtitle}</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 size={28} className="animate-spin text-usco-vinotinto" />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {user.rol === 'estudiante' && <>
            <StatCard label="Convocatorias Abiertas" value={stats.convocatorias} icon={<BookOpen size={24} />} color="bg-usco-vinotinto" />
            <StatCard label="Mis Postulaciones" value={stats.postulaciones} icon={<ClipboardList size={24} />} color="bg-usco-gris" />
            <StatCard label="Prácticas Activas" value={stats.practicas} icon={<MapPin size={24} />} color="bg-amber-500" />
            <StatCard label="Período Actual" value={stats.periodoActivo || '—'} icon={<CheckCircle size={24} />} color="bg-emerald-600" />
          </>}
          {user.rol === 'profesor' && <>
            <StatCard label="Mis Convocatorias" value={stats.convocatorias} icon={<BookOpen size={24} />} color="bg-usco-vinotinto" />
            <StatCard label="Prácticas Registradas" value={stats.practicas} icon={<MapPin size={24} />} color="bg-usco-gris" />
            <StatCard label="Período Activo" value={stats.periodoActivo || '—'} icon={<Clock size={24} />} color="bg-amber-500" />
            <StatCard label="Sede" value={user.sede ?? 'Neiva'} icon={<CheckCircle size={24} />} color="bg-emerald-600" />
          </>}
          {(['jefe_programa', 'decano', 'admin'].includes(user.rol)) && <>
            <StatCard label="Convocatorias" value={stats.convocatorias} icon={<BookOpen size={24} />} color="bg-usco-vinotinto" />
            <StatCard label="Prácticas Registradas" value={stats.practicas} icon={<MapPin size={24} />} color="bg-usco-gris" />
            <StatCard
              label={p?.monto_solicitado ? 'Presupuesto Aprobado' : 'Presupuesto Asignado'}
              value={p ? formatCOP(p.monto_total_asignado) : '—'}
              icon={<DollarSign size={24} />}
              color="bg-amber-500"
            />
            <StatCard
              label="Ejecutado %"
              value={p ? `${p.porcentaje_ejecutado}%` : '—'}
              icon={<TrendingUp size={24} />}
              color={p && p.porcentaje_ejecutado >= 85 ? 'bg-red-500' : 'bg-emerald-600'}
            />
          </>}
        </div>
      )}

      {/* Alerta: incremento de presupuesto pendiente */}
      {!loading && p?.monto_solicitado && (
        <Link to="/presupuesto" className="flex items-center gap-3 bg-amber-50 border border-amber-300 text-amber-800 rounded-xl px-5 py-3 hover:bg-amber-100 transition-colors">
          <AlertTriangle size={18} className="shrink-0" />
          <span className="text-sm font-semibold">
            Incremento de presupuesto pendiente — {p.periodo_academico}:
            {' '}<span className="font-bold">{formatCOP(p.monto_total_asignado)}</span>
            {' '}→ <span className="font-bold text-amber-900">{formatCOP(p.monto_solicitado)}</span>
            {' · Esperando aprobación.'}
          </span>
        </Link>
      )}

      {/* ─── SF-11: Gráfico de progreso académico (solo estudiante) ──────── */}
      {!loading && user.rol === 'estudiante' && (user.promedio != null || user.porcentaje_creditos != null) && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Perfil académico</h2>
          <div className="flex flex-col sm:flex-row items-center gap-6">
            {user.promedio != null && (
              <div className="flex flex-col items-center">
                <ResponsiveContainer width={120} height={120}>
                  <RadialBarChart cx="50%" cy="50%" innerRadius={35} outerRadius={55}
                    data={[{ name: 'Promedio', value: (user.promedio / 5) * 100, fill: user.promedio >= 3.5 ? '#10B981' : '#EF4444' }]}
                    startAngle={90} endAngle={-270}>
                    <RadialBar dataKey="value" cornerRadius={6} />
                    <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle"
                      className="text-sm" style={{ fontSize: 14, fontWeight: 700, fill: user.promedio >= 3.5 ? '#10B981' : '#EF4444' }}>
                      {user.promedio.toFixed(2)}
                    </text>
                  </RadialBarChart>
                </ResponsiveContainer>
                <p className="text-xs text-gray-400 mt-1">Promedio</p>
              </div>
            )}
            {user.porcentaje_creditos != null && (
              <div className="flex flex-col items-center">
                <ResponsiveContainer width={120} height={120}>
                  <RadialBarChart cx="50%" cy="50%" innerRadius={35} outerRadius={55}
                    data={[{ name: 'Créditos', value: user.porcentaje_creditos, fill: '#6366F1' }]}
                    startAngle={90} endAngle={-270}>
                    <RadialBar dataKey="value" cornerRadius={6} />
                    <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle"
                      style={{ fontSize: 14, fontWeight: 700, fill: '#6366F1' }}>
                      {user.porcentaje_creditos}%
                    </text>
                  </RadialBarChart>
                </ResponsiveContainer>
                <p className="text-xs text-gray-400 mt-1">Créditos aprobados</p>
              </div>
            )}
            <div className="flex-1 space-y-3 min-w-0">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-500">Promedio académico</span>
                  <span className={`font-bold ${(user.promedio ?? 0) >= 3.5 ? 'text-emerald-600' : 'text-red-600'}`}>{user.promedio?.toFixed(2) ?? '—'} / 5.0</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all" style={{ width: `${((user.promedio ?? 0) / 5) * 100}%`, background: (user.promedio ?? 0) >= 3.5 ? '#10B981' : '#EF4444' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-500">Créditos aprobados</span>
                  <span className="font-bold text-indigo-600">{user.porcentaje_creditos ?? 0}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full rounded-full bg-indigo-400 transition-all" style={{ width: `${user.porcentaje_creditos ?? 0}%` }} />
                </div>
              </div>
              <p className="text-xs text-gray-400">Período activo: <span className="font-semibold">{stats.periodoActivo || '—'}</span></p>
            </div>
          </div>
        </div>
      )}

      {/* ─── Widget: Mis Materias (solo profesor) ───────────────────────────────── */}
      {!loading && user.rol === 'profesor' && misMaterias.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen size={16} className="text-usco-vinotinto" />
              <h2 className="text-sm font-semibold text-gray-700">Mis materias asignadas</h2>
            </div>
            <span className="text-xs text-gray-400">{misMaterias.length} asignaturas · {misMaterias.reduce((s, m) => s + m.total_estudiantes, 0)} estudiantes</span>
          </div>
          <div className="divide-y divide-gray-50">
            {misMaterias.map(mat => (
              <div key={mat.id}>
                <button
                  onClick={() => setExpandedMat(expandedMat === mat.id ? null : mat.id)}
                  className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-gray-50 transition-colors text-left">
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] font-mono font-bold text-usco-vinotinto bg-usco-vinotinto/10 px-2 py-0.5 rounded">{mat.codigo}</span>
                    <div>
                      <p className="text-sm font-semibold text-gray-800">{mat.nombre}</p>
                      <p className="text-xs text-gray-400">Semestre {mat.semestre} · {mat.creditos} créditos</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-sm font-bold text-usco-vinotinto">{mat.total_estudiantes} estudiantes</span>
                    <span className="text-xs text-gray-300">{expandedMat === mat.id ? '▲' : '▼'}</span>
                  </div>
                </button>
                {expandedMat === mat.id && (
                  <div className="bg-gray-50 px-5 pb-3">
                    {mat.estudiantes.length === 0 ? (
                      <p className="text-xs text-gray-400 py-2">Sin estudiantes matriculados.</p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="text-gray-400 uppercase tracking-wide">
                              <th className="text-left py-2 pr-4">Código</th>
                              <th className="text-left py-2 pr-4">Nombre</th>
                              <th className="text-right py-2 pr-4">Promedio</th>
                              <th className="text-center py-2">Monitoría</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {mat.estudiantes.map(e => (
                              <tr key={e.id} className="hover:bg-white">
                                <td className="py-1.5 pr-4 font-mono text-gray-500">{e.codigo}</td>
                                <td className="py-1.5 pr-4 font-medium text-gray-700">{e.nombre}</td>
                                <td className={`py-1.5 pr-4 text-right font-bold ${
                                  (e.promedio ?? 0) >= 3.5 ? 'text-emerald-600' : 'text-red-500'
                                }`}>{e.promedio?.toFixed(2) ?? '—'}</td>
                                <td className="py-1.5 text-center">
                                  {e.apto_monitoria
                                    ? <span className="text-emerald-600 font-semibold">✓ Apto</span>
                                    : <span className="text-gray-400">—</span>}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ─── Charts ─────────────────────────────────────────────────────── */}
      {!loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Convocatorias por estado */}
          {stats.convByEstado.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-3">Convocatorias por estado</h2>
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={stats.convByEstado} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                  <XAxis dataKey="estado" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="total" radius={[4,4,0,0]}>
                    {stats.convByEstado.map((_, i) => (
                      <Cell key={i} fill={['#8D191D','#4E6470','#D8CEA3','#059669','#F59E0B'][i % 5]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          {/* Presupuesto dona */}
          {p && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-3">Distribución del presupuesto</h2>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Ejecutado', value: p.monto_ejecutado },
                      { name: 'Comprometido', value: p.monto_comprometido },
                      { name: 'Disponible', value: p.monto_disponible },
                    ]}
                    dataKey="value" cx="50%" cy="50%" outerRadius={60} innerRadius={30}
                  >
                    <Cell fill="#EF4444" />
                    <Cell fill="#F59E0B" />
                    <Cell fill="#10B981" />
                  </Pie>
                  <Tooltip formatter={(v: unknown) => formatCOP(Number(v))} />
                  <Legend iconSize={10} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-base font-semibold text-gray-700 mb-4">Accesos Rápidos</h2>
          <div className="space-y-2">
            {[
              { to: '/convocatorias', label: 'Ver convocatorias de monitoría', color: 'text-usco-vinotinto' },
              { to: '/practicas', label: 'Ver prácticas extramuros', color: 'text-usco-gris' },
              ...(user.rol === 'estudiante' ? [{ to: '/postulaciones', label: 'Mis postulaciones', color: 'text-emerald-600' }] : []),
              ...(user.rol === 'profesor' ? [{ to: '/evaluaciones', label: 'Mis evaluaciones y selección', color: 'text-indigo-600' }] : []),
              ...(['jefe_programa', 'decano', 'admin'].includes(user.rol) ? [{ to: '/presupuesto', label: 'Control presupuestal', color: 'text-amber-600' }] : []),
              ...(['jefe_programa', 'decano'].includes(user.rol) ? [{ to: '/configuracion', label: 'Configuración del sistema', color: 'text-gray-500' }] : []),
            ].map(item => (
              <Link key={item.to} to={item.to}
                className={`flex items-center gap-2 text-sm font-medium ${item.color} hover:underline py-1.5`}>
                <ArrowRight size={14} /> {item.label}
              </Link>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-base font-semibold text-gray-700 mb-4">Información del Sistema</h2>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Sistema</span>
              <span className="font-semibold text-gray-800">SIPAM-USCO v1.0</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Sede</span>
              <span className="font-semibold text-gray-800">{user.sede ?? 'Neiva'}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Programa</span>
              <span className="font-semibold text-gray-800 text-right max-w-48 truncate">
                {user.programa ?? 'Ingeniería de Software'}
              </span>
            </div>
            {user.promedio != null && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Promedio Académico</span>
                <span className={`font-bold ${user.promedio >= 3.5 ? 'text-emerald-600' : 'text-red-600'}`}>
                  {user.promedio.toFixed(2)}
                </span>
              </div>
            )}
            {user.porcentaje_creditos != null && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Créditos Aprobados</span>
                <span className="font-semibold text-gray-800">{user.porcentaje_creditos}%</span>
              </div>
            )}
            {p && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Disponible Presupuesto</span>
                <span className={`font-bold ${p.monto_disponible > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                  {formatCOP(p.monto_disponible)}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
