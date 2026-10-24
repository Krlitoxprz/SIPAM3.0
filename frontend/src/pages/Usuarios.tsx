import { useState, useEffect, useCallback } from 'react';
import { Users, Plus, Search, ToggleLeft, ToggleRight, Loader2, X, ChevronDown, KeyRound, Copy, CheckCircle, ShieldAlert, ShieldCheck, FlaskConical } from 'lucide-react';
import { usuariosService, adminService } from '../services/api';
import { useSystemContext } from '../context/SystemContext';
import type { User, Rol } from '../types';

const ROL_LABEL: Record<Rol, string> = {
  admin: 'Administrador',
  estudiante: 'Estudiante',
  profesor: 'Profesor',
  jefe_programa: 'Jefe de Programa',
  decano: 'Decano de Facultad',
};

const ROL_COLOR: Record<Rol, string> = {
  admin: 'bg-purple-100 text-purple-700',
  estudiante: 'bg-blue-100 text-blue-700',
  profesor: 'bg-indigo-100 text-indigo-700',
  jefe_programa: 'bg-usco-vinotinto/10 text-usco-vinotinto',
  decano: 'bg-rose-100 text-rose-700',
};

const ROLES_OPTIONS: { value: Rol | ''; label: string }[] = [
  { value: '', label: 'Todos los roles' },
  { value: 'admin', label: 'Administradores' },
  { value: 'estudiante', label: 'Estudiantes' },
  { value: 'profesor', label: 'Profesores' },
  { value: 'jefe_programa', label: 'Jefe de Programa' },
  { value: 'decano', label: 'Decano' },
];

interface NuevoUsuarioForm {
  codigo: string;
  nombres: string;
  apellidos: string;
  email: string;
  cedula: string;
  password: string;
  rol: Rol;
  promedio: string;
  porcentaje_creditos: string;
  programa: string;
  sede: string;
}

const FORM_INICIAL: NuevoUsuarioForm = {
  codigo: '', nombres: '', apellidos: '', email: '',
  cedula: '', password: '', rol: 'estudiante',
  promedio: '', porcentaje_creditos: '', programa: '', sede: '',
};

