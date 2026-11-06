# See LICENSE file for full copyright and licensing details

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class IncomeExpenditure(models.AbstractModel):
    _name = 'report.property_management_ee.report_income_expenditure'
    _description = 'Income Expenditure Report'

    def get_details(self, start_date, end_date):
        """Income (rent schedule) and expenditure (vendor bills) per property.

        :return: (rows, totals) where rows is a list of dicts per property and
            totals holds total_in, total_ex, total_gr and currency_id.
        """
        rows = []
        currency = self.env.company.currency_id
        total_in = total_ex = 0.0
        properties = self.env['account.asset'].search(
            [('is_property', '=', True)])
        for prop in properties:
            schedules = self.env['tenancy.rent.schedule'].search([
                ('start_date', '>=', start_date),
                ('start_date', '<=', end_date),
                ('tenancy_id', 'in', prop.tenancy_property_ids.ids),
            ])
            total_income = sum(schedules.mapped('amount'))
            bills = self.env['account.move'].search([
                ('property_id', '=', prop.id),
                ('move_type', 'in', ('in_invoice', 'in_refund')),
                ('state', '=', 'posted'),
                ('invoice_date', '>=', start_date),
                ('invoice_date', '<=', end_date),
            ])
            total_expence = -sum(bills.mapped('amount_total_signed'))
            total_in += total_income
            total_ex += total_expence
            rows.append({
                'property': prop.name,
                'total_income': total_income,
                'total_expence': total_expence,
                'currency_id': prop.currency_id or currency,
            })
        totals = {
            'total_in': total_in,
            'total_ex': total_ex,
            'total_gr': total_in - total_ex,
            'currency_id': currency,
        }
        return rows, totals

    def _format_date(self, date_val):
        if not date_val:
            return ''
        date_val = fields.Date.to_date(date_val)
        lang = self.env['res.lang'].search(
            [('code', '=', self.env.user.lang)], limit=1)
        if lang:
            return date_val.strftime(lang.date_format)
        return str(date_val)

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.asset'].browse(docids)
        form_data = (data or {}).get('form', {})
        start_date = form_data.get('start_date', str(fields.Date.today()))
        end_date = form_data.get(
            'end_date',
            str(fields.Date.today() + relativedelta(months=1, day=1, days=-1)))
        detail_res, totals = self.get_details(start_date, end_date)
        form_data['start_date'] = self._format_date(start_date)
        form_data['end_date'] = self._format_date(end_date)
        return {
            'doc_ids': docids,
            'doc_model': 'account.asset',
            'data': form_data,
            'docs': docs,
            'get_details': detail_res,
            'totals': totals,
        }
