# See LICENSE file for full copyright and licensing details
from odoo import api, models


class PropertyDemoLoader(models.AbstractModel):
    _inherit = 'property.demo.loader'

    @api.model
    def _load_penalty_demo(self):
        """5 % penalty after 5 days on Alice's tenancy (has overdue rent)."""
        tenancy = self.env.ref(
            'property_management_ee.demo_tenancy_alice',
            raise_if_not_found=False)
        if tenancy:
            tenancy.write({'penalty': 5.0, 'penalty_day': 5})
        return True
