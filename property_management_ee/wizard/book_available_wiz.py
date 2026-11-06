# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api


class BookAvailableWiz(models.TransientModel):
    _name = 'book.available.wiz'
    _description = 'Book Available Wizard'

    
    def print_yes(self):
        """
        @param self: The object pointer
        """
        asset_rec = self.env['account.asset'].browse(
            self._context.get('active_id'))
        if asset_rec and asset_rec.state in ('book', 'normal', 'close', 'sold'):
            asset_rec.write({'state': 'draft', 'property_manager': False})
