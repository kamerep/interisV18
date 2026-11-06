# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    def _compute_request_count(self):
        for asset in self:
            asset.maint_request = len(asset.maintenance_ids)

    maint_request = fields.Integer(
        string='Maintenance Requests',
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

    @api.depends('tenancy_property_ids', 'tenancy_property_ids.rent',
                 'maintenance_ids', 'maintenance_ids.cost')
    def roi_calculation(self):
        for prop_rec in self:
            cost = sum(m.cost for m in prop_rec.maintenance_ids)
            gain = sum(t.rent for t in prop_rec.tenancy_property_ids)
            if cost and gain and cost != gain:
                prop_rec.roi = (gain - cost) / cost
            else:
                prop_rec.roi = 0.0
