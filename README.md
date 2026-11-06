# Property Management Suite for Odoo 18 Enterprise

Real-estate management for Odoo 18: properties and sub-properties,
tenancies and rent schedules, deposits, landlords, bookings, commissions,
maintenance, penalties, purchase/sale instalments and reporting.

| Module | Purpose |
| --- | --- |
| `property_management_ee` | Core: properties (on `account.asset`), tenants, tenancies, rent schedules, deposits, CRM rent leads, reports |
| `property_booking_ee` | Create floors/units under a building, book, merge and split units |
| `property_commission_ee` | Agent commissions on tenancies, commission bills and reports |
| `property_landlord_management_ee` | Landlords, landlord tenancies, owner deposits and rent bills |
| `property_maintenance_ee` | Property maintenance requests and equipment per property, invoicing, tenant/manager notifications |
| `property_recurring_maintenance_ee` | Recurring maintenance costs added to rent invoices |
| `property_penalty_ee` | Late-payment penalties on rent invoices |
| `property_rent_report_ee` | Rent voucher report |
| `property_sale_purchase_ee` | Purchase/sale instalments, investment and finance analysis |
| `property_ee` | Installs the whole suite |

## Requirements

- Odoo **18.0 Enterprise** (`account_asset`, `web_gantt` are Enterprise apps)
- Community apps pulled in automatically: `account`, `analytic`, `sale_crm`, `maintenance`
- PostgreSQL 13+ and Python 3.10–3.12

## Install

```bash
git clone https://github.com/kamerep/interisV18.git /opt/odoo18-addons/interisV18
# add /opt/odoo18-addons/interisV18 to addons_path (see deploy/odoo18.conf.example)
deploy/deploy.sh -c /etc/odoo18.conf -d mydb --install
```

Upgrading an existing database:

```bash
git -C /opt/odoo18-addons/interisV18 pull
deploy/deploy.sh -c /etc/odoo18.conf -d mydb          # runs -u on every suite module
sudo systemctl restart odoo18
```

Run the tests (installs into a throw-away database first if you prefer):

```bash
deploy/deploy.sh -c /etc/odoo18.conf -d test_db --install --test
```

### Running next to other Odoo versions

Ports 8069/8070 are commonly used by other Odoo versions. The example
config uses **8018** (HTTP) and **8073** (longpolling). `deploy/run_local.sh`
runs an Odoo 18 build unpacked from the official `.deb`
(`dpkg-deb -x odoo_18.0.*.deb ~/odoo18ee`) with a private PostgreSQL
cluster, so it never touches the system Odoo service or database.

## Upgrade notes for 18.0.1.1.0

- The property hierarchy moved from `account.asset.parent_id` (used by Odoo 18
  for gross-increase assets) to **`property_parent_id`**. The migration script
  moves existing links automatically when you upgrade `property_management_ee`.
- Custom views, reports or server actions that used `parent_id` for the
  property hierarchy must switch to `property_parent_id`.

## Demo data and testing

Install with demo data to get a complete, date-relative test scenario:
five tenants and tenancies (running with overdue rent, expiring soon, draft,
weekly, closed), deposits, a CRM rent lead, rooms, floor plans, phases and
insurance, maintenance equipment linked to properties with requests in
every stage (preventive, recurring, blocked, invoiced), an agent
commission, a landlord lease, a 12-unit building for bookings, purchase and
sale instalments, and expiring documents. `docs/Testing_Guide` lists every
demo record and 14 step-by-step test scenarios with expected results.

## Documentation

`docs/` holds HTML and PDF versions of:

- **Property_Management_Suite_Documentation** – functional and technical reference
- **Property_Management_End_User_Guide** – day-to-day user guide
- **Deployment_and_Release_Notes** – installation, upgrade, deployment and the 18.0.1.1.0 fixes
- **Testing_Guide** – test instance access, demo data inventory and test scenarios

See `CHANGES_LOG.md` for the full change history.

## License

LGPL-3. The modules derive from work by Serpent Consulting Services Pvt. Ltd.;
their copyright notices are kept in each module's `LICENSE` file.
