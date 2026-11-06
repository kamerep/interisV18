# See LICENSE file for full copyright and licensing details

from markupsafe import Markup

from odoo import _, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    facing = fields.Char(string='Facing')
    furnished = fields.Selection(
        [('none', 'None'),
         ('semi_furnished', 'Semi Furnished'),
         ('full_furnished', 'Full Furnished')],
        string='Furnishing',
        default='none',
        help='Required furnishing status.')
    demand = fields.Boolean(string='Is Demand')
    max_price = fields.Float(string='Max Price')
    min_price = fields.Float(string='Min. Price')
    is_buy = fields.Boolean(string='Is Buy', default=False)
    is_rent = fields.Boolean(string='Is Rent', default=False)
    max_bedroom = fields.Integer(string='Max Bedroom Required')
    min_bedroom = fields.Integer(string='Min. Bedroom Required')
    max_bathroom = fields.Integer(string='Max Bathroom Required')
    min_bathroom = fields.Integer(string='Min. Bathroom Required')
    type_id = fields.Many2one(
        comodel_name='property.type',
        string='Property Type',
        help='Property Type')
    email_send = fields.Boolean(
        string='Email Sent',
        help="Checked when email is sent")
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')

    def _prepare_customer_values(self, partner_name, is_company=False,
                                 parent_id=False):
        """Flag partners created from rent leads as tenants.

        Core CRM expects a dict of res.partner values here (it is also used
        by chatter suggestions and mail templates), so no record may be
        created in this method.
        """
        vals = super()._prepare_customer_values(
            partner_name, is_company=is_company, parent_id=parent_id)
        if self.is_rent:
            vals['tenant'] = True
        return vals

    def _get_or_create_tenant(self):
        """Return the tenant.partner linked to the lead customer."""
        self.ensure_one()
        Tenant = self.env['tenant.partner']
        if not self.partner_id:
            self._handle_partner_assignment(create_missing=True)
        partner = self.partner_id
        if not partner:
            return Tenant
        tenant = Tenant.search([('parent_id', '=', partner.id)], limit=1)
        if not tenant:
            tenant = Tenant.create({'parent_id': partner.id})
        if not partner.tenant:
            partner.tenant = True
        return tenant


class CrmMakeContract(models.TransientModel):
    _name = "crm.make.contract"
    _description = "Make Contract from CRM Lead"

    date = fields.Date(string='End Date')
    date_start = fields.Date(
        string='Start Date',
        default=fields.Date.context_today)
    close = fields.Boolean(
        string='Mark Won',
        default=False,
        help='Close the opportunity after creating the contract.')

    def makecontract(self):
        context = dict(self._context or {})
        context.pop('default_state', False)
        active_ids = context.get('active_ids', [])
        lead_obj = self.env['crm.lead']
        new_ids = []
        view_id = self.env.ref(
            'property_management_ee.property_analytic_view_form').id

        for make in self:
            case = None
            for case in lead_obj.browse(active_ids):
                tenant = case._get_or_create_tenant()
                vals = {
                    'name': case.name,
                    'partner_id': case.partner_id.id or False,
                    'property_id': case.property_id.id or False,
                    'tenant_id': tenant.id or False,
                    'company_id': self.env.company.id,
                    'date_start': make.date_start or False,
                    'date': make.date or False,
                    'is_property': True,
                    'rent': case.property_id.ground_rent or 0.0,
                    'resident_type': 'tenant_tenancy',
                }
                new_rec = self.env['account.analytic.account'].create(vals)
                new_ids.append(new_rec.id)
                case.message_post(body=Markup(_(
                    "Opportunity converted to Contract <em>%s</em>."
                )) % new_rec.name)
            if make.close and case:
                case.action_set_won()

        if not new_ids:
            return {'type': 'ir.actions.act_window_close'}

        action = {
            'view_mode': 'list,form',
            'res_model': 'account.analytic.account',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'name': _('Contracts'),
            'domain': [('id', 'in', new_ids)],
        }
        if len(new_ids) == 1:
            action.update({'view_mode': 'form', 'res_id': new_ids[0]})
        return action
