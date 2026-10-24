import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { SystemProvider } from './context/SystemContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { MainLayout } from './components/layout/MainLayout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Convocatorias } from './pages/Convocatorias';
import { Postulaciones } from './pages/Postulaciones';
import { Practicas } from './pages/Practicas';
import { Presupuesto } from './pages/Presupuesto';
import { Evaluaciones } from './pages/Evaluaciones';
import { Usuarios } from './pages/Usuarios';
import { Configuracion } from './pages/Configuracion';
import { Reportes } from './pages/Reportes';
import { Perfil } from './pages/Perfil';
import { MonitorHoras } from './pages/MonitorHoras';
import { Notificaciones } from './pages/Notificaciones';
import { Transporte } from './pages/Transporte';
import { NotFound } from './pages/NotFound';
import { ResetPassword } from './pages/ResetPassword';
import { Calendario } from './pages/Calendario';
import { AdminPanel } from './pages/AdminPanel';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <SystemProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          <Route
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/convocatorias" element={<Convocatorias />} />
            <Route path="/postulaciones" element={
              <ProtectedRoute allowedRoles={['estudiante']}>
                <Postulaciones />
              </ProtectedRoute>
            } />
            <Route path="/evaluaciones" element={
              <ProtectedRoute allowedRoles={['profesor']}>
                <Evaluaciones />
              </ProtectedRoute>
            } />
            <Route path="/practicas" element={<Practicas />} />
            <Route path="/presupuesto" element={
              <ProtectedRoute allowedRoles={['jefe_programa', 'decano', 'admin']}>
                <Presupuesto />
              </ProtectedRoute>
            } />
            <Route path="/usuarios" element={
              <ProtectedRoute allowedRoles={['admin']}>
                <Usuarios />
              </ProtectedRoute>
            } />
            <Route path="/reportes" element={
              <ProtectedRoute allowedRoles={['decano', 'admin']}>
                <Reportes />
              </ProtectedRoute>
            } />
            <Route path="/configuracion" element={
              <ProtectedRoute allowedRoles={['admin']}>
                <Configuracion />
              </ProtectedRoute>
            } />
            <Route path="/perfil" element={<Perfil />} />
            <Route path="/monitor-horas" element={
              <ProtectedRoute allowedRoles={['estudiante', 'profesor', 'jefe_programa', 'decano']}>
                <MonitorHoras />
              </ProtectedRoute>
            } />
            <Route path="/notificaciones" element={<Notificaciones />} />
            <Route path="/transporte" element={
              <ProtectedRoute allowedRoles={['admin']}>
                <Transporte />
              </ProtectedRoute>
            } />
            <Route path="/calendario" element={<Calendario />} />
            <Route path="/admin" element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AdminPanel />
              </ProtectedRoute>
            } />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
        </SystemProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
