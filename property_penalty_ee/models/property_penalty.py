# See LICENSE file for full copyright and licensing details

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    penalty = fields.Float(string='Penalty (%)')
    penalty_day = fields.Integer(string='Penalty Count After Days')


class TenancyRentSchedule(models.Model):
    _inherit = "tenancy.rent.schedule"
    _rec_name = "tenancy_id"
    _order = 'start_date'

    penalty_amount = fields.Float(string='Penalty Amount')

    def calculate_penalty(self):
        today = fields.Date.today()
        for tenancy in self:
            if tenancy.paid or not tenancy.start_date:
                continue
            effective_date = tenancy.start_date
            if tenancy.tenancy_id.penalty_day:
                effective_date = effective_date + relativedelta(
                    days=int(tenancy.tenancy_id.penalty_day))
            if effective_date < today and (today - effective_date).days:
                penalty_amt = (
                    tenancy.tenancy_id.rent
                    * tenancy.tenancy_id.penalty) / 100
                tenancy.penalty_amount = penalty_amt
        return True

    def get_invoice_lines(self):
        inv_lines = super().get_invoice_lines()
        for tenancy in self:
            if not inv_lines:
                continue
            inv_line_values = inv_lines[0][2]
            tenancy.calculate_penalty()
            if tenancy.tenancy_id.penalty < 0:
                raise ValidationError(_(
                    'The Penalty % must be strictly positive.'))
            if tenancy.tenancy_id.penalty_day < 0:
                raise ValidationError(_(
                    'Penalty Count After Days must be strictly positive.'))
            amt = tenancy.amount + tenancy.penalty_amount
            inv_line_values.update({'price_unit': amt or 0.00})
        return inv_lines
