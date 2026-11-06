# See LICENSE file for full copyright and licensing details
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models



class tenancy_detail_by_tenant(models.AbstractModel):
    _name = 'report.property_management_ee.report_tenancy_by_tenant'
    _description = 'Tenancy By Tenant'

    def _fmt_date(self, value):
        """Format a date with the user's language date format."""
        if not value:
            return ''
        lang = self.env['res.lang']._lang_get(self.env.user.lang)
        return value.strftime(lang.date_format if lang else '%Y-%m-%d')

    def get_details(self, start_date, end_date, tenant_id):
        data_1 = []
        tenancy_obj = self.env["account.analytic.account"]
        tenancy_ids = tenancy_obj.search([
            ('tenant_id', '=', tenant_id[0]),
            ('date_start', '>=', start_date),
            ('date_start', '<=', end_date),
            ('resident_type', '=', 'tenant_tenancy')])
        for data in tenancy_ids:
            state_value = dict(data._fields['state'].selection).get(
                data.state, '')
            start_date = self._fmt_date(data.date_start)
            date = self._fmt_date(data.date)
            cur = data.currency_id.symbol or ''
            if data.multi_prop and data.prop_ids:
                property_str = ', '.join(data.prop_ids.mapped('name'))
            else:
                property_str = data.property_id.name or ''
            data_1.append({
                'property_id': property_str,
                'date_start': start_date,
                'date': date,
                'rent': cur + str(data.rent),
                'deposit': cur + str(data.deposit),
                'rent_type_id': data.rent_type_id.name,
                'rent_type_month': data.rent_type_id.renttype,
                'state': state_value
            })
        return data_1

    def date_format(self, date):
        from_date = datetime.strptime(date, '%Y-%m-%d')
        user_lang = self.env.user.lang
        lang = self.env['res.lang'].search(
            [('code', '=', user_lang)])
        if from_date:
            final_from_date = from_date.strftime(lang.date_format)
        return final_from_date

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.asset'].browse(docids)
        start_date = data['form'].get('start_date', fields.Date.today())
        end_date = data['form'].get(
            'end_date', str(datetime.now() + relativedelta(
                months=+1, day=1, days=-1))[:10])
        tenant_id = data['form'].get('tenant_id')

        detail_res = self.with_context(data['form'].get(
            'used_context', {})).get_details(
            start_date, end_date, tenant_id)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.asset',
            'data': data['form'],
            'docs': docs,
            'time': time,
            'date_format': self.date_format,
            'get_details': detail_res,
        }
        docargs['data'].update({
            'end_date': docargs.get('data').get('end_date'),
            'start_date': docargs.get('data').get('start_date')})
        return docargs
