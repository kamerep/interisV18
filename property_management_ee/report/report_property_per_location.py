# See LICENSE file for full copyright and licensing details
from odoo import api, models


class property_per_location_report(models.AbstractModel):
    _name = "report.property_management_ee.report_property_per_location1"
    _description = 'Property per Location Report'

    def property_location(self, data, state):
        property_obj = self.env['account.asset']

        if not data:
            if state and state.id:
                domain = [('state_id', '=', state.id)]
            else:
                domain = []
        elif data:
            domain = [('state_id', '=', data['state_id'][0])]

        property_ids = property_obj.search(domain)
        property_list = []
        sub_property_list = []
        for property_data in property_obj.browse(property_ids.ids):
            if property_data.child_ids:
                for sub in property_data.child_ids:
                    sub_property_list.append(sub.id)
                    property_dict = {
                        'name': property_data.name,
                        'child_ids': sub.name,
                        'city': sub.city,
                        'state_id': property_data.state_id.name,
                        'township': sub.township
                    }
                    property_list.append(property_dict)
            else:
                if property_data.id not in sub_property_list:
                    property_dict = {
                        'name': property_data.name,
                        'child_ids': False,
                        'city': property_data.city,
                        'state_id': property_data.state_id.name,
                        'township': property_data.township
                    }
                    property_list.append(property_dict)
        return property_list

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.asset'].browse(docids)
        state_id = data.get('state_id')[0]
        detail_res = self.with_context(
            data.get('used_context', {})).property_location(data, state_id)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'account.asset',
            'data': data,
            'docs': docs,
            'property_location': detail_res,
        }
        return docargs
