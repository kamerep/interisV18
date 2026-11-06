# See LICENSE file for full copyright and licensing details
"""Demo scenario: realistic, date-relative records for testing.

Only called from demo XML (``<function>``) so it never runs on production
databases installed without demo data.
"""
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class PropertyDemoLoader(models.AbstractModel):
    _name = 'property.demo.loader'
    _description = 'Property Management demo data loader'

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _register_xmlid(self, module, name, record):
        self.env['ir.model.data']._update_xmlids([{
            'xml_id': '%s.%s' % (module, name),
            'record': record,
            'noupdate': True,
        }])

    def _today(self):
        return fields.Date.context_today(self)

    def _post_invoice(self, invoice):
        if invoice and invoice.state == 'draft':
            invoice.action_post()
        return invoice

    def _pay_invoice(self, invoice, date=None):
        """Register a full payment on a posted invoice/bill."""
        if not invoice or invoice.payment_state in ('paid', 'in_payment'):
            return
        wizard = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoice.ids).create(
            {'payment_date': date or invoice.invoice_date or self._today()})
        wizard.action_create_payments()

    def _invoice_schedule(self, schedule, pay=False):
        schedule.create_invoice()
        schedule.invoice_id.invoice_date = schedule.start_date
        self._post_invoice(schedule.invoice_id)
        if pay:
            self._pay_invoice(schedule.invoice_id, schedule.start_date)

    def _new_tenancy(self, name, prop, tenant, rent, deposit, start, end,
                     rent_type, **extra):
        vals = {
            'name': name,
            'property_id': prop.id,
            'tenant_id': tenant.id,
            'rent': rent,
            'deposit': deposit,
            'date_start': start,
            'date': end,
            'rent_type_id': rent_type.id,
            'resident_type': 'tenant_tenancy',
            'is_property': True,
            'manager_id': self.env.ref('base.user_admin').id,
        }
        vals.update(extra)
        return self.env['account.analytic.account'].with_context(
            is_property=True).create(vals)

    # ------------------------------------------------------------------
    # core scenario
    # ------------------------------------------------------------------
    @api.model
    def _load_core_demo(self):
        ref = self.env.ref
        today = self._today()
        month_start = today.replace(day=1)
        module = 'property_management_ee'
        Asset = self.env['account.asset']

        # Properties: realistic purchase dates and a complete Silver Palace
        demo_props = Asset.search([('is_property', '=', True)], order='id')
        for idx, prop in enumerate(demo_props):
            prop.acquisition_date = today - relativedelta(
                years=3, months=idx)
        golden = ref('%s.property1' % module)
        silver = ref('%s.property_silver_palace' % module)
        silver.write({
            'street': 'Ngong Road 14',
            'city': 'Nairobi',
            'country_id': ref('base.ke').id,
            'type_id': golden.type_id.id,
            'property_manager': golden.property_manager.id,
            'income_acc_id': golden.income_acc_id.id,
            'maint_account_id': golden.maint_account_id.id,
            'ground_rent': 1500.0,
            'rent_type_id': ref('%s.rent_type1' % module).id,
            'gfa_feet': 1800.0,
            'unit_price': 950.0,
        })

        monthly = ref('%s.rent_type1' % module)
        weekly = ref('%s.demo_rent_type_weekly' % module)
        alice = ref('%s.demo_tenant_alice' % module)
        brian = ref('%s.demo_tenant_brian' % module)
        carol = ref('%s.demo_tenant_carol' % module)
        david = ref('%s.demo_tenant_david' % module)
        eva = ref('%s.demo_tenant_eva' % module)

        # A. Running tenancy with history, a received deposit, one overdue
        #    unpaid invoice and overdue lines not yet invoiced.
        t_alice = self._new_tenancy(
            'Grimfield - Alice Wanjiru', ref('%s.childproperty1' % module),
            alice, 1200.0, 2400.0,
            month_start - relativedelta(months=8),
            month_start + relativedelta(months=4, days=-1), monthly)
        t_alice.button_start()
        t_alice.create_rent_schedule()
        payment = self.env['account.payment'].browse(
            t_alice.button_receive()['res_id'])
        payment.action_post()
        due = t_alice.rent_schedule_ids.filtered(
            lambda s: s.start_date <= today).sorted('start_date')
        # paid history, then: 1 invoiced but unpaid, last month not yet
        # invoiced (past the penalty grace period), current month open
        for schedule in due[:-3]:
            self._invoice_schedule(schedule, pay=True)
        if len(due) >= 3:
            self._invoice_schedule(due[-3], pay=False)
        self._register_xmlid(module, 'demo_tenancy_alice', t_alice)

        # B. Tenancy expiring in ~3 weeks, fully paid so far.
        t_brian = self._new_tenancy(
            'Dawson Drive - Brian Otieno', ref('%s.childproperty2' % module),
            brian, 950.0, 1900.0,
            today + relativedelta(days=21, years=-1),
            today + relativedelta(days=21), monthly)
        t_brian.button_start()
        t_brian.create_rent_schedule()
        payment = self.env['account.payment'].browse(
            t_brian.button_receive()['res_id'])
        payment.action_post()
        for schedule in t_brian.rent_schedule_ids.filtered(
                lambda s: s.start_date <= today):
            self._invoice_schedule(schedule, pay=True)
        self._register_xmlid(module, 'demo_tenancy_brian', t_brian)

        # C. Draft tenancy starting next month (to test the start flow).
        t_carol = self._new_tenancy(
            'Glohork Villa - Carol Mwangi', ref('%s.childproperty3' % module),
            carol, 1100.0, 2200.0,
            month_start + relativedelta(months=1),
            month_start + relativedelta(months=13, days=-1), monthly)
        self._register_xmlid(module, 'demo_tenancy_carol', t_carol)

        # D. Weekly tenancy that started three weeks ago.
        t_david = self._new_tenancy(
            'Cleveland - David Kimani', ref('%s.childproperty4' % module),
            david, 300.0, 600.0,
            today - relativedelta(weeks=3),
            today + relativedelta(weeks=9), weekly)
        t_david.button_start()
        t_david.create_rent_schedule()
        self._register_xmlid(module, 'demo_tenancy_david', t_david)

        # E. Closed tenancy from last year (history).
        t_eva = self._new_tenancy(
            'New Plazza - Eva Njeri (2025)', ref('%s.childproperty5' % module),
            eva, 1000.0, 0.0,
            month_start - relativedelta(years=2),
            month_start - relativedelta(years=1, days=1), monthly)
        t_eva.button_start()
        t_eva.create_rent_schedule()
        for schedule in t_eva.rent_schedule_ids:
            self._invoice_schedule(schedule, pay=True)
        t_eva.button_close()
        self._register_xmlid(module, 'demo_tenancy_eva', t_eva)

        # Compliance documents about to expire (expiry reports)
        self.env['property.attachment'].create([{
            'name': 'Fire insurance policy',
            'property_id': golden.id,
            'expiry_date': today + relativedelta(days=15),
        }, {
            'name': 'Lift inspection report',
            'property_id': ref('%s.property2' % module).id,
            'expiry_date': today + relativedelta(days=40),
        }])
        self.env['property.safety.certificate'].create([{
            'name': 'Gas safety certificate',
            'property_id': ref('%s.childproperty1' % module).id,
            'contact_id': alice.id,
            'expiry_date': today + relativedelta(days=10),
        }, {
            'name': 'Electrical installation certificate',
            'property_id': ref('%s.childproperty2' % module).id,
            'contact_id': brian.id,
            'expiry_date': today + relativedelta(days=25),
        }])
        return True
