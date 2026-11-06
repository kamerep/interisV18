# See LICENSE file for full copyright and licensing details

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    _PAYMENT_DONE_STATES = ('in_process', 'paid')

    @api.depends('resident_type',
                 'acc_pay_dep_rec_id', 'acc_pay_dep_rec_id.state',
                 'acc_pay_dep_ret_id', 'acc_pay_dep_ret_id.state')
    def _compute_payment_type(self):
        """Landlord tenancies: the deposit is paid out to the owner."""
        super()._compute_payment_type()
        for tenancy in self.filtered(
                lambda t: t.resident_type == 'landlord_partner'):
            payment = tenancy.acc_pay_dep_ret_id
            tenancy.deposit_received = bool(
                payment and payment.payment_type == 'outbound'
                and payment.state in self._PAYMENT_DONE_STATES)

    @api.depends('resident_type', 'invoice_id', 'invoice_id.payment_state',
                 'acc_pay_dep_rec_id', 'acc_pay_dep_rec_id.state')
    def compute_amount_return(self):
        """Landlord tenancies: the deposit comes back from the owner."""
        super().compute_amount_return()
        for tenancy in self.filtered(
                lambda t: t.resident_type == 'landlord_partner'):
            payment = tenancy.acc_pay_dep_rec_id
            tenancy.deposit_return = bool(
                payment and payment.payment_type == 'inbound'
                and payment.state in self._PAYMENT_DONE_STATES)

    property_owner_id = fields.Many2one(
        comodel_name='landlord.partner',
        string='Owner',
        help="Owner of property.")
    landlord_rent = fields.Monetary(
        string='Landlord Rent',
        currency_field='currency_id')
    resident_type = fields.Selection(
        selection_add=[('landlord_partner', 'Landlord Partner')],
        ondelete={'landlord_partner': 'set null'})

    @api.onchange('property_id')
    def _onchange_property(self):
        if self.property_id:
            self.property_owner_id = self.property_id.property_owner.id

    def create_rent_schedule_landlord(self):
        rent_obj = self.env['tenancy.rent.schedule']
        for tenancy_rec in self:
            amount = tenancy_rec.landlord_rent
            if not (tenancy_rec.date_start and tenancy_rec.date
                    and tenancy_rec.rent_type_id):
                raise ValidationError(_(
                    'Please set the Start Date, Expiration Date and Rent '
                    'Type before creating the rent schedule.'))
            if tenancy_rec.date < tenancy_rec.date_start:
                raise ValidationError(_(
                    'End date must be greater than start date.'))
            if tenancy_rec.rent_type_id.renttype == 'Weekly':
                d1 = tenancy_rec.date_start
                d2 = tenancy_rec.date
                interval = int(tenancy_rec.rent_type_id.name)
                if d2 < d1:
                    raise ValidationError(_(
                        'End date must be greater than start date.'))
                wek_diff = d2 - d1
                wek_tot1 = wek_diff.days // (interval * 7)
                wek_tot = wek_diff.days % (interval * 7)
                if wek_diff.days == 0:
                    wek_tot = 1
                for _i in range(wek_tot1):
                    rent_obj.create({
                        'start_date': d1,
                        'amount': amount * interval or 0.0,
                        'property_id': tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id,
                    })
                    d1 = d1 + relativedelta(days=(7 * interval))
                if wek_tot > 0:
                    one_day_rent = amount / 7 if amount else 0.0
                    rent_obj.create({
                        'start_date': d1,
                        'amount': one_day_rent * wek_tot or 0.0,
                        'property_id': tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id,
                    })
            else:
                if tenancy_rec.rent_type_id.renttype == 'Monthly':
                    interval = int(tenancy_rec.rent_type_id.name)
                else:
                    interval = int(tenancy_rec.rent_type_id.name) * 12
                d1 = tenancy_rec.date_start
                d2 = tenancy_rec.date
                diff = abs(
                    (d1.year - d2.year) * 12 + (d1.month - d2.month))
                tot_rec = diff // interval
                tot_rec2 = diff % interval
                if abs(d1.month - d2.month) >= 0 and d1.day < d2.day:
                    tot_rec2 += 1
                if diff == 0:
                    tot_rec2 = 1
                for _i in range(tot_rec):
                    rent_obj.create({
                        'start_date': d1,
                        'amount': amount * interval or 0.0,
                        'property_id': tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id,
                    })
                    d1 = d1 + relativedelta(months=interval)
                if tot_rec2 > 0:
                    rent_obj.create({
                        'start_date': d1,
                        'amount': amount * tot_rec2 or 0.0,
                        'property_id': tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id,
                    })
        return self.write({'rent_entry_chck': True})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if self._context.get('is_landlord_rent'):
                rec.code = (
                    self.env['ir.sequence'].next_by_code('landlord.rent')
                    or '/')
                if rec.property_id and not rec.property_id.property_owner:
                    rec.property_id.write(
                        {'property_owner': rec.property_owner_id.id})
        return records

    def unlink(self):
        if self._context.get('is_landlord_rent'):
            for tenancy_rec in self:
                tenancy_rec.line_ids.unlink()
                rent_ids = self.env['tenancy.rent.schedule'].search(
                    [('tenancy_id', '=', tenancy_rec.id)])
                if any(r.move_check for r in rent_ids):
                    raise ValidationError(_(
                        'You cannot delete a Tenancy record with posted '
                        'Rent Schedule entries.'))
                rent_ids.unlink()
        return super().unlink()

    def landlord_button_start(self):
        if self._context.get('is_landlord_rent'):
            self.write({'state': 'open', 'rent_entry_chck': False})

    def landlord_button_deposite_pay(self):
        acc_pay_form = self.env.ref('account.view_account_payment_form')
        journal = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        context = dict(self._context, close_after_process=True)
        payment_id = False
        for tenancy_rec in self:
            # outbound deposit payments are linked as acc_pay_dep_ret_id
            # by account.payment.create()
            if tenancy_rec.acc_pay_dep_ret_id:
                return {
                    'view_id': acc_pay_form.id,
                    'view_mode': 'form',
                    'res_model': 'account.payment',
                    'res_id': tenancy_rec.acc_pay_dep_ret_id.id,
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'context': context,
                }
            if tenancy_rec.deposit == 0.00:
                raise ValidationError(_('Please Enter Deposit amount.'))
            if tenancy_rec.deposit < 0.00:
                raise ValidationError(
                    _('The deposit amount must be strictly positive.'))
            payment_method_line = journal.outbound_payment_method_line_ids.filtered(
                lambda l: l.code == 'manual')[:1]
            vals = {
                'partner_id': tenancy_rec.property_owner_id.parent_id.id,
                'partner_type': 'supplier',
                'journal_id': journal.id,
                'payment_type': 'outbound',
                'memo': _('Deposit Payment'),
                'tenancy_id': tenancy_rec.id,
                'amount': tenancy_rec.deposit,
                'property_id': tenancy_rec.property_id.id,
            }
            if payment_method_line:
                vals['payment_method_line_id'] = payment_method_line.id
            payment_id = self.env['account.payment'].create(vals)
        return {
            'view_id': acc_pay_form.id,
            'view_mode': 'form',
            'res_id': payment_id and payment_id.id,
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
        }

    def landlord_button_deposite_received(self):
        acc_pay_form = self.env.ref('account.view_account_payment_form')
        journal = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        payment_id = False
        for tenancy_rec in self:
            if tenancy_rec.acc_pay_dep_rec_id:
                return {
                    'view_id': acc_pay_form.id,
                    'view_mode': 'form',
                    'res_model': 'account.payment',
                    'res_id': tenancy_rec.acc_pay_dep_rec_id.id,
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                }
            if tenancy_rec.deposit == 0.00:
                raise ValidationError(_('Please Enter Deposit amount.'))
            if tenancy_rec.deposit < 0.00:
                raise ValidationError(
                    _('The deposit amount must be strictly positive.'))
            payment_method_line = journal.inbound_payment_method_line_ids.filtered(
                lambda l: l.code == 'manual')[:1]
            vals = {
                'partner_id': tenancy_rec.property_owner_id.parent_id.id,
                'partner_type': 'customer',
                'journal_id': journal.id,
                'payment_type': 'inbound',
                'memo': _('Deposit Received'),
                'tenancy_id': tenancy_rec.id,
                'amount': tenancy_rec.deposit,
                'property_id': tenancy_rec.property_id.id,
            }
            if payment_method_line:
                vals['payment_method_line_id'] = payment_method_line.id
            payment_id = self.env['account.payment'].create(vals)
        return {
            'view_id': acc_pay_form.id,
            'view_mode': 'form',
            'res_id': payment_id and payment_id.id,
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'close_after_process': True},
        }

    def landlord_button_close(self):
        return self.write({'state': 'close'})

    def landlord_button_cancel_tenancy(self):
        for record in self:
            record.write({'state': 'cancelled', 'tenancy_cancelled': True})
            self.env['tenancy.rent.schedule'].search([
                ('tenancy_id', '=', record.id),
                ('paid', '=', False),
                ('move_check', '=', False),
            ]).write({'is_readonly': True})
        return True


