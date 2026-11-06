# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ContractExpiryReport(models.TransientModel):
    _name = 'contract.expiry.report'
    _description = 'Contract Expiry Report'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_(
                    'End date should be greater than Start Date!'))

    def open_contract_expiry_tree(self):
        wiz_form_id = self.env.ref(
            'property_management_ee.property_analytic_report_view_tree').id
        tenancy_ids = self.env['account.analytic.account'].search([
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ])
        return {
            'name': _('Tenancy Contract Expiry'),
            'view_mode': 'list',
            'view_id': wiz_form_id,
            'res_model': 'account.analytic.account',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', tenancy_ids.ids)],
        }

    def print_report(self):
        return self.env.ref(
            'property_management_ee.action_report_contract_expiry'
        ).report_action([], data={
            'ids': self.ids,
            'model': 'account.asset',
            'form': self.read(['start_date', 'end_date'])[0],
        })
