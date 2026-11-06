# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CommissionInvoiceLine(models.Model):
    _name = "commission.invoice.line"
    _description = "Commission Invoice Line"
    _order = 'date desc, id desc'

    date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    name = fields.Char(string="Description")
    commission_type = fields.Selection(
        selection=[('fixed', 'Fixed Percentage'),
                   ('fixedcost', 'By Fixed Cost')],
        string='Type')
    rent_amt = fields.Float(string='Rent Amount')
    amount = fields.Float(store=True, string='Commission Amount')
    commission_id = fields.Many2one(
        comodel_name='commission.invoice',
        string='Commission')
    invc_id = fields.Many2one(comodel_name='account.move', string='Invoice')
    inv = fields.Boolean(string='INV')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Owner Company")
    invoiced = fields.Boolean(string='Invoiced')

    @api.constrains('date', 'end_date')
    def _constraint_date_limit(self):
        for rec in self:
            if rec.date and rec.end_date and rec.end_date < rec.date:
                raise ValidationError(_(
                    'Commission end date must be greater than or equal to '
                    'start date!'))


class CommissionInvoice(models.Model):
    _name = "commission.invoice"
    _rec_name = 'number'
    _description = "Commission Invoice"

    @api.depends('commission_line.amount')
    def _amount_all(self):
        for rec in self:
            rec.amount_total = sum(
                line.amount for line in rec.commission_line)

    number = fields.Char(string='Commission ID', default='/')
    partner_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Partner',
        help='Tenant from whom commission is taken.')
    date = fields.Date(
        string='Commission Date',
        default=fields.Date.context_today)
    tenancy = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')
    description = fields.Text(string='Description')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')
    state = fields.Selection(
        [('draft', 'Open'),
         ('cancel', 'Cancel'),
         ('invoice', 'Invoiced')],
        string='State',
        readonly=True,
        default='draft')
    commission_type = fields.Selection(
        selection=[('fixed', 'Fixed Percentage'),
                   ('fixedcost', 'By Fixed Cost')],
        string='Type',
        default='fixed')
    commission_line = fields.One2many(
        comodel_name='commission.invoice.line',
        inverse_name='commission_id',
        string='Commission Lines')
    amount_total = fields.Float(
        string='Total',
        store=True,
        readonly=True,
        compute='_amount_all')
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency")
    agent = fields.Many2one(
        comodel_name='res.partner',
        domain=[('agent', '=', True)])
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company)
    invc_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice')
    inv = fields.Boolean(string='INV')
    color = fields.Integer('Color Index')

    @api.onchange('tenancy')
    def parent_tenancy_onchange(self):
        if self.tenancy:
            self.agent = self.tenancy.agent.id or False
            self.property_id = self.tenancy.property_id.id or False
            self.partner_id = self.tenancy.tenant_id.id or False
            self.currency_id = self.tenancy.currency_id.id or False

    def create_invoice(self):
        journal = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1)
        for data in self:
            analytic_dist = (
                {str(data.tenancy.id): 100} if data.tenancy else {})
            inv_line_values = {
                'name': 'Commission For %s' % (data.number or ''),
                'analytic_distribution': analytic_dist,
                'quantity': 1,
                'account_id': (
                    data.property_id.account_depreciation_expense_id.id
                    or False),
                'price_unit': data.amount_total or 0.00,
            }
            inv_values = {
                'invoice_origin': 'Commission For %s' % (data.number or ''),
                'move_type': 'in_invoice',
                'property_id': data.property_id.id,
                'partner_id': data.agent.id or False,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                'invoice_date': fields.Date.today(),
                'journal_id': journal.id if journal else False,
                'currency_id': data.currency_id.id or False,
            }
            acc_id = self.env['account.move'].create(inv_values)
            data.write({'inv': True, 'invc_id': acc_id.id, 'state': 'invoice'})
            # the owner report works on invoiced commission lines
            data.commission_line.write({'inv': True, 'invc_id': acc_id.id})
        if len(self) != 1:
            return True
        return {
            'view_id': self.env.ref('account.view_move_form').id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def open_invoice(self):
        self.ensure_one()
        return {
            'view_id': self.env.ref('account.view_move_form').id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec.number = (
                self.env['ir.sequence'].next_by_code('commission.invoice')
                or '/')
        return records

    def button_close(self):
        for rec in self:
            if rec.tenancy.state not in ('close', 'cancelled'):
                raise ValidationError(_(
                    'Please close the tenancy "%s" first!'
                ) % rec.tenancy.name)
            rec.write({'state': 'cancel'})


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    @api.depends('commission', 'commission_type', 'fix_qty', 'fix_cost',
                 'total_rent')
    def calculate_commission(self):
        for data in self:
            total = 0.0
            if data.commission:
                if data.commission_type == 'fixed':
                    total = data.total_rent * (data.fix_qty / 100.0)
                elif data.commission_type == 'fixedcost':
                    total = data.fix_cost
            data.total_commission = total

    commission_type = fields.Selection(
        selection=[('fixed', 'Fixed Percentage'),
                   ('fixedcost', 'By Fixed Cost')],
        string='Commission Type')
    fix_qty = fields.Float(string='Fixed Percentage (%)')
    fix_cost = fields.Float(string='Fixed Cost')
    agent = fields.Many2one(
        comodel_name='res.partner',
        domain=[('agent', '=', True)])
    commission = fields.Boolean('Commission')
    commission_create = fields.Boolean('Created')
    total_commission = fields.Float(
        string="Total Commission",
        compute="calculate_commission")

    def create_commission(self):
        for data in self:
            if data.total_commission == 0.00:
                raise ValidationError(_(
                    'Total Commission must be greater than zero.'))
            line_vals = {
                'name': 'Commission',
                'commission_type': data.commission_type,
                'rent_amt': data.total_rent,
                'date': data.date_start,
                'end_date': data.date,
                'amount': data.total_commission,
            }
            self.env['commission.invoice'].create({
                'partner_id': data.tenant_id.id,
                'tenancy': data.id,
                'property_id': data.property_id.id,
                'agent': data.agent.id,
                'commission_line': [(0, 0, line_vals)],
            })
            data.write({'commission_create': True})

    @api.onchange('commission')
    def onchange_commission(self):
        if not self.commission:
            self.agent = False
            self.commission_type = False
            self.fix_qty = 0.00
            self.fix_cost = 0.00
