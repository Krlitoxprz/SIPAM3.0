import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthContext } from '../context/AuthContext';
import { Eye, EyeOff, GraduationCap } from 'lucide-react';

export function Login() {
  const navigate = useNavigate();
  const { login } = useAuthContext();
  const [codigo, setCodigo] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(codigo, password);
      navigate('/dashboard');
    } catch {
      setError('Código, cédula o contraseña incorrectos. Verifique sus credenciales.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <div className="hidden lg:flex lg:w-1/2 bg-usco-vinotinto flex-col justify-center items-center p-12 text-white">
        <div className="max-w-md text-center">
          <div className="bg-white/10 rounded-full p-6 inline-flex mb-8">
            <GraduationCap size={64} className="text-usco-ocre" />
          </div>
          <h1 className="text-4xl font-bold mb-4">SIPAM-USCO</h1>
          <p className="text-xl font-semibold text-usco-ocre mb-3">
            Sistema Integrado de Prácticas Académicas y Monitorías
          </p>
          <p className="text-white/80 text-sm leading-relaxed">
            Facultad de Ingeniería · Universidad Surcolombiana
          </p>
          <div className="mt-12 grid grid-cols-2 gap-4 text-left">
            {[
              { label: 'Monitorías', desc: 'Gestión MI-FOR-FO-14' },
              { label: 'Prácticas', desc: 'Gestión MI-FOR-FO-15' },
              { label: 'Presupuesto', desc: 'Control de viáticos' },
              { label: 'Reportes', desc: 'Actas digitales' },
            ].map((item) => (
              <div key={item.label} className="bg-white/10 rounded-lg p-4">
                <p className="font-semibold text-usco-ocre">{item.label}</p>
                <p className="text-sm text-white/70 mt-1">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col justify-center items-center p-8">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="lg:hidden mb-4">
              <GraduationCap size={48} className="text-usco-vinotinto mx-auto" />
            </div>
            <h2 className="text-3xl font-bold text-gray-800">Iniciar Sesión</h2>
            <p className="text-gray-500 mt-2">Ingresa con tu código o número de cédula</p>
          </div>

          {/* Accesos rápidos de prueba — solo en desarrollo */}
          {import.meta.env.DEV && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 mb-4">
              <p className="text-xs font-semibold text-gray-400 mb-3 uppercase tracking-wider">Acceso rápido — entorno de pruebas</p>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: 'Admin',       codigo: 'Krlitoxprz', pw: 'Sasuke24',  color: 'bg-gray-100 text-gray-700 hover:bg-gray-200' },
                  { label: 'Decano',      codigo: '12791500',   pw: 'sipam2025', color: 'bg-usco-vinotinto/10 text-usco-vinotinto hover:bg-usco-vinotinto/20' },
                  { label: 'Jefe Prog.',  codigo: '76001001',   pw: 'sipam2025', color: 'bg-purple-50 text-purple-700 hover:bg-purple-100' },
                  { label: 'Enc. Gastos',codigo: '12345100',   pw: 'sipam2025', color: 'bg-amber-50 text-amber-700 hover:bg-amber-100' },
                  { label: 'Profesor',    codigo: '87650001',   pw: 'sipam2025', color: 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100' },
                  { label: 'Estudiante',  codigo: '1136279761', pw: 'sipam2025', color: 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100' },
                ].map(u => (
                  <button key={u.codigo} type="button"
                    onClick={() => { setCodigo(u.codigo); setPassword(u.pw); }}
                    className={`text-xs font-semibold px-2 py-2 rounded-lg transition-colors ${u.color}`}>
                    {u.label}
                    <span className="block font-normal opacity-70 truncate">{u.codigo}</span>
                  </button>
                ))}
              </div>
              <p className="text-xs text-gray-400 mt-2 text-center">Clic para rellenar · Admin: Sasuke24 · Resto: sipam2025</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-lg p-8 space-y-5">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                Código institucional o Cédula
              </label>
              <input
                type="text"
                value={codigo}
                onChange={(e) => setCodigo(e.target.value)}
                placeholder="Ej: 36313456 · 7754321 · 2026115A1000"
                required
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto focus:border-transparent transition"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                Contraseña
              </label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Tu contraseña"
                  required
                  className="w-full border border-gray-300 rounded-lg px-4 py-2.5 pr-11 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto focus:border-transparent transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-usco-vinotinto hover:bg-usco-vinotinto-dark text-white font-semibold py-3 rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed mt-2"
            >
              {loading ? 'Verificando...' : 'Ingresar al Sistema'}
            </button>
            <div className="text-center">
              <Link to="/reset-password" className="text-xs text-usco-vinotinto hover:underline">
                ¿Olvidaste tu contraseña?
              </Link>
            </div>
          </form>

          <p className="text-center text-xs text-gray-400 mt-6">
            Universidad Surcolombiana · Facultad de Ingeniería<br />
            Neiva, Huila — Colombia
          </p>
        </div>
      </div>
    </div>
  );
}
