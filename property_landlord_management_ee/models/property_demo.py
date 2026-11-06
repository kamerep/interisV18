# See LICENSE file for full copyright and licensing details
from dateutil.relativedelta import relativedelta

from odoo import api, models


class PropertyDemoLoader(models.AbstractModel):
    _inherit = 'property.demo.loader'

    @api.model
    def _load_landlord_demo(self):
        """Royal Manor is leased from a landlord; monthly payout bills."""
        ref = self.env.ref
        today = self._today()
        month_start = today.replace(day=1)
        owner = ref('property_landlord_management_ee.demo_landlord_lucy')
        royal = ref('property_management_ee.property3')
        royal.property_owner = owner
        tenancy = self.env['account.analytic.account'].with_context(
            is_landlord_rent=True).create({
                'name': 'Royal Manor - landlord lease',
                'resident_type': 'landlord_partner',
                'property_id': royal.id,
                'property_owner_id': owner.id,
                'landlord_rent': 5000.0,
                'deposit': 10000.0,
                'date_start': month_start - relativedelta(months=6),
                'date': month_start + relativedelta(months=6, days=-1),
                'rent_type_id': ref('property_management_ee.rent_type1').id,
            })
        tenancy.with_context(is_landlord_rent=True).landlord_button_start()
        tenancy.with_context(is_landlord_rent=True) \
            .create_rent_schedule_landlord()
        for schedule in tenancy.rent_schedule_ids.filtered(
                lambda s: s.start_date <= today).sorted('start_date')[:3]:
            schedule.create_landlord_invoice()
            self._post_invoice(schedule.invoice_id)
        self._register_xmlid(
            'property_landlord_management_ee', 'demo_landlord_tenancy',
            tenancy)
        return True
