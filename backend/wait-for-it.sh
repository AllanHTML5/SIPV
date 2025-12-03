#!/bin/sh
set -e

host="$1"
shift

if [ "$1" = "--" ]; then
  shift
fi

cmd="$@"

echo "Esperando a que $host esté listo..."

while ! nc -z "$host" 3306 2>/dev/null; do
  echo "MySQL no está listo, reintentando..."
  sleep 1
done

echo "$host está ARRIBA!"
exec $cmd
