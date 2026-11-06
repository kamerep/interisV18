# See LICENSE file for full copyright and licensing details

from odoo import fields, models, tools


class PropertyFinanceReports(models.Model):
    _name = "property.finance.report"
    _description = 'Property Finance Report'
    _auto = False

    type_id = fields.Many2one('property.type', string='Property Type')
    date = fields.Date('Purchase Date')
    parent_id = fields.Many2one('account.asset', string='Parent Property')
    name = fields.Char("Property")
    purchase_price = fields.Float('Purchase Price')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'property_finance_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW property_finance_report AS
            SELECT id, name, type_id, purchase_price,
                   property_parent_id AS parent_id, acquisition_date AS date
            FROM account_asset
            WHERE is_property IS TRUE
        """)
