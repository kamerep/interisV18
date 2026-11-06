# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LandlordPartner(models.Model):
    _name = "landlord.partner"
    _description = 'Landlord Partner'
    _inherits = {'res.partner': 'parent_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

    doc_name = fields.Char(string='Filename')
    id_attachment = fields.Binary(string='Identity Proof')
    owner_tenancy_ids = fields.One2many(
        comodel_name='account.analytic.account',
        inverse_name='property_owner_id',
        string='Landlord Tenancies',
        help='Landlord Tenancy Details')
    parent_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        index=True,
        ondelete='cascade')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if self._context.get('is_owner'):
            for rec in records:
                password = (
                    rec.company_id.default_password
                    if rec.company_id else '') or ''
                new_user = self.env['res.users'].create({
                    'login': rec.email or rec.name,
                    'name': rec.name,
                    'password': password,
                    'partner_id': rec.parent_id.id,
                })
                group = False
                if rec.customer_rank > 0:
                    group = self.env.ref(
                        'property_management_ee.group_property_user',
                        raise_if_not_found=False)
                if getattr(rec, 'agent', False):
                    group = self.env.ref(
                        'property_management_ee.group_property_agent',
                        raise_if_not_found=False)
                owner_group = self.env.ref(
                    'property_management_ee.group_property_owner',
                    raise_if_not_found=False)
                if owner_group:
                    group = owner_group
                if group:
                    group.write({'users': [(4, new_user.id)]})
        return records

    def unlink(self):
        for rec in self:
            active_tenancies = self.env['account.analytic.account'].search(
                [('property_owner_id', '=', rec.id)])
            if active_tenancies:
                raise UserError(_(
                    'You cannot delete a landlord who has active tenancies.'))
        return super().unlink()

    def _message_get_suggested_recipients(self):
        recipients = super()._message_get_suggested_recipients()
        for partner in self:
            if partner.parent_id:
                partner._message_add_suggested_recipient(
                    recipients,
                    partner=partner.parent_id,
                    reason=_('Partner Profile'))
        return recipients


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_owner = fields.Boolean(
        string='Is an Owner',
        help="Check this box if this contact is a landlord (owner).")
