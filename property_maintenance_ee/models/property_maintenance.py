# See LICENSE file for full copyright and licensing details

import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    property_id = fields.Many2one(
        comodel_name="account.asset",
        string="Property Name",
        help="Name of the property.")
    company_currency_id = fields.Many2one(
        related='company_id.currency_id',
        string='Company Currency',
        readonly=True,
        store=True)
    cost = fields.Monetary(
        string='Cost',
        default=0.0,
        currency_field='company_currency_id',
        help='Overall maintenance cost.')
    # V18 core already defines done = related('stage_id.done'); track the
    # "done" notification separately so it is sent exactly once.
    done_notified = fields.Boolean(string='Done Notified', copy=False)
    renters_fault = fields.Boolean(
        string="Renter's Fault",
        default=False,
        copy=True,
        help='True if the maintenance is due to tenant fault.')
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        copy=False,
        string='Invoice')
    date_invoice = fields.Date(
        related="invoice_id.invoice_date",
        store=True,
        string='Invoice Date')
    invoice_check = fields.Boolean(
        string='Already Created',
        copy=False,
        default=False)
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Maintenance Account',
        check_company=True,
        domain="[('deprecated', '=', False)]")
    city = fields.Char(related='property_id.city', string='City')
    street = fields.Char(related='property_id.street', string='Street')
    street2 = fields.Char(related='property_id.street2', string='Street2')
    township = fields.Char(related='property_id.township', string='Township')
    zip = fields.Char(
        related='property_id.zip',
        string='Zip',
        size=24,
        change_default=True)
    state_id = fields.Many2one(
        related='property_id.state_id',
        comodel_name='res.country.state',
        string='State',
        ondelete='restrict')
    country_id = fields.Many2one(
        related='property_id.country_id',
        comodel_name='res.country',
        string='Country',
        ondelete='restrict')
    tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Tenant')
    is_in_progress = fields.Boolean(string='In Progress', default=False)

    @api.constrains('request_date', 'schedule_date')
    def check_date_overlap(self):
        for maintenance in self:
            if (maintenance.request_date and maintenance.schedule_date
                    and maintenance.schedule_date.date() < maintenance.request_date):
                raise ValidationError(_(
                    'Schedule Date should be greater than Requested Date!'))
            if maintenance.cost < 0:
                raise ValidationError(_(
                    'Total Maintenance cost must be greater than zero.'))

    @api.model_create_multi
    def create(self, vals_list):
        requests = super().create(vals_list)
        for request in requests:
            if request.property_id and not request.tenant_id:
                tenant = self.env['account.analytic.account'].search([
                    ('property_id', '=', request.property_id.id),
                    ('resident_type', '=', 'tenant_tenancy'),
                    ('state', 'not in', ['close', 'cancelled']),
                ], limit=1).tenant_id
                if tenant:
                    request.tenant_id = tenant.id
        return requests

    def open_google_map(self):
        url = "http://maps.google.com/maps?oi=map&q="
        prop = self.property_id
        if prop:
            for val in [
                prop.name, prop.street, prop.street2, prop.township,
                prop.city,
                prop.state_id.name if prop.state_id else '',
                prop.country_id.name if prop.country_id else '',
            ]:
                if val:
                    url += re.sub(' +', '+', re.sub(r'[^\w]', ' ', val)) + '+'
            if prop.zip:
                url += prop.zip
        return {
            'name': _('Go to website'),
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'current',
            'url': url,
        }

    @api.onchange('property_id')
    def state_details_change(self):
        if self.property_id:
            self.tenant_id = self.env['account.analytic.account'].search([
                ('property_id', '=', self.property_id.id),
                ('resident_type', '=', 'tenant_tenancy'),
                ('state', 'not in', ['close', 'cancelled']),
            ], limit=1).tenant_id
            if self.property_id.maint_account_id:
                self.account_id = self.property_id.maint_account_id.id

    def write(self, vals):
        res = super().write(vals)
        if 'stage_id' not in vals:
            return res
        for rec in self:
            if rec.stage_id.is_in_progress and not rec.is_in_progress:
                rec.is_in_progress = True
                if rec.renters_fault:
                    template = self.env.ref(
                        'property_maintenance_ee'
                        '.mail_maintenance_tenant_inprogress_template',
                        raise_if_not_found=False)
                    if template and rec.tenant_id.email:
                        template.send_mail(
                            rec.id, force_send=True,
                            email_values={'email_to': rec.tenant_id.email})
                else:
                    template = self.env.ref(
                        'property_maintenance_ee'
                        '.mail_maintenance_manager_inprogress_template',
                        raise_if_not_found=False)
                    if template and rec.property_id.property_manager.email:
                        template.send_mail(
                            rec.id, force_send=True,
                            email_values={'email_to': rec.property_id.property_manager.email})
            elif not rec.stage_id.is_in_progress:
                rec.is_in_progress = False

            if not rec.stage_id.done:
                rec.done_notified = False
            elif not rec.done_notified:
                rec.done_notified = True
                if rec.renters_fault:
                    template = self.env.ref(
                        'property_maintenance_ee'
                        '.mail_maintenance_tenant_done_template',
                        raise_if_not_found=False)
                    if template and rec.tenant_id.email:
                        template.send_mail(
                            rec.id, force_send=True,
                            email_values={'email_to': rec.tenant_id.email})
                else:
                    template = self.env.ref(
                        'property_maintenance_ee'
                        '.mail_maintenance_manager_done_template',
                        raise_if_not_found=False)
                    if template and rec.property_id.property_manager.email:
                        template.send_mail(
                            rec.id, force_send=True,
                            email_values={'email_to': rec.property_id.property_manager.email})
        return res

    def create_invoice(self):
        for maintenance in self:
            if not maintenance.property_id:
                raise ValidationError(_("Please Select Property"))
            inv_line = (0, 0, {
                'name': 'Maintenance For ' + (maintenance.name or ''),
                'quantity': 1,
                'account_id': maintenance.account_id.id or False,
                'price_unit': maintenance.cost or 0.00,
            })
            tenancies = self.env['account.analytic.account'].search([
                ('property_id', '=', maintenance.property_id.id),
                ('state', '!=', 'close'),
            ])
            if not tenancies:
                partner_id = (
                    maintenance.property_id.company_id.partner_id.id
                    or False)
            elif maintenance.renters_fault:
                partner_id = (
                    tenancies[:1].tenant_id.parent_id.id or False)
            else:
                partner_id = (
                    maintenance.property_id.property_manager.id or False)

            inv_values = {
                'invoice_origin': 'Maintenance Request',
                'move_type': 'out_invoice',
                'partner_id': partner_id,
                'property_id': maintenance.property_id.id,
                'invoice_line_ids': [inv_line],
                'invoice_date': maintenance.request_date or False,
            }
            move_id = self.env['account.move'].create(inv_values)
            maintenance.write({
                'invoice_check': True,
                'invoice_id': move_id.id,
            })

    def open_invoice(self):
        self.ensure_one()
        wiz_form_id = self.env.ref('account.view_move_form').id
        return {
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


class MaintenanceStage(models.Model):
    _inherit = 'maintenance.stage'

    is_in_progress = fields.Boolean(string='In Progress', default=False)
