import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { GraduationCap, KeyRound, Mail, CheckCircle, ArrowLeft, Eye, EyeOff } from 'lucide-react';
import { resetPasswordService } from '../services/api';

export function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get('token');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [ok, setOk] = useState(false);

  async function handleSolicitar(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await resetPasswordService.solicitar(email.trim());
      setOk(true);
    } catch {
      setError('Ocurrió un error. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirmar(e: React.FormEvent) {
    e.preventDefault();
    if (password !== passwordConfirm) { setError('Las contraseñas no coinciden.'); return; }
    if (password.length < 8) { setError('La contraseña debe tener al menos 8 caracteres.'); return; }
    setError('');
    setLoading(true);
    try {
      await resetPasswordService.confirmar(token!, password);
      setOk(true);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? 'Token inválido o expirado. Solicita un nuevo enlace.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <GraduationCap size={48} className="text-usco-vinotinto mx-auto mb-3" />
          <h1 className="text-2xl font-bold text-gray-800">SIPAM-USCO</h1>
          <p className="text-gray-500 text-sm mt-1">Recuperación de contraseña</p>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-8">
          {ok ? (
            <div className="text-center py-4">
              <CheckCircle size={48} className="text-emerald-500 mx-auto mb-4" />
              <h2 className="text-lg font-bold text-gray-800 mb-2">
                {token ? '¡Contraseña actualizada!' : 'Correo enviado'}
              </h2>
              <p className="text-sm text-gray-500 mb-6">
                {token
                  ? 'Tu contraseña fue restablecida exitosamente. Ya puedes iniciar sesión.'
                  : 'Si el correo está registrado, recibirás un enlace en los próximos minutos.'}
              </p>
              <Link to="/login"
                className="inline-flex items-center gap-2 bg-usco-vinotinto text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-usco-vinotinto/90">
                <ArrowLeft size={15} /> Ir al inicio de sesión
              </Link>
            </div>
          ) : token ? (
            <>
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-usco-vinotinto/10 p-2.5 rounded-lg">
                  <KeyRound size={20} className="text-usco-vinotinto" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-gray-800">Crear nueva contraseña</h2>
                  <p className="text-xs text-gray-400">Mínimo 8 caracteres</p>
                </div>
              </div>
              {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>}
              <form onSubmit={handleConfirmar} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1.5">Nueva contraseña</label>
                  <div className="relative">
                    <input type={showPass ? 'text' : 'password'} required value={password}
                      onChange={e => setPassword(e.target.value)}
                      className="w-full border border-gray-300 rounded-lg px-4 py-2.5 pr-11 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto" />
                    <button type="button" onClick={() => setShowPass(!showPass)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                      {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1.5">Confirmar contraseña</label>
                  <input type={showPass ? 'text' : 'password'} required value={passwordConfirm}
                    onChange={e => setPasswordConfirm(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto" />
                </div>
                <button type="submit" disabled={loading}
                  className="w-full bg-usco-vinotinto text-white font-semibold py-2.5 rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 mt-2">
                  {loading ? 'Guardando...' : 'Guardar contraseña'}
                </button>
              </form>
            </>
          ) : (
            <>
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-usco-vinotinto/10 p-2.5 rounded-lg">
                  <Mail size={20} className="text-usco-vinotinto" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-gray-800">Restablecer contraseña</h2>
                  <p className="text-xs text-gray-400">Ingresa tu correo institucional</p>
                </div>
              </div>
              {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>}
              <form onSubmit={handleSolicitar} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1.5">Correo electrónico</label>
                  <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
                    placeholder="usuario@usco.edu.co"
                    className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto" />
                </div>
                <button type="submit" disabled={loading}
                  className="w-full bg-usco-vinotinto text-white font-semibold py-2.5 rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60">
                  {loading ? 'Enviando...' : 'Enviar enlace de recuperación'}
                </button>
              </form>
            </>
          )}
          {!ok && (
            <div className="mt-4 text-center">
              <Link to="/login" className="text-xs text-gray-400 hover:text-usco-vinotinto flex items-center justify-center gap-1">
                <ArrowLeft size={12} /> Volver al inicio de sesión
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
