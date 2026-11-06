# See LICENSE file for full copyright and licensing details

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models


class TenancyRentSchedule(models.Model):
    _name = "tenancy.rent.schedule"
    _description = 'Tenancy Rent Schedule'
    _rec_name = "tenancy_id"
    _order = 'start_date'

    @api.depends('invoice_id', 'invoice_id.state', 'move_id')
    def compute_move_check(self):
        for data in self:
            data.move_check = bool(data.move_id)
            if data.invoice_id and data.invoice_id.state == 'posted':
                data.move_check = True

    @api.depends('invoice_id', 'invoice_id.amount_residual')
    def compute_paid(self):
        for data in self:
            data.paid = bool(
                data.invoice_id
                and data.invoice_id.amount_residual == 0)

    note = fields.Text(string='Notes', help='Additional Notes.')
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='tenancy_id.company_id',
        string='Company',
        store=True,
        index=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string='Currency',
        required=True)
    amount = fields.Monetary(
        string='Amount',
        default=0.0,
        currency_field='currency_id',
        help="Rent Amount.")
    start_date = fields.Date(string='Date', help='Start Date.')
    end_date = fields.Date(string='End Date', help='End Date.')
    cheque_detail = fields.Char(string='Cheque Detail', size=30)
    move_check = fields.Boolean(
        compute='compute_move_check',
        string='Posted',
        store=True)
    rel_tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string="Tenant",
        related='tenancy_id.tenant_id',
        store=True)
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Depreciation Entry')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property',
        help='Property Name.')
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        domain="[('resident_type', '=', 'tenant_tenancy')]",
        help='Tenancy Name.',
        required=True)
    paid = fields.Boolean(
        compute='compute_paid',
        store=True,
        string='Paid',
        help="True if this rent is paid by tenant")
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice')
    is_invoiced = fields.Boolean(string='Invoiced?')
    rent_residual = fields.Monetary(
        string='Pending Amount',
        related="invoice_id.amount_residual",
        currency_field='currency_id',
        help="Pending Amount.")
    is_readonly = fields.Boolean(string='Readonly')

    def get_invoice_lines(self):
        inv_line = {}
        for rec in self:
            analytic_dist = (
                {str(rec.tenancy_id.id): 100}
                if rec.tenancy_id else {})
            inv_line = {
                'name': _('Tenancy (Rent) Cost'),
                'price_unit': rec.amount or 0.00,
                'quantity': 1,
                'account_id': (
                    rec.tenancy_id.property_id.income_acc_id.id or False),
                'analytic_distribution': analytic_dist,
            }
        return [(0, 0, inv_line)]

    def create_invoice(self):
        inv_obj = self.env['account.move']
        inv_form_id = self.env.ref('account.view_move_form').id
        for rec in self:
            inv_values = {
                'partner_id': (
                    rec.tenancy_id.tenant_id.parent_id.id or False),
                'move_type': 'out_invoice',
                'property_id': rec.tenancy_id.property_id.id or False,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': rec.get_invoice_lines(),
                'new_tenancy_id': rec.tenancy_id.id,
            }
            invoice_id = inv_obj.create(inv_values)
            rec.write({'invoice_id': invoice_id.id, 'is_invoiced': True})
        if len(self) != 1:
            return True
        return {
            'view_id': inv_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def open_invoice(self):
        self.ensure_one()
        return {
            'view_id': self.env.ref('account.view_move_form').id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.model
    def send_mail_tenant_rent_schedule(self):
        """Cron: remind tenants of unpaid rent due within the next 7 days."""
        template = self.env.ref(
            'property_management_ee.mail_tenant_rent',
            raise_if_not_found=False)
        if not template:
            return True
        today = fields.Date.context_today(self)
        schedules = self.search([
            ('paid', '=', False),
            ('start_date', '>=', today),
            ('start_date', '<=', today + relativedelta(days=7)),
            ('tenancy_id.state', '=', 'open'),
        ])
        for schedule in schedules:
            to_email = schedule.tenancy_id.tenant_id.email
            if not to_email:
                continue
            email_values = {'email_to': to_email}
            manager_email = (
                schedule.tenancy_id.property_id.property_manager.email)
            if manager_email:
                email_values['email_from'] = manager_email
            # Per-mail values: never write recipients on the shared template
            template.send_mail(schedule.id, email_values=email_values)
        return True
