# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TenantWizardMail(models.TransientModel):
    """Send rent reminders for selected (or all overdue) rent schedules."""
    _name = "tenant.wizard.mail"
    _description = "Rent Reminder Mailing"

    schedule_ids = fields.Many2many(
        comodel_name='tenancy.rent.schedule',
        string='Rent Schedules',
        help="Rent lines to remind. Leave empty to remind every unpaid, "
             "overdue rent line of running tenancies.")
    template_id = fields.Many2one(
        comodel_name='mail.template',
        string='Email Template',
        domain="[('model', '=', 'tenancy.rent.schedule')]",
        default=lambda self: self.env.ref(
            'property_management_ee.mail_tenant_rent_overdue',
            raise_if_not_found=False))
    skipped_count = fields.Integer(readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if (self.env.context.get('active_model') == 'tenancy.rent.schedule'
                and self.env.context.get('active_ids')):
            res['schedule_ids'] = [
                (6, 0, self.env.context['active_ids'])]
        return res

    def _get_schedules(self):
        self.ensure_one()
        schedules = self.schedule_ids
        if not schedules:
            schedules = self.env['tenancy.rent.schedule'].search([
                ('start_date', '<', fields.Date.context_today(self)),
                ('paid', '=', False),
                ('tenancy_id.state', '=', 'open'),
            ])
        return schedules.filtered(lambda s: not s.paid)

    def mass_mail_send(self):
        self.ensure_one()
        if not self.template_id:
            raise UserError(_('Please select an email template.'))
        sent = skipped = 0
        for schedule in self._get_schedules():
            tenant = schedule.rel_tenant_id or schedule.tenancy_id.tenant_id
            if not tenant.email:
                skipped += 1
                continue
            email_values = {'email_to': tenant.email}
            manager = schedule.tenancy_id.property_id.property_manager
            if manager.email:
                email_values['email_from'] = manager.email
            self.template_id.send_mail(
                schedule.id, email_values=email_values)
            sent += 1
        message = _('%(sent)s reminder(s) queued.', sent=sent)
        if skipped:
            message += ' ' + _(
                '%(skipped)s skipped: tenant has no email address.',
                skipped=skipped)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Rent reminders'),
                'message': message,
                'type': 'success' if sent else 'warning',
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
