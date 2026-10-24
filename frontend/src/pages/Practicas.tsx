import { useState, useEffect, useCallback } from 'react';
import { MapPin, Plus, Trash2, Send, CheckCircle, AlertTriangle, DollarSign, Users, X, AlertCircle, Loader2 as Spin, Search, FileText, Truck, Clock, Edit2 } from 'lucide-react';
import type { Practica, EstadoPractica, Asignatura } from '../types';
import { practicasService, convocatoriasService, configuracionService, reportesService, transporteService, pagoViaticosService, geoService, pdfService, downloadBlob } from '../services/api';
import { generarConsentimientoPDF, generarFO05, generarFO15Consolidado } from '../utils/pdfForms';
import { useAuthContext } from '../context/AuthContext';
import { MapaRuta } from '../components/maps/MapaRuta';

const estadoConfig: Record<EstadoPractica, { label: string; color: string }> = {
  borrador:           { label: 'Borrador',                color: 'bg-gray-100 text-gray-600' },
  solicitada:         { label: 'Solicitada',              color: 'bg-blue-100 text-blue-700' },
  pendiente_quorum:   { label: 'Pendiente Quórum',        color: 'bg-yellow-100 text-yellow-700' },
  aprobada_curriculo: { label: 'Aprobada Comité Currículo', color: 'bg-cyan-100 text-cyan-700' },
  aprobada_facultad:  { label: 'Avalada Consejo Facultad', color: 'bg-violet-100 text-violet-700' },
  aprobado_transporte:{ label: 'Aprobada Vicerrectoría',  color: 'bg-emerald-100 text-emerald-700' },
  en_ejecucion:       { label: 'En Ejecución',            color: 'bg-indigo-100 text-indigo-700' },
  finalizada:         { label: 'Finalizada',              color: 'bg-usco-ocre-light text-usco-gris' },
  rechazada:          { label: 'Rechazada',               color: 'bg-red-100 text-red-700' },
};

interface RutaForm {
  orden: number;
  tipo_punto: string;
  lugar: string;
  municipio: string;
  departamento: string;
  distancia_km: string;
  vereda: string;
  es_rural: boolean;
}

interface ViaticosItem {
  tarifa_id: number;
  descripcion: string;
  valor_dia: number;
  num_dias: number;
  num_personas: number;
  subtotal: number;
}

