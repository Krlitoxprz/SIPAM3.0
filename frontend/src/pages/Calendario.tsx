import { useState, useEffect } from 'react';
import { Calendar, ChevronLeft, ChevronRight, BookOpen, MapPin } from 'lucide-react';
import { convocatoriasService, practicasService } from '../services/api';

interface Evento {
  id: string;
  titulo: string;
  fecha: Date;
  fechaFin?: Date;
  tipo: 'convocatoria_abre' | 'convocatoria_cierra' | 'convocatoria_resultados' | 'practica_inicio' | 'practica_fin';
  color: string;
}

const TIPO_CONFIG: Record<Evento['tipo'], { label: string; color: string; icon: React.ReactNode }> = {
  convocatoria_abre: { label: 'Abre postulación', color: 'bg-emerald-100 text-emerald-700 border-emerald-300', icon: <BookOpen size={11} /> },
  convocatoria_cierra: { label: 'Cierra postulación', color: 'bg-orange-100 text-orange-700 border-orange-300', icon: <BookOpen size={11} /> },
  convocatoria_resultados: { label: 'Publicación resultados', color: 'bg-indigo-100 text-indigo-700 border-indigo-300', icon: <BookOpen size={11} /> },
  practica_inicio: { label: 'Inicio práctica', color: 'bg-usco-vinotinto/10 text-usco-vinotinto border-usco-vinotinto/30', icon: <MapPin size={11} /> },
  practica_fin: { label: 'Fin práctica', color: 'bg-gray-100 text-gray-600 border-gray-300', icon: <MapPin size={11} /> },
};

const MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
const DIAS = ['Dom','Lun','Mar','Mié','Jue','Vie','Sáb'];

