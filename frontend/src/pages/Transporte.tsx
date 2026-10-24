import { useState, useEffect } from 'react';
import {
  Fuel, MapPin, Navigation, AlertCircle, Loader2, CheckCircle,
  Route, Info, RefreshCw, ChevronDown, ChevronUp,
} from 'lucide-react';
import { transporteService } from '../services/api';

// ── Tipos locales ─────────────────────────────────────────────────────────────

interface PrecioCombustible {
  tipo: string;
  precio_litro_cop: number;
  fecha_vigencia: string;
  fuente: string;
  actualizado_en: string | null;
}

interface PeajeDetalle {
  id: number;
  nombre: string;
  departamento: string;
  municipio: string | null;
  corredor: string | null;
  tarifa_cop: number;
  distancia_ruta_km: number | null;
}

interface ResultadoRuta {
  origen: string;
  destino: string;
  ruta: {
    distancia_km_ida: number | null;
    distancia_km_ida_vuelta: number | null;
    duracion_min: number | null;
    fuente: string;
  };
  combustible: {
    tipo: string;
    rendimiento_km_litro: number;
    litros_estimados: number | null;
    precio_litro_cop: number;
    costo_cop: number | null;
    fuente_precio: string;
    fecha_precio: string;
  };
  peajes: {
    categoria_vehiculo: number;
    num_peajes: number;
    detalle: PeajeDetalle[];
    costo_unitario_cop: number;
    costo_total_cop: number | null;
    metodo_deteccion: string;
  };
  resumen: {
    num_vehiculos: number;
    costo_combustible_cop: number | null;
    costo_peajes_cop: number | null;
    total_estimado_cop: number | null;
  };
  nota: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const TIPO_LABELS: Record<string, string> = {
  gasolina_corriente: 'Gasolina Corriente',
  diesel: 'ACPM / Diésel',
  gasolina_extra: 'Gasolina Extra',
};

const VEHICULO_LABELS: Record<string, string> = {
  bus: 'Bus / Van escolar',
  camioneta: 'Camioneta 4WD',
  moto: 'Moto',
};

const CAT_LABELS: Record<number, string> = {
  1: 'Cat 1 — Auto / camioneta / moto',
  2: 'Cat 2 — Bus 2 ejes liviano (≤30 pas.)',
  3: 'Cat 3 — Bus 2 ejes pesado / van escolar',
  4: 'Cat 4 — Camión 2 ejes',
  5: 'Cat 5 — Camión 3+ ejes',
};

function cop(n: number | null | undefined): string {
  if (n == null) return '—';
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n);
}

function duracionFmt(min: number | null): string {
  if (min == null) return '—';
  const h = Math.floor(min / 60);
  const m = min % 60;
  return h > 0 ? `${h}h ${m}min` : `${m}min`;
}

// ── Componente ────────────────────────────────────────────────────────────────