class TenancyRentSchedule(models.Model):
    _inherit = "tenancy.rent.schedule"
    _rec_name = "tenancy_id"

    def create_landlord_invoice(self):
        self.ensure_one()
        if self.tenancy_id.resident_type != 'landlord_partner':
            return
        journal = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1)
        property_id = self.tenancy_id.property_id
        analytic_dist = (
            {str(self.tenancy_id.id): 100} if self.tenancy_id else {})
        inv_line = {
            'name': 'Rent Cost for %s' % self.tenancy_id.name,
            'quantity': 1,
            'price_unit': self.amount or 0.00,
            'account_id': (
                property_id.account_depreciation_expense_id.id or False),
            'analytic_distribution': analytic_dist,
        }
        invo_values = {
            'partner_id': (
                self.tenancy_id.property_owner_id.parent_id.id or False),
            'move_type': 'in_invoice',
            'invoice_line_ids': [(0, 0, inv_line)],
            'property_id': property_id.id or False,
            'invoice_date': self.start_date or False,
            'new_tenancy_id': self.tenancy_id.id,
            'journal_id': journal.id or False,
        }
        acc_id = self.env['account.move'].create(invo_values)
        self.write({'invoice_id': acc_id.id, 'is_invoiced': True})
        return {
            'view_id': self.env.ref('account.view_move_form').id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def open_landlord_invoice(self):
        self.ensure_one()
        return {
            'view_id': self.env.ref('account.view_move_form').id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
