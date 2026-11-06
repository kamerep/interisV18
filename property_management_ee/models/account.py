# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property',
        help='Property Name.')
    new_tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')
    schedule_date = fields.Date(
        string='Schedule Date',
        help='Rent Schedule Date.')
    source = fields.Char(
        string='Account Source',
        help='Source from where account move created.')


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property',
        help='Property Name.')


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        help='Tenancy Name.')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property',
        help='Property Name.')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        context = self._context
        active_model = context.get('active_model')
        active_id = context.get('active_id')
        if active_model and active_id:
            active_rec = self.env[active_model].browse(active_id)
            res['property_id'] = (
                active_rec.property_id.id
                if hasattr(active_rec, 'property_id') else False)
            res['tenancy_id'] = (
                active_rec.new_tenancy_id.id
                if hasattr(active_rec, 'new_tenancy_id') else False)
        return res

    def _create_payment_vals_from_wizard(self, batch_result):
        res = super()._create_payment_vals_from_wizard(batch_result)
        if self.property_id:
            res['property_id'] = self.property_id.id
        return res


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        help='Tenancy Name.')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property',
        help='Property Name.')
    amount_due = fields.Monetary(
        related='partner_id.credit',
        string='Amount Due',
        readonly=True,
        help='Display Due amount of Customer')

    def action_post(self):
        res = super().action_post()
        context = self._context
        for rec in self:
            if context.get('return'):
                move = self.env['account.move'].browse(
                    context.get('active_id'))
                if move.new_tenancy_id:
                    move.new_tenancy_id.write(
                        {'amount_return': rec.amount})
            if context.get('deposite_received'):
                tenancy = self.env['account.analytic.account'].browse(
                    context.get('active_id'))
                if tenancy:
                    tenancy.write({'amount_return': rec.amount})
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.tenancy_id:
                if rec.payment_type == 'inbound':
                    rec.tenancy_id.write({'acc_pay_dep_rec_id': rec.id})
                elif rec.payment_type == 'outbound':
                    rec.tenancy_id.write({'acc_pay_dep_ret_id': rec.id})
        return records

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        result = super()._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals)
        context = self._context
        for line in result:
            if self.property_id and not self.move_id.property_id:
                self.move_id.property_id = self.property_id.id
            if (context.get('account_deposit_received')
                    and line.get('debit', 0) > 0
                    and self.tenancy_id):
                line['property_id'] = self.property_id.id or False
                if self.tenancy_id.id:
                    line['analytic_distribution'] = {
                        str(self.tenancy_id.id): 100}
        return result
