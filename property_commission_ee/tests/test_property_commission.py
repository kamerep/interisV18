# See LICENSE file for full copyright and licensing details

from odoo.tests import common


class PropertyCommissionTestCase(common.TransactionCase):

    def setUp(self):
        super(PropertyCommissionTestCase, self).setUp()

    def test_commission(self):
        self.details = self.browse_ref(
            'property_management_ee.property_tenancy_t0')
        self.property_id = self.browse_ref('property_management_ee.property3')
        self.tenant_id = self.browse_ref('property_management_ee.tenant2')
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
                'commission': True,
                'agent': self.agent.id,
                'tenant_id': self.tenant_id.id,
                'commission_type': 'fixed',
                'fix_qty': 10.00,
                'deposit': 5000.00,
                'rent': 8000.00,
                'date_start': '07/17/2016',
                'date': '07/07/2017',
                'rent_type_id': self.rent_type.id,
            })
        self.tenancy.button_start()
        self.tenancy.create_rent_schedule()
        self.tenancy.calculate_commission()
        self.tenancy.create_commission()
