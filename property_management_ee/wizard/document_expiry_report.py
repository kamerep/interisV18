# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DocumentExpiryReport(models.TransientModel):
    _name = 'document.expiry.report'
    _description = 'Document Expiry Report'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_(
                    'End date should be greater than Start Date!'))

    def open_document_expiry_tree(self):
        wiz_form_id = self.env.ref(
            'property_management_ee.property_attachment_view_tree').id
        certificate_ids = self.env['property.attachment'].search([
            ('expiry_date', '>=', self.start_date),
            ('expiry_date', '<=', self.end_date),
        ])
        return {
            'name': _('Document Expiry Report'),
            'view_id': wiz_form_id,
            'view_mode': 'list',
            'res_model': 'property.attachment',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', certificate_ids.ids)],
        }

    def print_report(self):
        return self.env.ref(
            'property_management_ee.action_report_document_expiry'
        ).report_action([], data={
            'ids': self.ids,
            'model': 'account.asset',
            'form': self.read(['start_date', 'end_date'])[0],
        })