function mismodia(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

export function Calendario() {
  const hoy = new Date();
  const [año, setAño] = useState(hoy.getFullYear());
  const [mes, setMes] = useState(hoy.getMonth());
  const [eventos, setEventos] = useState<Evento[]>([]);
  const [loading, setLoading] = useState(true);
  const [seleccionado, setSeleccionado] = useState<Date | null>(null);

  useEffect(() => {
    async function cargar() {
      setLoading(true);
      const evts: Evento[] = [];
      try {
        const [convRes, praRes] = await Promise.all([
          convocatoriasService.getAll(),
          practicasService.getAll(),
        ]);
        for (const c of convRes.data) {
          if (c.fecha_inicio_postulacion)
            evts.push({ id: `ci-${c.id}`, titulo: c.titulo, fecha: new Date(c.fecha_inicio_postulacion), tipo: 'convocatoria_abre', color: '' });
          if (c.fecha_fin_postulacion)
            evts.push({ id: `cf-${c.id}`, titulo: c.titulo, fecha: new Date(c.fecha_fin_postulacion), tipo: 'convocatoria_cierra', color: '' });
          if (c.fecha_publicacion_resultados)
            evts.push({ id: `cr-${c.id}`, titulo: c.titulo, fecha: new Date(c.fecha_publicacion_resultados), tipo: 'convocatoria_resultados', color: '' });
        }
        for (const p of praRes.data) {
          if (p.fecha_inicio)
            evts.push({ id: `pi-${p.id}`, titulo: p.nombre_practica, fecha: new Date(p.fecha_inicio), tipo: 'practica_inicio', color: '' });
          if (p.fecha_fin)
            evts.push({ id: `pf-${p.id}`, titulo: p.nombre_practica, fecha: new Date(p.fecha_fin), tipo: 'practica_fin', color: '' });
        }
      } catch { /* silencioso */ }
      setEventos(evts);
      setLoading(false);
    }
    cargar();
  }, []);

  function navegar(delta: number) {
    let m = mes + delta;
    let a = año;
    if (m < 0) { m = 11; a--; }
    if (m > 11) { m = 0; a++; }
    setMes(m); setAño(a); setSeleccionado(null);
  }

  const primerDia = new Date(año, mes, 1).getDay();
  const diasEnMes = new Date(año, mes + 1, 0).getDate();
  const celdas = Array.from({ length: Math.ceil((primerDia + diasEnMes) / 7) * 7 }, (_, i) => {
    const d = i - primerDia + 1;
    return (d >= 1 && d <= diasEnMes) ? new Date(año, mes, d) : null;
  });

  const eventosDelDia = (dia: Date) => eventos.filter(e => mismodia(e.fecha, dia));
  const eventosSeleccionados = seleccionado ? eventosDelDia(seleccionado) : [];

  const proximosEventos = eventos
    .filter(e => e.fecha >= hoy)
    .sort((a, b) => a.fecha.getTime() - b.fecha.getTime())
    .slice(0, 8);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <Calendar size={20} className="text-usco-vinotinto" /> Calendario
        </h1>
        <p className="text-sm text-gray-500 mt-0.5">Convocatorias y prácticas en el tiempo</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Calendario */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-100 shadow-sm p-4">
          <div className="flex items-center justify-between mb-4">
            <button onClick={() => navegar(-1)} className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
              <ChevronLeft size={18} className="text-gray-600" />
            </button>
            <h2 className="font-bold text-gray-800">{MESES[mes]} {año}</h2>
            <button onClick={() => navegar(1)} className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
              <ChevronRight size={18} className="text-gray-600" />
            </button>
          </div>

          <div className="grid grid-cols-7 mb-2">
            {DIAS.map(d => (
              <div key={d} className="text-center text-xs font-semibold text-gray-400 py-1">{d}</div>
            ))}
          </div>

          {loading ? (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">Cargando eventos…</div>
          ) : (
            <div className="grid grid-cols-7 gap-px bg-gray-100 rounded-lg overflow-hidden border border-gray-100">
              {celdas.map((dia, idx) => {
                const esHoy = dia && mismodia(dia, hoy);
                const esSel = dia && seleccionado && mismodia(dia, seleccionado);
                const evts = dia ? eventosDelDia(dia) : [];
                return (
                  <div key={idx}
                    onClick={() => dia && setSeleccionado(dia)}
                    className={`bg-white min-h-[64px] p-1.5 cursor-pointer hover:bg-gray-50 transition-colors ${!dia ? 'opacity-0 pointer-events-none' : ''} ${esSel ? 'ring-2 ring-inset ring-usco-vinotinto' : ''}`}>
                    {dia && (
                      <>
                        <p className={`text-xs font-semibold w-6 h-6 flex items-center justify-center rounded-full mb-1 ${esHoy ? 'bg-usco-vinotinto text-white' : 'text-gray-600'}`}>
                          {dia.getDate()}
                        </p>
                        <div className="space-y-0.5">
                          {evts.slice(0, 2).map(e => {
                            const cfg = TIPO_CONFIG[e.tipo];
                            return (
                              <div key={e.id} className={`text-[9px] font-semibold px-1 py-0.5 rounded truncate border ${cfg.color}`}>
                                {e.titulo}
                              </div>
                            );
                          })}
                          {evts.length > 2 && (
                            <div className="text-[9px] text-gray-400 px-1">+{evts.length - 2} más</div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Leyenda */}
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(TIPO_CONFIG).map(([tipo, cfg]) => (
              <div key={tipo} className={`flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${cfg.color}`}>
                {cfg.icon} {cfg.label}
              </div>
            ))}
          </div>
        </div>

        {/* Panel lateral */}
        <div className="space-y-4">
          {/* Eventos del día seleccionado */}
          {seleccionado && (
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <h3 className="font-bold text-sm text-gray-700 mb-3">
                {seleccionado.toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long' })}
              </h3>
              {eventosSeleccionados.length === 0 ? (
                <p className="text-xs text-gray-400">Sin eventos este día</p>
              ) : eventosSeleccionados.map(e => {
                const cfg = TIPO_CONFIG[e.tipo];
                return (
                  <div key={e.id} className={`flex items-center gap-2 text-xs font-semibold px-2.5 py-2 rounded-lg border mb-2 ${cfg.color}`}>
                    {cfg.icon}
                    <div>
                      <p className="font-bold truncate">{e.titulo}</p>
                      <p className="font-normal opacity-80">{cfg.label}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Próximos eventos */}
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
            <h3 className="font-bold text-sm text-gray-700 mb-3">Próximos eventos</h3>
            {proximosEventos.length === 0 ? (
              <p className="text-xs text-gray-400">No hay eventos próximos</p>
            ) : proximosEventos.map(e => {
              const cfg = TIPO_CONFIG[e.tipo];
              const dias = Math.ceil((e.fecha.getTime() - hoy.getTime()) / 86400000);
              return (
                <div key={e.id} className="flex items-start gap-2 py-2 border-b border-gray-50 last:border-0">
                  <div className={`shrink-0 w-8 h-8 rounded-lg flex items-center justify-center border ${cfg.color}`}>
                    {cfg.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-gray-800 truncate">{e.titulo}</p>
                    <p className="text-[10px] text-gray-400">{cfg.label} · {e.fecha.toLocaleDateString('es-CO')}</p>
                  </div>
                  <span className={`shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded-full ${dias <= 3 ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-500'}`}>
                    {dias === 0 ? 'Hoy' : `${dias}d`}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
