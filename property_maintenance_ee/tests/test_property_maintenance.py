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
