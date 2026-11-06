# See LICENSE file for full copyright and licensing details

from odoo import fields, models, tools


class OccupancyPerformanceReport(models.Model):
    _name = "occupancy.performance.report"
    _description = 'Occupancy Performance Report'
    _auto = False

    active = fields.Boolean('Active')
    parent_id = fields.Many2one('account.asset', 'Parent Property')
    type_id = fields.Many2one('property.type', 'Property Type')
    acquisition_date = fields.Date('Purchase Date')
    parent_id = fields.Many2one('account.asset', 'Parent Property')
    name = fields.Char("Property Name")
    occupancy_rates = fields.Float('Occupancy Rates')

    def init(self):
        tools.drop_view_if_exists(self._cr, 'occupancy_performance_report')
        self._cr.execute(
            """CREATE or REPLACE VIEW occupancy_performance_report as
            SELECT id,name,type_id,active,parent_id,occupancy_rates,
            acquisition_date FROM account_asset""")
