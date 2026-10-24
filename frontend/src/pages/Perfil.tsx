import { useState, useRef, useCallback } from 'react';
import {
  User, Mail, Lock, Save, CheckCircle, AlertCircle, Loader2, Shield,
  Camera, Phone, MapPin, GraduationCap, Calendar, TrendingUp, BookOpen,
  Award, Hash, Info, Linkedin, Github, FileText, Trash2, Globe,
} from 'lucide-react';
import { useAuthContext } from '../context/AuthContext';
import { perfilService } from '../services/api';

const ROL_LABEL: Record<string, string> = {
  estudiante: 'Estudiante',
  profesor: 'Profesor',
  jefe_programa: 'Jefe de Programa',
  decano: 'Decano de Facultad',
  admin: 'Administrador',
};

const ROL_COLOR: Record<string, string> = {
  estudiante: 'bg-blue-100 text-blue-700',
  profesor: 'bg-emerald-100 text-emerald-700',
  jefe_programa: 'bg-usco-vinotinto/10 text-usco-vinotinto',
  decano: 'bg-rose-100 text-rose-700',
  admin: 'bg-gray-100 text-gray-700',
};

type Tab = 'personal' | 'contacto' | 'seguridad';

const INPUT = 'w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white';
const ICON_INPUT = 'w-full pl-8 pr-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white';
const LABEL = 'block text-xs font-semibold text-gray-600 mb-1.5';

