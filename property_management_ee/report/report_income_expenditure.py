# See LICENSE file for full copyright and licensing details

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.tools.misc import formatLang


class IncomeExpenditure(models.AbstractModel):
    _name = 'report.property_management_ee.report_income_expenditure'
    _description = 'Income Expenditure Report'

    def get_details(self, start_date, end_date):
        report_rec = []
        total_in = 0.00
        total_ex = 0.00
        currency = False
        properties = self.env['account.asset'].search(
            [('is_property', '=', True)])
        for prop in properties:
            currency = prop.currency_id
            tenancies = self.env['tenancy.rent.schedule'].search([
                ('start_date', '>=', start_date),
                ('start_date', '<=', end_date),
                ('tenancy_id', 'in', prop.tenancy_property_ids.ids),
            ])
            total_income = sum(tenancies.mapped('amount'))
            # Expenditure: posted vendor bills/refunds booked on the property
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
            report_rec.append({
                'property': prop.name,
                'total_income': total_income,
                'total_expence': total_expence,
                'currency_id': prop.currency_id,
                'total_in': '',
                'total_ex': '',
                'total_gr': '',
            })
        total_gr = total_in - total_ex
        if total_in or total_ex:
            report_rec.append({
                'property': '',
                'total_income': '',
                'total_expence': '',
                'currency_id': currency,
                'total_in': formatLang(self.env, total_in, currency_obj=currency),
                'total_ex': formatLang(self.env, total_ex, currency_obj=currency),
                'total_gr': formatLang(self.env, total_gr, currency_obj=currency),
            })
        return report_rec

    def _format_date(self, date_val):
        if not date_val:
            return ''
        if isinstance(date_val, str):
            from datetime import datetime
            date_val = datetime.strptime(date_val, '%Y-%m-%d').date()
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
        detail_res = self.get_details(start_date, end_date)
        form_data['start_date'] = self._format_date(start_date)
        form_data['end_date'] = self._format_date(end_date)
        return {
            'doc_ids': docids,
            'doc_model': 'account.asset',
            'data': form_data,
            'docs': docs,
            'get_details': detail_res,
        }
