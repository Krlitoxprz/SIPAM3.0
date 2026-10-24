import { useEffect, useRef, useState } from 'react';
import { MapPin, Navigation, Loader2, AlertCircle } from 'lucide-react';
import { geoService } from '../../services/api';

interface PuntoRuta {
  orden: number;
  tipo_punto: string;
  municipio: string;
  departamento: string;
  lugar?: string;
  distancia_km?: string;
}

interface Coords {
  lat: number;
  lon: number;
  label: string;
  tipo: string;
}

interface MapaRutaProps {
  rutas: PuntoRuta[];
  className?: string;
}

const TIPO_COLOR: Record<string, string> = {
  origen: '#10b981',
  waypoint: '#3b82f6',
  destino: '#ef4444',
};

const TIPO_LABEL: Record<string, string> = {
  origen: 'Origen',
  waypoint: 'Escala',
  destino: 'Destino',
};

export function MapaRuta({ rutas, className = '' }: MapaRutaProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<import('leaflet').Map | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [coordsList, setCoordsList] = useState<Coords[]>([]);
  const [distanciaTotal, setDistanciaTotal] = useState<number | null>(null);

  const puntosValidos = rutas.filter(r => r.municipio && r.departamento);

  useEffect(() => {
    if (puntosValidos.length < 2) {
      setCoordsList([]);
      setDistanciaTotal(null);
      setError('');
      return;
    }

    let cancelled = false;
    async function geocodeAll() {
      setLoading(true);
      setError('');
      try {
        const promises = puntosValidos.map(p =>
          geoService.geocodificar(p.municipio, p.departamento)
            .then(r => ({
              lat: (r.data as { lat: number; lon: number }).lat,
              lon: (r.data as { lat: number; lon: number }).lon,
              label: p.lugar ? `${p.lugar}, ${p.municipio}` : `${p.municipio} (${p.departamento})`,
              tipo: p.tipo_punto,
            }))
            .catch(() => null)
        );
        const results = (await Promise.all(promises)).filter(Boolean) as Coords[];
        if (cancelled) return;
        setCoordsList(results);

        let total = 0;
        for (let i = 0; i < puntosValidos.length - 1; i++) {
          const km = parseFloat(puntosValidos[i + 1].distancia_km ?? '0');
          if (!isNaN(km)) total += km;
        }
        setDistanciaTotal(total > 0 ? total : null);
      } catch {
        if (!cancelled) setError('No se pudo geocodificar la ruta');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    geocodeAll();
    return () => { cancelled = true; };
  }, [JSON.stringify(puntosValidos.map(p => `${p.municipio}-${p.departamento}`))]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!mapRef.current || coordsList.length < 1) return;

    import('leaflet').then(L => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }

      const map = L.map(mapRef.current!, { zoomControl: true, scrollWheelZoom: false });
      mapInstanceRef.current = map;

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 18,
      }).addTo(map);

      const latLngs: [number, number][] = coordsList.map(c => [c.lat, c.lon]);

      coordsList.forEach((c, i) => {
        const color = TIPO_COLOR[c.tipo] ?? '#6b7280';
        const icon = L.divIcon({
          className: '',
          html: `<div style="
            width:28px;height:28px;border-radius:50% 50% 50% 0;
            background:${color};border:2px solid white;
            box-shadow:0 2px 6px rgba(0,0,0,.4);
            transform:rotate(-45deg);display:flex;align-items:center;justify-content:center;">
            <span style="transform:rotate(45deg);color:white;font-weight:bold;font-size:11px;">${i + 1}</span>
          </div>`,
          iconSize: [28, 28],
          iconAnchor: [14, 28],
          popupAnchor: [0, -30],
        });
        L.marker([c.lat, c.lon], { icon })
          .addTo(map)
          .bindPopup(`<strong>${TIPO_LABEL[c.tipo] ?? 'Punto'} ${i + 1}</strong><br/>${c.label}`);
      });

      if (latLngs.length >= 2) {
        L.polyline(latLngs, { color: '#8D191D', weight: 3, opacity: 0.75, dashArray: '6 4' }).addTo(map);
      }

      const bounds = L.latLngBounds(latLngs);
      map.fitBounds(bounds, { padding: [30, 30] });
    });

    return () => {
      mapInstanceRef.current?.remove();
      mapInstanceRef.current = null;
    };
  }, [coordsList]);

  if (puntosValidos.length < 2) {
    return (
      <div className={`flex items-center justify-center h-40 bg-gray-50 rounded-xl border border-dashed border-gray-300 text-gray-400 text-sm gap-2 ${className}`}>
        <MapPin size={16} /> Selecciona al menos 2 municipios para ver el mapa
      </div>
    );
  }

  return (
    <div className={`rounded-xl overflow-hidden border border-gray-200 ${className}`}>
      {loading && (
        <div className="flex items-center justify-center h-52 bg-gray-50 text-gray-500 text-sm gap-2">
          <Loader2 size={16} className="animate-spin" /> Geocodificando ruta…
        </div>
      )}
      {error && !loading && (
        <div className="flex items-center justify-center h-52 bg-red-50 text-red-600 text-sm gap-2">
          <AlertCircle size={16} /> {error}
        </div>
      )}
      {!loading && !error && (
        <>
          <div ref={mapRef} style={{ height: '240px', width: '100%' }} />
          {distanciaTotal !== null && (
            <div className="bg-gray-50 border-t border-gray-200 px-3 py-2 flex items-center gap-1.5 text-xs text-gray-600">
              <Navigation size={13} className="text-usco-vinotinto" />
              <span>Distancia total aprox.: <strong>{distanciaTotal.toFixed(1)} km</strong></span>
              <span className="ml-auto text-gray-400">© OpenStreetMap · OSRM</span>
            </div>
          )}
        </>
      )}
    </div>
  );
}