export function Perfil() {
  const { user, refreshUser } = useAuthContext();
  const [tab, setTab] = useState<Tab>('personal');
  const [saving, setSaving] = useState(false);
  const [uploadingFoto, setUploadingFoto] = useState(false);
  const [editingPersonal, setEditingPersonal] = useState(false);
  const [editingContacto, setEditingContacto] = useState(false);
  const [flash, setFlash] = useState<{ tipo: 'ok' | 'err'; texto: string } | null>(null);

  // ── Datos personales ───────────────────────────────────────────────────
  const [nombres, setNombres]     = useState(user?.nombres ?? '');
  const [apellidos, setApellidos] = useState(user?.apellidos ?? '');
  const [telefono, setTelefono]   = useState(user?.telefono ?? '');
  const [bio, setBio]             = useState(user?.bio ?? '');
  const [fechaNac, setFechaNac]   = useState(user?.fecha_nacimiento ?? '');
  const [ciudad, setCiudad]       = useState(user?.ciudad ?? '');

  // ── Contacto y redes ──────────────────────────────────────────────────
  const [email, setEmail] = useState(user?.email ?? '');
  const [emailPersonal, setEmailPersonal] = useState(user?.email_personal ?? '');
  const [linkedin, setLinkedin] = useState(user?.linkedin_url ?? '');
  const [github, setGithub] = useState(user?.github_url ?? '');

  // ── Seguro social (AP-INF-FO-05) ──────────────────────────────────────
  const [eps, setEps] = useState(user?.eps ?? '');
  const [arl, setArl] = useState(user?.arl ?? '');
  const [fondoPensiones, setFondoPensiones] = useState(user?.fondo_pensiones ?? '');

  // ── Seguridad ─────────────────────────────────────────────────────────
  const [passActual, setPassActual] = useState('');
  const [passNuevo, setPassNuevo] = useState('');
  const [passConfirm, setPassConfirm] = useState('');

  // ── Foto ──────────────────────────────────────────────────────────────
  const fileRef = useRef<HTMLInputElement>(null);
  const [avatarSrc, setAvatarSrc] = useState<string | null>(
    user?.foto_url
      ? (user.foto_url.startsWith('/uploads')
          ? `http://localhost:8000${user.foto_url}`
          : user.foto_url)
      : null
  );

  function showFlash(tipo: 'ok' | 'err', texto: string) {
    setFlash({ tipo, texto });
    setTimeout(() => setFlash(null), 4500);
  }

  const handleFotoChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';
    setUploadingFoto(true);
    try {
      const res = await perfilService.subirFoto(file);
      const fotoUrl = res.data?.foto_url;
      setAvatarSrc(fotoUrl
        ? (fotoUrl.startsWith('/uploads') ? `http://localhost:8000${fotoUrl}` : fotoUrl)
        : null);
      await refreshUser();
      showFlash('ok', 'Foto de perfil actualizada.');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al subir la foto.');
    } finally {
      setUploadingFoto(false);
    }
  }, [refreshUser]);

  async function eliminarFoto() {
    if (!avatarSrc) return;
    setUploadingFoto(true);
    try {
      await perfilService.eliminarFoto();
      setAvatarSrc(null);
      await refreshUser();
      showFlash('ok', 'Foto de perfil eliminada.');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al eliminar la foto.');
    } finally {
      setUploadingFoto(false);
    }
  }

  async function guardarPersonal(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await perfilService.actualizar({
        nombres: nombres || undefined,
        apellidos: apellidos || undefined,
        telefono: telefono || undefined,
        bio: bio || undefined,
        fecha_nacimiento: fechaNac || undefined,
        ciudad: ciudad || undefined,
        eps: eps || undefined,
        arl: arl || undefined,
        fondo_pensiones: fondoPensiones || undefined,
      });
      await refreshUser();
      setEditingPersonal(false);
      showFlash('ok', 'Datos personales actualizados.');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al guardar datos.');
    } finally { setSaving(false); }
  }

  async function guardarContacto(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await perfilService.actualizar({
        email: email || undefined,
        email_personal: emailPersonal || undefined,
        linkedin_url: linkedin || undefined,
        github_url: github || undefined,
      });
      await refreshUser();
      setEditingContacto(false);
      showFlash('ok', 'Información de contacto actualizada.');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al guardar contacto.');
    } finally { setSaving(false); }
  }

  async function cambiarPassword(e: React.FormEvent) {
    e.preventDefault();
    if (passNuevo !== passConfirm) { showFlash('err', 'Las contraseñas nuevas no coinciden.'); return; }
    if (passNuevo.length < 8) { showFlash('err', 'La nueva contraseña debe tener al menos 8 caracteres.'); return; }
    setSaving(true);
    try {
      await perfilService.actualizar({ password_actual: passActual, password_nuevo: passNuevo });
      setPassActual(''); setPassNuevo(''); setPassConfirm('');
      showFlash('ok', 'Contraseña actualizada correctamente.');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al cambiar contraseña.');
    } finally { setSaving(false); }
  }

  if (!user) return null;

  const initials = `${user.nombres?.[0] ?? ''}${user.apellidos?.[0] ?? ''}`.toUpperCase();
  const esEstudiante = user.rol === 'estudiante';
  const aptoPromedio = (user.promedio ?? 0) >= 3.5;
  const aptoCreditos = (user.porcentaje_creditos ?? 0) >= 30;
  const apto = aptoPromedio && aptoCreditos;
  const miembroDesde = user.created_at
    ? new Date(user.created_at).toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' })
    : '—';

  const TABS: { id: Tab; label: string; icon: React.FC<{ size?: number }> }[] = [
    { id: 'personal',  label: 'Datos personales', icon: User },
    { id: 'contacto',  label: 'Contacto y redes', icon: Globe },
    { id: 'seguridad', label: 'Seguridad',         icon: Shield },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {flash && (
        <div className={`flex items-center gap-3 rounded-xl px-5 py-3 text-sm font-semibold shadow-sm ${
          flash.tipo === 'ok'
            ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
            : 'bg-red-50 border border-red-200 text-red-700'
        }`}>
          {flash.tipo === 'ok' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {flash.texto}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-5 items-start">

        {/* ── Columna izquierda: avatar + info sistema ─────────────── */}
        <div className="space-y-4">

          {/* Avatar card */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex flex-col items-center text-center gap-4">
            <div className="relative">
              <div
                role="button" tabIndex={0}
                onClick={() => !uploadingFoto && fileRef.current?.click()}
                onKeyDown={e => e.key === 'Enter' && fileRef.current?.click()}
                className="w-24 h-24 rounded-full overflow-hidden bg-linear-to-br from-usco-vinotinto to-usco-vinotinto/70 flex items-center justify-center text-white text-3xl font-bold cursor-pointer ring-4 ring-white shadow-lg select-none"
              >
                {uploadingFoto
                  ? <Loader2 size={28} className="animate-spin opacity-80" />
                  : avatarSrc
                    ? <img src={avatarSrc} alt="Foto de perfil" className="w-full h-full object-cover" />
                    : <span>{initials}</span>
                }
              </div>
              <button type="button" onClick={() => fileRef.current?.click()}
                className="absolute -bottom-1 -right-1 w-8 h-8 bg-usco-vinotinto rounded-full flex items-center justify-center text-white shadow-md hover:bg-usco-vinotinto/90 transition-colors border-2 border-white"
                title="Cambiar foto">
                <Camera size={14} />
              </button>
              <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={handleFotoChange} />
            </div>

            <div className="w-full">
              <h2 className="text-base font-bold text-gray-800 leading-tight">{user.nombres} {user.apellidos}</h2>
              <p className="text-xs text-gray-400 mt-0.5 break-all">{user.email}</p>
              {user.email_personal && (
                <p className="text-xs text-gray-400 break-all">{user.email_personal}</p>
              )}
              {user.ciudad && (
                <p className="text-xs text-gray-400 flex items-center justify-center gap-1 mt-0.5">
                  <MapPin size={10} /> {user.ciudad}
                </p>
              )}
              {user.telefono && (
                <p className="text-xs text-gray-400 flex items-center justify-center gap-1 mt-0.5">
                  <Phone size={10} /> {user.telefono}
                </p>
              )}
              <div className="flex items-center justify-center gap-2 mt-2.5 flex-wrap">
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${ROL_COLOR[user.rol] ?? 'bg-gray-100 text-gray-700'}`}>
                  {ROL_LABEL[user.rol] ?? user.rol}
                </span>
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${user.is_active ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-500'}`}>
                  {user.is_active ? '● Activo' : '● Inactivo'}
                </span>
              </div>

              {user.bio && (
                <p className="text-xs text-gray-500 mt-3 text-left bg-gray-50 rounded-lg px-3 py-2 leading-relaxed italic">
                  "{user.bio}"
                </p>
              )}

              {/* Links redes sociales */}
              {(user.linkedin_url || user.github_url) && (
                <div className="flex items-center justify-center gap-3 mt-3">
                  {user.linkedin_url && (
                    <a href={user.linkedin_url} target="_blank" rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-700 transition-colors" title="LinkedIn">
                      <Linkedin size={18} />
                    </a>
                  )}
                  {user.github_url && (
                    <a href={user.github_url} target="_blank" rel="noopener noreferrer"
                      className="text-gray-700 hover:text-gray-900 transition-colors" title="GitHub">
                      <Github size={18} />
                    </a>
                  )}
                </div>
              )}
            </div>

            {avatarSrc && (
              <button type="button" onClick={eliminarFoto} disabled={uploadingFoto}
                className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-600 transition-colors disabled:opacity-50">
                <Trash2 size={11} /> Eliminar foto
              </button>
            )}
            {!avatarSrc && (
              <p className="text-[10px] text-gray-300 flex items-center gap-1">
                <Info size={10} /> JPEG, PNG o WEBP · máx. 5 MB
              </p>
            )}
          </div>

          {/* Info del sistema (solo lectura) */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h3 className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-3">Información del sistema</h3>
            <div className="space-y-2.5">
              {[
                { icon: Hash, label: 'Código', value: user.codigo },
                { icon: User, label: 'Cédula', value: user.cedula },
                ...(user.programa ? [{ icon: GraduationCap, label: 'Programa', value: user.programa }] : []),
                ...(user.sede ? [{ icon: MapPin, label: 'Sede', value: user.sede }] : []),
                { icon: Calendar, label: 'Registrado', value: miembroDesde },
              ].map(({ icon: Icon, label, value }) => (
                <div key={label} className="flex items-start justify-between gap-2 text-sm">
                  <span className="flex items-center gap-1.5 text-gray-400 shrink-0 text-xs">
                    <Icon size={12} /> {label}
                  </span>
                  <span className="font-semibold text-gray-700 text-xs text-right">{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Estadísticas académicas — solo estudiante */}
          {esEstudiante && (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
              <h3 className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-3">Estadísticas académicas</h3>
              <div className="space-y-4">
                {user.promedio != null && (
                  <div>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="flex items-center gap-1 text-gray-500"><TrendingUp size={11} /> Promedio</span>
                      <span className={`font-bold ${user.promedio >= 3.5 ? 'text-emerald-600' : 'text-red-500'}`}>
                        {user.promedio.toFixed(2)} / 5.0
                      </span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${user.promedio >= 3.5 ? 'bg-emerald-500' : 'bg-red-400'}`}
                        style={{ width: `${(user.promedio / 5) * 100}%` }} />
                    </div>
                  </div>
                )}
                {user.porcentaje_creditos != null && (
                  <div>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="flex items-center gap-1 text-gray-500"><BookOpen size={11} /> Créditos</span>
                      <span className={`font-bold ${user.porcentaje_creditos >= 30 ? 'text-emerald-600' : 'text-amber-500'}`}>
                        {user.porcentaje_creditos.toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${user.porcentaje_creditos >= 30 ? 'bg-emerald-500' : 'bg-amber-400'}`}
                        style={{ width: `${Math.min(user.porcentaje_creditos, 100)}%` }} />
                    </div>
                  </div>
                )}
                <div className={`flex items-center gap-2 text-xs font-semibold px-3 py-2.5 rounded-xl ${
                  apto ? 'bg-emerald-50 border border-emerald-100 text-emerald-700' : 'bg-amber-50 border border-amber-100 text-amber-700'
                }`}>
                  <Award size={14} />
                  {apto ? 'Apto para monitorías' : 'No cumple requisitos mínimos'}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ── Columna derecha: tabs + formularios ──────────────────── */}
        <div className="space-y-4">

          {/* Tabs */}
          <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit flex-wrap">
            {TABS.map(t => {
              const Icon = t.icon;
              return (
                <button key={t.id} onClick={() => setTab(t.id)}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                    tab === t.id ? 'bg-white shadow-sm text-usco-vinotinto' : 'text-gray-500 hover:text-gray-700'
                  }`}>
                  <Icon size={14} /> {t.label}
                </button>
              );
            })}
          </div>

          {/* ── Tab: Datos personales ─────────────────────────────── */}
          {tab === 'personal' && (
            <form onSubmit={guardarPersonal} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-5">
              {/* Cabecera con título y botón Editar */}
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-gray-700">Datos personales</h3>
                {!editingPersonal && (
                  <button type="button"
                    onClick={() => setEditingPersonal(true)}
                    className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-usco-vinotinto border border-usco-vinotinto/30 rounded-lg hover:bg-usco-vinotinto/5 transition-colors">
                    ✏️ Editar información
                  </button>
                )}
              </div>

              {/* ── Modo vista ─────────────────────── */}
              {!editingPersonal && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {([
                      ['Nombres', nombres],
                      ['Apellidos', apellidos],
                      ['Teléfono', telefono],
                      ['Ciudad', ciudad],
                      ['Fecha de nacimiento', fechaNac],
                    ] as [string, string][]).map(([lbl, val]) => (
                      <div key={lbl}>
                        <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-0.5">{lbl}</p>
                        <p className="text-sm text-gray-700 font-medium">{val || <span className="text-gray-300 italic">No ingresado</span>}</p>
                      </div>
                    ))}
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-0.5">Biografía</p>
                    <p className="text-sm text-gray-700">{bio || <span className="text-gray-300 italic">No ingresada</span>}</p>
                  </div>

                  {/* Seguro social — vista (solo estudiantes) */}
                  {esEstudiante && (user?.eps || user?.arl || user?.fondo_pensiones) && (
                    <div className="border-t border-gray-100 pt-4">
                      <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wide mb-2 flex items-center gap-1"><Shield size={11} /> Seguridad Social</p>
                      <div className="grid grid-cols-3 gap-4">
                        {[['EPS', user?.eps], ['ARL', user?.arl], ['F. Pensiones', user?.fondo_pensiones]].map(([lbl, val]) => (
                          <div key={lbl}>
                            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-0.5">{lbl}</p>
                            <p className="text-sm text-gray-700 font-medium">{val || <span className="text-gray-300 italic">No ingresado</span>}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* ── Modo edición ───────────────────── */}
              {editingPersonal && (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className={LABEL}>Nombres</label>
                      <input value={nombres} onChange={e => setNombres(e.target.value)}
                        className={INPUT} placeholder="Ej: Carlos Alberto" />
                    </div>
                    <div>
                      <label className={LABEL}>Apellidos</label>
                      <input value={apellidos} onChange={e => setApellidos(e.target.value)}
                        className={INPUT} placeholder="Ej: Ramírez Gutiérrez" />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className={LABEL}>Teléfono <span className="font-normal text-gray-400">(opcional)</span></label>
                      <div className="relative">
                        <Phone size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input type="tel" inputMode="numeric" value={telefono}
                          onChange={e => setTelefono(e.target.value.replace(/\D/g, '').slice(0, 10))}
                          placeholder="3001234567" maxLength={10} className={ICON_INPUT} />
                      </div>
                    </div>
                    <div>
                      <label className={LABEL}>Ciudad <span className="font-normal text-gray-400">(opcional)</span></label>
                      <div className="relative">
                        <MapPin size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input value={ciudad} onChange={e => setCiudad(e.target.value)}
                          placeholder="Ej: Neiva, Huila" className={ICON_INPUT} />
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className={LABEL}>Fecha de nacimiento <span className="font-normal text-gray-400">(opcional)</span></label>
                    <div className="relative">
                      <Calendar size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input type="date" value={fechaNac} onChange={e => setFechaNac(e.target.value)}
                        max={new Date().toISOString().split('T')[0]} className={ICON_INPUT} />
                    </div>
                  </div>

                  <div>
                    <label className={LABEL}>Biografía <span className="font-normal text-gray-400">(opcional · máx. 500 caracteres)</span></label>
                    <div className="relative">
                      <FileText size={14} className="absolute left-3 top-3 text-gray-400" />
                      <textarea value={bio} onChange={e => setBio(e.target.value.slice(0, 500))}
                        rows={3} maxLength={500} placeholder="Cuéntanos un poco sobre ti..."
                        className="w-full pl-8 pr-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 resize-none bg-white" />
                      <span className="absolute bottom-2 right-3 text-[10px] text-gray-300">{bio.length}/500</span>
                    </div>
                  </div>

                  {/* Seguro social — solo para estudiantes (AP-INF-FO-05) */}
                  {esEstudiante && (
                    <>
                      <div className="border-t border-gray-100 pt-4">
                        <p className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                          <Shield size={12} /> Seguridad Social (AP-INF-FO-05)
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                          <div>
                            <label className={LABEL}>EPS</label>
                            <input value={eps} onChange={e => setEps(e.target.value)}
                              placeholder="Ej: Sanitas, Nueva EPS…" className={INPUT} />
                          </div>
                          <div>
                            <label className={LABEL}>ARL</label>
                            <input value={arl} onChange={e => setArl(e.target.value)}
                              placeholder="Ej: Positiva, Sura…" className={INPUT} />
                          </div>
                          <div>
                            <label className={LABEL}>Fondo de Pensiones</label>
                            <input value={fondoPensiones} onChange={e => setFondoPensiones(e.target.value)}
                              placeholder="Ej: Porvenir, Colpensiones…" className={INPUT} />
                          </div>
                        </div>
                      </div>
                    </>
                  )}
                </>
              )}

              {/* Datos de sistema (solo lectura) */}
              <div className="bg-gray-50 rounded-xl p-4">
                <p className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-3">Datos del sistema (solo lectura)</p>
                <div className="grid grid-cols-2 gap-x-4 gap-y-2.5 text-sm">
                  {[
                    ['Código', user.codigo],
                    ['Cédula', user.cedula],
                    ...(user.programa ? [['Programa', user.programa]] : []),
                    ...(user.sede ? [['Sede', user.sede]] : []),
                    ...(esEstudiante && user.promedio != null ? [['Promedio', user.promedio.toFixed(2)]] : []),
                    ...(esEstudiante && user.porcentaje_creditos != null ? [['Créditos', `${user.porcentaje_creditos.toFixed(1)}%`]] : []),
                  ].map(([lbl, val]) => (
                    <div key={lbl}>
                      <p className="text-[10px] text-gray-400 uppercase font-semibold tracking-wide">{lbl}</p>
                      <p className="font-semibold text-gray-700 text-xs">{val}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Botones — solo en modo edición */}
              {editingPersonal && (
                <div className="flex justify-end gap-2">
                  <button type="button"
                    onClick={() => {
                      setNombres(user.nombres ?? ''); setApellidos(user.apellidos ?? '');
                      setTelefono(user.telefono ?? ''); setCiudad(user.ciudad ?? '');
                      setFechaNac(user.fecha_nacimiento ?? ''); setBio(user.bio ?? '');
                      setEps(user.eps ?? ''); setArl(user.arl ?? ''); setFondoPensiones(user.fondo_pensiones ?? '');
                      setEditingPersonal(false);
                    }}
                    className="px-4 py-2.5 text-sm font-semibold text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" disabled={saving}
                    className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 transition-colors">
                    {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                    Guardar cambios
                  </button>
                </div>
              )}
            </form>
          )}

          {/* ── Tab: Contacto y redes ─────────────────────────────── */}
          {tab === 'contacto' && (
            <form onSubmit={guardarContacto} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-5">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-gray-700">Contacto y redes sociales</h3>
                {!editingContacto && (
                  <button type="button"
                    onClick={() => setEditingContacto(true)}
                    className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-usco-vinotinto border border-usco-vinotinto/30 rounded-lg hover:bg-usco-vinotinto/5 transition-colors">
                    ✏️ Editar información
                  </button>
                )}
              </div>

              {/* ── Modo vista ─────────────────────── */}
              {!editingContacto && (
                <div className="space-y-4">
                  <div>
                    <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-0.5">Correo institucional</p>
                    <p className="text-sm text-gray-700 font-medium flex items-center gap-1.5"><Mail size={13} className="text-gray-400" />{email}</p>
                    <p className="text-[10px] text-gray-400 mt-0.5">Se usa para notificaciones del sistema.</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-0.5">Correo personal</p>
                    <p className="text-sm text-gray-700 font-medium flex items-center gap-1.5"><Mail size={13} className="text-gray-400" />{emailPersonal || <span className="text-gray-300 italic">No ingresado</span>}</p>
                  </div>
                  <div className="border-t border-gray-100 pt-3 space-y-2">
                    <div>
                      <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-0.5">LinkedIn</p>
                      {linkedin
                        ? <a href={linkedin} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline flex items-center gap-1.5"><Linkedin size={13} />{linkedin}</a>
                        : <p className="text-sm text-gray-300 italic">No ingresado</p>}
                    </div>
                    <div>
                      <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-0.5">GitHub</p>
                      {github
                        ? <a href={github} target="_blank" rel="noopener noreferrer" className="text-sm text-gray-700 hover:underline flex items-center gap-1.5"><Github size={13} />{github}</a>
                        : <p className="text-sm text-gray-300 italic">No ingresado</p>}
                    </div>
                  </div>
                </div>
              )}

              {/* ── Modo edición ───────────────────── */}
              {editingContacto && (
                <>
                  <div>
                    <label className={LABEL}>Correo institucional (USCO)</label>
                    <div className="relative">
                      <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                        placeholder="usuario@usco.edu.co" className={ICON_INPUT} />
                    </div>
                    <p className="text-[10px] text-gray-400 mt-1">Se usa para notificaciones del sistema.</p>
                  </div>
                  <div>
                    <label className={LABEL}>Correo personal <span className="font-normal text-gray-400">(opcional)</span></label>
                    <div className="relative">
                      <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input type="email" value={emailPersonal} onChange={e => setEmailPersonal(e.target.value)}
                        placeholder="tucorreo@gmail.com" className={ICON_INPUT} />
                    </div>
                    <p className="text-[10px] text-gray-400 mt-1">Alternativo para recuperación de contraseña.</p>
                  </div>
                  <div className="border-t border-gray-100 pt-4">
                    <p className="text-xs font-bold text-gray-500 mb-4 flex items-center gap-1.5">
                      <Globe size={13} /> Redes sociales <span className="font-normal text-gray-400">(opcional)</span>
                    </p>
                    <div className="space-y-4">
                      <div>
                        <label className={LABEL}>LinkedIn</label>
                        <div className="relative">
                          <Linkedin size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-blue-500" />
                          <input value={linkedin} onChange={e => setLinkedin(e.target.value)}
                            placeholder="https://linkedin.com/in/tu-perfil" className={ICON_INPUT} />
                        </div>
                      </div>
                      <div>
                        <label className={LABEL}>GitHub</label>
                        <div className="relative">
                          <Github size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-700" />
                          <input value={github} onChange={e => setGithub(e.target.value)}
                            placeholder="https://github.com/tu-usuario" className={ICON_INPUT} />
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              )}

              {editingContacto && (
                <div className="flex justify-end gap-2">
                  <button type="button"
                    onClick={() => {
                      setEmail(user.email ?? ''); setEmailPersonal(user.email_personal ?? '');
                      setLinkedin(user.linkedin_url ?? ''); setGithub(user.github_url ?? '');
                      setEditingContacto(false);
                    }}
                    className="px-4 py-2.5 text-sm font-semibold text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" disabled={saving}
                    className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 transition-colors">
                    {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                    Guardar cambios
                  </button>
                </div>
              )}
            </form>
          )}

          {/* ── Tab: Seguridad ────────────────────────────────────── */}
          {tab === 'seguridad' && (
            <form onSubmit={cambiarPassword} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-5">
              <div>
                <h3 className="text-sm font-bold text-gray-700 mb-1">Cambiar contraseña</h3>
                <p className="text-xs text-gray-400">Usa al menos 8 caracteres con letras y números.</p>
              </div>

              {([
                { label: 'Contraseña actual', value: passActual, set: setPassActual },
                { label: 'Nueva contraseña', value: passNuevo, set: setPassNuevo },
                { label: 'Confirmar nueva contraseña', value: passConfirm, set: setPassConfirm },
              ] as const).map(f => (
                <div key={f.label}>
                  <label className={LABEL}>{f.label}</label>
                  <div className="relative">
                    <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input type="password" required value={f.value}
                      onChange={e => f.set(e.target.value)}
                      className={ICON_INPUT} />
                  </div>
                </div>
              ))}

              <div className="bg-amber-50 border border-amber-100 rounded-xl p-3.5 text-xs text-amber-700 flex items-start gap-2">
                <AlertCircle size={14} className="mt-0.5 shrink-0" />
                <span>Tras cambiar la contraseña se recomienda cerrar sesión y volver a ingresar.</span>
              </div>

              <div className="flex justify-end">
                <button type="submit" disabled={saving}
                  className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 transition-colors">
                  {saving ? <Loader2 size={14} className="animate-spin" /> : <Lock size={14} />}
                  Cambiar contraseña
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
