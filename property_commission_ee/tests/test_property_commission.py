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
