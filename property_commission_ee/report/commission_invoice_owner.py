# See LICENSE file for full copyright and licensing details

from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


class CommissionInvoiceOwner(models.AbstractModel):
    _name = 'report.property_commission_ee.commission_invoice_owner'
    _description = 'Commission Invoice Owner Report'

    def get_data(self, start_date, end_date, company_id):
        invoices = self.env['account.move']
        lines = self.env['commission.invoice.line'].search([
            ('inv', '=', True),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('commission_id.company_id', '=', company_id),
        ])
        for line in lines:
            invoices |= line.invc_id
        return invoices

    def _parse_date(self, value):
        if not value:
            return ''
        return parser.parse(str(value)).strftime('%d/%m/%Y')

    @api.model
    def _get_report_values(self, docids, data=None):
        form = (data or {}).get('form') or self._context.get(
            'data', {}).get('form', {})
        model = self.env.context.get('active_model') or (
            data or {}).get('model', 'commission.invoice.owner')
        start_date = form.get('start_date', str(fields.Date.today()))
        end_date = form.get(
            'end_date',
            str(fields.Date.today() + relativedelta(months=1, day=1, days=-1)))
        company = form.get('company_id')
        company_id = company[1] if isinstance(company, (list, tuple)) else company
        invoices = self.get_data(start_date, end_date, company_id)
        form['start_date'] = self._parse_date(start_date)
        form['end_date'] = self._parse_date(end_date)
        return {
            'doc_ids': docids,
            'doc_model': model,
            'data': form,
            'docs': invoices,
            'get_data': invoices,
        }
