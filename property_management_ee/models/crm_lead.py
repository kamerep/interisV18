# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models, tools


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
        if self.is_rent:
            email_split = tools.email_split(self.email_from)
            vals = {
                'name': partner_name,
                'user_id': (
                    self.env.context.get('default_user_id')
                    or self.user_id.id),
                'comment': self.description,
                'team_id': self.team_id.id,
                'parent_id': parent_id,
                'phone': self.phone,
                'mobile': self.mobile,
                'email': email_split[0] if email_split else False,
                'title': self.title.id,
                'function': self.function,
                'street': self.street,
                'street2': self.street2,
                'zip': self.zip,
                'city': self.city,
                'country_id': self.country_id.id,
                'state_id': self.state_id.id,
                'website': self.website,
                'is_company': is_company,
                'type': 'contact',
                'tenant': True,
            }
            tenant = self.env['tenant.partner'].create(vals)
            tenant.parent_id.write({'tenant': True})
            return tenant
        return super()._prepare_customer_values(
            partner_name, is_company=is_company, parent_id=parent_id)


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
                tenant = case._prepare_customer_values(
                    case.contact_name or case.partner_name or '',
                    is_company=False)
                if hasattr(tenant, 'parent_id'):
                    case.partner_id = tenant.parent_id.id
                vals = {
                    'name': case.name,
                    'partner_id': (
                        tenant.parent_id.id
                        if hasattr(tenant, 'parent_id')
                        else (tenant.id if tenant else False)),
                    'property_id': case.property_id.id or False,
                    'tenant_id': tenant.id if hasattr(tenant, 'parent_id') else False,
                    'company_id': self.env.company.id,
                    'date_start': make.date_start or False,
                    'date': make.date or False,
                    'is_property': True,
                    'rent': case.property_id.ground_rent or 0.0,
                    'resident_type': 'tenant_tenancy',
                }
                new_rec = self.env['account.analytic.account'].create(vals)
                case.write({
                    'description': (
                        'account.analytic.account,%s' % new_rec.id)})
                new_ids.append(new_rec.id)
                case.message_post(body=_(
                    "Opportunity converted to Contract <em>%s</em>."
                ) % new_rec.name)
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
