# See LICENSE file for full copyright and licensing details
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class PropertyRecurringTestCase(common.TransactionCase):

    def test_recurring_maintenance(self):
        property_id = self.env.ref('property_management_ee.property_8')
        tenant = self.env.ref('property_management_ee.tenant1')
        rent_type = self.env.ref('property_management_ee.rent_type1')
        maint1 = self.env.ref(
            'property_recurring_maintenance_ee.maintenance_type6')
        maint2 = self.env.ref(
            'property_recurring_maintenance_ee.maintenance_type7')
        tenancy = self.env['account.analytic.account'].create({
            'name': 'Tenancy for Radhika Recidency',
            'property_id': property_id.id,
            'is_property': True,
            'resident_type': 'tenant_tenancy',
            'tenant_id': tenant.id,
            'deposit': 5000.00,
            'rent': 8000.00,
            'date_start': '2016-07-17',
            'date': '2017-07-07',
            'rent_type_id': rent_type.id,
            'maintenance_cost_ids': [
                (0, 0, {'maintenance_type': maint1.id, 'cost': 100.0}),
                (0, 0, {'maintenance_type': maint2.id, 'cost': 50.0}),
            ],
        })
        self.assertEqual(tenancy.maintenance_cost, 150.0)
        tenancy.button_start()
        tenancy.create_rent_schedule()
        self.assertTrue(tenancy.rent_schedule_ids)
        tenancy.rent_schedule_ids[0].create_invoice()
        self.assertTrue(tenancy.rent_schedule_ids[0].invoice_id)
