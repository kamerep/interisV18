# See LICENSE file for full copyright and licensing details
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestPropertyMaintenance(common.TransactionCase):

    def test_net_income_and_done_invoice(self):
        request = self.env.ref('property_maintenance_ee.demo_request_done')
        prop = request.property_id
        self.assertTrue(request.invoice_id)
        self.assertTrue(request.done_notified)
        self.assertEqual(
            prop.maintenance_cost_total,
            sum(prop.maintenance_ids.mapped('cost')))
        self.assertEqual(prop.net_income,
                         prop.roi - prop.maintenance_cost_total)

    def test_stage_change_notifies_once(self):
        request = self.env.ref('property_maintenance_ee.demo_request_new')
        request.stage_id = self.env.ref('maintenance.stage_3')
        self.assertTrue(request.done_notified)
        request.stage_id = self.env.ref('maintenance.stage_0')
        self.assertFalse(request.done_notified)

    def test_equipment_links_request_to_property(self):
        equipment = self.env.ref(
            'property_maintenance_ee.demo_equipment_heater')
        prop = equipment.property_id
        self.assertIn(equipment, prop.equipment_ids)
        self.assertEqual(prop.equipment_count, len(prop.equipment_ids))
        request = self.env['maintenance.request'].create({
            'name': 'Heater element check',
            'equipment_id': equipment.id,
        })
        self.assertEqual(request.property_id, prop)
        # the running tenancy's tenant is filled in from the property
        self.assertTrue(request.tenant_id)
        self.assertIn(request, prop.maintenance_ids)

    def test_renters_fault_invoice_bills_request_tenant(self):
        request = self.env.ref('property_maintenance_ee.demo_request_moveout')
        self.assertEqual(request.invoice_id.partner_id,
                         request.tenant_id.parent_id)
