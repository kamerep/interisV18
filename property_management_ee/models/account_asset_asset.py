# See LICENSE file for full copyright and licensing details

from dateutil.relativedelta import relativedelta
import re
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset'

    is_property = fields.Boolean('Is Property', default=False)

    @api.depends('property_phase_ids', 'property_phase_ids.lease_price')
    def _compute_sales_rates(self):
        for prop_rec in self:
            phases = prop_rec.property_phase_ids
            count = len(phases)
            total = sum(p.lease_price for p in phases)
            prop_rec.sales_rates = (total / count) if count else 0.0

    @api.depends('roi')
    def _compute_ten_year_roi(self):
        for rec in self:
            rec.ten_year_roi = 10 * rec.roi

    @api.depends('tenancy_property_ids', 'tenancy_property_ids.rent')
    def _compute_roi(self):
        for prop_rec in self:
            prop_rec.roi = sum(
                g.rent for g in prop_rec.tenancy_property_ids)

    @api.depends('tenancy_property_ids', 'tenancy_property_ids.rent',
                 'property_phase_ids', 'property_phase_ids.lease_price')
    def _compute_operational_costs(self):
        for prop_rec in self:
            gain = sum(g.rent for g in prop_rec.tenancy_property_ids)
            op_cost = sum(
                p.lease_price / 100 for p in prop_rec.property_phase_ids)
            prop_rec.operational_costs = (
                op_cost / gain if gain and op_cost else 0.0)

    @api.depends('acquisition_date',
                 'tenancy_property_ids',
                 'tenancy_property_ids.date',
                 'tenancy_property_ids.date_start')
    def _compute_occupancy_rates(self):
        """Share (%) of the days since acquisition covered by tenancies."""
        today = fields.Date.today()
        for prop_rec in self:
            occ_rate = 0.0
            if prop_rec.acquisition_date:
                owned_days = (today - prop_rec.acquisition_date).days
                occupied_days = sum(
                    (min(t.date, today) - max(t.date_start,
                                              prop_rec.acquisition_date)).days
                    for t in prop_rec.tenancy_property_ids
                    if t.date and t.date_start and t.date_start <= today)
                if owned_days > 0 and occupied_days > 0:
                    occ_rate = min(occupied_days * 100.0 / owned_days, 100.0)
            prop_rec.occupancy_rates = occ_rate

    @api.depends('tenancy_property_ids',
                 'tenancy_property_ids.rent_schedule_ids',
                 'tenancy_property_ids.rent_schedule_ids.amount')
    def _compute_simulation(self):
        for pd in self:
            pd.simulation = sum(
                rs.amount
                for tp in pd.tenancy_property_ids
                for rs in tp.rent_schedule_ids)

    @api.depends('tenancy_property_ids',
                 'tenancy_property_ids.rent_schedule_ids',
                 'tenancy_property_ids.rent_schedule_ids.move_check',
                 'tenancy_property_ids.rent_schedule_ids.amount')
    def _compute_revenue(self):
        for pd in self:
            pd.revenue = sum(
                rs.amount
                for tp in pd.tenancy_property_ids
                for rs in tp.rent_schedule_ids
                if rs.move_check)

    @api.depends('gfa_feet', 'unit_price')
    def _compute_total_price(self):
        for rec in self:
            rec.total_price = rec.gfa_feet * rec.unit_price

    image = fields.Binary(
        "Logo",
        attachment=True,
        help="Logo image for the property, limited to 1024x1024px.")
    simulation_date = fields.Date(string='Simulation Date')
    city = fields.Char(string='City')
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    township = fields.Char(string='Township')
    simulation_name = fields.Char(string='Simulation Name')
    construction_cost = fields.Float(string='Construction Cost')
    zip = fields.Char(string='Zip', size=24, change_default=True)
    video_url = fields.Char(
        string='Video URL',
        help="e.g. //www.youtube.com/embed/VIDEO_ID?rel=0")
    unit_price = fields.Float(
        string='Unit Price',
        help='Unit Price Per Sqft.')
    ground_rent = fields.Float(
        string='Ground Rent',
        help='Ground rent of Property.')
    gfa_meter = fields.Float(
        string='GFA(m)',
        help='Gross floor area in Meter.')
    sale_price = fields.Float(
        string='Sale Price',
        help='Sale price of the Property.')
    gfa_feet = fields.Float(
        string='GFA(Sqft)',
        help='Gross floor area in Square feet.')
    furnished = fields.Selection(
        [('none', 'None'),
         ('semi_furnished', 'Semi Furnished'),
         ('full_furnished', 'Full Furnished')],
        string='Furnishing',
        default='none',
        help='Furnishing status.')
    sales_rates = fields.Float(
        string="Sales Rate",
        compute='_compute_sales_rates',
        help='Average Sale/Lease price from property phase per Month.')
    ten_year_roi = fields.Float(
        string="10 Year ROI",
        compute='_compute_ten_year_roi',
        help="10 year Return of Investment.")
    roi = fields.Float(
        string="ROI",
        compute='_compute_roi',
        store=True,
        help='Return On Investment based on total tenancy rent.')
    operational_costs = fields.Float(
        string="Operational Costs (%)",
        store=True,
        compute='_compute_operational_costs',
        help='Average operational budget vs total rent.')
    occupancy_rates = fields.Float(
        string="Occupancy Rate",
        store=True,
        compute='_compute_occupancy_rates',
        help='Total Occupancy rate of Property.')
    parent_path = fields.Char(index=True)
    simulation = fields.Float(
        string='Total Amount',
        compute='_compute_simulation',
        store=True)
    revenue = fields.Float(
        string='Revenue',
        compute='_compute_revenue',
        store=True)
    total_price = fields.Float(
        string='Total Price',
        compute='_compute_total_price',
        help='Total Price = Unit Price * GFA (Sqft).')
    pur_instl_chck = fields.Boolean(
        string='Purchase Installment Check',
        default=False)
    sale_instl_chck = fields.Boolean(
        string='Sale Installment Check',
        default=False)
    color = fields.Integer(string='Color', default=4)
    floor = fields.Integer(
        string='Floor',
        help='Number of Floors.')
    no_of_towers = fields.Integer(
        string='No of Towers',
        help='Number of Towers.')
    no_of_property = fields.Integer(
        string='Property Per Floor',
        help='Number of Properties Per Floor.')
    bedroom = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5+')],
        string='Bedrooms',
        default='1')
    bathroom = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5+')],
        string='Bathrooms',
        default='1')
    parking = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5+')],
        string='Parking',
        default='1')
    facing = fields.Selection(
        [('north', 'North'), ('south', 'South'),
         ('east', 'East'), ('west', 'West')],
        string='Facing',
        default='east')
    income_acc_id = fields.Many2one(
        comodel_name='account.account',
        string='Income Account',
        help='Income Account of Property.')
    # V18 EE uses parent_id/children_ids for gross-increase assets (they
    # feed the parent's book value and depreciation), so the property
    # hierarchy lives on dedicated fields.
    property_parent_id = fields.Many2one(
        comodel_name='account.asset',
        string='Parent Property',
        index=True,
        ondelete='restrict',
        domain="[('is_property', '=', True)]")
    maint_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Maintenance Account')
    current_tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Current Tenant')
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        ondelete='restrict')
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Property State',
        ondelete='restrict')
    type_id = fields.Many2one(
        comodel_name='property.type',
        string='Property Type',
        help='Types of property.',
        index=True)
    rent_type_id = fields.Many2one(
        comodel_name='rent.type',
        string='Rent Type',
        help='Type of Rent.')
    contact_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Contact Name',
        domain="[('tenant', '=', True)]")
    property_manager = fields.Many2one(
        comodel_name='res.partner',
        string='Property Manager')
    room_ids = fields.One2many(
        comodel_name='property.room',
        inverse_name='property_id',
        string='Rooms')
    property_phase_ids = fields.One2many(
        comodel_name='property.phase',
        inverse_name='property_id',
        string='Phases')
    property_photo_ids = fields.One2many(
        comodel_name='property.photo',
        inverse_name='property_id',
        string='Photos')
    floor_plans_ids = fields.One2many(
        comodel_name='property.floor.plans',
        inverse_name='property_id',
        string='Floor Plans')
    utility_ids = fields.One2many(
        comodel_name='property.utility',
        inverse_name='property_id',
        string='Utilities')
    nearby_ids = fields.One2many(
        comodel_name='nearby.property',
        inverse_name='property_id',
        string='Nearest Properties')
    contract_attachment_ids = fields.One2many(
        comodel_name='property.attachment',
        inverse_name='property_id',
        string='Documents')
    child_ids = fields.One2many(
        comodel_name='account.asset',
        inverse_name='property_parent_id',
        string='Child Properties')
    property_insurance_ids = fields.One2many(
        comodel_name='property.insurance',
        inverse_name='property_id',
        string='Insurance')
    tenancy_property_ids = fields.One2many(
        comodel_name='account.analytic.account',
        inverse_name='property_id',
        string='Tenancies')
    safety_certificate_ids = fields.One2many(
        comodel_name='property.safety.certificate',
        inverse_name='property_id',
        string='Safety Certificates')
    # V18: add property-specific states while keeping base asset states
    state = fields.Selection(
        selection_add=[
            ('new_draft', 'Booking Open'),
            ('book', 'Booked'),
            ('normal', 'On Lease'),
            ('sold', 'Sold'),
            ('cancel', 'Cancel'),
        ],
        ondelete={
            'new_draft': 'set default',
            'book': 'set default',
            'normal': 'set default',
            'sold': 'set default',
            'cancel': 'set default',
        })
    latitude = fields.Float(
        string='Latitude',
        digits=(16, 8),
        help='Latitude of the place.')
    longitude = fields.Float(
        string='Longitude',
        digits=(16, 8),
        help='Longitude of the place.')
    note = fields.Text()
    tenancy_entries_count = fields.Integer(
        compute='_get_tenancy_count',
        string='Tenancy')

    @api.constrains('no_of_towers', 'no_of_property', 'ground_rent',
                    'gfa_feet', 'gfa_meter', 'unit_price')
    def check_negative_value(self):
        for prop in self:
            if prop.no_of_towers < 0:
                raise ValidationError(
                    _('You cannot enter a negative No of Towers.'))
            if prop.no_of_property < 0:
                raise ValidationError(
                    _('You cannot enter a negative No of Property.'))
            if prop.ground_rent < 0:
                raise ValidationError(
                    _('You cannot enter a negative Ground Rent.'))
            if prop.gfa_feet < 0:
                raise ValidationError(
                    _('You cannot enter a negative GFA (Sqft).'))
            if prop.gfa_meter < 0:
                raise ValidationError(
                    _('You cannot enter a negative GFA (m).'))
            if prop.unit_price < 0:
                raise ValidationError(
                    _('You cannot enter a negative Unit Price.'))

    def _get_tenancy_count(self):
        for rec in self:
            rec.tenancy_entries_count = len(rec.tenancy_property_ids)

    def open_property_entries(self):
        self.ensure_one()
        return {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': ['|', ('asset_id', '=', self.id),
                       ('property_id', '=', self.id)],
            'context': {'create': False},
        }

    def open_tenancy(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            'property_management_ee.action_property_analytic_view')
        action['domain'] = [
            ('property_id', '=', self.id),
            ('resident_type', '=', 'tenant_tenancy'),
        ]
        action['context'] = {
            'create': False,
            'is_property': True,
            'default_resident_type': 'tenant_tenancy',
        }
        return action

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'message_follower_ids' in vals:
                del vals['message_follower_ids']
            if vals.get('property_parent_id'):
                parent = self.browse(vals['property_parent_id'])
                if parent.rent_type_id:
                    vals.setdefault('rent_type_id', parent.rent_type_id.id)
        assets = super().create(vals_list)
        plan = self.env['account.analytic.plan'].search(
            [('name', '=', 'Property Management')], limit=1)
        if not plan:
            plan = self.env['account.analytic.plan'].create(
                {'name': 'Property Management'})
        for asset in assets:
            if asset.is_property:
                self.env['account.analytic.account'].create({
                    'name': asset.name,
                    'plan_id': plan.id,
                })
        return assets

    def write(self, vals):
        state_color = {
            'new_draft': 0, 'draft': 4, 'book': 2,
            'normal': 7, 'close': 9, 'sold': 9,
            'cancel': 1, 'open': 10, 'paused': 5,
        }
        if 'state' in vals and vals['state'] in state_color:
            vals['color'] = state_color[vals['state']]
        return super().write(vals)

    def create_tenancy(self):
        analytic_obj = self.env['account.analytic.account']
        account_asset_id = self.env['account.analytic.account']
        for asset in self:
            account_asset_id = analytic_obj.with_context(
                is_property=True).create({
                    'name': asset.name,
                    'property_id': asset.id,
                    'resident_type': 'tenant_tenancy',
                })
            account_asset_id.onchange_date_start()
        form_view_id = self.env.ref(
            'property_management_ee.property_analytic_view_form').id
        return {
            'view_id': form_view_id,
            'view_mode': 'form',
            'res_model': 'account.analytic.account',
            'res_id': account_asset_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.onchange('property_parent_id')
    def parent_property_onchange(self):
        if self.property_parent_id:
            p = self.property_parent_id
            self.street = p.street or ''
            self.street2 = p.street2 or ''
            self.township = p.township or ''
            self.city = p.city or ''
            self.state_id = p.state_id.id or False
            self.zip = p.zip or ''
            self.country_id = p.country_id.id or False

    @api.onchange('gfa_feet')
    def sqft_to_meter(self):
        self.gfa_meter = (
            self.gfa_feet / 10.7639104 if self.gfa_feet else 0.0)

    @api.onchange('unit_price', 'gfa_feet')
    def unit_price_calc(self):
        if self.unit_price and self.gfa_feet:
            self.total_price = self.unit_price * self.gfa_feet
        if self.unit_price and not self.gfa_feet:
            raise ValidationError(_('Please enter GFA (Sqft).'))

    def edit_status(self):
        for rec in self:
            if not rec.property_manager:
                raise ValidationError(_('Please enter the Property Manager!'))
        return self.write({'state': 'book'})

    def edit_status_book(self):
        context = dict(self._context)
        for rec in self:
            context['edit_result'] = rec.id
        return {
            'name': _('Wizard'),
            'res_model': 'book.available.wiz',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }

    def open_url(self):
        url = "http://maps.google.com/maps?oi=map&q="
        for line in self:
            for attr, val in [
                ('name', line.name), ('street', line.street),
                ('street2', line.street2), ('township', line.township),
                ('city', line.city),
                ('state_id', line.state_id.name if line.state_id else ''),
                ('country_id', line.country_id.name if line.country_id else ''),
            ]:
                if val:
                    part = re.sub(r'[^\w]', ' ', val)
                    url += re.sub(' +', '+', part) + '+'
            if line.zip:
                url += line.zip
        return {
            'name': _('Go to website'),
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'current',
            'url': url,
        }

    def button_normal(self):
        self.write({'state': 'normal'})

    def button_cancel(self):
        self.write({'state': 'cancel'})

    def button_draft(self):
        self.write({'state': 'draft'})

    def date_addition(self, starting_date, end_date, period):
        """Generate list of dates between starting_date and end_date."""
        date_list = []
        delta = relativedelta(months=1) if period == 'monthly' else relativedelta(years=1)
        while starting_date < end_date:
            date_list.append(starting_date)
            starting_date += delta
        return date_list
