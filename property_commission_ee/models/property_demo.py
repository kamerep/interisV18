# See LICENSE file for full copyright and licensing details
from odoo import api, models


class PropertyDemoLoader(models.AbstractModel):
    _inherit = 'property.demo.loader'

    @api.model
    def _load_commission_demo(self):
        """10 % agent commission on Brian's tenancy, invoiced to the agent."""
        tenancy = self.env.ref(
            'property_management_ee.demo_tenancy_brian',
            raise_if_not_found=False)
        if not tenancy:
            return True
        tenancy.write({
            'commission': True,
            'commission_type': 'fixed',
            'fix_qty': 10.0,
            'agent': self.env.ref('property_commission_ee.demo_agent').id,
        })
        tenancy.create_commission()
        commission = self.env['commission.invoice'].search(
            [('tenancy', '=', tenancy.id)], limit=1)
        commission.create_invoice()
        self._post_invoice(commission.invc_id)
        self._register_xmlid(
            'property_commission_ee', 'demo_commission_brian', commission)
        return True
