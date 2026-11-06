# See LICENSE file for full copyright and licensing details

from odoo import _, models, fields, api
from odoo.exceptions import ValidationError


class CommissionInvoiceOwner(models.TransientModel):
    _name = 'commission.invoice.owner'
    _description = 'Commission Invoice Owner Report'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Owner Company",
        required=True,
        default=lambda self: self.env.company)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_(
                    'End date should be greater than Start date.'))

    def print_yes(self):
        datas = {
            'ids': self.ids,
            'model': 'commission.invoice.owner',
            'form': self.read(['start_date', 'end_date', 'company_id'])[0],
        }
        comm_inv_ids = self.env['commission.invoice.line'].search([
            ('inv', '=', True),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('commission_id.company_id', '=', self.company_id.id),
        ])
        if not comm_inv_ids:
            raise ValidationError(_(
                'No commission records found in this period for this company.'))
        return self.env.ref(
            'property_commission_ee.commission_owner_invoice_report'
        ).report_action(self, data=datas)

    def action_invoice_sent(self):
        self.ensure_one()
        template = self.env.ref(
            'property_commission_ee.email_invoice_template_id',
            raise_if_not_found=False)
        compose_form = self.env.ref(
            'mail.email_compose_message_wizard_form',
            raise_if_not_found=False)
        datas = {
            'ids': self.ids,
            'model': 'commission.invoice.owner',
            'form': self.read(['start_date', 'end_date', 'company_id'])[0],
        }
        ctx = {
            'default_model': 'commission.invoice.owner',
            'default_res_id': self.id,
            'default_use_template': bool(template),
            'default_template_id': template.id if template else False,
            'default_composition_mode': 'comment',
            'data': datas,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id if compose_form else False, 'form')],
            'view_id': compose_form.id if compose_form else False,
            'target': 'new',
            'context': ctx,
        }
