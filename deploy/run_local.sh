#!/usr/bin/env bash
# Run an Odoo 18 build unpacked from the official .deb without installing it
# system-wide (dpkg-deb -x odoo_18.0.*.deb ~/odoo18ee). Uses a private
# PostgreSQL cluster so it never touches the system one.
#   ODOO18_HOME=~/odoo18ee deploy/run_local.sh -d property18
set -euo pipefail
B="${ODOO18_HOME:-$HOME/odoo18ee}"
PG=/usr/lib/postgresql/18/bin
"$PG/pg_ctl" -D "$B/pgdata" status >/dev/null 2>&1 || \
  "$PG/pg_ctl" -D "$B/pgdata" -o "-k $B/pgrun -c listen_addresses=localhost -p 55418" -l "$B/pg.log" start >/dev/null
export PYTHONPATH="$B/usr/lib/python3/dist-packages"
exec "$B/venv/bin/python" "$B/usr/bin/odoo" -c "$B/odoo18.conf" "$@"
