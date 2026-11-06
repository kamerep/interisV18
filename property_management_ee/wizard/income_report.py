# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class IncomeReport(models.TransientModel):
    _name = 'income.report'
    _description = 'Income Report'

    start_date = fields.Date(
        string='Start date',
        required=True)
    end_date = fields.Date(
        string='End date',
        required=True)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date smaller than
        the Exiration date.
        @param self : object pointer
        """
        for ver in self:
            if ver.start_date and ver.end_date and \
                    ver.end_date < ver.start_date:
                raise ValidationError(_(
                    'End date should be greater than Start Date!'))

    def print_report(self):
        return self.env.ref(
            'property_management_ee.action_report_income_expenditure'
        ).report_action(
            [], data={
                'ids': self.ids,
                'model': 'account.asset',
                'form': self.read(['start_date', 'end_date'])[0]
            })
