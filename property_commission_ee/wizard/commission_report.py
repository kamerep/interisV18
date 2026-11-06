# See LICENSE file for full copyright and licensing details

from odoo import _, models, fields, api
from odoo.exceptions import ValidationError


class CommissionReport(models.TransientModel):
    _name = 'commission.report'
    _description = 'Commission Report'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_(
                    'End date should be greater than Start date.'))

    def print_report(self):
        data = {
            'ids': self.ids,
            'model': 'commission.report',
            'form': self.read(['start_date', 'end_date'])[0],
        }
        return self.env.ref(
            'property_commission_ee.commission_for_invoice_report'
        ).report_action([], data=data)
