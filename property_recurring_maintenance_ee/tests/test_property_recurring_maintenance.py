# See LICENSE file for full copyright and licensing details
from odoo.tests import common


class PropertyRecurringTestCase(common.TransactionCase):

    def setup(self):
        super(PropertyRecurringTestCase, self).setup()

    def test_recurring_maintenance(self):
        self.details = self.browse_ref(
            'property_management_ee.property_tenancy_t0')
        self.property_id = self.browse_ref('property_management_ee.property_8')
        self.tenant_id = self.browse_ref('property_management_ee.tenant2')
        self.rent_type = self.browse_ref("property_management_ee.rent_type1")
        self.maint1 = self.browse_ref(
            'property_recurring_maintenance.maintenance_type6')
        self.maint2 = self.browse_ref(
            'property_recurring_maintenance.maintenance_type7')
        self.recurring1 = {
            'maint_type': self.maint1.id,
        }
        self.recurring2 = {
            'maint_type': self.maint2.id,
        }

        self.tenancy = self.env['account.analytic.account'].sudo().create(
            {
                'name': 'Tenancy for Radhika Recidency',
                'property_id': self.property_id.id,
                'state': 'draft',
                'is_property': True,
                'tenant_id': self.tenant_id.id,
                'deposit': 5000.00,
                'rent': 8000.00,
                'rent_entry_chck': False,
                'date_start': '07/17/2016',
                'date': '07/07/2017',
                'rent_type_id': self.rent_type.id,
                'cost_id': [(0, 0, self.recurring1),
                            (0, 0, self.recurring2)],
            })
        self.tenancy.cost_id.onchange_property_id()
        self.tenancy._total_cost_maint()
        self.tenancy.button_start()
        self.tenancy.create_rent_schedule()
        self.tenancy.rent_schedule_ids[0].create_invoice()
