# See LICENSE file for full copyright and licensing details
from odoo import api, models


class PropertyDemoLoader(models.AbstractModel):
    _inherit = 'property.demo.loader'

    @api.model
    def _load_booking_demo(self):
        """A 3-floor building with 4 units per floor; one unit booked."""
        ref = self.env.ref
        golden = ref('property_management_ee.property1')
        building = self.env['property.created'].create({
            'name': 'Sunrise Towers',
            'is_property': True,
            'is_sub_property': True,
            'floor': 3,
            'no_of_property': 4,
            'prefix3': '2',
            'type_id': golden.type_id.id,
            'property_manager': golden.property_manager.id,
            'street': 'Kenyatta Avenue 5',
            'city': 'Nairobi',
            'country_id': ref('base.ke').id,
            'ground_rent': 900.0,
            'original_value': 150000.0,
            'rent_type_id': ref('property_management_ee.rent_type1').id,
            'income_acc_id': golden.income_acc_id.id,
            'account_depreciation_expense_id':
                golden.account_depreciation_expense_id.id,
        })
        building.create_property()
        unit = self.env['property.created'].search(
            [('property_parent_id', '=', building.asset_id.id)],
            order='id', limit=1)
        if unit:
            unit.asset_id.edit_status()
        self._register_xmlid(
            'property_booking_ee', 'demo_building_sunrise', building)
        return True
