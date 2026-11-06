# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    tenant = fields.Boolean(
        string='Tenant',
        help="Check this box if this contact is a tenant.")
    occupation = fields.Char(string='Occupation', size=20)
    agent = fields.Boolean(
        string='Agent',
        help="Check this box if this contact is an Agent.")

    def write(self, vals):
        res = super().write(vals)
        tenant_group = self.env.ref(
            'property_management_ee.group_property_user',
            raise_if_not_found=False)
        agent_group = self.env.ref(
            'property_management_ee.group_property_agent',
            raise_if_not_found=False)
        # Keep the portal/internal users of tenants and agents in the
        # matching property groups. Removing a group a user does not have is
        # a no-op, so no has_group() check is needed (it requires a single
        # user record in V18).
        for flag, group in (('tenant', tenant_group), ('agent', agent_group)):
            if flag not in vals or not group:
                continue
            for partner in self.filtered('user_ids'):
                cmd = 4 if partner[flag] else 3
                partner.user_ids.write({'groups_id': [(cmd, group.id)]})
        return res


class ResUsers(models.Model):
    _inherit = "res.users"

    tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Related Tenant')
    tenant_ids = fields.Many2many(
        comodel_name='tenant.partner',
        relation='rel_ten_user',
        column1='user_id',
        column2='tenant_id',
        string='All Tenants')


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_password = fields.Char(string='Default Password')
