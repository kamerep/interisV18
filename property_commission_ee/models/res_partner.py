# See LICENSE file for full copyright and licensing details

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    commission_line = fields.One2many(
        comodel_name='account.analytic.account',
        inverse_name='agent',
        string='Commission')
    agent = fields.Boolean(
        string='Agent',
        help="Check this box if this contact is a Agent.")
