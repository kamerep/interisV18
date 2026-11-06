# See LICENSE file for full copyright and licensing details

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class AccountAnalyticAccount(models.Model):
    _name = "account.analytic.account"
    _description = 'Tenant Tenancy'
    _inherit = ["account.analytic.account", "mail.activity.mixin"]
    _order = 'code'

    @api.depends('line_ids.amount')
    def _compute_total_deb_cre_amt(self):
        for tenancy_brw in self:
            tenancy_brw.total_deb_cre_amt = (
                tenancy_brw.total_credit_amt - tenancy_brw.total_debit_amt
            )

    @api.depends('line_ids.amount')
    def _compute_total_credit_amt(self):
        for tenancy_brw in self:
            tenancy_brw.total_credit_amt = sum(
                l.amount for l in tenancy_brw.line_ids if l.amount > 0)

    @api.depends('line_ids.amount')
    def _compute_total_debit_amt(self):
        for tenancy_brw in self:
            tenancy_brw.total_debit_amt = abs(sum(
                l.amount for l in tenancy_brw.line_ids if l.amount < 0))

    @api.depends('rent_schedule_ids', 'rent_schedule_ids.amount')
    def _compute_total_rent(self):
        for tenancy_brw in self:
            tenancy_brw.total_rent = sum(
                r.amount for r in tenancy_brw.rent_schedule_ids)

    @api.depends('acc_pay_dep_rec_id', 'acc_pay_dep_rec_id.state')
    def _compute_payment_type(self):
        for tennancy in self:
            tennancy.deposit_received = bool(
                tennancy.acc_pay_dep_rec_id
                and tennancy.acc_pay_dep_rec_id.state in ('in_process', 'paid')
                and tennancy.acc_pay_dep_rec_id.payment_type == 'inbound'
            )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get('date_start') and 'date' in fields_list:
            res['date'] = fields.Date.to_date(
                res['date_start']) + relativedelta(years=1)
        return res

    def _get_property_analytic_plan(self):
        """Return (or create) the Property Management analytic plan."""
        plan = self.env['account.analytic.plan'].search(
            [('name', '=', 'Property Management')], limit=1)
        if not plan:
            plan = self.env['account.analytic.plan'].create(
                {'name': 'Property Management'})
        return plan

    contract_attachment = fields.Binary(
        string='Tenancy Contract',
        help='Contract document attachment for selected property')
    is_property = fields.Boolean(string='Is Property?')
    resident_type = fields.Selection(
        [('tenant_tenancy', 'Tenant Tenancy')],
        string="Resident Type")
    rent_entry_chck = fields.Boolean(
        string='Rent Entries Check',
        default=False)
    deposit_received = fields.Boolean(
        string='Deposit Received?',
        default=False,
        compute='_compute_payment_type',
        store=True,
        copy=False,
        help="True if deposit amount received for current Tenancy.")
    deposit_return = fields.Boolean(
        string='Deposit Returned?',
        default=False,
        compute='compute_amount_return',
        store=True,
        copy=False,
        help="True if deposit amount returned for current Tenancy.")
    code = fields.Char(
        string='Reference',
        default="/")
    doc_name = fields.Char(string='Filename')
    date = fields.Date(
        string='Expiration Date',
        index=True,
        help="Tenancy contract end date.")
    date_start = fields.Date(
        string='Start Date',
        default=fields.Date.context_today,
        help="Tenancy contract start date.")
    ten_date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        index=True,
        help="Tenancy contract creation date.")
    amount_fee_paid = fields.Integer(string='Amount of Fee Paid')
    manager_id = fields.Many2one(
        comodel_name='res.users',
        string='Account Manager',
        help="Manager of Tenancy.")
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property',
        domain="[('is_property','=', True)]",
        copy=False,
        help="Name of Property.")
    tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Tenant',
        domain="[('tenant', '=', True)]",
        help="Tenant Name of Tenancy.")
    contact_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        help="Contact person name.")
    rent_schedule_ids = fields.One2many(
        comodel_name='tenancy.rent.schedule',
        inverse_name='tenancy_id',
        string='Rent Schedule')
    # account_move_line_ids replaced by line_ids (account.analytic.line)
    # which is defined on the base account.analytic.account model in V18
    rent = fields.Monetary(
        string='Tenancy Rent',
        default=0.0,
        currency_field='currency_id',
        help="Tenancy rent for selected property per Month.")
    deposit = fields.Monetary(
        string='Deposit',
        default=0.0,
        currency_field='currency_id',
        copy=False,
        help="Deposit amount for tenancy.")
    total_rent = fields.Monetary(
        string='Total Rent',
        store=True,
        readonly=True,
        currency_field='currency_id',
        compute='_compute_total_rent',
        help='Total rent of this Tenancy.')
    amount_return = fields.Monetary(
        string='Deposit Returned',
        default=0.0,
        currency_field='currency_id',
        copy=False,
        help="Deposit Returned amount for Tenancy.")
    total_debit_amt = fields.Monetary(
        string='Total Debit Amount',
        default=0.0,
        compute='_compute_total_debit_amt',
        currency_field='currency_id')
    total_credit_amt = fields.Monetary(
        string='Total Credit Amount',
        default=0.0,
        compute='_compute_total_credit_amt',
        currency_field='currency_id')
    total_deb_cre_amt = fields.Monetary(
        string='Total Expenditure',
        default=0.0,
        compute='_compute_total_deb_cre_amt',
        currency_field='currency_id')
    description = fields.Text(
        string='Description',
        help='Additional Terms and Conditions')
    duration_cover = fields.Text(
        string='Duration of Cover',
        help='Additional Notes')
    acc_pay_dep_rec_id = fields.Many2one(
        comodel_name='account.payment',
        string='Account Payment',
        copy=False)
    acc_pay_dep_ret_id = fields.Many2one(
        comodel_name='account.payment',
        string='Return Payment',
        copy=False)
    rent_type_id = fields.Many2one(
        comodel_name='rent.type',
        string='Rent Type')
    deposit_scheme_type = fields.Selection(
        [('insurance', 'Insurance-based')],
        'Type of Scheme')
    state = fields.Selection(
        [('template', 'Template'),
         ('draft', 'New'),
         ('open', 'In Progress'),
         ('pending', 'To Renew'),
         ('close', 'Closed'),
         ('cancelled', 'Cancelled')],
        string='Status',
        required=True,
        copy=False,
        default='draft')
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        copy=False,
        string='Invoice')
    multi_prop = fields.Boolean(
        string='Multiple Property',
        help="Check this box Multiple property.")
    prop_ids = fields.Many2many(
        comodel_name='account.asset',
        relation='tenancy_property_rel',
        column1='tenancy_id',
        column2='property_id',
        string='Properties')
    recurring = fields.Boolean('Recurring')
    main_cost = fields.Float(
        string='Maintenance Cost',
        default=0.0,
        help="Insert maintenance cost")
    tenancy_cancelled = fields.Boolean(
        string='Tenancy Cancelled',
        default=False)

    @api.constrains('date_start', 'date')
    def check_date_overlap(self):
        for rec in self:
            if rec.date_start and rec.date:
                if rec.date < rec.date_start:
                    raise ValidationError(
                        _('End date should be greater than Start Date!'))

    @api.constrains('rent', 'deposit')
    def check_rent_positive(self):
        for rec in self:
            if rec.rent < 0:
                raise ValidationError(
                    _('Rent amount should be strictly positive.'))
            if rec.deposit < 0:
                raise ValidationError(
                    _('Deposit amount should be positive.'))

    @api.model_create_multi
    def create(self, vals_list):
        plan = self._get_property_analytic_plan()
        for vals in vals_list:
            if 'resident_type' in vals:
                vals['code'] = self.env['ir.sequence'].next_by_code(
                    'account.analytic.account') or '/'
            if 'plan_id' not in vals:
                vals['plan_id'] = plan.id
        records = super().create(vals_list)
        for record in records:
            if record.property_id and self._context.get('is_property'):
                record.property_id.write({
                    'current_tenant_id': record.tenant_id.id or False,
                    'state': 'book',
                })
        return records

    def write(self, vals):
        rec = super().write(vals)
        for tenancy_rec in self:
            if (tenancy_rec.resident_type == 'tenant_tenancy'
                    and vals.get('state') in ['open', 'close']):
                state_dict = {
                    'open': {
                        'current_tenant_id': tenancy_rec.tenant_id.id,
                        'state': 'normal',
                    },
                    'close': {
                        'state': 'draft',
                        'current_tenant_id': False,
                    },
                }
                tenancy_rec.property_id.write(
                    state_dict[vals['state']])
        return rec

    def unlink(self):
        for tenancy_rec in self:
            if tenancy_rec.state not in ('draft', 'cancelled'):
                state_label = dict(
                    self._fields['state'].selection
                ).get(tenancy_rec.state, tenancy_rec.state)
                raise UserError(_(
                    'You cannot delete a tenancy record which '
                    'is in "%s" state.') % state_label)
            # V18: analytic lines reference the account through the
            # plan column (x_plan<id>_id); line_ids resolves it for us.
            tenancy_rec.line_ids.unlink()
            rent_ids = self.env['tenancy.rent.schedule'].search(
                [('tenancy_id', '=', tenancy_rec.id)])
            if any(rent.move_check for rent in rent_ids):
                raise ValidationError(_(
                    'You cannot delete Tenancy record if any related '
                    'Rent Schedule entries are posted.'))
            rent_ids.unlink()
            if (tenancy_rec.property_id.property_manager
                    and tenancy_rec.property_id.property_manager.id):
                related_user = tenancy_rec.property_id.property_manager.id
                users = self.env['res.users'].search(
                    [('partner_id', '=', related_user)])
                if users:
                    users.write(
                        {'tenant_ids': [(3, tenancy_rec.tenant_id.id)]})
            tenancy_rec.property_id.write(
                {'state': 'draft', 'current_tenant_id': False})
        return super().unlink()

    @api.depends('invoice_id', 'invoice_id.payment_state')
    def compute_amount_return(self):
        for data in self:
            data.deposit_return = bool(
                data.invoice_id
                and data.invoice_id.payment_state in ['in_payment', 'paid'])

    @api.onchange('date_start', 'property_id')
    def onchange_date_start(self):
        if self.date_start:
            self.date = self.date_start + relativedelta(years=1)
        if self.property_id:
            self.rent_type_id = self.property_id.rent_type_id.id
            self.rent = self.property_id.ground_rent or 0.0

    def button_receive(self):
        context = dict(self._context) or {}
        acc_pay_form = self.env.ref('account.view_account_payment_form')
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        context.update({
            'close_after_process': True,
            'account_deposit_received': True,
        })
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
                    'context': context,
                }
            if tenancy_rec.deposit == 0.00:
                raise ValidationError(_('Please Enter Deposit amount.'))
            if tenancy_rec.deposit < 0.00:
                raise ValidationError(
                    _('The deposit amount must be strictly positive.'))
            payment_method_line = account_jrnl_obj.inbound_payment_method_line_ids.filtered(
                lambda l: l.code == 'manual')[:1]
            vals = {
                'partner_id': tenancy_rec.tenant_id.parent_id.id,
                'partner_type': 'customer',
                'journal_id': account_jrnl_obj.id,
                'payment_type': 'inbound',
                'memo': _('Deposit Received'),
                'tenancy_id': tenancy_rec.id,
                'amount': tenancy_rec.deposit,
                'property_id': tenancy_rec.property_id.id,
            }
            if payment_method_line:
                vals['payment_method_line_id'] = payment_method_line.id
            payment_id = self.env['account.payment'].with_context(
                context).create(vals)
        return {
            'view_id': acc_pay_form.id,
            'view_mode': 'form',
            'res_id': payment_id and payment_id.id,
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
        }

    def button_return(self):
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1)
        invoice_obj = self.env['account.move']
        wiz_form_id = self.env.ref('account.view_move_form').id
        for rec in self:
            account_id = rec.property_id.account_depreciation_expense_id.id
            if rec.multi_prop and rec.prop_ids:
                account_id = (
                    rec.prop_ids[:1].income_acc_id.id or account_id)
            inv_line_values = {
                'name': _('Deposit Return'),
                'quantity': 1,
                'account_id': account_id or False,
                'price_unit': rec.deposit or 0.00,
                'analytic_distribution': {str(rec.id): 100} if rec.id else {},
            }
            inv_values = {
                'move_type': 'in_invoice',
                'property_id': rec.property_id.id,
                'partner_id': rec.tenant_id.parent_id.id or False,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                'invoice_date': fields.Date.today(),
                'new_tenancy_id': rec.id,
                'journal_id': account_jrnl_obj.id if account_jrnl_obj else False,
            }
            acc_id = invoice_obj.create(inv_values)
            rec.write({'invoice_id': acc_id.id})
        if len(self) != 1:
            return True
        return {
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def button_open_recived(self):
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

    def button_start(self):
        user_obj = self.env['res.users']
        for current_rec in self:
            if current_rec.resident_type == 'tenant_tenancy':
                if (current_rec.property_id.property_manager
                        and current_rec.property_id.property_manager.id):
                    related_user = current_rec.property_id.property_manager.id
                    new_ids = user_obj.search(
                        [('partner_id', '=', related_user)])
                    if new_ids:
                        new_ids.write(
                            {'tenant_ids': [(4, current_rec.tenant_id.id)]})
        return self.write({'state': 'open', 'rent_entry_chck': False})

    def button_close(self):
        for rec in self:
            rec.state = 'close'

    def button_set_to_draft(self):
        for rec in self:
            rec.write({
                'state': 'draft',
                'rent_schedule_ids': [(5, 0, 0)],
            })

    def button_set_to_renew(self):
        self.ensure_one()
        rent_schedule_obj = self.env['tenancy.rent.schedule']
        if rent_schedule_obj.search([
                ('tenancy_id', '=', self.id),
                ('move_check', '=', False)]):
            raise ValidationError(_(
                'In order to Renew a Tenancy, Please make all related '
                'Rent Schedule entries posted.'))
        return {
            'name': _('Tenancy Renew Wizard'),
            'res_model': 'renew.tenancy',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_start_date': self.date},
        }

    @api.model
    def cron_property_states_changed(self):
        current_date = fields.Date.today()
        tncy_rec = self.search([
            ('date_start', '<=', current_date),
            ('date', '>=', current_date),
            ('state', '=', 'open'),
            ('resident_type', '=', 'tenant_tenancy'),
        ])
        for tncy_data in tncy_rec:
            if tncy_data.property_id:
                tncy_data.property_id.write({'state': 'normal', 'color': 7})
        return True

    def create_rent_schedule(self):
        rent_obj = self.env['tenancy.rent.schedule']
        for tenancy_rec in self:
            if not (tenancy_rec.date_start and tenancy_rec.date
                    and tenancy_rec.rent_type_id):
                raise UserError(_(
                    'Please set the Start Date, Expiration Date and Rent '
                    'Type of tenancy "%s" before creating the rent '
                    'schedule.') % tenancy_rec.display_name)
            if tenancy_rec.date < tenancy_rec.date_start:
                raise ValidationError(
                    _('End date must be greater than start date.'))
            if tenancy_rec.rent_type_id.renttype == 'Weekly':
                d1 = tenancy_rec.date_start
                d2 = tenancy_rec.date
                interval = int(tenancy_rec.rent_type_id.name)
                if d2 < d1:
                    raise ValidationError(
                        _('End date must be greater than start date.'))
                wek_diff = d2 - d1
                wek_tot1 = wek_diff.days // (interval * 7)
                wek_tot = wek_diff.days % (interval * 7)
                if wek_diff.days == 0:
                    wek_tot = 1
                for _wek_rec in range(wek_tot1):
                    rent_obj.create({
                        'start_date': d1,
                        'amount': tenancy_rec.rent * interval or 0.0,
                        'property_id': tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id,
                    })
                    d1 = d1 + relativedelta(days=(7 * interval))
                if wek_tot > 0:
                    # rent is per week; charge the leftover days pro rata
                    one_day_rent = (
                        tenancy_rec.rent / 7 if tenancy_rec.rent else 0.0)
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
                for _rec in range(tot_rec):
                    rent_obj.create({
                        'start_date': d1,
                        'amount': tenancy_rec.rent * interval or 0.0,
                        'property_id': tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id,
                    })
                    d1 = d1 + relativedelta(months=interval)
                if tot_rec2 > 0:
                    rent_obj.create({
                        'start_date': d1,
                        'amount': tenancy_rec.rent * tot_rec2 or 0.0,
                        'property_id': tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id,
                    })
        return self.write({'rent_entry_chck': True})

    def button_cancel_tenancy(self):
        for record in self:
            record.write({'state': 'cancelled', 'tenancy_cancelled': True})
            record.property_id.write({'state': 'draft'})
            rent_ids = self.env['tenancy.rent.schedule'].search([
                ('tenancy_id', '=', record.id),
                ('paid', '=', False),
                ('move_check', '=', False),
            ])
            rent_ids.write({'is_readonly': True})
        return True
