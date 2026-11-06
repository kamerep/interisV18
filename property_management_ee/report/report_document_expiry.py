# See LICENSE file for full copyright and licensing details
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models

DEFAULT_FACTURX_DATE_FORMAT = '%Y-%m-%d'


class document_expiry(models.AbstractModel):
    _name = 'report.property_management_ee.report_document_expiry'
    _description = 'Document Expiry Report'

    def _fmt_date(self, value):
        """Format a date with the user's language date format."""
        if not value:
            return ''
        lang = self.env['res.lang']._lang_get(self.env.user.lang)
        return value.strftime(lang.date_format if lang else '%Y-%m-%d')

    def get_details(self, start_date, end_date):
        data_1 = []
        certificate_obj = self.env["property.attachment"]
        certificate_ids = certificate_obj.search(
            [('expiry_date', '>=', start_date),
             ('expiry_date', '<=', end_date)])
        for data in certificate_ids:
            expiry_date = self._fmt_date(data.expiry_date)
            property_str = data.property_id.name or ''
            data_1.append({
                'name': data.name,
                'property_id': property_str,
                'expiry_date': expiry_date,
            })
        return data_1

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.asset'].browse(docids)
        start_date_obj = datetime.strptime(
            data['form'].get('start_date'), '%Y-%m-%d')
        start_date_report = start_date_obj.strftime('%m-%d-%Y')
        end_date_obj = datetime.strptime(
            data['form'].get('end_date'), '%Y-%m-%d')
        end_date_report = end_date_obj.strftime('%m-%d-%Y')
        start_date_report = start_date_obj.strftime('%m-%d-%Y')
        user_lang = self.env.user.lang
        lang = self.env['res.lang'].search(
            [('code', '=', user_lang)])
        start_date_report = start_date_obj.strftime(lang.date_format)
        end_date_obj = datetime.strptime(
            data['form'].get('end_date'), '%Y-%m-%d')
        end_date_report = end_date_obj.strftime('%m-%d-%Y')
        end_date_report = end_date_obj.strftime(lang.date_format)
        start_date = data['form'].get('start_date', fields.Date.today())
        end_date = data['form'].get(
            'end_date', str(datetime.now() + relativedelta(
                months=+1, day=1, days=-1))[:10])
        detail_res = self.with_context(
            data['form'].get('used_context', {})).get_details(
                start_date, end_date)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.asset',
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_details': detail_res,
        }
        docargs['data'].update({
            'end_date': end_date_report,
            'start_date': start_date_report})
        return docargs
