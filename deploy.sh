#!/bin/bash
# ── SIPAM-USCO — Script de despliegue en servidor Linux ──────────────────────
# Uso: bash deploy.sh [--reset-seed]
# Probado en: Ubuntu 22.04 / Debian 12
#
# Flags:
#   --reset-seed   → limpia la BD y vuelve a poblar desde cero
set -e

# Convertir saltos de línea CRLF→LF en scripts bash (problema al editar en Windows)
if command -v dos2unix &>/dev/null; then
    dos2unix "$0" 2>/dev/null || true
fi

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC}  $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── 1. Verificar dependencias ─────────────────────────────────────────────────
info "Verificando dependencias..."

if ! command -v docker &>/dev/null; then
    warn "Docker no encontrado. Instalando..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    info "Docker instalado. Puede ser necesario cerrar sesión y volver a entrar."
fi

if ! docker compose version &>/dev/null; then
    warn "Docker Compose plugin no encontrado. Instalando..."
    sudo apt-get update -qq
    sudo apt-get install -y docker-compose-plugin
fi

# Convertir CRLF→LF en todos los scripts bash del proyecto (edición desde Windows)
if ! command -v dos2unix &>/dev/null; then
    sudo apt-get install -y dos2unix -qq 2>/dev/null || true
fi
if command -v dos2unix &>/dev/null; then
    find . -name "*.sh" | xargs dos2unix -q 2>/dev/null || true
    info "Scripts .sh convertidos a LF."
fi

info "Docker $(docker --version)"
info "Docker Compose $(docker compose version)"

# ── 2. Verificar .env.production ─────────────────────────────────────────────
if [ ! -f ".env.production" ]; then
    error ".env.production no encontrado. Copia .env.production y ajusta las variables."
fi

# Alertar si aún tiene valores de ejemplo
if grep -q "CAMBIA_ESTA" .env.production; then
    error "Edita .env.production y reemplaza todos los valores 'CAMBIA_ESTA_...' antes de continuar."
fi

# ── 3. Actualizar código ──────────────────────────────────────────────────────
if [ -d ".git" ]; then
    info "Actualizando código desde git..."
    git pull origin main
fi

# ── 4. Detener contenedores anteriores ───────────────────────────────────────
info "Deteniendo contenedores existentes..."
docker compose --env-file .env.production down --remove-orphans || true

# ── 5. Construir imágenes ─────────────────────────────────────────────────────
info "Construyendo imágenes Docker (puede tomar varios minutos)..."
docker compose --env-file .env.production build --no-cache

# ── 6. Iniciar servicios ──────────────────────────────────────────────────────
info "Iniciando todos los servicios..."
docker compose --env-file .env.production up -d

# ── 7. Esperar a que el backend esté listo ───────────────────────────────────
info "Esperando a que el backend esté listo..."
RETRIES=30
until docker compose exec -T backend curl -sf http://localhost:8000/ &>/dev/null; do
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -eq 0 ]; then
        error "El backend no respondió a tiempo. Revisa: docker compose logs backend"
    fi
    sleep 3
done
info "Backend listo."

# ── 8. Migraciones de BD (siempre — son idempotentes) ───────────────────────
info "Ejecutando migraciones de BD..."
docker compose exec -T backend python migrate_rename_observaciones.py \
    || warn "migrate_rename_observaciones.py: sin cambios o ya aplicado."

# ── 9. Sembrar datos iniciales ────────────────────────────────────────────────
SEED_FLAG=".seed_done"
RESET_SEED=false
for arg in "$@"; do
    [ "$arg" = "--reset-seed" ] && RESET_SEED=true
done

if [ "$RESET_SEED" = true ]; then
    warn "Modo --reset-seed: vaciando BD y resembrando..."
    docker compose exec -T backend python seed.py --reset
    touch "$SEED_FLAG"
    info "Seed completado (reset)."
elif [ ! -f "$SEED_FLAG" ]; then
    warn "Primera instalación — ejecutando seed de datos..."
    docker compose exec -T backend python seed.py \
        || warn "seed.py falló o ya hay datos."
    touch "$SEED_FLAG"
    info "Seed completado."
else
    info "Seed ya ejecutado anteriormente. Usa --reset-seed para forzar."
fi

# ── 10. Estado final ──────────────────────────────────────────────────────────
echo ""
info "═══════════════════════════════════════════════════"
info "  SIPAM-USCO desplegado correctamente"
info "═══════════════════════════════════════════════════"
info "  Frontend:  http://$(hostname -I | awk '{print $1}')"
info "  Backend:   http://$(hostname -I | awk '{print $1}'):8000"
info "  AI health: http://$(hostname -I | awk '{print $1}'):5001/health  (interno)"
echo ""
info "  Logs:      docker compose logs -f"
info "  Detener:   docker compose down"
info "═══════════════════════════════════════════════════"
