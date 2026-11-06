# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api


class BookAvailableWiz(models.TransientModel):
    _name = 'book.available.wiz'
    _description = 'Book Available Wizard'

    
    def print_yes(self):
        """
        @param self: The object pointer
        """
        # edit_result is the property the button was clicked on (it may be
        # a sub-property row, whereas active_id is then the parent form)
        asset_rec = self.env['account.asset'].browse(
            self._context.get('edit_result') or self._context.get('active_id'))
        if asset_rec and asset_rec.state in ('book', 'normal', 'close', 'sold'):
            asset_rec.write({'state': 'draft', 'property_manager': False})