export function Usuarios() {
  const { testingMode, refreshMode } = useSystemContext();
  const [usuarios, setUsuarios] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [rolFiltro, setRolFiltro] = useState<Rol | ''>('');
  const [toggling, setToggling] = useState<number | null>(null);
  const [sancionando, setSancionando] = useState<number | null>(null);
  const [togglingTest, setTogglingTest] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<NuevoUsuarioForm>(FORM_INICIAL);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [formError, setFormError] = useState('');
  const [resetting, setResetting] = useState<number | null>(null);
  const [resetResult, setResetResult] = useState<{ codigo: string; password: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const cargar = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params: Record<string, string> = {};
      if (rolFiltro) params.rol = rolFiltro;
      if (search.trim()) params.q = search.trim();
      const res = await usuariosService.getAll(params);
      setUsuarios(res.data);
    } catch {
      setError('No se pudo cargar la lista de usuarios.');
    } finally {
      setLoading(false);
    }
  }, [rolFiltro, search]);

  useEffect(() => {
    const t = setTimeout(cargar, 300);
    return () => clearTimeout(t);
  }, [cargar]);

  const handleToggleTestingMode = async () => {
    setTogglingTest(true);
    try {
      await adminService.setTestingMode(!testingMode);
      await refreshMode();
    } catch {
      setError('Error al cambiar el modo de prueba.');
    } finally {
      setTogglingTest(false);
    }
  };

  const handleReset = async (u: User) => {
    if (!window.confirm(`¿Restablecer contraseña de ${u.nombres} ${u.apellidos} (${u.codigo})?`)) return;
    setResetting(u.id);
    try {
      const res = await usuariosService.resetPassword(u.id);
      setResetResult({ codigo: u.codigo, password: res.data.nueva_password });
    } catch {
      setError('Error al restablecer la contraseña.');
    } finally {
      setResetting(null);
    }
  };

  const handleToggleSancionado = async (u: User) => {
    setSancionando(u.id);
    try {
      const res = await usuariosService.toggleSancionado(u.id);
      setUsuarios((prev) => prev.map((x) => (x.id === u.id ? res.data : x)));
    } catch {
      setError('Error al cambiar sanción disciplinaria.');
    } finally {
      setSancionando(null);
    }
  };

  const handleToggle = async (u: User) => {
    setToggling(u.id);
    try {
      const res = await usuariosService.toggleActivo(u.id);
      setUsuarios((prev) => prev.map((x) => (x.id === u.id ? res.data : x)));
    } catch {
      setError('Error al cambiar estado del usuario.');
    } finally {
      setToggling(null);
    }
  };

  const handleCrear = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password.length < 8) {
      setFormError('La contraseña debe tener al menos 8 caracteres.');
      return;
    }
    setSaving(true);
    setFormError('');
    try {
      const payload: Record<string, unknown> = {
        codigo: form.codigo.trim(),
        nombres: form.nombres.trim(),
        apellidos: form.apellidos.trim(),
        email: form.email.trim(),
        cedula: form.cedula.trim(),
        password: form.password,
        rol: form.rol,
        programa: form.programa.trim() || null,
        sede: form.sede.trim() || null,
      };
      if (form.rol === 'estudiante') {
        if (form.promedio) payload.promedio = parseFloat(form.promedio);
        if (form.porcentaje_creditos) payload.porcentaje_creditos = parseFloat(form.porcentaje_creditos);
      }
      await usuariosService.create(payload);
      setShowModal(false);
      setForm(FORM_INICIAL);
      cargar();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(msg || 'Error al crear el usuario.');
    } finally {
      setSaving(false);
    }
  };

  const activos = usuarios.filter((u) => u.is_active).length;

  return (
    <div className="space-y-5">

      {/* ── BANNER MODO DE PRUEBA ────────────────────────────────────────── */}
      <div className={`rounded-2xl border-2 px-5 py-4 flex items-center gap-4 transition-colors ${
        testingMode
          ? 'border-amber-400 bg-amber-50'
          : 'border-gray-200 bg-white'
      }`}>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
          testingMode ? 'bg-amber-400 text-white' : 'bg-gray-100 text-gray-500'
        }`}>
          <FlaskConical size={20} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-gray-800">
            Modo de prueba &nbsp;
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
              testingMode ? 'bg-amber-200 text-amber-800' : 'bg-gray-100 text-gray-500'
            }`}>{testingMode ? 'ACTIVO' : 'INACTIVO'}</span>
          </p>
          <p className="text-xs text-gray-500 mt-0.5">
            {testingMode
              ? '⚠️ Restricciones desactivadas — cualquier fecha y quórum son válidos. Recuerda desactivar antes de producción.'
              : 'Actívalo para hacer pruebas sin restricciones de anticipación (30 días), semanas de calendario, ventana de consentimiento y días mínimos de convocatoria.'}
          </p>
        </div>
        <button
          onClick={handleToggleTestingMode}
          disabled={togglingTest}
          className={`shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold border-2 transition-colors disabled:opacity-60 ${
            testingMode
              ? 'border-amber-400 bg-amber-400 text-white hover:bg-amber-500'
              : 'border-gray-300 bg-white text-gray-700 hover:border-usco-vinotinto hover:text-usco-vinotinto'
          }`}>
          {togglingTest
            ? <Loader2 size={15} className="animate-spin" />
            : testingMode ? <ToggleRight size={18} /> : <ToggleLeft size={18} />}
          {testingMode ? 'Desactivar' : 'Activar'}
        </button>
      </div>

      {/* Modal: resultado reset password */}
      {resetResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
                <KeyRound size={18} className="text-emerald-600" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-gray-800">Contraseña restablecida</h3>
                <p className="text-xs text-gray-400">Usuario: {resetResult.codigo}</p>
              </div>
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 mb-4 flex items-center justify-between gap-3">
              <code className="text-base font-bold text-usco-vinotinto tracking-widest">{resetResult.password}</code>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(resetResult.password);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                }}
                className="shrink-0 text-gray-400 hover:text-usco-vinotinto transition-colors">
                {copied ? <CheckCircle size={16} className="text-emerald-500" /> : <Copy size={16} />}
              </button>
            </div>
            <p className="text-xs text-amber-600 mb-4">⚠️ Copia esta contraseña temporal y compártela al usuario de forma segura. No se podrá recuperar después de cerrar esta ventana.</p>
            <button onClick={() => { setResetResult(null); setCopied(false); }}
              className="w-full py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90">
              Entendido
            </button>
          </div>
        </div>
      )}

      {/* Encabezado */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Gestión de Usuarios</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {usuarios.length} usuario(s) · {activos} activo(s)
          </p>
        </div>
        <button
          onClick={() => { setShowModal(true); setFormError(''); setForm(FORM_INICIAL); }}
          className="flex items-center gap-2 bg-usco-vinotinto text-white text-sm font-semibold px-4 py-2.5 rounded-lg hover:bg-usco-vinotinto/90 transition-colors"
        >
          <Plus size={16} />
          Nuevo Usuario
        </button>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar por código, nombre o email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30"
          />
        </div>
        <div className="relative">
          <select
            value={rolFiltro}
            onChange={(e) => setRolFiltro(e.target.value as Rol | '')}
            className="appearance-none pl-3 pr-8 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white"
          >
            {ROLES_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
        </div>
      </div>

      {/* Error global */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Tabla */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16 text-gray-400">
            <Loader2 size={28} className="animate-spin mr-2" /> Cargando usuarios...
          </div>
        ) : usuarios.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <Users size={40} className="mx-auto mb-2 opacity-40" />
            <p className="font-medium">No se encontraron usuarios</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Código</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Nombre</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Email</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Rol</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Programa</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">Promedio / Créd.</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600">Estado</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600">Sanción</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {usuarios.map((u) => (
                  <tr key={u.id} className={`hover:bg-gray-50 transition-colors ${!u.is_active ? 'opacity-50' : ''}`}>
                    <td className="px-4 py-3 font-mono text-xs text-gray-700 font-medium">{u.codigo}</td>
                    <td className="px-4 py-3 text-gray-800 font-medium">
                      {u.nombres} {u.apellidos}
                      <span className="block text-xs text-gray-400 font-normal">{u.cedula}</span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{u.email}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-semibold px-2 py-1 rounded-full ${ROL_COLOR[u.rol]}`}>
                        {ROL_LABEL[u.rol]}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{u.programa ?? '—'}</td>
                    <td className="px-4 py-3 text-xs text-gray-600">
                      {u.rol === 'estudiante' ? (
                        <span>
                          {u.promedio != null ? `${u.promedio.toFixed(2)}` : '—'}
                          <span className="text-gray-400"> / </span>
                          {u.porcentaje_creditos != null ? `${u.porcentaje_creditos}%` : '—'}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => handleToggle(u)}
                        disabled={toggling === u.id}
                        title={u.is_active ? 'Desactivar' : 'Activar'}
                        className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors disabled:opacity-40 hover:bg-gray-100"
                      >
                        {toggling === u.id ? (
                          <Loader2 size={15} className="animate-spin text-gray-400" />
                        ) : u.is_active ? (
                          <ToggleRight size={20} className="text-emerald-500" />
                        ) : (
                          <ToggleLeft size={20} className="text-gray-400" />
                        )}
                        <span className={u.is_active ? 'text-emerald-600' : 'text-gray-400'}>
                          {u.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                      </button>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {u.rol === 'estudiante' ? (
                        <button
                          onClick={() => handleToggleSancionado(u)}
                          disabled={sancionando === u.id}
                          title={u.sancionado_disciplinariamente ? 'Levantar sanción disciplinaria (Art.4.c)' : 'Sancionar disciplinariamente (Art.4.c)'}
                          className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors disabled:opacity-40 hover:bg-gray-100"
                        >
                          {sancionando === u.id ? (
                            <Loader2 size={15} className="animate-spin text-gray-400" />
                          ) : u.sancionado_disciplinariamente ? (
                            <ShieldAlert size={15} className="text-red-500" />
                          ) : (
                            <ShieldCheck size={15} className="text-emerald-500" />
                          )}
                          <span className={u.sancionado_disciplinariamente ? 'text-red-600' : 'text-emerald-600'}>
                            {u.sancionado_disciplinariamente ? 'Sancionado' : 'Sin sanción'}
                          </span>
                        </button>
                      ) : <span className="text-xs text-gray-300">—</span>}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => handleReset(u)}
                        disabled={resetting === u.id}
                        title="Restablecer contraseña"
                        className="inline-flex items-center gap-1 text-xs font-medium text-gray-400 hover:text-amber-600 px-2 py-1.5 rounded-lg hover:bg-amber-50 transition-colors disabled:opacity-40"
                      >
                        {resetting === u.id ? <Loader2 size={14} className="animate-spin" /> : <KeyRound size={14} />}
                        Reset
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal crear usuario */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-gray-100">
              <h2 className="text-base font-bold text-gray-800">Nuevo Usuario</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCrear} className="px-6 py-4 space-y-3">
              {formError && (
                <div className="bg-red-50 border border-red-200 text-red-700 text-xs px-3 py-2 rounded-lg">
                  {formError}
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Código *</label>
                  <input required value={form.codigo}
                    maxLength={20}
                    onChange={(e) => setForm({ ...form, codigo: e.target.value.replace(/\s/g, '').toUpperCase() })}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Cédula *</label>
                  <input required value={form.cedula}
                    inputMode="numeric"
                    maxLength={12}
                    pattern="[0-9]{5,12}"
                    title="Solo números, entre 5 y 12 dígitos"
                    onChange={(e) => setForm({ ...form, cedula: e.target.value.replace(/\D/g, '').slice(0, 12) })}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Nombres *</label>
                  <input required value={form.nombres} onChange={(e) => setForm({ ...form, nombres: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Apellidos *</label>
                  <input required value={form.apellidos} onChange={(e) => setForm({ ...form, apellidos: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Email *</label>
                <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Contraseña *</label>
                  <input required type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Rol *</label>
                  <select required value={form.rol} onChange={(e) => setForm({ ...form, rol: e.target.value as Rol })}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
                    <option value="estudiante">Estudiante</option>
                    <option value="profesor">Profesor</option>
                    <option value="jefe_programa">Jefe de Programa</option>
                    <option value="decano">Decano de Facultad</option>
                    {/* Rol admin no es creatable por esta interfaz */}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Programa</label>
                  <select value={form.programa} onChange={(e) => setForm({ ...form, programa: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
                    <option value="">Seleccione...</option>
                    <option value="Ingeniería Agroindustrial">Ingeniería Agroindustrial</option>
                    <option value="Ingeniería Agrícola">Ingeniería Agrícola</option>
                    <option value="Ingeniería Civil">Ingeniería Civil</option>
                    <option value="Ingeniería de Petróleos">Ingeniería de Petróleos</option>
                    <option value="Ingeniería de Software">Ingeniería de Software</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Sede</label>
                  <select value={form.sede} onChange={(e) => setForm({ ...form, sede: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
                    <option value="">Seleccione...</option>
                    <option value="Neiva">Neiva</option>
                    <option value="La Plata">La Plata</option>
                    <option value="Garzón">Garzón</option>
                    <option value="Pitalito">Pitalito</option>
                  </select>
                </div>
              </div>

              {form.rol === 'estudiante' && (
                <div className="grid grid-cols-2 gap-3 pt-1 border-t border-gray-100">
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1">Promedio (0–5)</label>
                    <input type="number" min="0" max="5" step="0.01"
                      value={form.promedio} onChange={(e) => setForm({ ...form, promedio: e.target.value })}
                      className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1">% Créditos aprobados</label>
                    <input type="number" min="0" max="100" step="0.1"
                      value={form.porcentaje_creditos} onChange={(e) => setForm({ ...form, porcentaje_creditos: e.target.value })}
                      className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-3 border-t border-gray-100">
                <button type="button" onClick={() => setShowModal(false)}
                  className="flex-1 py-2.5 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  Cancelar
                </button>
                <button type="submit" disabled={saving}
                  className="flex-1 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 transition-colors disabled:opacity-60 flex items-center justify-center gap-2">
                  {saving && <Loader2 size={15} className="animate-spin" />}
                  {saving ? 'Guardando...' : 'Crear Usuario'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