export function Transporte() {
  const [precios, setPrecios] = useState<PrecioCombustible[]>([]);
  const [loadingPrecios, setLoadingPrecios] = useState(true);

  const [origen, setOrigen] = useState('');
  const [destino, setDestino] = useState('');
  const [tipoVehiculo, setTipoVehiculo] = useState('bus');
  const [numVehiculos, setNumVehiculos] = useState(1);
  const [categoriaPeaje, setCategoriaPeaje] = useState(3);
  const [tipoCombustible, setTipoCombustible] = useState('diesel');
  const [calculando, setCalculando] = useState(false);
  const [resultado, setResultado] = useState<ResultadoRuta | null>(null);
  const [errorCalc, setErrorCalc] = useState('');
  const [showPeajes, setShowPeajes] = useState(true);

  useEffect(() => {
    transporteService.getPrecios()
      .then(r => setPrecios(r.data.precios ?? []))
      .catch(() => setPrecios([]))
      .finally(() => setLoadingPrecios(false));
  }, []);

  async function handleCalcular(e: React.FormEvent) {
    e.preventDefault();
    if (!origen.trim() || !destino.trim()) return;
    setCalculando(true);
    setErrorCalc('');
    setResultado(null);
    try {
      const r = await transporteService.calcularRuta({
        origen: origen.trim(),
        destino: destino.trim(),
        tipo_vehiculo: tipoVehiculo,
        num_vehiculos: numVehiculos,
        categoria_peaje: categoriaPeaje,
        tipo_combustible: tipoCombustible,
      });
      setResultado(r.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErrorCalc(msg ?? 'Error al calcular la ruta.');
    } finally {
      setCalculando(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <Route size={22} className="text-usco-vinotinto" /> Calculadora de Transporte
        </h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Estima costos de combustible y peajes para prácticas extramuros. Precios actualizados diariamente desde SICOM.
        </p>
      </div>

      {/* Precios de combustible */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-gray-700 flex items-center gap-2">
            <Fuel size={16} className="text-amber-500" /> Precios vigentes de combustible (Huila)
          </h2>
          <span className="text-[10px] text-gray-400 flex items-center gap-1">
            <RefreshCw size={10} /> Actualizado diariamente · Fuente: SICOM
          </span>
        </div>
        {loadingPrecios ? (
          <div className="flex items-center gap-2 text-gray-400 text-sm"><Loader2 size={14} className="animate-spin" /> Cargando...</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {precios.map(p => (
              <div key={p.tipo} className="bg-amber-50 border border-amber-100 rounded-xl px-4 py-3">
                <p className="text-[11px] text-amber-600 font-semibold uppercase tracking-wide">{TIPO_LABELS[p.tipo] ?? p.tipo}</p>
                <p className="text-2xl font-bold text-amber-700 mt-0.5">{cop(p.precio_litro_cop)}</p>
                <p className="text-[10px] text-amber-500 mt-0.5">por litro · vigente {p.fecha_vigencia}</p>
              </div>
            ))}
            {precios.length === 0 && (
              <p className="text-sm text-gray-400 col-span-3">No hay precios disponibles. El servidor los actualiza al iniciar.</p>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-5 items-start">

        {/* Formulario calculadora */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h2 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
            <Navigation size={16} className="text-usco-vinotinto" /> Calcular trayecto
          </h2>
          <form onSubmit={handleCalcular} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                  <MapPin size={12} className="inline mr-1 text-gray-400" /> Ciudad de origen *
                </label>
                <input
                  required
                  value={origen}
                  onChange={e => setOrigen(e.target.value)}
                  placeholder="Ej: Neiva"
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                  <MapPin size={12} className="inline mr-1 text-usco-vinotinto" /> Ciudad de destino *
                </label>
                <input
                  required
                  value={destino}
                  onChange={e => setDestino(e.target.value)}
                  placeholder="Ej: Pitalito"
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Tipo de vehículo</label>
                <select value={tipoVehiculo} onChange={e => setTipoVehiculo(e.target.value)}
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
                  {Object.entries(VEHICULO_LABELS).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Número de vehículos</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={numVehiculos}
                  onChange={e => setNumVehiculos(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Combustible</label>
                <select value={tipoCombustible} onChange={e => setTipoCombustible(e.target.value)}
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
                  <option value="diesel">ACPM / Diésel</option>
                  <option value="gasolina_corriente">Gasolina Corriente</option>
                  <option value="gasolina_extra">Gasolina Extra</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Categoría peaje</label>
                <select value={categoriaPeaje} onChange={e => setCategoriaPeaje(parseInt(e.target.value))}
                  className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
                  {Object.entries(CAT_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>
            </div>

            {errorCalc && (
              <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 text-xs px-3 py-2.5 rounded-lg">
                <AlertCircle size={14} /> {errorCalc}
              </div>
            )}

            <button type="submit" disabled={calculando}
              className="w-full flex items-center justify-center gap-2 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 transition-colors">
              {calculando ? <Loader2 size={15} className="animate-spin" /> : <Navigation size={15} />}
              {calculando ? 'Calculando...' : 'Calcular costo de trayecto'}
            </button>
          </form>

          {/* Resultado */}
          {resultado && (
            <div className="mt-5 space-y-4 border-t border-gray-100 pt-5">
              {/* Ruta */}
              <div className="flex items-center gap-3 text-sm">
                <div className="flex items-center gap-1.5 font-semibold text-gray-700">
                  <MapPin size={14} className="text-gray-400" /> {resultado.origen}
                </div>
                <span className="text-gray-300">→</span>
                <div className="flex items-center gap-1.5 font-semibold text-gray-700">
                  <MapPin size={14} className="text-usco-vinotinto" /> {resultado.destino}
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-blue-50 rounded-xl p-3 text-center">
                  <p className="text-[10px] text-blue-500 font-semibold uppercase">Distancia (ida)</p>
                  <p className="text-lg font-bold text-blue-700 mt-0.5">
                    {resultado.ruta.distancia_km_ida != null ? `${resultado.ruta.distancia_km_ida} km` : '—'}
                  </p>
                </div>
                <div className="bg-purple-50 rounded-xl p-3 text-center">
                  <p className="text-[10px] text-purple-500 font-semibold uppercase">Duración</p>
                  <p className="text-lg font-bold text-purple-700 mt-0.5">{duracionFmt(resultado.ruta.duracion_min)}</p>
                </div>
                <div className="bg-orange-50 rounded-xl p-3 text-center">
                  <p className="text-[10px] text-orange-500 font-semibold uppercase">Peajes</p>
                  <p className="text-lg font-bold text-orange-700 mt-0.5">{resultado.peajes.num_peajes}</p>
                </div>
              </div>

              {/* Fuente ruta */}
              <p className="text-[10px] text-gray-400 flex items-center gap-1">
                <Info size={10} /> Ruta: {resultado.ruta.fuente}
              </p>

              {/* Desglose de costos */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold text-gray-600 uppercase tracking-wide">Desglose de costos (ida + vuelta)</h3>
                {[
                  { label: 'Combustible', value: resultado.resumen.costo_combustible_cop,
                    sub: `${resultado.combustible.litros_estimados ?? '—'} L × ${cop(resultado.combustible.precio_litro_cop)}/L`, color: 'text-amber-600' },
                  { label: 'Peajes', value: resultado.resumen.costo_peajes_cop,
                    sub: `${resultado.peajes.num_peajes} peaje(s) × 2 trayectos × ${numVehiculos} vehículo(s)`, color: 'text-orange-600' },
                ].map(item => (
                  <div key={item.label} className="flex items-center justify-between text-sm py-1.5 border-b border-gray-50">
                    <div>
                      <p className="font-semibold text-gray-700">{item.label}</p>
                      <p className="text-[10px] text-gray-400">{item.sub}</p>
                    </div>
                    <span className={`font-bold ${item.color}`}>{cop(item.value)}</span>
                  </div>
                ))}
                <div className="flex items-center justify-between pt-2">
                  <p className="text-sm font-bold text-gray-800">Total estimado</p>
                  <p className="text-lg font-bold text-usco-vinotinto">{cop(resultado.resumen.total_estimado_cop)}</p>
                </div>
              </div>

              {/* Peajes detalle */}
              {resultado.peajes.detalle.length > 0 && (
                <div>
                  <button onClick={() => setShowPeajes(v => !v)}
                    className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-gray-700">
                    {showPeajes ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                    Ver {resultado.peajes.detalle.length} peaje(s) en la ruta
                  </button>
                  {showPeajes && (
                    <div className="mt-2 space-y-1.5">
                      {resultado.peajes.detalle.map(p => (
                        <div key={p.id} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2 text-xs">
                          <div>
                            <p className="font-semibold text-gray-700">{p.nombre}</p>
                            <p className="text-gray-400">{p.departamento}{p.corredor ? ` · ${p.corredor}` : ''}</p>
                          </div>
                          <span className="font-bold text-gray-700">{cop(p.tarifa_cop)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Nota */}
              <p className="text-[10px] text-gray-400 bg-gray-50 rounded-lg px-3 py-2 flex items-start gap-1.5">
                <Info size={10} className="mt-0.5 shrink-0" /> {resultado.nota}
              </p>
            </div>
          )}
        </div>

        {/* Panel info lateral */}
        <div className="space-y-4">
          {/* Cómo funciona */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
              <Info size={15} className="text-blue-500" /> Cómo funciona
            </h3>
            <div className="space-y-3 text-xs text-gray-500">
              <div className="flex items-start gap-2">
                <div className="w-5 h-5 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center text-[10px] font-bold shrink-0">1</div>
                <p><strong className="text-gray-700">Precios combustible</strong> — Se actualizan cada día a las 6:00 a.m. desde el portal SICOM del Ministerio de Minas.</p>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-[10px] font-bold shrink-0">2</div>
                <p><strong className="text-gray-700">Rutas y distancias</strong> — Usa OpenRouteService (OSM) para calcular la ruta real por carretera. Requiere API key en <code className="bg-gray-100 px-1 rounded">ORS_API_KEY</code>.</p>
              </div>
              <div className="flex items-start gap-2">
                <div className="w-5 h-5 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center text-[10px] font-bold shrink-0">3</div>
                <p><strong className="text-gray-700">Peajes</strong> — Base de datos con los ~40 principales peajes nacionales (INVIAS/ANI 2024-2025). Se detectan automáticamente en la ruta.</p>
              </div>
            </div>
          </div>

          {/* ORS configuración */}
          <div className="bg-blue-50 border border-blue-100 rounded-2xl p-4 text-xs text-blue-700 space-y-2">
            <p className="font-bold flex items-center gap-1.5"><CheckCircle size={13} /> Activar rutas reales (ORS)</p>
            <ol className="list-decimal list-inside space-y-1 text-blue-600">
              <li>Regístrate gratis en <strong>openrouteservice.org</strong></li>
              <li>Copia tu API key (2 000 req/día gratis)</li>
              <li>Agrega en <code className="bg-blue-100 px-1 rounded">.env</code>:<br /><code className="bg-blue-100 px-1 rounded">ORS_API_KEY=tu_clave_aquí</code></li>
              <li>Reinicia el servidor backend</li>
            </ol>
            <p className="text-blue-500">Sin ORS: la calculadora detecta peajes por municipio y requiere que ingreses la distancia manualmente.</p>
          </div>

          {/* Rendimientos */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Rendimiento de vehículos</h3>
            <div className="space-y-2 text-sm">
              {[
                { vehiculo: 'Bus / Van escolar', rendimiento: '8.5 km/L', combustible: 'ACPM' },
                { vehiculo: 'Camioneta 4WD', rendimiento: '11.0 km/L', combustible: 'Gasolina' },
                { vehiculo: 'Moto', rendimiento: '35.0 km/L', combustible: 'Gasolina' },
              ].map(v => (
                <div key={v.vehiculo} className="flex items-center justify-between text-xs">
                  <span className="text-gray-600">{v.vehiculo}</span>
                  <div className="text-right">
                    <span className="font-semibold text-gray-700">{v.rendimiento}</span>
                    <span className="text-gray-400 ml-1">({v.combustible})</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
