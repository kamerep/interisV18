# See LICENSE file for full copyright and licensing details
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')
    is_property = fields.Boolean(
        string='Is Property')


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_property = fields.Boolean(
        string='Is Property',
        default=False)
