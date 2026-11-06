# See LICENSE file for full copyright and licensing details
from odoo import models, api


class PaymentParser(models.AbstractModel):
    _name = 'report.property_rent_report_ee.report_rent_voucher_details'
    _description = 'Property Rent Report'

    def get_amount(self, data):
        """Total rent already paid on the tenancy."""
        return sum(data.rent_schedule_ids.filtered('paid').mapped('amount'))

    def get_amount_due(self, data):
        """Rent still to be paid (scheduled but unpaid lines)."""
        return sum(data.rent_schedule_ids.filtered(
            lambda line: not line.paid).mapped('amount'))

    @api.model
    def _get_report_values(self, docids, data=None):
        payslips = self.env['account.analytic.account'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.analytic.account',
            'docs': payslips,
            'data': data,
            'get_amount': self.get_amount,
            'get_amount_due': self.get_amount_due,
        }
        return docargs
