# See LICENSE file for full copyright and licensing details

from odoo import fields, models, tools


class OperationalCostsReport(models.Model):
    _name = "operational.costs.report"
    _description = 'Operational Cost Report'
    _auto = False

    active = fields.Boolean('Active')
    parent_id = fields.Many2one(
        'account.asset', string='Parent Property')
    type_id = fields.Many2one('property.type', string='Property Type')
    acquisition_date = fields.Date('Purchase Date')
    operational_costs = fields.Float("Operational costs(%)")
    name = fields.Char('Asset Name')

    def init(self):
        tools.drop_view_if_exists(self._cr, 'operational_costs_report')
        self._cr.execute(
            """CREATE or REPLACE VIEW operational_costs_report as
            SELECT id,name,active,parent_id,type_id,operational_costs,
            acquisition_date FROM account_asset""")
