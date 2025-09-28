#!/usr/bin/env sh
set -e

SQUID_USER=${SQUID_USER:-proxy}
SQUID_GROUP=${SQUID_GROUP:-proxy}
LOG_DIR=${LOG_DIR:-/var/log/squid}
SPOOL_DIR=${SPOOL_DIR:-/var/spool/squid}
RUN_DIR=${RUN_DIR:-/var/run/squid}

# Crear rutas requeridas
mkdir -p "$LOG_DIR" "$SPOOL_DIR" "$RUN_DIR"

# Ajustar ownership (importante si hay bind mounts)
chown -R "$SQUID_USER:$SQUID_GROUP" "$LOG_DIR" "$SPOOL_DIR" "$RUN_DIR"

# Inicializar caché si volumen recién montado (o vacío)
if [ -z "$(ls -A "$SPOOL_DIR" 2>/dev/null)" ] || [ ! -d "$SPOOL_DIR/00" ]; then
  echo "Inicializando cache de Squid..."
  squid -z -f /etc/squid/squid.conf || true
  chown -R "$SQUID_USER:$SQUID_GROUP" "$SPOOL_DIR"
fi

# Limpiar PIDs previos
rm -f /var/run/squid.pid /run/squid.pid "$RUN_DIR/squid.pid" || true

# Arrancar en foreground (para docker logs)
echo "Iniciando Squid..."
exec squid -N -d 1 -f /etc/squid/squid.conf