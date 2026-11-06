# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    sale_date = fields.Date(
        string='Sale Date',
        help='Sale Date of the Property.')
    sale_price = fields.Monetary(
        currency_field='currency_id',
        string='Sale Price',
        help='Sale price of the Property.')
    payment_term = fields.Many2one(
        comodel_name='account.payment.term',
        string='Payment Terms')
    sale_cost_ids = fields.One2many(
        comodel_name='sale.cost',
        inverse_name='property_id',
        string='Sale Installments')
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer')
    end_date = fields.Date(string='End Date')
    purchase_price = fields.Monetary(
        currency_field='currency_id',
        string='Purchase Price',
        help='Purchase price of the Property.')
    multiple_owners = fields.Boolean(
        string='Multiple Owners',
        help="Check if there are multiple owners of the Property.")
    total_owners = fields.Integer(string='Number of Owners')
    recurring_rule_type = fields.Selection(
        [('monthly', 'Month(s)')],
        string='Recurrency',
        default='monthly')
    purchase_cost_ids = fields.One2many(
        comodel_name='cost.cost',
        inverse_name='property_id',
        string='Purchase Installments')
    return_period = fields.Float(
        compute='_compute_calc_return_period',
        string="Return Period (Months)",
        store=True,
        help='Purchase Price / Ground Rent.')
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner')

    @api.constrains('sale_price')
    def check_negative_sale_price(self):
        for prop in self:
            if prop.sale_price < 0:
                raise ValidationError(_(
                    'You cannot enter a negative Sale Price.'))

    @api.depends('purchase_price', 'ground_rent')
    def _compute_calc_return_period(self):
        for prop in self:
            if prop.ground_rent and prop.purchase_price:
                prop.return_period = prop.purchase_price / prop.ground_rent
            else:
                prop.return_period = 0.0

    def create_purchase_installment(self):
        for res in self:
            amount = res.purchase_price
            if not amount:
                raise UserError(_('Please Enter a Valid Purchase Price.'))
            if not res.end_date:
                raise UserError(_('Please Select an End Date.'))
            if res.end_date < res.acquisition_date:
                raise UserError(_(
                    'End Date must be greater than the Purchase Date.'))

            def diff_month(d1, d2):
                return (d1.year - d2.year) * 12 + d1.month - d2.month

            difference_month = diff_month(res.end_date, res.acquisition_date)
            if difference_month == 0:
                amnt = amount
            else:
                if res.end_date.day > res.acquisition_date.day:
                    difference_month += 1
                amnt = amount / difference_month

            # Use parameterized query to prevent SQL injection
            self.env.cr.execute(
                "SELECT date FROM cost_cost WHERE property_id = %s",
                (res.id,))
            exist_dates = set(row[0] for row in self.env.cr.fetchall())
            date_add = self.date_addition(
                res.acquisition_date, res.end_date, res.recurring_rule_type)
            result = sorted(set(date_add) - exist_dates)

            year_create = []
            for dates in result:
                remain_amnt = abs(amount - amnt)
                remain_amnt_per = abs((remain_amnt / res.purchase_price) * 100)
                year_create.append((0, 0, {
                    'currency_id': res.currency_id.id or False,
                    'date': dates,
                    'property_id': res.id,
                    'amount': amnt,
                    'remaining_amount': remain_amnt,
                    'rmn_amnt_per': remain_amnt_per,
                }))
                amount = remain_amnt
            res.write({
                'purchase_cost_ids': year_create,
                'pur_instl_chck': True,
            })
        return True

    def genrate_payment_enteries(self):
        for data in self:
            if not data.payment_term:
                raise UserError(_('Please Enter Payment Terms.'))
            if not data.sale_price:
                raise UserError(_('Please Enter a Valid Sale Price.'))
            # V18: public compute() was removed; use _compute_terms()
            term_data = data.payment_term._compute_terms(
                date_ref=data.sale_date or fields.Date.today(),
                currency=data.currency_id,
                company=data.company_id or self.env.company,
                tax_amount=0.0,
                tax_amount_currency=0.0,
                sign=1,
                untaxed_amount=data.sale_price,
                untaxed_amount_currency=data.sale_price)
            amount = data.sale_price
            year_create = []
            for line in term_data['line_ids']:
                line_date = line['date']
                lst = line['foreign_amount']
                remain_amnt = abs(amount - lst)
                remain_amnt_per = abs(
                    (remain_amnt / data.sale_price) * 100
                    if data.sale_price else 0.0)
                year_create.append((0, 0, {
                    'currency_id': data.currency_id.id or False,
                    'date': line_date,
                    'property_id': data.id,
                    'amount': lst,
                    'remaining_amount': remain_amnt,
                    'rmn_amnt_per': remain_amnt_per,
                }))
                amount -= lst
            data.write({
                'sale_cost_ids': year_create,
                'sale_instl_chck': True,
            })
        return True
