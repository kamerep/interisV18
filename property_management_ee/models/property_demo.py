# See LICENSE file for full copyright and licensing details
"""Demo scenario: realistic, date-relative records for testing.

Only called from demo XML (``<function>``) so it never runs on production
databases installed without demo data.
"""
import base64
import io

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

    # ------------------------------------------------------------------
    # property details: rooms, phases, floor plans, insurance
    # ------------------------------------------------------------------
    def _floor_plan_png(self, rooms, title):
        """Draw a simple labelled floor plan (PNG bytes, base64)."""
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (640, 420), 'white')
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 620, 400], outline='#005E7A', width=6)
        x = 20
        total = sum(width for _label, width in rooms)
        for idx, (label, width) in enumerate(rooms):
            span = int(600 * width / total)
            top = 20 if idx % 2 == 0 else 210
            draw.rectangle([x, top, x + span, top + 190],
                           outline='#985184', width=3)
            draw.text((x + 12, top + 12), label, fill='#374151')
            x += span
        draw.text((30, 404 - 18), title, fill='#005E7A')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return base64.b64encode(buf.getvalue())

    @api.model
    def _load_property_details_demo(self):
        ref = self.env.ref
        module = 'property_management_ee'
        today = self._today()
        bedroom = ref('%s.room_type2' % module)
        living = ref('%s.room_type1' % module)
        kitchen = ref('%s.room_type3' % module)
        Room = self.env['property.room']

        layouts = {
            'childproperty1': [  # Grimfield (Alice)
                ('Living room', living, (6.0, 4.5, 2.8),
                 [('Sofa set', 'movable', 1), ('TV unit', 'fixed', 1)]),
                ('Master bedroom', bedroom, (4.5, 4.0, 2.8),
                 [('Double bed', 'movable', 1),
                  ('Built-in wardrobe', 'fixed', 1)]),
                ('Bedroom 2', bedroom, (3.5, 3.5, 2.8),
                 [('Single bed', 'movable', 2)]),
                ('Kitchen', kitchen, (4.0, 3.0, 2.8),
                 [('Cooker', 'fixed', 1), ('Fridge', 'movable', 1)]),
            ],
            'childproperty2': [  # Dawson Drive (Brian)
                ('Living room', living, (5.5, 4.0, 2.7),
                 [('Sofa set', 'movable', 1)]),
                ('Bedroom', bedroom, (4.0, 3.8, 2.7),
                 [('Queen bed', 'movable', 1),
                  ('Wardrobe', 'fixed', 1)]),
                ('Kitchen', kitchen, (3.5, 2.8, 2.7),
                 [('Kitchen cabinets', 'fixed', 1)]),
            ],
            'childproperty3': [  # Glohork Villa (Carol, starts soon)
                ('Lounge', living, (7.0, 5.0, 3.0),
                 [('Fireplace', 'fixed', 1)]),
                ('Bedroom 1', bedroom, (5.0, 4.0, 3.0), []),
                ('Bedroom 2', bedroom, (4.0, 4.0, 3.0), []),
                ('Bedroom 3', bedroom, (3.5, 3.5, 3.0), []),
                ('Kitchen', kitchen, (4.5, 3.5, 3.0),
                 [('Island counter', 'fixed', 1)]),
            ],
            'childproperty4': [  # Cleveland flat (David)
                ('Studio room', living, (6.0, 5.0, 2.6),
                 [('Sofa bed', 'movable', 1), ('Desk', 'movable', 1)]),
                ('Kitchenette', kitchen, (2.5, 2.0, 2.6),
                 [('Hob', 'fixed', 1)]),
            ],
        }
        for xmlid, rooms in layouts.items():
            prop = ref('%s.%s' % (module, xmlid))
            for name, rtype, (length, width, height), assets in rooms:
                Room.create({
                    'name': name,
                    'type_id': rtype.id,
                    'property_id': prop.id,
                    'length': length,
                    'width': width,
                    'height': height,
                    'attach': rtype == bedroom,
                    'assets_ids': [(0, 0, {
                        'name': a_name, 'type': a_type, 'qty': qty,
                        'date': prop.acquisition_date or today,
                    }) for a_name, a_type, qty in assets],
                })
            self.env['property.floor.plans'].create({
                'property_id': prop.id,
                'photos_description': 'Ground floor plan',
                'doc_name': '%s floor plan.png' % prop.name,
                'photos': self._floor_plan_png(
                    [(r[0], r[2][0]) for r in rooms],
                    '%s - ground floor' % prop.name),
            })

        # Development phases and sales simulation on the parent buildings
        for xmlid, cost, phases in [
            ('property1', 250000.0, [(-36, -24, 950.0, 60.0, 4.0),
                                     (-24, -12, 1100.0, 78.0, 4.0),
                                     (-12, 0, 1200.0, 92.0, 4.5)]),
            ('property2', 180000.0, [(-30, -18, 800.0, 55.0, 4.0),
                                     (-18, 0, 950.0, 85.0, 4.0)]),
        ]:
            prop = ref('%s.%s' % (module, xmlid))
            prop.write({
                'simulation_name': '%s yield plan' % prop.name,
                'simulation_date': today,
                'construction_cost': cost,
                'property_phase_ids': [(0, 0, {
                    'start_date': today + relativedelta(months=start),
                    'end_date': today + relativedelta(months=end, days=-1),
                    'lease_price': price,
                    'occupancy_rate': occupancy,
                    'company_income': price * 12 * occupancy / 100,
                    'commercial_tax': tax,
                }) for start, end, price, occupancy, tax in phases],
            })

        # Insurance on the leased buildings
        company = self.env.company
        for xmlid, name, policy, premium, mode in [
            ('property1', 'Building insurance', 'BLD-2026-0141', 1800.0,
             'yearly'),
            ('property1', 'Public liability cover', 'PL-2026-0075', 95.0,
             'monthly'),
            ('childproperty1', 'Contents insurance', 'CNT-2026-3310', 240.0,
             'semi_annually'),
            ('childproperty2', 'Fire insurance', 'FIR-2026-4410', 310.0,
             'yearly'),
        ]:
            self.env['property.insurance'].create({
                'name': name,
                'policy_no': policy,
                'premium': premium,
                'payment_mode_type': mode,
                'property_id': ref('%s.%s' % (module, xmlid)).id,
                'company_id': company.id,
                'contact': company.id,
                'start_date': today - relativedelta(months=3),
                'end_date': today + relativedelta(months=9),
            })
        return True

