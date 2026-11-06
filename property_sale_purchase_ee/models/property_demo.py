# See LICENSE file for full copyright and licensing details
from dateutil.relativedelta import relativedelta

from odoo import api, models


class PropertyDemoLoader(models.AbstractModel):
    _inherit = 'property.demo.loader'

    @api.model
    def _load_sale_purchase_demo(self):
        """Trek Rise bought in 24 monthly instalments; White Villa sold."""
        ref = self.env.ref
        trek = ref('property_management_ee.property_5')
        trek.write({
            'purchase_price': 1800000.0,
            'partner_id': ref('base.res_partner_12').id,
            'end_date': trek.acquisition_date + relativedelta(months=24),
            'payment_term': ref('account.account_payment_term_30days').id,
        })
        trek.create_purchase_installment()
        white = ref('property_management_ee.property_6')
        term = ref('account.account_payment_term_advance_60days',
                   raise_if_not_found=False) or ref(
            'account.account_payment_term_30days')
        white.write({
            'sale_price': 2500000.0,
            'sale_date': self._today(),
            'customer_id': ref('base.res_partner_4').id,
            'payment_term': term.id,
        })
        white.genrate_payment_enteries()
        return True
