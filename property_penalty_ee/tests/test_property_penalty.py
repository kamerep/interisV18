# See LICENSE file for full copyright and licensing details
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class PropertyPenaltyTestCase(common.TransactionCase):

    def setUp(self):
        super(PropertyPenaltyTestCase, self).setUp()

    def test_property_penalty(self):
        self.property_id = self.browse_ref('property_management_ee.property_8')
        self.tenant_id = self.browse_ref('property_management_ee.tenant1')
        self.rent_type = self.browse_ref("property_management_ee.rent_type1")
        self.tenancy = self.env['account.analytic.account'].sudo().create(
            {
                'name': 'Tenancy for Radhika Recidency',
                'property_id': self.property_id.id,
                'state': 'draft',
                'is_property': True,
                'resident_type': 'tenant_tenancy',
                'tenant_id': self.tenant_id.id,
                'deposit': 5000.00,
                'rent': 8000.00,
                'rent_entry_chck': False,
                'date_start': '2016-07-17',
                'date': '2017-07-07',
                'rent_type_id': self.rent_type.id,
                'penalty': 10.00,
                'penalty_day': 2,
            })
        self.tenancy.button_start()
        self.tenancy.create_rent_schedule()
        self.tenancy.rent_schedule_ids[0].calculate_penalty()
        self.tenancy.rent_schedule_ids[0].create_invoice()
