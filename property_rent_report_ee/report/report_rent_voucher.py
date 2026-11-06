# See LICENSE file for full copyright and licensing details
from odoo import models, api


class PaymentParser(models.AbstractModel):
    _name = 'report.property_rent_report_ee.report_rent_voucher_details'
    _description = 'Property Rent Report'

    def get_amount(self, data):
        """
        This method is used to get total amount
        -----------------------------------
        @param self: The object pointer
        """
        tot_amount = 0.0
        rent_amt = data.total_rent
        for line in data.rent_schedule_ids:
            if line.paid is True:
                tot_amount = tot_amount + line.amount
        return tot_amount

    def get_amount_due(self, data):
        """
        This method is used to get total amount due
        -------------------------------------------
        @param self: The object pointer
        """
        tot_amount = 0.0
        tot_paid_amount = 0.0
        due_amt = 0.0
        upto_rent = data.rent
        for line in data.rent_schedule_ids:
            if line.paid is True:
                tot_paid_amount = tot_paid_amount + line.amount
                tot_amount = tot_amount + upto_rent
        due_amt = tot_amount - tot_paid_amount
        return due_amt

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
