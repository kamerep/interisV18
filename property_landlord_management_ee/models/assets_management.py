# See LICENSE file for full copyright and licensing details
from odoo import fields, models


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset'

    property_owner = fields.Many2one(
        comodel_name='landlord.partner',
        string='Property Owner')
