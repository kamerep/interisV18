# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WizardRenewTenancy(models.TransientModel):
    _name = 'renew.tenancy'
    _description = 'Renew Tenancy'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    rent_type_id = fields.Many2one(
        comodel_name='rent.type',
        string='Rent Type',
        required=True)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_(
                    'End date should be greater than Start Date!'))

    def renew_contract(self):
        active_ids = self._context.get('active_ids', [])
        modid = self.env.ref(
            'property_management_ee.property_analytic_view_form').id
        if active_ids:
            for rec in self:
                if (rec.start_date and rec.end_date
                        and rec.start_date > rec.end_date):
                    raise ValidationError(_(
                        'End Date must be greater than Start Date!'))
                self.env['account.analytic.account'].browse(
                    active_ids).write({
                        'date_start': rec.start_date,
                        'date': rec.end_date,
                        'rent_type_id': rec.rent_type_id.id or False,
                        'state': 'draft',
                        'rent_entry_chck': False,
                    })
        return {
            'view_mode': 'form',
            'view_id': modid,
            'res_model': 'account.analytic.account',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': active_ids[0] if active_ids else False,
        }
