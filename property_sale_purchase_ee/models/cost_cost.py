# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CostCost(models.Model):
    _name = "cost.cost"
    _description = 'Purchase Installment'
    _order = 'date'

    @api.depends('move_id')
    def _compute_move_check(self):
        for cost in self:
            cost.move_check = bool(cost.move_id)

    date = fields.Date(string='Date')
    name = fields.Char(string='Description', size=100)
    payment_details = fields.Char(string='Payment Details', size=100)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='property_id.company_id',
        required=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency',
        related="company_id.currency_id",
        required=True,
        readonly=False,
        string='Currency')
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')
    remaining_amount = fields.Monetary(
        string='Remaining Amount',
        currency_field='currency_id')
    amount = fields.Monetary(
        currency_field='currency_id',
        string='Amount')
    move_check = fields.Boolean(
        compute='_compute_move_check',
        string='Posted',
        store=True)
    rmn_amnt_per = fields.Monetary(
        string='Remaining Amount (%)',
        currency_field='currency_id')
    invc_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice')

    @api.constrains('remaining_amount', 'amount')
    def check_negative_value(self):
        for rec in self:
            if rec.remaining_amount < 0:
                raise ValidationError(_(
                    'You cannot enter a negative Remaining Amount.'))
            if rec.amount < 0:
                raise ValidationError(_(
                    'You cannot enter a negative Amount.'))

    def create_invoice(self):
        journal = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1)
        for cost in self:
            if not cost.property_id.partner_id:
                raise UserError(_('Please Select a Partner!'))
            if not cost.property_id.account_depreciation_expense_id:
                raise UserError(_('Please Select an Expense Account!'))
            inv_values = {
                'invoice_payment_term_id': (
                    cost.property_id.payment_term.id or False),
                'partner_id': cost.property_id.partner_id.id or False,
                'move_type': 'in_invoice',
                'property_id': cost.property_id.id or False,
                'invoice_line_ids': [(0, 0, {
                    'name': _('Purchase Cost For %s') % cost.property_id.name,
                    'price_unit': cost.amount or 0.00,
                    'quantity': 1,
                    'account_id': (
                        cost.property_id.account_depreciation_expense_id.id),
                })],
                'journal_id': journal.id if journal else False,
            }
            invoice = self.env['account.move'].create(inv_values)
            cost.write({'invc_id': invoice.id, 'move_check': True})
        return {
            'view_id': self.env.ref('account.view_move_form').id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def open_invoice(self):
        return {
            'view_id': self.env.ref('account.view_move_form').id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
