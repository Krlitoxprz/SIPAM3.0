import { useNavigate } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';

export function NotFound() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 text-center px-4">
      <AlertTriangle size={64} className="text-usco-vinotinto mb-4 opacity-60" />
      <h1 className="text-5xl font-bold text-gray-800 mb-2">404</h1>
      <p className="text-xl text-gray-600 mb-1">Página no encontrada</p>
      <p className="text-sm text-gray-400 mb-8">
        La ruta que estás buscando no existe en SIPAM-USCO.
      </p>
      <button
        onClick={() => navigate('/dashboard')}
        className="bg-usco-vinotinto hover:bg-usco-vinotinto-dark text-white font-semibold px-6 py-3 rounded-lg transition-colors"
      >
        Volver al Inicio
      </button>
    </div>
  );
}
