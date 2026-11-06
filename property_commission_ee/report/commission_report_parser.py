# See LICENSE file for full copyright and licensing details

from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


class CommissionInvoiceReport(models.AbstractModel):
    _name = 'report.property_commission_ee.commission_report_template2'
    _description = 'Commission Report'

    def get_datas(self, start_date, end_date):
        datas = []
        invoices = self.env['commission.invoice'].search([
            ('date', '<=', end_date),
            ('date', '>=', start_date),
            ('inv', '=', True),
        ])
        for value in invoices:
            datas.append({
                'property': value.property_id.name,
                'tenancy': value.tenancy.name,
                'commission': value.amount_total,
                'currency_id': (value.currency_id
                                or self.env.company.currency_id),
                'agent': value.agent.name,
            })
        return datas

    def _parse_date(self, value):
        if not value:
            return ''
        return parser.parse(str(value)).strftime('%d/%m/%Y')

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model') or 'commission.invoice'
        docs = self.env[model].browse(
            self.env.context.get('active_ids', []))
        form = (data or {}).get('form', {})
        start_date = form.get('start_date', str(fields.Date.today()))
        end_date = form.get(
            'end_date',
            str(fields.Date.today() + relativedelta(months=1, day=1, days=-1)))
        data_res = self.get_datas(start_date, end_date)
        form['start_date'] = self._parse_date(start_date)
        form['end_date'] = self._parse_date(end_date)
        return {
            'doc_ids': docids,
            'doc_model': model,
            'data': form,
            'docs': docs,
            'get_datas': data_res,
        }
