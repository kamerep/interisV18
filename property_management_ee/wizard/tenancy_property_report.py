# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TenancyPropertyReport(models.TransientModel):
    _name = 'tenancy.property.report'
    _description = 'Tenancy Property Report'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property',
        required=True)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_(
                    'End date should be greater than Start Date!'))

    def _get_tenancy_ids(self):
        return self.env['account.analytic.account'].search([
            ('property_id', '=', self.property_id.id),
            ('date_start', '>=', self.start_date),
            ('date_start', '<=', self.end_date),
        ])

    def open_tenancy_by_property_tree(self):
        wiz_form_id = self.env.ref(
            'property_management_ee.property_analytic_report_view_tree').id
        return {
            'name': _('Tenancy Report By Property'),
            'view_id': wiz_form_id,
            'view_mode': 'list',
            'res_model': 'account.analytic.account',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', self._get_tenancy_ids().ids)],
        }

    def print_report(self):
        data = self.read([])[0]
        data['property_name'] = self.property_id.name
        return self.env.ref(
            'property_management_ee.action_report_tenancy_by_property'
        ).report_action([], data={
            'ids': self.ids,
            'model': 'account.asset',
            'form': data,
        })