function PagoViaticoButton({ practicaId, yaPagado: yaRegistrado }: { practicaId: number; yaPagado?: boolean }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ monto_pagado: '', fecha_pago: new Date().toISOString().slice(0, 10), observaciones: '' });
  const [saving, setSaving] = useState(false);
  const [ok, setOk] = useState(false);
  const [pagado, setPagado] = useState(yaRegistrado ?? false);

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await pagoViaticosService.registrar(practicaId, {
        monto_pagado: parseFloat(form.monto_pagado),
        fecha_pago: form.fecha_pago,
        observaciones: form.observaciones || undefined,
      });
      setOk(true);
      setPagado(true);
      setTimeout(() => { setOpen(false); setOk(false); setForm({ monto_pagado: '', fecha_pago: new Date().toISOString().slice(0, 10), observaciones: '' }); }, 1500);
    } catch { /* silencioso */ }
    finally { setSaving(false); }
  }

  if (pagado) {
    return (
      <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg">
        <CheckCircle size={13} /> Viáticos pagados
      </span>
    );
  }

  return (
    <>
      <button onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 text-xs font-semibold text-amber-600 border border-amber-300 hover:bg-amber-50 px-3 py-1.5 rounded-lg transition-colors">
        <DollarSign size={13} /> Registrar pago viáticos
      </button>
      {open && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6">
            <h3 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
              <DollarSign size={16} className="text-amber-500" /> Registrar pago de viáticos
            </h3>
            {ok ? (
              <div className="text-center py-4">
                <CheckCircle size={36} className="text-emerald-500 mx-auto mb-2" />
                <p className="text-sm font-semibold text-emerald-600">Pago registrado</p>
              </div>
            ) : (
              <form onSubmit={guardar} className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Monto pagado (COP)</label>
                  <input required type="number" min="1" step="100" value={form.monto_pagado}
                    onChange={e => setForm(p => ({ ...p, monto_pagado: e.target.value }))}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-300" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Fecha de pago</label>
                  <input required type="date" value={form.fecha_pago}
                    onChange={e => setForm(p => ({ ...p, fecha_pago: e.target.value }))}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-300" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Observaciones</label>
                  <input value={form.observaciones} onChange={e => setForm(p => ({ ...p, observaciones: e.target.value }))}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-300" />
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setOpen(false)}
                    className="flex-1 border border-gray-300 text-gray-700 font-semibold py-2 rounded-lg hover:bg-gray-50 text-sm">
                    Cancelar
                  </button>
                  <button type="submit" disabled={saving}
                    className="flex-1 bg-amber-500 text-white font-semibold py-2 rounded-lg hover:bg-amber-600 disabled:opacity-60 text-sm flex items-center justify-center gap-2">
                    {saving ? <Spin size={13} className="animate-spin" /> : <CheckCircle size={13} />}
                    Guardar
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
}


interface WaypointRowProps {
  ruta: RutaForm;
  idx: number;
  totalRutas: number;
  departamentos: string[];
  kmLoading: boolean;
  onFieldChange: (idx: number, field: keyof RutaForm, value: string | boolean) => void;
  onDeptChange: (idx: number, dept: string) => void;
  onMunicipioChange: (idx: number, municipio: string) => void;
  onRemove: (idx: number) => void;
}

function WaypointRow({ ruta, idx, totalRutas, departamentos, kmLoading, onFieldChange, onDeptChange, onMunicipioChange, onRemove }: WaypointRowProps) {
  const [municipios, setMunicipios] = useState<string[]>([]);
  const [loadingMunicipios, setLoadingMunicipios] = useState(false);

  useEffect(() => {
    if (!ruta.departamento) { setMunicipios([]); return; }
    setLoadingMunicipios(true);
    geoService.getMunicipios(ruta.departamento)
      .then(r => setMunicipios((r.data as { municipios: string[] }).municipios))
      .catch(() => setMunicipios([]))
      .finally(() => setLoadingMunicipios(false));
  }, [ruta.departamento]);

  const tipoBadge = ruta.tipo_punto === 'origen'
    ? 'bg-emerald-100 text-emerald-700 border border-emerald-300'
    : ruta.tipo_punto === 'destino'
    ? 'bg-red-100 text-red-700 border border-red-300'
    : 'bg-blue-100 text-blue-700 border border-blue-300';

  return (
    <div className="bg-gray-50 rounded-xl border border-gray-200 p-3 space-y-2">
      {/* Fila 1: badge orden + tipo + departamento + municipio */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`shrink-0 w-6 h-6 flex items-center justify-center text-xs font-bold rounded-full ${tipoBadge}`}>
          {ruta.orden}
        </span>
        <select value={ruta.tipo_punto} onChange={e => onFieldChange(idx, 'tipo_punto', e.target.value)}
          className="w-24 border border-gray-300 rounded-lg px-2 py-1.5 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-usco-vinotinto">
          <option value="origen">Origen</option>
          <option value="waypoint">Escala</option>
          <option value="destino">Destino</option>
        </select>
        <select
          value={ruta.departamento}
          onChange={e => onDeptChange(idx, e.target.value)}
          className="flex-1 min-w-[130px] border border-gray-300 rounded-lg px-2 py-1.5 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-usco-vinotinto">
          <option value="">— Departamento —</option>
          {departamentos.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <select
          value={ruta.municipio}
          onChange={e => onMunicipioChange(idx, e.target.value)}
          disabled={!ruta.departamento || loadingMunicipios}
          className="flex-1 min-w-[130px] border border-gray-300 rounded-lg px-2 py-1.5 text-xs bg-white disabled:bg-gray-100 disabled:text-gray-400 focus:outline-none focus:ring-1 focus:ring-usco-vinotinto">
          <option value="">
            {loadingMunicipios ? 'Cargando...' : ruta.departamento ? '— Municipio —' : 'Seleccione depto.'}
          </option>
          {municipios.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      {/* Fila 2: Lugar + Rural + Vereda + Km + papelera */}
      <div className="flex items-center gap-2 pl-8 flex-wrap">
        <input
          placeholder="Lugar / Sitio (opcional)"
          value={ruta.lugar}
          onChange={e => onFieldChange(idx, 'lugar', e.target.value)}
          className="flex-1 min-w-[120px] border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-usco-vinotinto" />
        <label className="flex items-center gap-1 cursor-pointer shrink-0 select-none">
          <input
            type="checkbox"
            checked={ruta.es_rural}
            onChange={e => onFieldChange(idx, 'es_rural', e.target.checked)}
            className="w-3.5 h-3.5 rounded border-gray-300 text-usco-vinotinto focus:ring-usco-vinotinto" />
          <span className="text-xs text-gray-600 whitespace-nowrap">Zona rural</span>
        </label>
        {ruta.es_rural && (
          <input
            placeholder="Vereda / Corregimiento"
            value={ruta.vereda}
            onChange={e => onFieldChange(idx, 'vereda', e.target.value)}
            className="flex-1 min-w-[140px] border border-amber-300 bg-amber-50 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-amber-400" />
        )}
        {/* Km auto */}
        <div className="flex items-center gap-1 shrink-0">
          {kmLoading && idx > 0 ? (
            <div className="flex items-center gap-1 px-2 py-1.5 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-500 w-24">
              <Spin size={11} className="animate-spin" /> calculando…
            </div>
          ) : (
            <div className="flex items-center gap-1">
              <input
                placeholder="Km"
                type="number"
                min="0"
                step="0.1"
                value={ruta.distancia_km}
                onChange={e => onFieldChange(idx, 'distancia_km', e.target.value)}
                className={`w-20 border rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 ${
                  ruta.distancia_km
                    ? 'border-emerald-300 bg-emerald-50 text-emerald-800 focus:ring-emerald-400'
                    : 'border-gray-300 focus:ring-usco-vinotinto'
                }`} />
              {ruta.distancia_km && (
                <span className="text-xs text-emerald-600 font-semibold">km</span>
              )}
            </div>
          )}
        </div>
        {totalRutas > 2 && (
          <button onClick={() => onRemove(idx)} className="text-red-400 hover:text-red-600 shrink-0">
            <Trash2 size={14} />
          </button>
        )}
      </div>
    </div>
  );
}


function NuevaPracticaModal({
  onClose,
  onSuccess,
  practicaEditar,
}: {
  onClose: () => void;
  onSuccess: () => void;
  practicaEditar?: Practica;
}) {
  const { user } = useAuthContext();
  const [asignaturas, setAsignaturas] = useState<Asignatura[]>([]);
  const [periodosDisponibles, setPeriodosDisponibles] = useState<string[]>([]);
  const [limitesDuracion, setLimitesDuracion] = useState<{ dentro_huila: number; fuera_huila: number }>({ dentro_huila: 5, fuera_huila: 10 });
  const [plantillas, setPlantillas] = useState<Array<{
    id: number; nombre: string; programa: string; sede: string;
    asignatura: string; caracter_curso: string; ruta_texto: string;
    tipo_bus: string; costo_bus_externo: number | null; costo_tiquetes: number | null;
    profesor: string | null;
  }>>([]);
  const [filterPrograma, setFilterPrograma] = useState<string>(
    user?.rol === 'profesor' ? (user.programa ?? '') : ''
  );

  const CIUDAD_DEPT: Record<string, string> = {
    'Bogotá': 'Cundinamarca', 'Bogota': 'Cundinamarca',
    'Soacha': 'Cundinamarca', 'Girardot': 'Cundinamarca', 'Guaduas': 'Cundinamarca',
    'Villeta': 'Cundinamarca', 'La Vega': 'Cundinamarca', 'Facatativá': 'Cundinamarca',
    'Medellín': 'Antioquia', 'Medellin': 'Antioquia',
    'Cali': 'Valle del Cauca', 'Palmira': 'Valle del Cauca', 'Buga': 'Valle del Cauca',
    'Manizales': 'Caldas', 'Villamaría': 'Caldas', 'Villamaria': 'Caldas',
    'Popayán': 'Cauca', 'Popayan': 'Cauca', 'Santander de Quilichao': 'Cauca',
    'Ibagué': 'Tolima', 'Ibague': 'Tolima', 'Espinal': 'Tolima',
    'Saldaña': 'Tolima', 'Saldana': 'Tolima', 'Mariquita': 'Tolima',
    'Armero': 'Tolima', 'Natagaima': 'Tolima', 'Payandé': 'Tolima',
    'Pasto': 'Nariño', 'Ipiales': 'Nariño', 'Tumaco': 'Nariño',
    'Armenia': 'Quindío', 'Calarcá': 'Quindío',
    'Pereira': 'Risaralda', 'Dosquebradas': 'Risaralda',
    'Bucaramanga': 'Santander', 'Barrancabermeja': 'Santander',
    'Villavicencio': 'Meta',
    'Barranquilla': 'Atlántico',
    'Cartagena': 'Bolívar',
    'Cúcuta': 'Norte de Santander', 'Cucuta': 'Norte de Santander',
    'Tunja': 'Boyacá', 'Duitama': 'Boyacá', 'Sogamoso': 'Boyacá',
    'Florencia': 'Caquetá',
    'Leticia': 'Amazonas',
    'Mocoa': 'Putumayo',
  };

  function parseLugar(lugar: string): { municipio: string; departamento: string } {
    const ciudad = lugar.split('(')[0].split(',')[0].trim();
    return { municipio: ciudad, departamento: CIUDAD_DEPT[ciudad] ?? 'Huila' };
  }
  const [filterAsignatura, setFilterAsignatura] = useState('');
  const [filterProfesor, setFilterProfesor] = useState('');
  const [asigInfo, setAsigInfo] = useState<{ sede?: string | null; facultad?: string | null; programa?: string | null } | null>(null);
  const [showPlantillaPanel, setShowPlantillaPanel] = useState(false);
  const [fo16Open, setFo16Open] = useState(!!practicaEditar);
  const [fo05Open, setFo05Open] = useState(false);
  const [form, setForm] = useState(
    practicaEditar ? {
      nombre_practica: practicaEditar.nombre_practica,
      asignatura_id: String(practicaEditar.asignatura_id),
      periodo_academico: practicaEditar.periodo_academico,
      fecha_inicio: practicaEditar.fecha_inicio.slice(0, 16),
      fecha_fin: practicaEditar.fecha_fin.slice(0, 16),
      num_alumnos: String(practicaEditar.num_alumnos),
      tipo_docente: practicaEditar.tipo_docente ?? 'planta',
      observaciones: practicaEditar.observaciones ?? '',
      caracter_curso: practicaEditar.caracter_curso ?? '',
      caracteristica_curso: practicaEditar.caracteristica_curso ?? '',
      modalidad_docente: practicaEditar.modalidad_docente ?? '',
      hora_salida: practicaEditar.hora_salida ?? '',
      hora_llegada: practicaEditar.hora_llegada ?? '',
      articulacion_curso: practicaEditar.articulacion_curso ?? '',
      descripcion_practica: practicaEditar.descripcion_practica ?? '',
      evaluacion: practicaEditar.evaluacion ?? '',
      justificacion: practicaEditar.justificacion ?? '',
      metodologia: practicaEditar.metodologia ?? '',
      carta_autorizacion_empresa: practicaEditar.carta_autorizacion_empresa ?? '',
      placa_vehiculo: (practicaEditar as unknown as Record<string, string>).placa_vehiculo ?? '',
      tipo_vehiculo: (practicaEditar as unknown as Record<string, string>).tipo_vehiculo ?? '',
      empresa_transporte: (practicaEditar as unknown as Record<string, string>).empresa_transporte ?? '',
      conductor_nombre: (practicaEditar as unknown as Record<string, string>).conductor_nombre ?? '',
    } : {
      nombre_practica: '',
      asignatura_id: '',
      periodo_academico: '',
      fecha_inicio: '',
      fecha_fin: '',
      num_alumnos: '',
      tipo_docente: user?.tipo_docente ?? 'planta',
      observaciones: '',
      caracter_curso: '',
      caracteristica_curso: '',
      modalidad_docente: user?.modalidad_docente ?? '',
      hora_salida: '',
      hora_llegada: '',
      articulacion_curso: '',
      descripcion_practica: '',
      evaluacion: '',
      justificacion: '',
      metodologia: '',
      carta_autorizacion_empresa: '',
      placa_vehiculo: '',
      tipo_vehiculo: '',
      empresa_transporte: '',
      conductor_nombre: '',
    }
  );
  const [rutas, setRutas] = useState<RutaForm[]>(
    practicaEditar?.rutas?.length
      ? practicaEditar.rutas.map(r => ({
          orden: r.orden,
          tipo_punto: r.tipo_punto,
          lugar: r.lugar,
          municipio: r.municipio ?? '',
          departamento: r.departamento ?? 'Huila',
          distancia_km: r.distancia_km != null ? String(r.distancia_km) : '',
          vereda: '',
          es_rural: false,
        }))
      : [
          { orden: 1, tipo_punto: 'origen', lugar: '', municipio: '', departamento: 'Huila', distancia_km: '', vereda: '', es_rural: false },
          { orden: 2, tipo_punto: 'destino', lugar: '', municipio: '', departamento: 'Huila', distancia_km: '', vereda: '', es_rural: false },
        ]
  );
  const [departamentos, setDepartamentos] = useState<string[]>([]);
  const [kmLoading, setKmLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  function applyPlantilla(pl: typeof plantillas[0]) {
    const caracter = pl.caracter_curso === 'TP' ? 'teorico_practico' : pl.caracter_curso === 'T' ? 'teorico' : '';
    setForm(prev => ({
      ...prev,
      nombre_practica: pl.nombre,
      caracter_curso: caracter,
    }));
    if (pl.ruta_texto) {
      const partes = pl.ruta_texto.split(' - ').map(s => s.trim()).filter(Boolean);
      if (partes.length >= 2) {
        const nuevasRutas: RutaForm[] = partes.map((parte, i) => {
          const { municipio, departamento } = parseLugar(parte);
          return {
            orden: i + 1,
            tipo_punto: i === 0 ? 'origen' : i === partes.length - 1 ? 'destino' : 'waypoint',
            lugar: parte,
            municipio,
            departamento,
            distancia_km: '',
            vereda: '',
            es_rural: false,
          };
        });
        setRutas(nuevasRutas);
      }
    }
    setShowPlantillaPanel(false);
  }

  useEffect(() => {
    practicasService.getPlantillas()
      .then(r => setPlantillas(r.data as typeof plantillas))
      .catch(() => {});
    convocatoriasService.getAsignaturas()
      .then(r => setAsignaturas(r.data as Asignatura[]))
      .catch(() => setAsignaturas([]));

    configuracionService.getPeriodoActivo()
      .then(r => {
        const cal = r.data as { periodo_academico: string };
        setPeriodosDisponibles([cal.periodo_academico]);
        setForm(prev => ({ ...prev, periodo_academico: cal.periodo_academico }));
      })
      .catch(() => { /* sin período activo configurado */ });

    geoService.getDepartamentos()
      .then(r => setDepartamentos((r.data as { departamentos: string[] }).departamentos))
      .catch(() => setDepartamentos([]));
    practicasService.limitesDuracion()
      .then(r => setLimitesDuracion(r.data as { dentro_huila: number; fuera_huila: number }))
      .catch(() => {});
  }, []);

  const duracionDias = form.fecha_inicio && form.fecha_fin
    ? Math.max(1, Math.ceil((new Date(form.fecha_fin).getTime() - new Date(form.fecha_inicio).getTime()) / (1000 * 60 * 60 * 24)))
    : 0;
  const esFueraHuila = rutas.some(r => r.departamento && r.departamento.toLowerCase() !== 'huila');
  const maxDiasPractica = esFueraHuila ? limitesDuracion.fuera_huila : limitesDuracion.dentro_huila;
  const duracionExcede = duracionDias > 0 && duracionDias > maxDiasPractica;

  const TIPO_DOCENTE_TO_MODALIDAD: Record<string, string> = {
    planta: 'TCP',
    ocasional: 'TCO',
    catedra: 'CAT',
    visitante: 'CAT',
  };

  async function handleAsignaturaChange(asignaturaId: string) {
    setForm(prev => ({ ...prev, asignatura_id: asignaturaId }));
    setAsigInfo(null);
    if (!asignaturaId || practicaEditar) return;

    try {
      const r = await practicasService.datosAsignatura(parseInt(asignaturaId));
      const d = r.data as {
        facultad?: string | null;
        programa?: string | null;
        caracter_curso?: string | null;
        caracteristica_curso?: string | null;
        num_estudiantes?: number;
        sede?: string | null;
        tipo_docente?: string | null;
        modalidad_docente?: string | null;
        found_practica: boolean;
        articulacion_curso?: string | null;
        descripcion_practica?: string | null;
        justificacion?: string | null;
        metodologia?: string | null;
        evaluacion?: string | null;
        carta_autorizacion_empresa?: string | null;
        placa_vehiculo?: string | null;
        tipo_vehiculo?: string | null;
        empresa_transporte?: string | null;
        conductor_nombre?: string | null;
        rutas?: RutaForm[];
      };
      setAsigInfo({ sede: d.sede, facultad: d.facultad, programa: d.programa });
      setForm(prev => ({
        ...prev,
        caracter_curso: d.caracter_curso ?? prev.caracter_curso,
        caracteristica_curso: d.caracteristica_curso ?? prev.caracteristica_curso,
        num_alumnos: d.num_estudiantes ? String(d.num_estudiantes) : prev.num_alumnos,
        tipo_docente: d.tipo_docente ?? prev.tipo_docente,
        modalidad_docente: d.modalidad_docente ?? prev.modalidad_docente,
        ...(d.found_practica && {
          articulacion_curso: d.articulacion_curso ?? prev.articulacion_curso,
          descripcion_practica: d.descripcion_practica ?? prev.descripcion_practica,
          justificacion: d.justificacion ?? prev.justificacion,
          metodologia: d.metodologia ?? prev.metodologia,
          evaluacion: d.evaluacion ?? prev.evaluacion,
          carta_autorizacion_empresa: d.carta_autorizacion_empresa ?? prev.carta_autorizacion_empresa,
          placa_vehiculo: d.placa_vehiculo ?? prev.placa_vehiculo,
          tipo_vehiculo: d.tipo_vehiculo ?? prev.tipo_vehiculo,
          empresa_transporte: d.empresa_transporte ?? prev.empresa_transporte,
          conductor_nombre: d.conductor_nombre ?? prev.conductor_nombre,
        }),
      }));
      if (d.found_practica && d.rutas && d.rutas.length >= 2) {
        setRutas(d.rutas);
      }
    } catch { /* silencioso */ }
  }

  function handleTipoDocenteChange(val: string) {
    setForm(prev => ({
      ...prev,
      tipo_docente: val,
      modalidad_docente: prev.modalidad_docente || TIPO_DOCENTE_TO_MODALIDAD[val] || '',
    }));
  }

  function addRuta() {
    setRutas(prev => [...prev, {
      orden: prev.length + 1,
      tipo_punto: 'waypoint',
      lugar: '',
      municipio: '',
      departamento: 'Huila',
      distancia_km: '',
      vereda: '',
      es_rural: false,
    }]);
  }

  function removeRuta(idx: number) {
    setRutas(prev => prev.filter((_, i) => i !== idx).map((r, i) => ({ ...r, orden: i + 1 })));
  }

  function updateRuta(idx: number, field: keyof RutaForm, value: string | boolean) {
    setRutas(prev => prev.map((r, i) => i === idx ? { ...r, [field]: value } : r));
  }

  function handleDeptChange(idx: number, dept: string) {
    setRutas(prev => prev.map((r, i) => i === idx ? { ...r, departamento: dept, municipio: '' } : r));
  }

  async function handleMunicipioChange(idx: number, municipio: string) {
    const updatedRutas = rutas.map((r, i) => i === idx ? { ...r, municipio } : r);
    setRutas(updatedRutas);
    if (!municipio) return;
    const pairs: [number, number][] = [];
    if (idx > 0) pairs.push([idx - 1, idx]);
    if (idx < updatedRutas.length - 1) pairs.push([idx, idx + 1]);
    if (pairs.length === 0) return;
    setKmLoading(true);
    const kmUpdates: Record<number, string> = {};
    for (const [fromIdx, toIdx] of pairs) {
      const from = updatedRutas[fromIdx];
      const to = updatedRutas[toIdx];
      if (from.municipio && from.departamento && to.municipio && to.departamento) {
        try {
          const r = await geoService.getDistancia({
            origen_municipio: from.municipio,
            origen_departamento: from.departamento,
            destino_municipio: to.municipio,
            destino_departamento: to.departamento,
          });
          const data = r.data as { distancia_km: number | null };
          if (data.distancia_km != null) kmUpdates[toIdx] = String(data.distancia_km);
        } catch { /* ignore */ }
      }
    }
    setKmLoading(false);
    if (Object.keys(kmUpdates).length > 0) {
      setRutas(prev => prev.map((r, i) => kmUpdates[i] !== undefined ? { ...r, distancia_km: kmUpdates[i] } : r));
    }
  }

  async function handleSubmit() {
    if (!form.nombre_practica || !form.fecha_inicio || !form.fecha_fin || !form.num_alumnos) {
      setError('Complete todos los campos obligatorios');
      return;
    }
    if (!practicaEditar && !form.asignatura_id) {
      setError('Seleccione una asignatura');
      return;
    }
    if (duracionExcede) {
      setError(`La duracion (${duracionDias} dias) supera el maximo permitido para practicas ${esFueraHuila ? 'fuera del Huila' : 'dentro del Huila'}: ${maxDiasPractica} dias.`);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const rutasPayload = rutas.map(r => ({
        ...r,
        distancia_km: r.distancia_km ? parseFloat(r.distancia_km) : null,
      }));
      if (practicaEditar) {
        await practicasService.update(practicaEditar.id, {
          nombre_practica: form.nombre_practica,
          fecha_inicio: form.fecha_inicio,
          fecha_fin: form.fecha_fin,
          num_alumnos: parseInt(form.num_alumnos),
          tipo_docente: form.tipo_docente || null,
          observaciones: form.observaciones || null,
          caracter_curso: form.caracter_curso || null,
          caracteristica_curso: form.caracteristica_curso || null,
          modalidad_docente: form.modalidad_docente || null,
          hora_salida: form.hora_salida || null,
          hora_llegada: form.hora_llegada || null,
          articulacion_curso: form.articulacion_curso || null,
          descripcion_practica: form.descripcion_practica || null,
          evaluacion: form.evaluacion || null,
          justificacion: form.justificacion || null,
          metodologia: form.metodologia || null,
          carta_autorizacion_empresa: form.carta_autorizacion_empresa || null,
          rutas: rutasPayload,
        });
      } else {
        await practicasService.create({
          ...form,
          asignatura_id: parseInt(form.asignatura_id),
          num_alumnos: parseInt(form.num_alumnos),
          rutas: rutasPayload,
        });
      }
      onSuccess();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: unknown } } };
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0] as { msg?: string };
        setError(first.msg ?? 'Error de validación en los datos enviados');
      } else {
        setError(practicaEditar ? 'Error al guardar los cambios.' : 'Error al crear la práctica. Revise los datos e intente de nuevo.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl flex flex-col" style={{ maxHeight: 'calc(100vh - 2rem)' }}>

        {/* ── HEADER STICKY ────────────────────────────────────────────── */}
        <div className="shrink-0 bg-linear-to-r from-usco-vinotinto to-usco-vinotinto-dark rounded-t-2xl px-6 py-4 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white leading-tight">
              {practicaEditar ? 'Editar Práctica Extramural' : 'Nueva Práctica Extramural'}
            </h3>
            <p className="text-xs text-white/70 mt-0.5">Formato MI-FOR-FO-16 · Acuerdo 003/2012 USCO</p>
          </div>
          <button type="button" onClick={onClose}
            className="w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center text-white transition-colors shrink-0">
            <X size={16} />
          </button>
        </div>

        {/* ── CUERPO SCROLLABLE ────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto px-6 py-4">

        {/* Selector de plantilla institucional */}
        {!practicaEditar && plantillas.length > 0 && (() => {
          const programas = Array.from(new Set(plantillas.map(p => p.programa))).sort();
          const asignaturas = Array.from(new Set(
            plantillas
              .filter(p => !filterPrograma || p.programa === filterPrograma)
              .map(p => p.asignatura)
          )).sort();
          const profesores = Array.from(new Set(
            plantillas
              .filter(p => (!filterPrograma || p.programa === filterPrograma) && (!filterAsignatura || p.asignatura === filterAsignatura))
              .flatMap(p => (p.profesor || '').split(' · ').map(x => x.trim()).filter(Boolean))
          )).sort();
          const filtradas = plantillas.filter(p =>
            (!filterPrograma || p.programa === filterPrograma) &&
            (!filterAsignatura || p.asignatura === filterAsignatura) &&
            (!filterProfesor || (p.profesor || '').includes(filterProfesor))
          );
          return (
            <div className="mb-4 border border-amber-200 rounded-xl overflow-hidden">
              <button
                type="button"
                onClick={() => setShowPlantillaPanel(v => !v)}
                className="w-full flex items-center justify-between px-4 py-3 bg-amber-50 hover:bg-amber-100 transition-colors"
              >
                <span className="text-xs font-semibold text-amber-700 flex items-center gap-1.5">
                  <FileText size={13} /> Cargar desde catálogo institucional (Excel Extramuros 2026)
                </span>
                <span className="text-xs text-amber-500">{showPlantillaPanel ? '▲ Ocultar' : '▼ Ver catálogo'}</span>
              </button>
              {showPlantillaPanel && (
                <div className="p-3 bg-white border-t border-amber-100 space-y-3">
                  {/* Filtros */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <div>
                      <label className="block text-xs font-semibold text-gray-500 mb-1">Programa</label>
                      <select value={filterPrograma} onChange={e => { setFilterPrograma(e.target.value); setFilterAsignatura(''); setFilterProfesor(''); }}
                        className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-amber-400">
                        <option value="">Todos</option>
                        {programas.map(p => <option key={p} value={p}>{p}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-500 mb-1">Asignatura</label>
                      <select value={filterAsignatura} onChange={e => { setFilterAsignatura(e.target.value); setFilterProfesor(''); }}
                        className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-amber-400">
                        <option value="">Todas</option>
                        {asignaturas.map(a => <option key={a} value={a}>{a}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-500 mb-1">Profesor</label>
                      <select value={filterProfesor} onChange={e => setFilterProfesor(e.target.value)}
                        className="w-full border border-gray-200 rounded-lg px-2 py-1.5 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-amber-400">
                        <option value="">Todos</option>
                        {profesores.map(pr => <option key={pr} value={pr}>{pr}</option>)}
                      </select>
                    </div>
                  </div>
                  {/* Lista de resultados */}
                  <div className="max-h-52 overflow-y-auto rounded-lg border border-gray-100 divide-y divide-gray-100">
                    {filtradas.length === 0 ? (
                      <p className="px-4 py-3 text-xs text-gray-400 italic">Sin resultados con los filtros actuales.</p>
                    ) : filtradas.map(p => (
                      <button key={p.id} type="button" onClick={() => applyPlantilla(p)}
                        className="w-full text-left px-3 py-2.5 hover:bg-amber-50 transition-colors group">
                        <p className="text-sm font-semibold text-gray-800 leading-snug group-hover:text-amber-700">{p.nombre}</p>
                        <div className="flex flex-wrap gap-x-3 mt-0.5">
                          <span className="text-xs text-gray-400">{p.asignatura}</span>
                          {p.profesor && <span className="text-xs text-usco-gris">{p.profesor}</span>}
                          <span className="text-xs text-gray-300">{p.sede}</span>
                        </div>
                        {p.ruta_texto && (
                          <p className="text-xs text-gray-400 mt-0.5 truncate flex items-center gap-1">
                            <MapPin size={10} className="shrink-0 text-usco-vinotinto" />{p.ruta_texto}
                          </p>
                        )}
                      </button>
                    ))}
                  </div>
                  <p className="text-xs text-gray-400 text-right">{filtradas.length} práctica{filtradas.length !== 1 ? 's' : ''} · Al seleccionar se auto-rellena el nombre y la ruta</p>
                </div>
              )}
            </div>
          );
        })()}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">
            {error}
          </div>
        )}
        {/* ── SECCIÓN 1: DATOS BÁSICOS ──────────────────────────────────────── */}
        <div className="rounded-xl border border-gray-200 overflow-hidden mb-4">
          <div className="bg-usco-vinotinto/5 border-b border-gray-200 px-4 py-2.5 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-usco-vinotinto text-white text-xs font-bold flex items-center justify-center shrink-0">1</span>
            <span className="text-sm font-bold text-usco-vinotinto">Datos Básicos</span>
            <span className="ml-auto text-xs text-gray-400">Campos obligatorios *</span>
          </div>
          <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-gray-600 mb-1">Nombre de la Práctica *</label>
              <input type="text" value={form.nombre_practica} onChange={e => setForm(p => ({ ...p, nombre_practica: e.target.value }))}
                placeholder="Ej: Visita técnica ENORCON — Gigante"
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/50" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Asignatura {!practicaEditar && '*'}</label>
              {practicaEditar ? (
                <div className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm bg-gray-50 text-gray-600">
                  {practicaEditar.asignatura?.nombre ?? `Asignatura #${practicaEditar.asignatura_id}`}
                </div>
              ) : (
                <select value={form.asignatura_id} onChange={e => handleAsignaturaChange(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/50 bg-white">
                  <option value="">Seleccionar...</option>
                  {asignaturas.map(a => <option key={a.id} value={a.id}>{a.nombre}{a.caracter_curso ? ` · ${a.caracter_curso === 'teorico_practico' ? 'T-P' : 'T'}` : ''}</option>)}
                </select>
              )}
              {asigInfo && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {asigInfo.sede && (
                    <span className="inline-flex items-center gap-1 text-xs bg-blue-50 text-blue-700 border border-blue-200 rounded-full px-2.5 py-0.5">
                      <MapPin size={9} /> {asigInfo.sede}
                    </span>
                  )}
                  {asigInfo.facultad && (
                    <span className="inline-flex items-center text-xs bg-usco-vinotinto/10 text-usco-vinotinto border border-usco-vinotinto/20 rounded-full px-2.5 py-0.5">
                      {asigInfo.facultad}
                    </span>
                  )}
                  {asigInfo.programa && (
                    <span className="inline-flex items-center text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full px-2.5 py-0.5">
                      {asigInfo.programa}
                    </span>
                  )}
                </div>
              )}
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">N° de Alumnos *</label>
              <input type="number" min="1" value={form.num_alumnos} onChange={e => setForm(p => ({ ...p, num_alumnos: e.target.value }))}
                placeholder="25" className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/50" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Fecha Inicio *</label>
              <input type="datetime-local" value={form.fecha_inicio}
                min={practicaEditar ? undefined : new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16)}
                onChange={e => setForm(p => ({ ...p, fecha_inicio: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/50" />
              <p className="text-xs text-amber-600 mt-1 flex items-center gap-1"><Clock size={10} /> Mín. 30 días de anticipación (Ac. 003/2012)</p>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Fecha Fin *</label>
              <input type="datetime-local" value={form.fecha_fin}
                min={practicaEditar ? form.fecha_inicio || undefined : (form.fecha_inicio || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16))}
                onChange={e => setForm(p => ({ ...p, fecha_fin: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/50" />
            </div>
            {duracionDias > 0 && (
              <div className={`sm:col-span-2 flex items-center gap-2 text-xs rounded-lg px-3 py-2 border ${
                duracionExcede ? 'bg-red-50 border-red-200 text-red-700' : 'bg-emerald-50 border-emerald-200 text-emerald-700'
              }`}>
                <AlertTriangle size={11} className="shrink-0" />
                <span>
                  <strong>{duracionDias} día{duracionDias !== 1 ? 's' : ''}</strong>
                  {' · Máx. '}<strong>{maxDiasPractica}</strong> día{maxDiasPractica !== 1 ? 's' : ''}
                  {' '}{esFueraHuila ? 'fuera del Huila' : 'dentro del Huila'}
                  {duracionExcede && <strong> — excede el límite permitido</strong>}
                </span>
              </div>
            )}
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Hora Salida USCO</label>
              <input type="time" value={form.hora_salida} onChange={e => setForm(p => ({ ...p, hora_salida: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/50" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Hora Llegada USCO</label>
              <input type="time" value={form.hora_llegada} onChange={e => setForm(p => ({ ...p, hora_llegada: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/50" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Tipo de Docente</label>
              <select value={form.tipo_docente} onChange={e => handleTipoDocenteChange(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/50 bg-white">
                <option value="planta">Docente de Planta</option>
                <option value="catedra">Docente Cátedra</option>
                <option value="ocasional">Nombramiento Ocasional</option>
                <option value="visitante">Cátedra Visitante</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Período Académico *</label>
              {periodosDisponibles.length > 1 ? (
                <select value={form.periodo_academico} onChange={e => setForm(p => ({ ...p, periodo_academico: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/50 bg-white">
                  {periodosDisponibles.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              ) : (
                <div className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm bg-gray-50 text-gray-700 font-medium">
                  {form.periodo_academico || <span className="text-gray-400 italic">Cargando...</span>}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── SECCIÓN 2: FORMULARIO FO-16 ──────────────────────────────────── */}
        <div className="rounded-xl border border-indigo-200 overflow-hidden mb-4">
          <button type="button" onClick={() => setFo16Open(o => !o)}
            className="w-full bg-indigo-50 hover:bg-indigo-100 transition-colors px-4 py-2.5 flex items-center gap-2 text-left">
            <span className="w-5 h-5 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center shrink-0">2</span>
            <span className="text-sm font-bold text-indigo-700">Documentación FO-16</span>
            <span className="text-xs text-indigo-400 ml-1">— Justificación Prácticas Extramuros</span>
            <span className="ml-auto text-indigo-400 text-base leading-none">{fo16Open ? '▲' : '▼'}</span>
          </button>
          {fo16Open && (
            <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 border-t border-indigo-100">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Modalidad docente</label>
                <select value={form.modalidad_docente} onChange={e => setForm(p => ({ ...p, modalidad_docente: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white">
                  <option value="">Seleccionar...</option>
                  <option value="TCP">TCP — Tiempo Completo Planta</option>
                  <option value="TCO">TCO — Tiempo Completo Ocasional</option>
                  <option value="MTP">MTP — Medio Tiempo Planta</option>
                  <option value="MTO">MTO — Medio Tiempo Ocasional</option>
                  <option value="CAT">CAT — Cátedra</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Carácter del Curso</label>
                <select value={form.caracter_curso} onChange={e => setForm(p => ({ ...p, caracter_curso: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white">
                  <option value="">Seleccionar...</option>
                  <option value="teorico">Teórico</option>
                  <option value="teorico_practico">Teórico Práctico</option>
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-gray-600 mb-1">Característica del Curso</label>
                <select value={form.caracteristica_curso} onChange={e => setForm(p => ({ ...p, caracteristica_curso: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white">
                  <option value="">Seleccionar...</option>
                  <option value="especifico">Específico de Programa</option>
                  <option value="facultad">De Facultad</option>
                  <option value="institucional">Institucional</option>
                  <option value="componente_flexible">Componente Flexible</option>
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-gray-600 mb-1">Articulación del Curso con la Práctica y Evaluación</label>
                <textarea value={form.articulacion_curso} onChange={e => setForm(p => ({ ...p, articulacion_curso: e.target.value }))} rows={2}
                  placeholder="Describa cómo se articula la práctica con el área del curso y los procesos de evaluación..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none" />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-gray-600 mb-1">Descripción de la Práctica</label>
                <textarea value={form.descripcion_practica} onChange={e => setForm(p => ({ ...p, descripcion_practica: e.target.value }))} rows={2}
                  placeholder="Describa los objetivos, actividades y metodología de la práctica extramural..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none" />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-gray-600 mb-1">Justificación — Art. 3.e Acuerdo 003/2012</label>
                <textarea value={form.justificacion} onChange={e => setForm(p => ({ ...p, justificacion: e.target.value }))} rows={2}
                  placeholder="Justifique la necesidad de la práctica extramural para el logro de los objetivos del curso..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none" />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-gray-600 mb-1">Metodología — Art. 3.e Acuerdo 003/2012</label>
                <textarea value={form.metodologia} onChange={e => setForm(p => ({ ...p, metodologia: e.target.value }))} rows={2}
                  placeholder="Describa la metodología pedagógica que se empleará durante la práctica..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none" />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-gray-600 mb-1">Evaluación</label>
                <textarea value={form.evaluacion} onChange={e => setForm(p => ({ ...p, evaluacion: e.target.value }))} rows={2}
                  placeholder="Criterios e instrumentos de evaluación que se aplicarán durante la práctica..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none" />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-gray-600 mb-1">
                  Carta de Autorización Empresa/Institución — Art. 3.l
                  {form.carta_autorizacion_empresa && <span className="ml-2 text-emerald-600 font-semibold">✓ Registrada</span>}
                </label>
                <textarea value={form.carta_autorizacion_empresa} onChange={e => setForm(p => ({ ...p, carta_autorizacion_empresa: e.target.value }))} rows={2}
                  placeholder="Nombre y datos de la empresa o institución que autoriza la visita, o pegue el texto de la carta..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none" />
              </div>
            </div>
          )}
        </div>

        {/* ── SECCIÓN 3: TRANSPORTE FO-05 ──────────────────────────────────── */}
        <div className="rounded-xl border border-emerald-200 overflow-hidden mb-4">
          <button type="button" onClick={() => setFo05Open(o => !o)}
            className="w-full bg-emerald-50 hover:bg-emerald-100 transition-colors px-4 py-2.5 flex items-center gap-2 text-left">
            <span className="w-5 h-5 rounded-full bg-emerald-600 text-white text-xs font-bold flex items-center justify-center shrink-0">3</span>
            <span className="text-sm font-bold text-emerald-700">Transporte — AP-INF-FO-05</span>
            <span className="text-xs text-emerald-500 ml-1">— Solicitud Desplazamiento Vial</span>
            {(form.placa_vehiculo || form.tipo_vehiculo) && (
              <span className="ml-2 text-xs bg-emerald-100 text-emerald-700 font-semibold px-2 py-0.5 rounded-full border border-emerald-200">
                {form.placa_vehiculo || form.tipo_vehiculo}
              </span>
            )}
            <span className="ml-auto text-emerald-400 text-base leading-none">{fo05Open ? '▲' : '▼'}</span>
          </button>
          {fo05Open && (
            <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 border-t border-emerald-100">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Placa del Vehículo</label>
                <input value={form.placa_vehiculo} onChange={e => setForm(p => ({ ...p, placa_vehiculo: e.target.value }))}
                  placeholder="Ej: ABC-123"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 uppercase" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Tipo de Vehículo</label>
                <input value={form.tipo_vehiculo} onChange={e => setForm(p => ({ ...p, tipo_vehiculo: e.target.value }))}
                  placeholder="Bus, Buseta, Microbús..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Empresa Transportadora</label>
                <input value={form.empresa_transporte} onChange={e => setForm(p => ({ ...p, empresa_transporte: e.target.value }))}
                  placeholder="Nombre de la empresa de transporte..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Nombre del Conductor</label>
                <input value={form.conductor_nombre} onChange={e => setForm(p => ({ ...p, conductor_nombre: e.target.value }))}
                  placeholder="Nombre completo del conductor..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" />
              </div>
            </div>
          )}
        </div>

        {/* ── OBSERVACIONES ──────────────────────────────────────────────────── */}
        <div className="mb-4">
          <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wider">Observaciones</label>
          <textarea value={form.observaciones} onChange={e => setForm(p => ({ ...p, observaciones: e.target.value }))} rows={2}
            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/50 resize-none" />
        </div>

        {/* ── SECCIÓN 4: RUTA ────────────────────────────────────────────── */}
        <div className="rounded-xl border border-gray-200 overflow-hidden mb-4">
          <div className="bg-gray-50 border-b border-gray-200 px-4 py-2.5 flex items-center justify-between">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="w-5 h-5 rounded-full bg-usco-gris text-white text-xs font-bold flex items-center justify-center shrink-0">4</span>
              <h4 className="text-sm font-bold text-gray-700 flex items-center gap-1.5"><MapPin size={14} /> Ruta e Itinerario</h4>
              <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border ${
                esFueraHuila
                  ? 'bg-amber-50 border-amber-300 text-amber-700'
                  : 'bg-blue-50 border-blue-300 text-blue-700'
              }`}>
                <MapPin size={9} />
                {esFueraHuila ? `Fuera del Huila · máx. ${limitesDuracion.fuera_huila} días` : `Dentro del Huila · máx. ${limitesDuracion.dentro_huila} días`}
              </span>
            </div>
            <button type="button" onClick={addRuta}
              className="flex items-center gap-1.5 text-xs font-semibold text-usco-vinotinto hover:text-usco-vinotinto-dark border border-usco-vinotinto/30 hover:border-usco-vinotinto/60 px-2.5 py-1 rounded-lg transition-colors">
              <Plus size={13} /> Waypoint
            </button>
          </div>
          <div className="p-3 space-y-2">
            {rutas.map((ruta, idx) => (
              <WaypointRow
                key={idx}
                ruta={ruta}
                idx={idx}
                totalRutas={rutas.length}
                departamentos={departamentos}
                kmLoading={kmLoading}
                onFieldChange={updateRuta}
                onDeptChange={handleDeptChange}
                onMunicipioChange={handleMunicipioChange}
                onRemove={removeRuta}
              />
            ))}
          </div>
          {/* Vista previa del mapa — Leaflet + OpenStreetMap */}
          <div className="px-3 pb-3">
            <MapaRuta rutas={rutas} />
          </div>
        </div>

        </div>{/* fin cuerpo scrollable */}

        {/* ── FOOTER STICKY ────────────────────────────────────────────── */}
        <div className="shrink-0 border-t border-gray-200 bg-gray-50 rounded-b-2xl px-6 py-3 flex gap-3">
          <button type="button" onClick={onClose}
            className="flex-1 border border-gray-300 text-gray-700 font-semibold py-2.5 rounded-lg hover:bg-gray-100 text-sm transition-colors">
            Cancelar
          </button>
          <button type="button" onClick={handleSubmit} disabled={loading}
            className="flex-1 bg-usco-vinotinto hover:bg-usco-vinotinto-dark text-white font-bold py-2.5 rounded-lg transition-colors disabled:opacity-60 text-sm shadow-sm">
            {loading ? 'Guardando…' : (practicaEditar ? 'Guardar cambios' : '+ Crear Práctica')}
          </button>
        </div>

      </div>
    </div>
  );
}

function ViaticosModal({ practicaId, onClose }: { practicaId: number; onClose: () => void }) {
  const [viaticos, setViaticos] = useState<ViaticosItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    practicasService.calcularViaticos(practicaId)
      .then(r => setViaticos(r.data))
      .catch(() => setViaticos([]))
      .finally(() => setLoading(false));
  }, [practicaId]);

  const total = viaticos.reduce((s, v) => s + v.subtotal, 0);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
        <div className="mb-4">
          <h3 className="text-lg font-bold text-gray-800">Cálculo de Viáticos</h3>
          <p className="text-xs text-gray-400 mt-0.5">Per-diem del docente responsable · Acuerdo 003/2012</p>
        </div>
        {loading ? <p className="text-sm text-gray-400 text-center py-4">Calculando...</p> : (
          <div className="space-y-3">
            {viaticos.map(v => (
              <div key={v.tarifa_id} className="flex items-center justify-between border border-gray-100 rounded-lg p-3">
                <div>
                  <p className="text-sm font-medium text-gray-700">{v.descripcion}</p>
                  <p className="text-xs text-gray-400">${v.valor_dia.toLocaleString('es-CO')}/día × {v.num_dias} día{v.num_dias !== 1 ? 's' : ''} × {v.num_personas} docente</p>
                </div>
                <p className="font-bold text-usco-vinotinto text-sm">${v.subtotal.toLocaleString('es-CO')}</p>
              </div>
            ))}
            <div className="border-t border-gray-200 pt-3 flex justify-between font-bold text-gray-800">
              <span>Total Estimado</span>
              <span className="text-usco-vinotinto">${total.toLocaleString('es-CO')}</span>
            </div>
          </div>
        )}
        <button onClick={onClose} className="mt-5 w-full border border-gray-300 text-gray-700 font-semibold py-2.5 rounded-lg hover:bg-gray-50 text-sm">
          Cerrar
        </button>
      </div>
    </div>
  );
}

// ─── Modal informe de resultados (Art. 7 Acuerdo 003/2012) ───────────────────
function InformeModal({
  practicaId,
  onClose,
  onSuccess,
}: { practicaId: number; onClose: () => void; onSuccess: () => void }) {
  const [informe, setInforme] = useState('');
  const [observaciones, setObservaciones] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit() {
    if (!informe.trim()) { setError('El informe no puede estar vacío.'); return; }
    setLoading(true);
    setError('');
    try {
      await practicasService.finalizar(practicaId, { informe_resultados: informe, observaciones: observaciones || undefined });
      onSuccess();
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? 'Error al finalizar la práctica.');
    } finally { setLoading(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <FileText size={18} className="text-usco-vinotinto" /> Informe de Resultados
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
        </div>
        <p className="text-xs text-gray-500 mb-4 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
          <strong>Art. 7 — Acuerdo 003/2012:</strong> El docente debe entregar el informe dentro de los <strong>5 días hábiles</strong> siguientes al regreso de la práctica.
        </p>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Informe de resultados *</label>
            <textarea
              rows={5}
              value={informe}
              onChange={e => setInforme(e.target.value)}
              placeholder="Describe los resultados, aprendizajes y cumplimiento de los objetivos de la práctica extramural..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/50 resize-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Observaciones adicionales</label>
            <textarea
              rows={2}
              value={observaciones}
              onChange={e => setObservaciones(e.target.value)}
              placeholder="Novedades, inconvenientes, recomendaciones..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/50 resize-none"
            />
          </div>
          {error && <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>}
        </div>
        <div className="flex gap-3 mt-5">
          <button onClick={onClose} className="flex-1 border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm font-semibold py-2.5 rounded-xl transition-colors">
            Cancelar
          </button>
          <button onClick={handleSubmit} disabled={loading}
            className="flex-1 bg-usco-vinotinto hover:bg-usco-vinotinto-dark text-white text-sm font-semibold py-2.5 rounded-xl transition-colors disabled:opacity-60 flex items-center justify-center gap-2">
            {loading ? <Spin size={14} className="animate-spin" /> : <CheckCircle size={14} />}
            {loading ? 'Guardando…' : 'Entregar informe y cerrar práctica'}
          </button>
        </div>
      </div>
    </div>
  );
}


// ─── Modal costos de transporte ──────────────────────────────────────────────
function TransporteModal({ practicaId, onClose }: { practicaId: number; onClose: () => void }) {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [errMsg, setErrMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const [tipoVehiculo, setTipoVehiculo] = useState('bus');
  const [numVehiculos, setNumVehiculos] = useState(1);
  const [categoriaPeaje, setCategoriaPeaje] = useState(3);

  const combustibleLabel: Record<string, string> = {
    bus: 'Diésel',
    camioneta: 'Gasolina corriente',
    moto: 'Gasolina corriente',
  };

  const calcular = useCallback(async () => {
    setLoading(true);
    setErrMsg('');
    try {
      const r = await transporteService.getCostos(practicaId, tipoVehiculo, numVehiculos, categoriaPeaje);
      setData(r.data);
    } catch (err: unknown) {
      setData(null);
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErrMsg(detail || 'No se pudo calcular el costo de transporte.');
    } finally { setLoading(false); }
  }, [practicaId, tipoVehiculo, numVehiculos, categoriaPeaje]);

  useEffect(() => { calcular(); }, [calcular]);

  const fmt = (v: number) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v);
  const desglose = data?.desglose as Record<string, { descripcion: string; valor_cop: number }> | undefined;
  const params = data?.parametros_calculo as Record<string, unknown> | undefined;
  const distAuto = data?.distancias_auto as string[] | undefined;

  const LABEL: Record<string, string> = {
    combustible: `Combustible (${combustibleLabel[tipoVehiculo] ?? 'Diésel'})`,
    peajes: 'Peajes (INVIAS)',
    conductor: 'Conductor',
    seguro_pasajeros: 'Seguro de pasajeros',
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <Truck size={18} className="text-usco-vinotinto" /> Costos de Transporte
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="col-span-1">
            <label className="block text-xs font-semibold text-gray-600 mb-1">Tipo de vehículo</label>
            <select value={tipoVehiculo} onChange={e => setTipoVehiculo(e.target.value)}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
              <option value="bus">Bus / Van (Diésel)</option>
              <option value="camioneta">Camioneta (Gasolina)</option>
            </select>
          </div>
          <div className="col-span-1">
            <label className="block text-xs font-semibold text-gray-600 mb-1">Cat. peaje</label>
            <select value={categoriaPeaje} onChange={e => setCategoriaPeaje(parseInt(e.target.value))}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
              <option value={2}>Cat 2 — Bus liviano</option>
              <option value={3}>Cat 3 — Bus pesado</option>
              <option value={4}>Cat 4 — Camión 2 ejes</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">N° vehículos</label>
            <input type="number" min={1} max={10} value={numVehiculos}
              onChange={e => setNumVehiculos(parseInt(e.target.value) || 1)}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
          </div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-8 gap-2">
            <Spin size={24} className="animate-spin text-usco-vinotinto" />
            <p className="text-xs text-gray-400">Calculando distancias y costos…</p>
          </div>
        ) : !data ? (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700 space-y-2">
            <p className="font-semibold flex items-center gap-2"><AlertTriangle size={15} /> No se pudo calcular</p>
            <p className="text-xs">{errMsg}</p>
            <p className="text-xs text-gray-500 mt-1">
              Sugerencia: edite la práctica e ingrese las distancias en km en cada punto de ruta, o asegúrese de que los municipios estén escritos correctamente (p.ej. "Neiva", "Bogotá", "Pitalito").
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {/* Info de km calculados */}
            {params && (
              <div className="bg-gray-50 rounded-xl p-3 text-xs text-gray-600 grid grid-cols-2 gap-x-4 gap-y-1 mb-1">
                <span>Distancia ida:</span>
                <span className="font-semibold text-right">{Number(params.km_total_ida).toFixed(0)} km</span>
                <span>Ida + vuelta:</span>
                <span className="font-semibold text-right">{Number(params.km_total_ida_vuelta).toFixed(0)} km</span>
                <span>Litros estimados:</span>
                <span className="font-semibold text-right">{Number(params.litros_estimados).toFixed(1)} L</span>
                <span>Precio diésel:</span>
                <span className="font-semibold text-right">
                  {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(Number(params.precio_diesel_litro))}/L
                </span>
              </div>
            )}
            {distAuto && distAuto.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700">
                <span className="font-semibold">Distancias calculadas automáticamente:</span>
                <ul className="mt-1 space-y-0.5">
                  {distAuto.map((d, i) => <li key={i}>• {d}</li>)}
                </ul>
              </div>
            )}
            {desglose && Object.entries(desglose).map(([key, item]) => (
              <div key={key} className="flex items-center justify-between border border-gray-100 rounded-lg p-3">
                <div>
                  <p className="text-sm font-medium text-gray-700">{LABEL[key] ?? key.replace(/_/g, ' ')}</p>
                  <p className="text-xs text-gray-400">{item.descripcion}</p>
                </div>
                <p className="font-bold text-usco-gris text-sm">{fmt(item.valor_cop)}</p>
              </div>
            ))}
            <div className="border-t-2 border-usco-vinotinto/20 pt-3 flex justify-between font-bold text-gray-800">
              <span>Total estimado</span>
              <span className="text-usco-vinotinto text-lg">{fmt((data.total_estimado_cop as number) ?? 0)}</span>
            </div>
            <p className="text-xs text-gray-400 italic">{data.nota as string}</p>
          </div>
        )}

        <button onClick={onClose} className="mt-5 w-full border border-gray-300 text-gray-700 font-semibold py-2 rounded-lg hover:bg-gray-50 text-sm">
          Cerrar
        </button>
      </div>
    </div>
  );
}

// ─── Modal de confirmación genérico ─────────────────────────────────────────
function ModalConfirmar({
  titulo, mensaje, colorBtn = 'bg-usco-vinotinto', loading, onConfirm, onClose,
}: {
  titulo: string; mensaje: React.ReactNode; colorBtn?: string;
  loading: boolean; onConfirm: () => void; onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
        <div className="flex items-start justify-between mb-4">
          <h3 className="font-bold text-gray-800 text-base">{titulo}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 ml-2"><X size={18} /></button>
        </div>
        <p className="text-sm text-gray-600 mb-5">{mensaje}</p>
        <div className="flex gap-3">
          <button onClick={onClose} disabled={loading}
            className="flex-1 py-2 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
            Cancelar
          </button>
          <button onClick={onConfirm} disabled={loading}
            className={`flex-1 py-2 text-sm font-semibold text-white rounded-lg disabled:opacity-60 flex items-center justify-center gap-2 ${colorBtn} hover:opacity-90`}>
            {loading && <Spin size={14} className="animate-spin" />}
            Confirmar
          </button>
        </div>
      </div>
    </div>
  );
}

export function Practicas() {
  const { user } = useAuthContext();
  const [practicas, setPracticas] = useState<Practica[]>([]);
  const [search, setSearch] = useState('');
  const [filterEstado, setFilterEstado] = useState('');
  const [filterAsignaturaId, setFilterAsignaturaId] = useState('');
  const [filterSede, setFilterSede] = useState('');
  const [filterFacultad, setFilterFacultad] = useState('');
  const [filterPrograma, setFilterPrograma] = useState('');
  const [filterProfesorLista, setFilterProfesorLista] = useState('');
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editarPractica, setEditarPractica] = useState<Practica | null>(null);
  const [viaticosModal, setViaticosModal] = useState<number | null>(null);
  const [flash, setFlash] = useState<{ tipo: 'ok' | 'err'; texto: string } | null>(null);
  const [accionId, setAccionId] = useState<{ tipo: 'aprobar' | 'rechazar' | 'firmar' | 'iniciar'; id: number } | null>(null);
  const [accionLoading, setAccionLoading] = useState(false);
  const [motivoRechazo, setMotivoRechazo] = useState('');
  const [transporteModal, setTransporteModal] = useState<number | null>(null);
  const [informeModal, setInformeModal] = useState<number | null>(null);
  const [mapaExpandido, setMapaExpandido] = useState<number | null>(null);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const r = await practicasService.getAll();
      setPracticas(r.data);
    } catch { setPracticas([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  function showFlash(tipo: 'ok' | 'err', texto: string) {
    setFlash({ tipo, texto });
    setTimeout(() => setFlash(null), 4000);
  }

  async function solicitar(id: number) {
    try {
      await practicasService.solicitar(id);
      showFlash('ok', 'Práctica enviada para aprobación.');
      cargar();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      showFlash('err', err.response?.data?.detail ?? 'Error al solicitar');
    }
  }

  async function ejecutarAccion() {
    if (!accionId) return;
    setAccionLoading(true);
    try {
      if (accionId.tipo === 'aprobar') {
        await practicasService.aprobar(accionId.id);
        showFlash('ok', 'Práctica aprobada y avanzada a la siguiente etapa.');
      } else if (accionId.tipo === 'rechazar') {
        await practicasService.rechazar(accionId.id, motivoRechazo || undefined);
        setMotivoRechazo('');
        showFlash('ok', 'Práctica rechazada.');
      } else if (accionId.tipo === 'iniciar') {
        await practicasService.iniciar(accionId.id);
        showFlash('ok', 'Práctica marcada en ejecución. ¡Buen viaje!');
      } else {
        await practicasService.firmarConsentimiento(accionId.id);
        showFlash('ok', 'Consentimiento firmado correctamente.');
      }
      cargar();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      showFlash('err', err.response?.data?.detail ?? 'Error en la operación');
    } finally {
      setAccionLoading(false);
      setAccionId(null);
    }
  }

  function abrirRechazo(id: number) {
    setMotivoRechazo('');
    setAccionId({ tipo: 'rechazar', id });
  }

  const term = search.toLowerCase();
  const asignaturasUnicas = Array.from(
    new Map(practicas.filter(p => p.asignatura).map(p => [p.asignatura_id, p.asignatura!])).values()
  ).sort((a, b) => a.nombre.localeCompare(b.nombre));
  const sedesUnicas = Array.from(new Set(practicas.map(p => p.profesor?.sede).filter(Boolean))).sort() as string[];
  const facultadesUnicas = Array.from(new Set(practicas.map(p => p.asignatura?.facultad).filter(Boolean))).sort() as string[];
  const programasUnicosLista = Array.from(new Set(practicas.map(p => p.asignatura?.programa).filter(Boolean))).sort() as string[];
  const profesoresUnicos = Array.from(new Set(practicas.map(p => p.profesor ? `${p.profesor.nombres} ${p.profesor.apellidos}`.trim() : '').filter(Boolean))).sort();
  const practicasFiltradas = practicas.filter(p =>
    (!filterEstado || p.estado === filterEstado) &&
    (!filterAsignaturaId || String(p.asignatura_id) === filterAsignaturaId) &&
    (!filterSede || p.profesor?.sede === filterSede) &&
    (!filterFacultad || p.asignatura?.facultad === filterFacultad) &&
    (!filterPrograma || p.asignatura?.programa === filterPrograma) &&
    (!filterProfesorLista || `${p.profesor?.nombres ?? ''} ${p.profesor?.apellidos ?? ''}`.toLowerCase().includes(filterProfesorLista.toLowerCase())) &&
    (!term || p.nombre_practica?.toLowerCase().includes(term) || p.asignatura?.nombre?.toLowerCase().includes(term))
  );

  const _practicaEnAccion = practicas.find(p => p.id === accionId?.id);
  const _esOverride = _practicaEnAccion?.estado === 'pendiente_quorum';
  const accionConfig = accionId ? {
    aprobar: {
      titulo: _esOverride ? '⚠ Aprobar sin quórum completo' : 'Aprobar / avalar práctica',
      mensaje: _esOverride
        ? 'La práctica NO ha alcanzado el quórum requerido (≥66% de firmas). Al confirmar, el Comité de Currículo ejerce su autoridad para avalar la práctica de todas formas. Esta decisión quedará registrada en el historial.'
        : '¿Confirmas la aprobación de esta práctica en la etapa actual del flujo?',
      colorBtn: _esOverride ? 'bg-amber-600' : 'bg-emerald-600',
    },
    rechazar: { titulo: 'Rechazar práctica', mensaje: '¿Estás seguro de que deseas rechazar esta práctica? Esta acción no se puede deshacer.', colorBtn: 'bg-red-600' },
    iniciar: { titulo: 'Confirmar inicio de práctica', mensaje: 'Al confirmar declaras que la práctica inició el día programado. El estado cambiará a «En Ejecución».', colorBtn: 'bg-indigo-600' },
    firmar: { titulo: 'Firmar consentimiento', mensaje: 'Al confirmar aceptas participar en la práctica extramural y das tu consentimiento. Se registrará tu IP y la fecha.', colorBtn: 'bg-usco-gris' },
  }[accionId.tipo] : null;

  return (
    <div className="space-y-5">
      {showModal && (
        <NuevaPracticaModal onClose={() => setShowModal(false)}
          onSuccess={() => { setShowModal(false); cargar(); showFlash('ok', 'Práctica creada correctamente.'); }} />
      )}
      {editarPractica && (
        <NuevaPracticaModal
          practicaEditar={editarPractica}
          onClose={() => setEditarPractica(null)}
          onSuccess={() => { setEditarPractica(null); cargar(); showFlash('ok', 'Práctica actualizada correctamente.'); }}
        />
      )}
      {viaticosModal !== null && (
        <ViaticosModal practicaId={viaticosModal} onClose={() => setViaticosModal(null)} />
      )}
      {transporteModal !== null && (
        <TransporteModal practicaId={transporteModal} onClose={() => setTransporteModal(null)} />
      )}
      {informeModal !== null && (
        <InformeModal
          practicaId={informeModal}
          onClose={() => setInformeModal(null)}
          onSuccess={() => { setInformeModal(null); cargar(); showFlash('ok', 'Práctica finalizada con informe de resultados. ✅'); }}
        />
      )}
      {accionId && accionConfig && (
        <ModalConfirmar
          titulo={accionConfig.titulo}
          mensaje={
            accionId.tipo === 'rechazar' ? (
              <div className="space-y-3">
                <p className="text-sm text-gray-600">{accionConfig.mensaje}</p>
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">Motivo del rechazo (opcional)</label>
                  <textarea
                    value={motivoRechazo}
                    onChange={e => setMotivoRechazo(e.target.value)}
                    rows={3}
                    placeholder="Ej: La ruta no es viable, faltan firmas de riesgo..."
                    className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-300 resize-none"
                  />
                </div>
              </div>
            ) : accionConfig.mensaje
          }
          colorBtn={accionConfig.colorBtn}
          loading={accionLoading}
          onConfirm={ejecutarAccion}
          onClose={() => { setAccionId(null); setMotivoRechazo(''); }}
        />
      )}

      {/* Flash */}
      {flash && (
        <div className={`flex items-center gap-3 rounded-xl px-5 py-3 text-sm font-medium ${
          flash.tipo === 'ok' ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
            : 'bg-red-50 border border-red-200 text-red-700'}`}>
          {flash.tipo === 'ok' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {flash.texto}
        </div>
      )}

      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Prácticas Extramuros</h1>
          <p className="text-sm text-gray-500 mt-0.5">Formato MI-FOR-FO-15 — Gestión digital de prácticas de campo.</p>
        </div>
        <div className="flex items-center gap-2">
          {user?.rol === 'profesor' && (
            <button onClick={() => setShowModal(true)}
              className="flex items-center gap-2 bg-usco-vinotinto hover:bg-usco-vinotinto/90 text-white font-semibold px-4 py-2.5 rounded-lg transition-colors text-sm">
              <Plus size={16} /> Nueva Práctica
            </button>
          )}
          {user?.rol === 'jefe_programa' && (
            <button
              onClick={async () => {
                try {
                  const r = await reportesService.getFO15Programa();
                  const lista = r.data as Array<{
                    nombre: string; asignatura: string; asignatura_codigo: string;
                    docente: string; fecha_inicio: string | null; hora_salida: string | null;
                    fecha_fin: string | null; hora_llegada: string | null;
                    ruta: string | null; duracion_dias: number; num_alumnos: number;
                    facultad: string; programa: string; periodo_academico: string;
                  }>;
                  const facultad = lista[0]?.facultad ?? user?.programa ?? '—';
                  const programa = user?.programa ?? lista[0]?.programa ?? '—';
                  const periodos = [...new Set(lista.map(p => p.periodo_academico))].join(' / ');
                  generarFO15Consolidado({
                    facultad,
                    programa,
                    periodo_academico: periodos || '—',
                    jefe_nombre: `${user?.nombres ?? ''} ${user?.apellidos ?? ''}`.trim() || undefined,
                    practicas: lista.map(p => ({
                      nombre: p.nombre,
                      asignatura: p.asignatura,
                      asignatura_codigo: p.asignatura_codigo,
                      docente: p.docente,
                      fecha_inicio: p.fecha_inicio,
                      hora_salida: p.hora_salida,
                      fecha_fin: p.fecha_fin,
                      hora_llegada: p.hora_llegada,
                      ruta: p.ruta,
                      duracion_dias: p.duracion_dias,
                      num_alumnos: p.num_alumnos,
                    })),
                  });
                } catch { /* silent */ }
              }}
              className="flex items-center gap-2 bg-usco-vinotinto/10 hover:bg-usco-vinotinto/20 text-usco-vinotinto border border-usco-vinotinto/30 font-semibold px-4 py-2.5 rounded-lg transition-colors text-sm">
              <FileText size={15} /> Descargar FO-15 Programa
            </button>
          )}
        </div>
      </div>

      {/* Búsqueda y filtros */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Buscar por nombre o asignatura..."
            className="w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
        </div>
        {asignaturasUnicas.length > 1 && (
          <select value={filterAsignaturaId} onChange={e => setFilterAsignaturaId(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
            <option value="">Todas las asignaturas</option>
            {asignaturasUnicas.map(a => (
              <option key={a.id} value={String(a.id)}>{a.nombre}</option>
            ))}
          </select>
        )}
        <select value={filterEstado} onChange={e => setFilterEstado(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
          <option value="">Todos los estados</option>
          {Object.entries(estadoConfig).map(([val, cfg]) => (
            <option key={val} value={val}>{cfg.label}</option>
          ))}
        </select>
        {(user?.rol === 'admin' || user?.rol === 'decano' || user?.rol === 'jefe_programa') && (
          <>
            {programasUnicosLista.length > 1 && (
              <select value={filterPrograma} onChange={e => setFilterPrograma(e.target.value)}
                className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
                <option value="">Todos los programas</option>
                {programasUnicosLista.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            )}
            {sedesUnicas.length > 1 && (
              <select value={filterSede} onChange={e => setFilterSede(e.target.value)}
                className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
                <option value="">Todas las sedes</option>
                {sedesUnicas.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            )}
            {facultadesUnicas.length > 1 && (
              <select value={filterFacultad} onChange={e => setFilterFacultad(e.target.value)}
                className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
                <option value="">Todas las facultades</option>
                {facultadesUnicas.map(f => <option key={f} value={f}>{f}</option>)}
              </select>
            )}
            {(user?.rol === 'admin' || user?.rol === 'decano') && profesoresUnicos.length > 1 && (
              <select value={filterProfesorLista} onChange={e => setFilterProfesorLista(e.target.value)}
                className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
                <option value="">Todos los profesores</option>
                {profesoresUnicos.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            )}
          </>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Spin size={24} className="animate-spin text-usco-vinotinto" />
        </div>
      ) : practicasFiltradas.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-100 text-gray-400">
          <MapPin size={48} className="mx-auto mb-3 opacity-40" />
          <p className="text-lg font-medium">No hay prácticas que coincidan</p>
          {user?.rol === 'profesor' && <p className="text-sm">Crea una nueva práctica extramural.</p>}
        </div>
      ) : (
        <div className="space-y-4">
          {practicasFiltradas.map(p => {
            const cfg = estadoConfig[p.estado];
            const pctQuorum = p.num_alumnos
              ? Math.min(100, Math.round((p.total_firmas_obtenidas / p.num_alumnos) * 100))
              : 0;
            return (
              <div key={p.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-800 truncate">{p.nombre_practica}</h3>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {p.asignatura?.nombre ?? `Asignatura #${p.asignatura_id}`} ·{' '}
                      {new Date(p.fecha_inicio).toLocaleDateString('es-CO')} – {new Date(p.fecha_fin).toLocaleDateString('es-CO')} ·{' '}
                      {Math.round((new Date(new Date(p.fecha_fin).toDateString()).getTime() - new Date(new Date(p.fecha_inicio).toDateString()).getTime()) / 86400000)} día(s)
                    </p>
                  </div>
                  <span className={`text-xs font-semibold px-3 py-1.5 rounded-full shrink-0 ${cfg.color}`}>{cfg.label}</span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-400 mb-1 flex items-center justify-center gap-1"><Users size={11} /> Alumnos</p>
                    <p className="font-bold text-gray-800">{p.num_alumnos}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-400 mb-1">Firmas req.</p>
                    <p className="font-bold text-gray-800">{p.total_firmas_requeridas ?? '—'}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-400 mb-1">Firmas obtenidas</p>
                    <p className={`font-bold ${p.quorum_alcanzado ? 'text-emerald-600' : 'text-amber-600'}`}>{p.total_firmas_obtenidas}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-400 mb-1">Quórum (≥66%)</p>
                    <p className={`font-bold ${p.quorum_alcanzado ? 'text-emerald-600' : 'text-gray-800'}`}>
                      {pctQuorum}%
                      {p.quorum_alcanzado && <span className="ml-1 text-xs">✓</span>}
                    </p>
                  </div>
                </div>

                {p.total_firmas_requeridas && (
                  <div className="mb-3">
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div className={`h-2 rounded-full transition-all ${p.quorum_alcanzado ? 'bg-emerald-500' : 'bg-amber-400'}`}
                        style={{ width: `${Math.min(100, pctQuorum)}%` }} />
                    </div>
                  </div>
                )}

                {(p.rutas ?? []).length > 0 && (
                  <div className="mb-3">
                    <div className="flex items-center gap-2 flex-wrap mb-1.5">
                      <MapPin size={14} className="text-usco-gris shrink-0" />
                      {(p.rutas ?? []).map((r, i) => (
                        <span key={r.id} className="flex items-center gap-1 text-xs text-gray-600">
                          {i > 0 && <span className="text-gray-300">→</span>}
                          <span className="bg-gray-100 px-2 py-0.5 rounded-full">{r.lugar || r.municipio}</span>
                          {r.distancia_km != null && i > 0 && (
                            <span className="text-gray-400 text-[10px]">{r.distancia_km}km</span>
                          )}
                        </span>
                      ))}
                      <button
                        onClick={() => setMapaExpandido(mapaExpandido === p.id ? null : p.id)}
                        className="ml-auto flex items-center gap-1 text-xs font-semibold text-usco-vinotinto hover:underline">
                        <MapPin size={11} />
                        {mapaExpandido === p.id ? 'Ocultar mapa' : 'Ver mapa'}
                      </button>
                    </div>
                    {mapaExpandido === p.id && (
                      <MapaRuta
                        rutas={(p.rutas ?? []).map(r => ({
                          orden: r.orden,
                          tipo_punto: r.tipo_punto,
                          municipio: r.municipio ?? '',
                          departamento: r.departamento ?? 'Huila',
                          lugar: r.lugar,
                          distancia_km: r.distancia_km != null ? String(r.distancia_km) : '',
                        }))}
                      />
                    )}
                  </div>
                )}

                <div className="flex flex-wrap gap-2 pt-3 border-t border-gray-100">
                  {user?.rol !== 'estudiante' && (
                    <>
                      <button onClick={() => setViaticosModal(p.id)}
                        className="flex items-center gap-1.5 text-xs font-semibold text-usco-gris hover:text-usco-vinotinto border border-gray-200 px-3 py-1.5 rounded-lg transition-colors">
                        <DollarSign size={13} /> Ver viáticos
                      </button>
                      <button onClick={() => setTransporteModal(p.id)}
                        className="flex items-center gap-1.5 text-xs font-semibold text-usco-gris hover:text-usco-vinotinto border border-gray-200 px-3 py-1.5 rounded-lg transition-colors">
                        <Truck size={13} /> Costos transporte
                      </button>
                    </>
                  )}

                  {/* Editar práctica */}
                  {((user?.rol === 'profesor' && p.profesor_id === user.id && ['borrador', 'solicitada'].includes(p.estado)) ||
                    ((user?.rol === 'jefe_programa' || user?.rol === 'decano') && !['finalizada', 'rechazada'].includes(p.estado))) && (
                    <button onClick={() => setEditarPractica(p)}
                      className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-usco-vinotinto border border-gray-200 px-3 py-1.5 rounded-lg transition-colors">
                      <Edit2 size={13} /> Editar
                    </button>
                  )}

                  {user?.rol === 'profesor' && p.estado === 'borrador' && (
                    <button onClick={() => solicitar(p.id)}
                      className="flex items-center gap-1.5 text-xs font-semibold text-white bg-usco-vinotinto hover:bg-usco-vinotinto/90 px-3 py-1.5 rounded-lg transition-colors">
                      <Send size={13} /> Solicitar aprobación
                    </button>
                  )}

                  {/* Etapa 1a — Comité de Currículo: aprobación normal */}
                  {user?.rol === 'jefe_programa' && p.estado === 'solicitada' && (
                    <>
                      <button onClick={() => setAccionId({ tipo: 'aprobar', id: p.id })}
                        className="flex items-center gap-1.5 text-xs font-semibold text-white bg-cyan-600 hover:bg-cyan-700 px-3 py-1.5 rounded-lg transition-colors">
                        <CheckCircle size={13} /> Aprobar (Comité Currículo)
                      </button>
                      <button onClick={() => abrirRechazo(p.id)}
                        className="flex items-center gap-1.5 text-xs font-semibold text-white bg-red-500 hover:bg-red-600 px-3 py-1.5 rounded-lg transition-colors">
                        <X size={13} /> Rechazar
                      </button>
                    </>
                  )}
                  {/* Etapa 1b — pendiente_quorum: override explícito del jefe */}
                  {user?.rol === 'jefe_programa' && p.estado === 'pendiente_quorum' && (
                    <>
                      <button onClick={() => setAccionId({ tipo: 'aprobar', id: p.id })}
                        className="flex items-center gap-1.5 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 px-3 py-1.5 rounded-lg transition-colors"
                        title="Aprobar aunque no se haya alcanzado el quórum requerido (Art. 2 Acuerdo 003/2012)">
                        <CheckCircle size={13} /> Aprobar sin quórum (override)
                      </button>
                      <button onClick={() => abrirRechazo(p.id)}
                        className="flex items-center gap-1.5 text-xs font-semibold text-white bg-red-500 hover:bg-red-600 px-3 py-1.5 rounded-lg transition-colors">
                        <X size={13} /> Rechazar
                      </button>
                    </>
                  )}
                  {/* Jefe puede retractar desde aprobada_curriculo */}
                  {user?.rol === 'jefe_programa' && p.estado === 'aprobada_curriculo' && (
                    <button onClick={() => abrirRechazo(p.id)}
                      className="flex items-center gap-1.5 text-xs font-semibold text-amber-700 border border-amber-300 hover:bg-amber-50 px-3 py-1.5 rounded-lg transition-colors">
                      <X size={13} /> Retractar aprobación
                    </button>
                  )}
                  {/* Etapa 2 — Consejo de Facultad (decano) */}
                  {user?.rol === 'decano' && p.estado === 'aprobada_curriculo' && (
                    <>
                      <button onClick={() => setAccionId({ tipo: 'aprobar', id: p.id })}
                        className="flex items-center gap-1.5 text-xs font-semibold text-white bg-violet-600 hover:bg-violet-700 px-3 py-1.5 rounded-lg transition-colors">
                        <CheckCircle size={13} /> Avalar (Consejo Facultad)
                      </button>
                      <button onClick={() => abrirRechazo(p.id)}
                        className="flex items-center gap-1.5 text-xs font-semibold text-white bg-red-500 hover:bg-red-600 px-3 py-1.5 rounded-lg transition-colors">
                        <X size={13} /> Rechazar
                      </button>
                    </>
                  )}
                  {/* Decano puede retractar desde aprobada_facultad */}
                  {user?.rol === 'decano' && p.estado === 'aprobada_facultad' && (
                    <button onClick={() => abrirRechazo(p.id)}
                      className="flex items-center gap-1.5 text-xs font-semibold text-amber-700 border border-amber-300 hover:bg-amber-50 px-3 py-1.5 rounded-lg transition-colors">
                      <X size={13} /> Retractar aval
                    </button>
                  )}
                  {/* Etapa 3 — Vicerrectoría (admin) */}
                  {user?.rol === 'admin' && p.estado === 'aprobada_facultad' && (
                    <>
                      <button onClick={() => setAccionId({ tipo: 'aprobar', id: p.id })}
                        className="flex items-center gap-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 px-3 py-1.5 rounded-lg transition-colors">
                        <CheckCircle size={13} /> Aprobar final (Vicerrectoría)
                      </button>
                      <button onClick={() => abrirRechazo(p.id)}
                        className="flex items-center gap-1.5 text-xs font-semibold text-white bg-red-500 hover:bg-red-600 px-3 py-1.5 rounded-lg transition-colors">
                        <X size={13} /> Rechazar
                      </button>
                    </>
                  )}

                  {user?.rol === 'estudiante' && ['solicitada', 'pendiente_quorum', 'aprobada_curriculo', 'aprobada_facultad', 'aprobado_transporte'].includes(p.estado) && (() => {
                    const fmtD = (iso?: string) => iso
                      ? new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' })
                      : '—';
                    if (p.ya_firme) {
                      return (
                        <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg">
                          <CheckCircle size={13} /> Consentimiento firmado
                        </span>
                      );
                    }
                    if (p.puede_firmar_ahora) {
                      return (
                        <button onClick={() => setAccionId({ tipo: 'firmar', id: p.id })}
                          className="flex items-center gap-1.5 text-xs font-semibold text-white bg-usco-gris hover:bg-usco-gris/90 px-3 py-1.5 rounded-lg transition-colors">
                          <CheckCircle size={13} /> Firmar consentimiento
                        </button>
                      );
                    }
                    // Ventana aún no abierta o ya cerrada
                    const ahora = new Date();
                    const vInicio = p.ventana_firma_inicio ? new Date(p.ventana_firma_inicio) : null;
                    if (vInicio && ahora < vInicio) {
                      return (
                        <span className="flex items-center gap-1.5 text-xs text-blue-700 bg-blue-50 border border-blue-200 px-3 py-1.5 rounded-lg">
                          <Clock size={13} /> Firma disponible: {fmtD(p.ventana_firma_inicio)} – {fmtD(p.ventana_firma_fin)}
                        </span>
                      );
                    }
                    return (
                      <span className="flex items-center gap-1.5 text-xs text-gray-500 bg-gray-50 border border-gray-200 px-3 py-1.5 rounded-lg">
                        <AlertCircle size={13} /> Ventana de firma cerrada
                      </span>
                    );
                  })()}

                  {user?.rol === 'estudiante' && p.ya_firme && (
                    <button
                      onClick={async () => {
                        try {
                          const r = await reportesService.getConsentimiento(p.id);
                          generarConsentimientoPDF(r.data);
                        } catch { /* silent */ }
                      }}
                      className="flex items-center gap-1.5 text-xs font-semibold text-usco-vinotinto border border-usco-vinotinto/30 hover:bg-usco-vinotinto/5 px-3 py-1.5 rounded-lg transition-colors">
                      <FileText size={13} /> Descargar consentimiento
                    </button>
                  )}

                  {p.estado === 'pendiente_quorum' && (
                    <span className="flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-lg">
                      <AlertTriangle size={13} /> Esperando quórum 66%
                    </span>
                  )}
                  {/* Iniciar práctica — docente titular cuando está aprobado_transporte */}
                  {user?.rol === 'profesor' && p.profesor_id === user.id && p.estado === 'aprobado_transporte' && (
                    <button onClick={() => setAccionId({ tipo: 'iniciar', id: p.id })}
                      className="flex items-center gap-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 px-3 py-1.5 rounded-lg transition-colors">
                      <Send size={13} /> Confirmar inicio
                    </button>
                  )}
                  {/* Finalizar — docente cuando en_ejecucion */}
                  {user?.rol === 'profesor' && p.profesor_id === user.id && p.estado === 'en_ejecucion' && (
                    <button onClick={() => setInformeModal(p.id)}
                      className="flex items-center gap-1.5 text-xs font-semibold text-white bg-usco-vinotinto hover:bg-usco-vinotinto-dark px-3 py-1.5 rounded-lg transition-colors">
                      <FileText size={13} /> Entregar informe
                    </button>
                  )}
                  {/* Cerrar — jefe/admin cuando en_ejecucion (si docente no entrega a tiempo) */}
                  {(user?.rol === 'jefe_programa' || user?.rol === 'admin') && p.estado === 'en_ejecucion' && (
                    <button onClick={() => setInformeModal(p.id)}
                      className="flex items-center gap-1.5 text-xs font-semibold text-white bg-usco-vinotinto hover:bg-usco-vinotinto-dark px-3 py-1.5 rounded-lg transition-colors">
                      <FileText size={13} /> Cerrar práctica
                    </button>
                  )}
                  {p.estado === 'aprobado_transporte' && user?.rol !== 'profesor' && (
                    <span className="flex items-center gap-1.5 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg">
                      <CheckCircle size={13} /> Listo para ejecución
                    </span>
                  )}

                  {(['jefe_programa', 'decano', 'profesor'].includes(user?.rol ?? '')) &&
                    !['borrador'].includes(p.estado) && (
                    <button
                      onClick={async () => {
                        try {
                          const r = await pdfService.fo16(p.id);
                          downloadBlob(new Blob([r.data], { type: 'application/pdf' }),
                            `FO-16_Practica${p.id}_${p.periodo_academico || ''}.pdf`);
                        } catch { /* silent */ }
                      }}
                      className="flex items-center gap-1.5 text-xs font-semibold text-usco-gris border border-gray-200 hover:text-usco-vinotinto hover:border-usco-vinotinto/30 px-3 py-1.5 rounded-lg transition-colors">
                      <FileText size={13} /> FO-16 PDF
                    </button>
                  )}

                  {(['jefe_programa', 'decano', 'profesor'].includes(user?.rol ?? '')) &&
                    ['aprobado_transporte', 'en_ejecucion', 'finalizada'].includes(p.estado) && (
                    <button
                      onClick={async () => {
                        try {
                          const r = await pdfService.fo15(p.id);
                          downloadBlob(new Blob([r.data], { type: 'application/pdf' }),
                            `FO-15_Participantes_Practica${p.id}.pdf`);
                        } catch { /* silent */ }
                      }}
                      className="flex items-center gap-1.5 text-xs font-semibold text-usco-vinotinto border border-usco-vinotinto/30 hover:bg-usco-vinotinto/5 px-3 py-1.5 rounded-lg transition-colors">
                      <FileText size={13} /> FO-15 PDF
                    </button>
                  )}

                  {(['jefe_programa', 'decano', 'profesor'].includes(user?.rol ?? '')) &&
                    ['aprobado_transporte', 'en_ejecucion', 'finalizada'].includes(p.estado) && (
                    <button
                      onClick={async () => {
                        try {
                          const r = await reportesService.getFO05(p.id);
                          generarFO05(r.data);
                        } catch { /* silent */ }
                      }}
                      className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 border border-emerald-200 hover:bg-emerald-50 px-3 py-1.5 rounded-lg transition-colors">
                      <Truck size={13} /> FO-05 PDF
                    </button>
                  )}

                  {user?.rol === 'admin' &&
                    ['aprobado_transporte', 'en_ejecucion', 'finalizada'].includes(p.estado) && (
                    <PagoViaticoButton practicaId={p.id} yaPagado={p.pago_registrado ?? false} />
                  )}
                </div>

                {/* Motivo de rechazo */}
                {p.estado === 'rechazada' && p.observaciones_jefe && (
                  <div className="mt-3 flex items-start gap-2 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                    <AlertTriangle size={13} className="text-red-500 mt-0.5 shrink-0" />
                    <p className="text-xs text-red-700"><span className="font-semibold">Motivo de rechazo:</span> {p.observaciones_jefe}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
