# See LICENSE file for full copyright and licensing details

from odoo import models, fields, tools


class InvestmentAnalysisReport(models.Model):
    _name = "investment.analysis.report"
    _description = 'Investment Analysis Report'
    _auto = False

    name = fields.Char('Property Name')
    active = fields.Boolean('Active')
    parent_id = fields.Many2one('account.asset', string='Parent Property')
    type_id = fields.Many2one('property.type', string='Property Type')
    acquisition_date = fields.Date('Purchase Date')
    purchase_price = fields.Float('Purchase Price')
    roi = fields.Float('ROI')
    return_period = fields.Float('Return Period')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'investment_analysis_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW investment_analysis_report AS
            SELECT id, name, active, type_id,
                   property_parent_id AS parent_id,
                   purchase_price, acquisition_date, roi, return_period
            FROM account_asset
            WHERE is_property IS TRUE
        """)
