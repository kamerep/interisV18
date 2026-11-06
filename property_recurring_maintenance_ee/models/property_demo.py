# See LICENSE file for full copyright and licensing details
from odoo import api, models


class PropertyDemoLoader(models.AbstractModel):
    _inherit = 'property.demo.loader'

    @api.model
    def _load_recurring_maintenance_demo(self):
        """Recurring costs on David's weekly tenancy, added to rent bills."""
        tenancy = self.env.ref(
            'property_management_ee.demo_tenancy_david',
            raise_if_not_found=False)
        if not tenancy:
            return True
        lines = []
        for xmlid in ('maintenance_type6', 'maintenance_type7'):
            mtype = self.env.ref(
                'property_recurring_maintenance_ee.%s' % xmlid)
            lines.append((0, 0, {
                'maintenance_type': mtype.id, 'cost': mtype.cost or 25.0}))
        tenancy.write({'recurring': True, 'maintenance_cost_ids': lines})
        return True
