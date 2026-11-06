# See LICENSE file for full copyright and licensing details

from odoo import models, fields, tools


class GfaAnalysisReport(models.Model):
    _name = "gfa.analysis.report"
    _description = 'GFA Analysis Report'
    _auto = False

    name = fields.Char('Property Name')
    active = fields.Boolean('Active')
    parent_id = fields.Many2one(
        'account.asset', string='Parent Property')
    type_id = fields.Many2one('property.type', string='Property Type')
    gfa_feet = fields.Float('GFA(Sqft)')
    date = fields.Date('Purchase Date')

    def init(self):
        tools.drop_view_if_exists(self._cr, 'gfa_analysis_report')
        self._cr.execute(
            """CREATE or REPLACE VIEW gfa_analysis_report as
            SELECT id,name,active,parent_id,type_id,gfa_feet
            FROM account_asset """)
