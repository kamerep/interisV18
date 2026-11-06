# See LICENSE file for full copyright and licensing details
from odoo import _, api, fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property',
        domain="[('is_property', '=', True)]",
        index=True,
        tracking=True,
        help='Property where this equipment is installed. Requests raised '
             'for the equipment are linked to this property.')


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    @api.onchange('equipment_id')
    def _onchange_equipment_property(self):
        if self.equipment_id.property_id:
            self.property_id = self.equipment_id.property_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('equipment_id') and not vals.get('property_id'):
                equipment = self.env['maintenance.equipment'].browse(
                    vals['equipment_id'])
                if equipment.property_id:
                    vals['property_id'] = equipment.property_id.id
        return super().create(vals_list)


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    equipment_ids = fields.One2many(
        comodel_name='maintenance.equipment',
        inverse_name='property_id',
        string='Equipment',
        help='Equipment installed in this property.')
    equipment_count = fields.Integer(
        string='Equipment Count',
        compute='_compute_equipment_count')

    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        for asset in self:
            asset.equipment_count = len(asset.equipment_ids)

    def open_equipment(self):
        self.ensure_one()
        return {
            'name': _('Equipment'),
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.equipment',
            'view_mode': 'kanban,list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }
