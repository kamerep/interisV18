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
        for partner in self:
            if 'tenant' in vals and tenant_group:
                cmd = (4 if partner.tenant else 3)
                if not partner.tenant and partner.user_ids.has_group(
                        'property_management_ee.group_property_user'):
                    partner.user_ids.write(
                        {'groups_id': [(3, tenant_group.id)]})
                elif partner.tenant:
                    partner.user_ids.write(
                        {'groups_id': [(4, tenant_group.id)]})
            if 'agent' in vals and agent_group:
                if not partner.agent and partner.user_ids.has_group(
                        'property_management_ee.group_property_agent'):
                    partner.user_ids.write(
                        {'groups_id': [(3, agent_group.id)]})
                elif partner.agent:
                    partner.user_ids.write(
                        {'groups_id': [(4, agent_group.id)]})
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
