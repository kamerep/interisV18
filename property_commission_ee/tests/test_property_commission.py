# See LICENSE file for full copyright and licensing details

from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class PropertyCommissionTestCase(common.TransactionCase):

    def setUp(self):
        super(PropertyCommissionTestCase, self).setUp()

    def test_commission(self):
        self.property_id = self.browse_ref('property_management_ee.property3')
        self.tenant_id = self.browse_ref('property_management_ee.tenant1')
        self.rent_type = self.browse_ref("property_management_ee.rent_type1")
        self.agent = self.env['res.partner'].sudo().create(
            {
                'name': 'Patel Kapil',
                'agent': True,
                'email': 'patel@yourcompany.com'
            })

        self.tenancy = self.env['account.analytic.account'].sudo().create(
            {
                'name': 'Tenancy for Radhika Recidency',
                'property_id': self.property_id.id,
                'state': 'draft',
                'is_property': True,
                'resident_type': 'tenant_tenancy',
                'commission': True,
                'agent': self.agent.id,
                'tenant_id': self.tenant_id.id,
                'commission_type': 'fixed',
                'fix_qty': 10.00,
                'deposit': 5000.00,
                'rent': 8000.00,
                'date_start': '2016-07-17',
                'date': '2017-07-07',
                'rent_type_id': self.rent_type.id,
            })
        self.tenancy.button_start()
        self.tenancy.create_rent_schedule()
        self.tenancy.calculate_commission()
        self.tenancy.create_commission()
        commission = self.env['commission.invoice'].search(
            [('tenancy', '=', self.tenancy.id)])
        self.assertTrue(commission)
        commission.create_invoice()
        self.assertTrue(commission.commission_line.mapped('inv'))
        self._render_reports()

    def _render_reports(self):
        Report = self.env['ir.actions.report']
        dates = {'start_date': '2000-01-01', 'end_date': '2100-12-31'}
        owner = self.env['commission.invoice.owner'].create(dates)
        for action in (owner.print_yes(),
                       self.env['commission.report'].create(
                           dates).print_report()):
            action = action.get('context', {}).get('report_action', action)
            html, _fmt = Report._render_qweb_html(
                action['report_name'], [], data=action['data'])
            self.assertIn(b'Agent', html)

