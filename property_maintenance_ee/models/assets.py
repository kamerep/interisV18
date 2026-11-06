# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    @api.depends('maintenance_ids')
    def _compute_request_count(self):
        for asset in self:
            asset.maint_request = len(asset.maintenance_ids)

    maint_request = fields.Integer(
        string='Maintenance Count',
        compute='_compute_request_count',
        help='Number of maintenance requests for this property.')
    maintenance_ids = fields.One2many(
        comodel_name='maintenance.request',
        inverse_name='property_id',
        string='Maintenance Requests',
        help='All maintenance requests for this property.')

    def open_maintenance(self):
        self.ensure_one()
        ctx = dict(self._context or {})
        ctx['default_property_id'] = self.id
        return {
            'name': _('Maintenance Requests'),
            'view_mode': 'list,form',
            'res_model': 'maintenance.request',
            'type': 'ir.actions.act_window',
            'domain': [('property_id', '=', self.id)],
            'context': ctx,
        }

    maintenance_cost_total = fields.Float(
        string='Maintenance Cost',
        compute='_compute_net_income',
        store=True,
        help='Total cost of all maintenance requests on this property.')
    net_income = fields.Float(
        string='Net Income (after maintenance)',
        compute='_compute_net_income',
        store=True,
        help='Tenancy rent (the ROI figure) minus maintenance cost.')

    @api.depends('roi', 'maintenance_ids', 'maintenance_ids.cost')
    def _compute_net_income(self):
        for prop_rec in self:
            cost = sum(prop_rec.maintenance_ids.mapped('cost'))
            prop_rec.maintenance_cost_total = cost
            prop_rec.net_income = prop_rec.roi - cost
