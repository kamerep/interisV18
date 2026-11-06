# Property Management Suite — Odoo 15 → Odoo 18 Migration Change Log

**Date:** 2026-06-02
**Scope:** Full production-grade upgrade of 10 modules from Odoo V15.0 to V18.0.
**Author:** Peter Kamere (geronimo)

---

## Table of Contents
1. [Overview](#1-overview)
2. [Modules Affected](#2-modules-affected)
3. [Global Migration Rules Applied](#3-global-migration-rules-applied)
4. [Step-by-Step Changes by Phase](#4-step-by-step-changes-by-phase)
   - [Step 1 — Manifests](#step-1--manifests)
   - [Step 2 — Core `property_management_ee` Python](#step-2--core-property_management_ee-python)
   - [Step 3 — Maintenance / Recurring / Penalty](#step-3--maintenance--recurring--penalty)
   - [Step 4 — Booking / Commission / Landlord](#step-4--booking--commission--landlord)
   - [Step 5 — Sale-Purchase / Rent Report / Reports](#step-5--sale-purchase--rent-report--reports)
   - [Step 6 — XML Views](#step-6--xml-views)
   - [Step 7 — Data & Demo](#step-7--data--demo)
5. [Verification](#5-verification)
6. [Post-Migration Notes](#6-post-migration-notes)

---

## 1. Overview

The Property Management suite was migrated from Odoo 15 to Odoo 18. The work
covered Python ORM/API modernization, the complete removal of the deprecated
`attrs`/`states` view syntax, the V18 analytic-accounting model change
(`analytic_account_id` → `analytic_distribution`), payment-method API changes,
and chart-of-accounts changes in demo data (`user_type_id` → `account_type`).

All Python files compile, all XML files are well-formed, and no deprecated
patterns remain in active (non-commented) code.

---

## 2. Modules Affected

| Module | Old Version | New Version |
| --- | --- | --- |
| property_management_ee (core) | 15.0.1.0.2 | 18.0.1.0.0 |
| property_maintenance_ee | 15.0.1.0.0 | 18.0.1.0.0 |
| property_recurring_maintenance_ee | 15.0.1.0.1 | 18.0.1.0.0 |
| property_penalty_ee | 15.0.1.1.1 | 18.0.1.0.0 |
| property_booking_ee | 15.0.1.1.1 | 18.0.1.0.0 |
| property_commission_ee | 15.0.1.0.0 | 18.0.1.0.0 |
| property_landlord_management_ee | 15.0.1.0.0 | 18.0.1.0.0 |
| property_sale_purchase_ee | 15.0.1.0.0 | 18.0.1.0.0 |
| property_rent_report_ee | 15.0.1.0.0 | 18.0.1.0.0 |
| property_ee (meta) | 15.0.1.0.0 | 18.0.1.0.0 |

---

## 3. Global Migration Rules Applied

These rules were applied uniformly across the codebase.

### Python
| V15 pattern | V18 replacement |
| --- | --- |
| `def name_get(self)` | `def _compute_display_name(self)` + `_rec_names_search` |
| `@api.model def create(self, vals)` | `@api.model_create_multi def create(self, vals_list)` |
| `'analytic_account_id': id` on move lines | `'analytic_distribution': {str(id): 100}` |
| `payment_method_id` | `payment_method_line_id` (resolved from journal) |
| `self.env['ir.sequence'].get(code)` | `self.env['ir.sequence'].next_by_code(code)` |
| `res.company._company_default_get()` | `self.env.company` |
| `raise Warning(...)` | `raise ValidationError(...)` / `UserError(...)` |
| `render_html` + `self.env['report'].render` | `_get_report_values` (AbstractModel) |
| `get_report_values` | `_get_report_values` |
| integer division `a / b` for counts | `a // b` |
| string interpolation in `cr.execute` | parameterized query (`%s`, params tuple) |
| `assert_balanced` custom override | removed (handled by core) |

### XML
| V15 pattern | V18 replacement |
| --- | --- |
| `attrs="{'invisible': [domain]}"` | `invisible="python-expr"` |
| `attrs="{'readonly': [domain]}"` | `readonly="python-expr"` |
| `attrs="{'required': [domain]}"` | `required="python-expr"` |
| `states="draft,open"` (button/field) | `invisible="state not in ['draft','open']"` |
| `<tree>` … `</tree>` | `<list>` … `</list>` |
| `view_mode` token `tree` | `list` |
| `<field name="view_type">form</field>` | removed |
| `searchpanel view_types="kanban,tree"` | `view_types="kanban,list"` |
| `tree_view_ref` context key | `list_view_ref` |
| xpath `…/tree/…` | xpath `…/list/…` |
| `statusbar_colors='...'`, `select="1"`, `nodestroy` | removed |

### Accounting / Data
| V15 pattern | V18 replacement |
| --- | --- |
| `account.account.user_type_id` (m2o) | `account_type` (Selection) |
| `ref('account.data_account_type_expenses')` | `'expense'` |
| `ref('account.data_account_type_fixed_assets')` | `'asset_fixed'` |
| `ref('account.data_account_type_revenue')` | `'income'` |
| `account.asset.value_residual` write in demo | removed (computed/readonly) |
| `account.asset.user_type_id` view field | removed |

---

## 4. Step-by-Step Changes by Phase

### Step 1 — Manifests

All 10 `__manifest__.py` files:
- Bumped `version` to `18.0.1.0.0`.

`property_management_ee/__manifest__.py`:
- `depends`: removed `l10n_generic_coa`, added `account`.

`property_ee/__manifest__.py`:
- `depends`: removed non-existent `multiple_property_rent_ee`.

`property_rent_report_ee/__manifest__.py`:
- `depends`: removed redundant `analytic` (pulled transitively).

---

### Step 2 — Core `property_management_ee` Python

**`models/property.py`**
- `rent.type`: `name_get()` → `_compute_display_name()`, removed manual
  `name_search()` (replaced by `_rec_names_search = ['name', 'renttype']`).
- Renamed duplicate class `PropertyPhoto` (floor plans) → `PropertyFloorPlans`.

**`models/account_analytic_account.py`**
- `create()` → `@api.model_create_multi`; injects `plan_id` from an
  auto-created "Property Management" analytic plan (V18 requires `plan_id`).
- `default_get(self, fields)` → `default_get(self, fields_list)`.
- Replaced `account_move_line_ids` computations to use base `line_ids`
  (analytic lines) for credit/debit/expenditure totals.
- `_compute_payment_type` / `compute_amount_return` made stored & dependency-correct.
- `unlink()`: replaced `_description_selection` with `dict(self._fields['state'].selection)`.
- `button_receive()`: payment now uses `payment_method_line_id` (manual inbound),
  removed `view_type` from returned actions.
- `button_return()`: invoice line uses `analytic_distribution`.
- `create_rent_schedule()`: integer division `//`, removed `DEFAULT_SERVER_DATE_FORMAT`.
- Added explicit `prop_ids` Many2many (multi-property support) referenced by computes.

**`models/account.py`**
- Removed the deprecated `assert_balanced()` override.
- `AccountPayment.create()` → `@api.model_create_multi`.
- `_prepare_move_line_default_vals(self, write_off_line_vals=None)` signature fixed;
  uses `analytic_distribution`; removed obsolete `_seek_for_lines` override.
- `AccountPaymentRegister.default_get` hardened with `hasattr` checks;
  `_create_payment_vals_from_wizard(self, batch_result)` signature updated.
- `amount_due` field: removed invalid `comodel_name` kwarg on Monetary.

**`models/tenancy_rent_schedule.py`**
- `get_invoice_lines()` uses `analytic_distribution`.
- `create_invoice()` / `open_invoice()`: removed `view_type`; use `fields.Date.today()`.
- `send_mail_tenant_rent_schedule()`: `fields.Date.today()`.

**`models/account_asset_asset.py`**
- `create()` → `@api.model_create_multi`; only auto-creates analytic account for
  `is_property` assets, attaches analytic `plan_id`.
- `state` selection_add reduced to property-only states
  (`new_draft`, `book`, `normal`, `sold`, `cancel`) with `ondelete` map — keeps
  base V18 asset states (`draft`, `open`, `close`, `paused`, `model`).
- Compute methods simplified/loop-safe; `datetime.now()` → `fields.Date.today()`.
- Removed `view_type` from `create_tenancy`, `edit_status_book`, `open_url`.
- `write()` state→color map extended with `paused`.

**`models/crm_lead.py`**
- `_prepare_customer_values` cleaned; tenant branch creates `tenant.partner`.
- `CrmMakeContract.makecontract()`: removed `view_type`, V18 action dict, sets
  `resident_type='tenant_tenancy'`.

**`models/tenant_partner.py`**
- `create()` → `@api.model_create_multi`; user/group provisioning rewritten per-record.
- `write()` rewritten to be per-record safe (portal/internal user sync).
- `_USER_GROUP` constant added.

**`models/res_partner.py`**
- `write()` group sync hardened with `raise_if_not_found=False`.
- Removed redundant `mobile`/`occupation` size-only redefinition collisions.

**`wizard/*.py`** (crm_make_sale, contract_expiry_report, document_expiry_report,
renew_tenancy, safety_certificate_report, tenancy_property_report,
tenancy_tenant_report, tenant_wizard_mail)
- Removed `view_type` from all returned actions.
- Removed gantt-only helper methods that referenced non-existent gantt views.
- `crm_make_sale`: `fields.Datetime.now()`, `raise Warning` → `UserError`.
- `tenant_wizard_mail`: replaced removed `tools.email_send` with `mail.mail` create+send.
- Reports use `_get_report_values` data contract; `read()`-based form data.

---

### Step 3 — Maintenance / Recurring / Penalty

**`property_maintenance_ee/models/property_maintenance.py`**
- `create()` → `@api.model_create_multi`.
- `write()` rewritten per-record with `raise_if_not_found=False` on mail templates,
  guarded email sends.
- `create_invoice()` consolidated; removed `view_type`.
- `open_google_map()` / address building refactored.

**`property_maintenance_ee/models/assets.py`**
- `_compute_request_count` loop-safe; `open_maintenance()` removed `view_type`.
- `roi_calculation` simplified.

**`property_recurring_maintenance_ee/models/property_recuring_maintenance.py`**
- `get_invoice_lines()` override uses `analytic_distribution`.
- `_compute_total_cost_maint` loop-safe.

**`property_penalty_ee/models/property_penalty.py`**
- `raise Warning` → `raise ValidationError`.
- `calculate_penalty()`: `fields.Date.today()`.
- `get_invoice_lines()` guarded against empty list.

---

### Step 4 — Booking / Commission / Landlord

**`property_booking_ee/models/property_booking.py`**
- `_search()` signature updated to V18
  (`domain, offset, limit, order, access_rights_uid` — removed `count`).
- `_compute_no_avl` no longer returns an action (pure compute).
- `create_property()` refactored (cleaner label generation, integer `//`).
- `property.label`: `name_get` → `_compute_display_name` + `_rec_names_search`.
- Removed `view_type`/`nodestroy` from wizard-opening actions.
- `_compute_available_property`/`_compute_book_property` use `child_ids` instead of `search_count` in compute.

**`property_booking_ee/wizard/property_booking_wizard.py`**
- Removed `view_type` and `nodestroy` from `property_method` action; used `_()`.

**`property_commission_ee/models/property_commission.py`**
- `create()` → `@api.model_create_multi`; `ir.sequence.next_by_code`.
- Removed `_company_default_get` (→ `self.env.company`).
- `create_invoice()` uses `analytic_distribution`, `fields.Date.today()`, removed `view_type`.
- `_amount_all` / `calculate_commission` loop-safe.

**`property_commission_ee/wizard/commission_report.py` & `commission_invoice_owner.py`**
- Removed `DEFAULT_SERVER_DATE_FORMAT` date parsing (Date fields are already dates).
- `print_yes()` uses `report_action`; removed `self.env['report'].get_action`.
- `action_invoice_sent()`: `env.ref(..., raise_if_not_found=False)`, removed `view_type`.

**`property_commission_ee/report/commission_invoice_owner.py` & `commission_report_parser.py`**
- `render_html` + `env['report'].render` → `_get_report_values`.
- `get_report_values` → `_get_report_values`.

**`property_commission_ee/wizard/commission_report_view.xml`**
- Removed `<field name="view_type">form</field>`.

**`property_landlord_management_ee/models/account_analytic.py`**
- `create()` / `unlink()` → V18 multi-create; integer `//`.
- `resident_type` selection_add given `ondelete` map.
- `_compute_payment_type` overrides base via super + landlord logic, stored.
- Deposit pay/receive actions use `payment_method_line_id`; removed `view_type`/`nodestroy`.
- `create_landlord_invoice()` uses `analytic_distribution`.

**`property_landlord_management_ee/models/res_partner.py`**
- `LandlordPartner.create()` → `@api.model_create_multi`, `raise_if_not_found=False`.
- `unlink()` per-record guard.

---

### Step 5 — Sale-Purchase / Rent Report / Reports

**`property_sale_purchase_ee/models/sale_purchase_asset.py`**
- **SQL injection fixed**: `cr.execute("… property_id=%s" % id)` →
  parameterized `cr.execute("… property_id = %s", (id,))`.
- Fixed stray string-concatenation syntax bug in `genrate_payment_enteries`.
- `payment_term.compute()` result handled for both dict (V18) and tuple shapes.
- Integer `//`; cleaner installment math.

**`property_sale_purchase_ee/models/sale_cost.py` & `cost_cost.py`**
- Removed `view_type` / `with_context(default_move_type=...)` redundancy.
- Invoice creation cleaned; `_compute_move_check` loop-safe.

**`property_sale_purchase_ee/report/investment_report.py` & `report_property_chart.py`**
- `self._cr` → `self.env.cr`; SQL view `account_asset_asset` → `account_asset`
  (table renamed in modern Odoo); `parent_id` comodel fixed to `account.asset`.

**`property_management_ee/report/report_income_expenditure.py`**
- Rewritten with `_get_report_values`, loop-safe aggregation, V18 date formatting.

**`property_rent_report_ee/views/report_configuration_view.xml`**
- `binding_model_id` ref `account.model_account_analytic_account` →
  `analytic.model_account_analytic_account` (model owned by `analytic` module).

Other management report parsers (`report_contract_expiry.py`, etc.) already used
`_get_report_values` and standard date formatting — left intact.

---

### Step 6 — XML Views

Converted across **all view files** in every module (handled in two batches):

- **`attrs` removed** → direct `invisible` / `readonly` / `required` Python
  expressions (domain → boolean expression conversion, including `|`/`and`/`or`/`in`).
- **`states` removed** on buttons and fields → `invisible="state not in [...]"`,
  combined with existing `invisible` via `or` where both were present.
- **`<tree>` → `<list>`** in all embedded and standalone list views.
- **`view_mode`** tokens `tree` → `list` in `ir.actions.act_window` and view records.
- **`<field name="view_type">…</field>`** lines removed.
- **`searchpanel view_types="kanban,tree"`** → `kanban,list`.
- **`tree_view_ref`** context key → `list_view_ref` (10 files).
- **xpath** selectors `…/tree/…` → `…/list/…`
  (`property_penalty_view.xml`, `view_sale.xml`).
- Removed obsolete `statusbar_colors`, `select="1"`, `nodestroy`.
- **`view_account_asset_asset.xml`**: removed obsolete `account.asset.user_type_id`
  field and rewrote the `model_id` radio domain to drop `user_type_id`.

Files touched include (non-exhaustive):
`view_account_analytic.xml`, `view_account_asset_asset.xml`, `view_lead.xml`,
`view_property.xml`, `view_tenant_partner.xml`, `view_tenancy_rent_schedule.xml`,
`view_account.xml`, `view_sale.xml`, all `wizard/view_*.xml`,
`property_commission_view.xml`, `property_res_partner_views.xml`,
`maintenance_view.xml`, `sale_purchase_asset.xml`,
`view_analytic_account.xml` (landlord), `view_res_partner.xml` (landlord),
`view_property_booking.xml`, `view_property_book_wizard.xml`,
`property_recuring_maintenance_view.xml`, `property_penalty_view.xml`.

---

### Step 7 — Data & Demo

**`property_management_ee/demo/account_asset_demo.xml`**
- `account.account.user_type_id` → `account_type` Selection:
  - expenses → `expense`
  - fixed assets → `asset_fixed`
  - revenue → `income`
- Search domains on `user_type_id` rewritten to `account_type`.
- Removed all `<field name="value_residual">…</field>` (computed/readonly in V18).

**`property_management_ee/data/mail_tenant_rent.xml`**
- Already V18 (`{{ }}` placeholders, `t-out`) — verified, no change needed.

**`property_management_ee/data/scheduler_email_tenant_rent.xml`**
- `ir.cron` records validated for V18 (model_id refs, `code` calls) — no change needed.

**Report templates**
- `commission_report_template2.xml` (the only loaded one) verified V18-valid.
- Unloaded legacy `report_template.xml` (uses `t-raw`, `rml_*`) left untouched as it
  is not referenced in the manifest.

---

## 5. Verification

| Check | Result |
| --- | --- |
| `python3 -m py_compile` on all `.py` | ✅ Pass (all modules) |
| XML well-formedness (`xml.dom.minidom`) on all `.xml` | ✅ Pass |
| Residual `attrs=` in active code | ✅ None |
| Residual `states=` (non-statusbar) in active code | ✅ None |
| Residual `view_type` | ✅ None |
| Residual `user_type_id` in active code | ✅ None |
| Residual `name_get` definitions | ✅ None |
| `l10n_generic_coa` / `multiple_property_rent_ee` deps | ✅ Removed (only comment refs remain) |
| Test files compile | ✅ Pass |

---

## 6. Post-Migration Notes

- **External dependencies required at install time:** `account_asset` (Enterprise),
  `sale_crm`, `analytic`, `account`, `maintenance`. A live install on an Odoo 18
  instance with these apps is recommended to exercise runtime behaviour and the
  bundled tests (`--test-enable`).
- The custom `property_asset_form` replaces the standard `account.asset` form; if
  Odoo 18's base asset form changes further in a point release, re-validate the
  helper fields (`display_model_choice`, `display_account_asset_id`, `asset_type`).
- `commission_ee/views/report_configuration.xml` remains commented out in the
  manifest (pre-existing); the commission "print report" wizard depends on those
  report actions and will only work if that file is re-enabled.
- Demo data is optional and loads only in demo mode; production installs are
  unaffected by demo records.

---

## 7. Release 18.0.1.1.0 — runtime fixes on Odoo 18 Enterprise (2026-11-06)

All modules were installed with demo data on Odoo 18.0 Enterprise
(build 20241125) and exercised with the bundled tests (12 tests, all
passing) and a browser check of the main screens in light and dark mode.

### Install blockers
- Demo data wrote into a non-existent `account_asset` record.
- Maintenance stat button xpath targeted a commented-out button.
- `account.account` has `company_ids` in 18; domain on `company_id` failed.
- Finance analysis views referenced XML IDs of another module.

### Crashes fixed
| Area | Problem | Fix |
| --- | --- | --- |
| Payments | `_prepare_move_line_default_vals` missed `force_balance` → every payment raised `TypeError` | V18 signature; property set in `_generate_journal_entry` |
| Deposits | `ref` field no longer exists on payments | use `memo` |
| CRM | `_prepare_customer_values` returned a record → lead conversion, chatter and templates crashed | returns a dict; wizard creates/reuses the tenant |
| Partners | `has_group` on several/no users raised “Expected singleton” | write group commands directly |
| Booking | `_search(access_rights_uid=…)` → every search on units failed | V18 signature |
| Landlord | payments with `ref`; duplicate deposit payments | `memo`; reuse linked payment |
| Commission | compute left value unset; bills with NULL currency | always assign; tenancy/company currency |
| Reports | `multi_prop` on wrong models, unset variables, missing SQL columns, `state_id[0]` on empty value | rewritten helpers and SQL views |
| Rent schedule | missing dates → `TypeError` | clear validation message |

### Wrong results fixed
- Deposit flags used the removed payment state `posted`.
- Property hierarchy used Odoo 18 gross-increase `parent_id`, distorting
  book value/depreciation → new `property_parent_id` + migration.
- Weekly part-period rent divided by the interval twice.
- Occupancy rate formula was inverted (could exceed 100 %).
- Income/expenditure totals were never summed; expenses now come from posted vendor bills.
- Rent voucher “Balance Due” was always ~0.
- Maintenance “done” e-mails never sent (core `done` field shadowed).
- Commission owner report always empty; unbook button never visible;
  unbook wizard acted on the parent property instead of the unit.
- Rent reminder cron mailed overdue rent daily and rewrote the shared template.
- Cost lines could write the company currency through an editable related field.

### Features enabled / UI
- Commission details and commission invoices reports (were disconnected).
- Financial Performance Analysis graph (sale/purchase).
- Odoo 18 kanban `card` templates in all modules; chatter on commission invoices.
- App icons redrawn in the Odoo 18 style (flat SVG glyphs, Odoo palette,
  transparent background) so they match core apps in light and dark mode.

### Deployment
- `deploy/` scripts and config template; GitHub Actions static checks.

### Follow-ups completed
- Rent reminder wizard rebuilt for Odoo 18 (bound to rent schedules,
  overdue-rent mail template, menu under Tenant Details).
- Daily cron refreshes property occupancy rates.
- Maintenance: Maintenance Cost and Net Income (after maintenance) on
  properties; ROI itself is unchanged.
- Rent lines count as paid when the invoice is in payment (V18 payments
  without journal entry).
- Booking: generated units are flagged as properties.
- Demo scenario for every module, generated relative to the install date;
  landlord demo data repaired. Testing Guide (HTML/PDF) added.
- 16 automated tests.

### Maintenance links and fuller demo data (2026-11-06)
property_maintenance_ee
- Equipment has a Property; a request on equipment takes its property
  (and so the current tenant). The request form keeps Odoo's Equipment
  field (it was replaced by Property before) and filters it by property.
- Property form: Equipment smart button; request search by property,
  tenant, Renter's Fault and To Invoice; group by property.
- Renter's-fault invoices bill the tenant on the request, also after the
  tenancy was closed.
- Mail templates sent from the user's login instead of an e-mail
  address; they now use the user or company e-mail.
- Property details moved into Odoo's request notebook (no empty Notes).
- Demo: maintenance team, building-services category, six equipment
  items, nine requests (preventive recurring, blocked, owner's cost,
  move-out damage invoiced and paid).

property_management_ee
- Demo: rooms with fixtures and generated floor plans for four units,
  development phases and yield simulation for two buildings, four more
  insurance policies.
- 18 automated tests.

