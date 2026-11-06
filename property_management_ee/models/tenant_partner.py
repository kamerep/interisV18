# See LICENSE file for full copyright and licensing details
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TenantPartner(models.Model):
    _name = "tenant.partner"
    _description = 'Tenant Partner'
    _inherits = {'res.partner': 'parent_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

    doc_name = fields.Char(string='Filename')
    id_attachment = fields.Binary(string='Identity Proof')
    tenancy_ids = fields.One2many(
        comodel_name='account.analytic.account',
        inverse_name='tenant_id',
        string='Tenancy Details',
        help='Tenancy Details')
    parent_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        index=True,
        ondelete='cascade')
    tenant_ids = fields.Many2many(
        comodel_name='tenant.partner',
        relation='agent_tenant_rel',
        column1='agent_id',
        column2='tenant_id',
        string='Tenant Details')
    tenant_user_type = fields.Selection(
        [('portal', 'Portal'), ('internal', 'Internal')],
        string='Tenant User Type',
        help="Portal: creates a portal user.\n"
             "Internal: creates an internal user.\n"
             "Leave empty: no user is created.")

    _USER_GROUP = {
        'portal': 'base.group_portal',
        'internal': 'base.group_user',
    }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.tenant_user_type:
                continue
            password = (
                rec.company_id.default_password
                if rec.company_id else '') or ''
            user_group_ref = self._USER_GROUP[rec.tenant_user_type]
            new_user = self.env['res.users'].create({
                'login': rec.email or rec.name,
                'name': rec.name,
                'password': password,
                'tenant_id': rec.id,
                'partner_id': rec.parent_id.id,
                'groups_id': [(6, 0, [self.env.ref(user_group_ref).id])],
            })
            extra_group = False
            if rec.customer_rank > 0:
                extra_group = self.env.ref(
                    'property_management_ee.group_property_user',
                    raise_if_not_found=False)
            if rec.agent:
                extra_group = self.env.ref(
                    'property_management_ee.group_property_agent',
                    raise_if_not_found=False)
            if extra_group:
                extra_group.write({'users': [(4, new_user.id)]})
        return records

    def write(self, vals):
        res = super().write(vals)
        new_user_type = vals.get('tenant_user_type')
        for rec in self:
            user_rec = self.env['res.users'].with_context(
                active_test=False).search(
                [('tenant_id', '=', rec.id)], limit=1)
            if rec.tenant_user_type and not user_rec:
                group_ref = self._USER_GROUP.get(rec.tenant_user_type)
                if group_ref:
                    self.env['res.users'].create({
                        'login': rec.email or rec.name,
                        'name': rec.name,
                        'partner_id': rec.parent_id.id,
                        'tenant_id': rec.id,
                        'groups_id': [(6, 0, [self.env.ref(group_ref).id])],
                    })
            elif user_rec and new_user_type in self._USER_GROUP:
                group_ref = self._USER_GROUP[new_user_type]
                user_rec.write({
                    'groups_id': [(6, 0, [self.env.ref(group_ref).id])]})
            elif user_rec and not rec.tenant_user_type:
                user_rec.action_archive()
            elif user_rec and rec.tenant_user_type:
                user_rec.action_unarchive()
        return res

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('tenant'):
            res['tenant'] = self._context['tenant']
        res['customer_rank'] = 1
        return res

    def unlink(self):
        for rec in self:
            active_tenancies = self.env['account.analytic.account'].search(
                [('tenant_id', '=', rec.id)])
            if active_tenancies:
                raise UserError(_(
                    'You cannot delete a tenant who has active tenancies.'))
            related_users = self.env['res.users'].search(
                [('partner_id', '=', rec.parent_id.id)])
            related_users.unlink()
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
