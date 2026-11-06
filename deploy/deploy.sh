#!/usr/bin/env bash
# Install or upgrade the Property Management suite on an Odoo 18 database.
#
#   deploy/deploy.sh -c /etc/odoo18.conf -d mydb            # upgrade installed modules
#   deploy/deploy.sh -c /etc/odoo18.conf -d mydb --install  # first install
#   deploy/deploy.sh ... --test                              # run the suite tests too
#
# ODOO_BIN may point to the odoo launcher (default: odoo on PATH).
set -euo pipefail
CONF="" DB="" MODE="-u" TEST=""
MODULES="property_ee"
while [ $# -gt 0 ]; do
  case "$1" in
    -c) CONF="$2"; shift 2 ;;
    -d) DB="$2"; shift 2 ;;
    --install) MODE="-i"; shift ;;
    --test) TEST="--test-enable --test-tags=/property_management_ee,/property_commission_ee,/property_penalty_ee,/property_recurring_maintenance_ee,/property_sale_purchase_ee"; shift ;;
    -m) MODULES="$2"; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
[ -n "$CONF" ] && [ -n "$DB" ] || { echo "usage: $0 -c CONF -d DB [--install] [--test] [-m modules]" >&2; exit 2; }
ODOO_BIN="${ODOO_BIN:-odoo}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
find "$HERE" -name __pycache__ -prune -exec rm -rf {} +
if [ "$MODE" = "-u" ]; then MODULES="$(echo "$MODULES" | sed 's/property_ee/property_management_ee,property_booking_ee,property_commission_ee,property_landlord_management_ee,property_maintenance_ee,property_penalty_ee,property_recurring_maintenance_ee,property_rent_report_ee,property_sale_purchase_ee,property_ee/')"; fi
# shellcheck disable=SC2086
"$ODOO_BIN" -c "$CONF" -d "$DB" $MODE "$MODULES" $TEST --stop-after-init
echo "Done: $MODE $MODULES on $DB. Restart the Odoo 18 service to load the new code."
