# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecurringMaintenanceType(models.Model):
    _name = 'recurring.maintenance.type'
    _description = 'Recurring Maintenance Type'

    name = fields.Char(
        string='Maintenance Type',
        size=50,
        required=True,
        help='E.g. Maintain Garden, Maintain Swimming Pool')
    cost = fields.Float(
        string='Maintenance Cost',
        help='Cost of this maintenance type.')
    maintenance_team_id = fields.Many2one(
        comodel_name='maintenance.team',
        string='Maintenance Team')

    @api.constrains('cost')
    def check_negative_value(self):
        for rec in self:
            if rec.cost < 0:
                raise ValidationError(_(
                    'You cannot enter a negative Maintenance Cost.'))


class RecurringMaintenanceLine(models.Model):
    _name = 'recurring.maintenance.line'
    _description = 'Recurring Maintenance Line'

    date = fields.Date(
        string='Expiration Date',
        help="Contract end date.")
    maintenance_type_ids = fields.Many2many(
        comodel_name='recurring.maintenance.type',
        relation='recurring_maintenance_type_rel',
        column1='recurring_line_id',
        column2='maintenance_typ_id',
        string='Maintenance Types')


class MaintenanceCost(models.Model):
    _name = 'maintenance.cost'
    _description = 'Maintenance Cost'

    maintenance_type = fields.Many2one(
        comodel_name='recurring.maintenance.type',
        string='Maintenance Type')
    cost = fields.Monetary(
        string='Maintenance Cost',
        currency_field='currency_id')
    tenancy = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='tenancy.company_id',
        required=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency',
        related="company_id.currency_id",
        required=True,
        readonly=False,
        string='Currency')

    @api.constrains('cost')
    def check_negative_value(self):
        for rec in self:
            if rec.cost < 0:
                raise ValidationError(_(
                    'You cannot enter a negative Maintenance Cost.'))

    @api.onchange('maintenance_type')
    def onchange_property_id(self):
        for data in self:
            if data.maintenance_type:
                data.cost = data.maintenance_type.cost or 0.00


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    @api.depends('maintenance_cost_ids.cost')
    def _compute_total_cost_maint(self):
        for rec in self:
            rec.maintenance_cost = sum(
                c.cost for c in rec.maintenance_cost_ids) or 0.0

    maintenance_cost_ids = fields.One2many(
        comodel_name='maintenance.cost',
        inverse_name='tenancy',
        string='Recurring Maintenance Costs')
    maintenance_cost = fields.Monetary(
        string='Maintenance Cost',
        store=True,
        currency_field='currency_id',
        compute='_compute_total_cost_maint')


class TenancyRentSchedule(models.Model):
    _inherit = "tenancy.rent.schedule"

    def get_invoice_lines(self):
        inv_lines = super().get_invoice_lines()
        for rec in self:
            if not rec.tenancy_id.maintenance_cost:
                continue
            maint_cost = rec.tenancy_id.maintenance_cost
            rent_type = rec.tenancy_id.rent_type_id
            if rent_type.renttype == 'Monthly':
                maint_cost *= float(rent_type.name)
            elif rent_type.renttype == 'Yearly':
                maint_cost *= float(rent_type.name) * 12
            analytic_dist = (
                {str(rec.tenancy_id.id): 100} if rec.tenancy_id else {})
            inv_lines.append((0, 0, {
                'name': _('Maintenance Cost'),
                'price_unit': maint_cost or 0.00,
                'quantity': 1,
                'account_id': (
                    rec.tenancy_id.property_id.income_acc_id.id or False),
                'analytic_distribution': analytic_dist,
            }))
        return inv_lines
