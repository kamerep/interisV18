# See LICENSE file for full copyright and licensing details

import datetime
from odoo import api, models


class TenantWizardMail(models.TransientModel):
    _name = "tenant.wizard.mail"
    _description = "Mass Mailing for Rent Reminder"

    def mass_mail_send(self):
        """Send rent payment reminder emails to tenants with overdue schedules."""
        today = datetime.date.today()
        schedules = self.env['tenancy.rent.schedule'].search([
            ('start_date', '<', today),
            ('paid', '=', False),
        ])
        for schedule in schedules:
            tenant = schedule.rel_tenant_id
            if not (tenant and tenant.parent_id and tenant.parent_id.email):
                continue
            self.env['mail.mail'].create({
                'subject': 'Reminder: Rent Payment Due',
                'email_to': tenant.parent_id.email,
                'body_html': (
                    '<p>Dear %s,</p>'
                    '<p>Your rent of <strong>%s %.2f</strong> due on %s '
                    'is unpaid. Please settle at your earliest convenience.'
                    '</p><p>Regards,<br/>Property Management</p>'
                ) % (
                    tenant.name,
                    schedule.currency_id.symbol or '',
                    schedule.amount,
                    schedule.start_date,
                ),
            }).send()
        return {'type': 'ir.actions.act_window_close'}
