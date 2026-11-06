# See LICENSE file for full copyright and licensing details

from odoo import api, fields, models


class PropertyPerLocation(models.TransientModel):
    _name = 'property.per.location'
    _description = 'Property Per Location'

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State')

    def print_report(self):
        report = self.env.ref(
            'property_management_ee.action_report_property_per_location1')
        for data1 in self:
            data = data1.read([])[0]
            return report.report_action([], data=data)
