# See LICENSE file for full copyright and licensing details
from datetime import date

from odoo import fields
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestPropertyFlows(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prop = cls.env.ref('property_management_ee.property1')
        cls.tenant = cls.env.ref('property_management_ee.tenant1')
        cls.monthly = cls.env.ref('property_management_ee.rent_type1')
        cls.weekly = cls.env['rent.type'].create({
            'name': '1', 'renttype': 'Weekly', 'sequence_in_view': 0})

    def _tenancy(self, **vals):
        values = {
            'name': 'Test tenancy',
            'property_id': self.prop.id,
            'tenant_id': self.tenant.id,
            'resident_type': 'tenant_tenancy',
            'is_property': True,
            'rent': 700.0,
            'deposit': 1500.0,
            'date_start': '2026-01-01',
            'date': '2026-12-31',
            'rent_type_id': self.monthly.id,
        }
        values.update(vals)
        return self.env['account.analytic.account'].create(values)

    def _render(self, action):
        # a fresh company first gets the "configure document layout" wizard
        action = action.get('context', {}).get('report_action', action)
        report = self.env['ir.actions.report']._get_report(
            action['report_name'])
        html, _fmt = self.env['ir.actions.report']._render_qweb_html(
            report, action.get('context', {}).get('active_ids') or [],
            data=action.get('data'))
        self.assertTrue(html)

    def test_deposit_payment_posts(self):
        """Receiving a deposit creates a payment that can be posted."""
        tenancy = self._tenancy()
        action = tenancy.button_receive()
        payment = self.env['account.payment'].browse(action['res_id'])
        self.assertEqual(payment.memo, 'Deposit Received')
        self.assertEqual(tenancy.acc_pay_dep_rec_id, payment)
        payment.action_post()
        self.assertIn(payment.state, ('in_process', 'paid'))
        self.assertTrue(tenancy.deposit_received)
        # with an outstanding account the payment gets a journal entry,
        # which must carry the property
        journal = payment.journal_id
        line = journal.inbound_payment_method_line_ids.filtered(
            lambda l: l.payment_method_id.code == 'manual')[:1]
        line.payment_account_id = self.env['account.account'].search([
            ('account_type', '=', 'asset_current'),
            ('company_ids', 'in', payment.company_id.id),
        ], limit=1)
        payment2 = self.env['account.payment'].create({
            'partner_id': self.tenant.parent_id.id,
            'payment_type': 'inbound', 'partner_type': 'customer',
            'journal_id': journal.id, 'amount': 10.0,
            'payment_method_line_id': line.id,
            'property_id': self.prop.id,
        })
        payment2.action_post()
        self.assertTrue(payment2.move_id)
        self.assertEqual(payment2.move_id.property_id, self.prop)

    def test_property_hierarchy_is_not_gross_increase(self):
        child = self.env['account.asset'].create({
            'name': 'Unit 1', 'is_property': True,
            'property_parent_id': self.prop.id,
        })
        self.assertIn(child, self.prop.child_ids)
        self.assertFalse(child.parent_id)
        self.assertNotIn(child, self.prop.children_ids)

    def test_weekly_rent_prorates_leftover_days(self):
        tenancy = self._tenancy(
            rent=70.0, rent_type_id=self.weekly.id,
            date_start='2026-01-01', date='2026-01-18')
        tenancy.create_rent_schedule()
        amounts = sorted(tenancy.rent_schedule_ids.mapped('amount'))
        # 17 days = 2 full weeks + 3 days at 70 / 7 per day
        self.assertEqual(amounts, [30.0, 70.0, 70.0])

    def test_rent_schedule_requires_dates(self):
        tenancy = self._tenancy(date=False)
        with self.assertRaises(Exception):
            tenancy.create_rent_schedule()

    def test_crm_rent_lead_to_contract(self):
        lead = self.env['crm.lead'].create({
            'name': 'Wants a flat', 'type': 'opportunity', 'is_rent': True,
            'contact_name': 'Rent Lead Contact',
            'email_from': 'rent.lead@example.com',
            'property_id': self.prop.id,
        })
        vals = lead._prepare_customer_values('Rent Lead Contact')
        self.assertIsInstance(vals, dict)
        self.assertTrue(vals['tenant'])
        wizard = self.env['crm.make.contract'].with_context(
            active_ids=lead.ids).create({'date': '2027-01-01'})
        action = wizard.makecontract()
        tenancy = self.env['account.analytic.account'].browse(
            action['res_id'])
        self.assertTrue(tenancy.tenant_id)
        self.assertEqual(tenancy.tenant_id.parent_id, lead.partner_id)

    def test_partner_flags_without_user(self):
        partner = self.env['res.partner'].create({'name': 'No user'})
        partner.write({'tenant': True, 'agent': True})
        partner.write({'tenant': False, 'agent': False})

    def test_reminder_cron(self):
        tenancy = self._tenancy(date_start=fields.Date.today())
        tenancy.button_start()
        tenancy.create_rent_schedule()
        template = self.env.ref('property_management_ee.mail_tenant_rent')
        email_to = template.email_to
        self.env['tenancy.rent.schedule'].send_mail_tenant_rent_schedule()
        self.assertEqual(template.email_to, email_to)

    def test_reports_render(self):
        start, end = date(2020, 1, 1), date(2030, 12, 31)
        tenancy = self._tenancy(multi_prop=True, prop_ids=[
            (6, 0, (self.prop | self.env.ref(
                'property_management_ee.property2')).ids)])
        tenancy.create_rent_schedule()
        for model in ('contract.expiry.report', 'document.expiry.report',
                      'safety.certificate.report', 'income.report'):
            wiz = self.env[model].create(
                {'start_date': start, 'end_date': end})
            self._render(wiz.print_report())
        self._render(self.env['tenancy.property.report'].create({
            'start_date': start, 'end_date': end,
            'property_id': self.prop.id}).print_report())
        self._render(self.env['tenancy.tenant.report'].create({
            'start_date': start, 'end_date': end,
            'tenant_id': self.tenant.id}).print_report())
        self._render(
            self.env['property.per.location'].create({}).print_report())
        for model in ('gfa.analysis.report', 'occupancy.performance.report',
                      'operational.costs.report',
                      'investment.analysis.report'):
            self.env[model].read_group(
                [], ['name'], ['parent_id', 'type_id'], lazy=False)
