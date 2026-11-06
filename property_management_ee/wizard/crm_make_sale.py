# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class CrmMakeSale(models.TransientModel):
    _name = "crm.make.sale.wiz"
    _description = "Make Sale from Opportunity"

    @api.model
    def _selectPartner(self):
        active_id = self._context.get('active_id')
        if not active_id:
            return False
        lead = self.env['crm.lead'].browse(active_id)
        return lead.partner_id.id if lead.partner_id else False

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
        default=_selectPartner)
    close = fields.Boolean(
        string='Mark Won',
        default=False,
        help='Close the opportunity after creating the sales order.')

    def makeOrder(self):
        context = dict(self._context or {})
        context.pop('default_state', False)
        active_ids = context.get('active_ids', [])
        lead_obj = self.env['crm.lead']
        order_obj = self.env['sale.order']
        new_ids = []
        case = None

        for make in self:
            partner = make.partner_id
            partner_addr = partner.address_get(
                ['default', 'invoice', 'delivery', 'contact'])
            if False in partner_addr.values():
                raise UserError(_(
                    'No address(es) defined for this customer.'))
            pricelist = partner.property_product_pricelist.id
            fpos = (partner.property_account_position_id.id
                    if partner.property_account_position_id else False)
            payment_term = (partner.property_payment_term_id.id
                            if partner.property_payment_term_id else False)

            for case in lead_obj.browse(active_ids):
                if case.property_id.state == 'sold':
                    raise ValidationError(_('This property is already sold!'))
                vals = {
                    'origin': _('Opportunity: %s') % str(case.id),
                    'team_id': case.team_id.id if case.team_id else False,
                    'tag_ids': [(6, 0, case.tag_ids.ids)],
                    'partner_id': partner.id,
                    'pricelist_id': pricelist,
                    'partner_invoice_id': partner_addr['invoice'],
                    'partner_shipping_id': partner_addr['delivery'],
                    'date_order': fields.Datetime.now(),
                    'fiscal_position_id': fpos,
                    'payment_term_id': payment_term,
                    'is_property': True,
                    'opportunity_id': case.id,
                    'user_id': (
                        partner.user_id.id if partner.user_id
                        else self.env.uid),
                }
                case.property_id.write({'state': 'sold'})
                new_rec = order_obj.create(vals)
                new_ids.append(new_rec.id)
                case.message_post(body=_(
                    "Opportunity converted to quotation <em>%s</em>."
                ) % new_rec.name)
            if make.close and case:
                case.action_set_won()

        if not new_ids:
            return {'type': 'ir.actions.act_window_close'}
        action = {
            'view_mode': 'form' if len(new_ids) == 1 else 'list,form',
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'name': _('Quotations'),
            'domain': [('id', 'in', new_ids)],
        }
        if len(new_ids) == 1:
            action['res_id'] = new_ids[0]
        return action
