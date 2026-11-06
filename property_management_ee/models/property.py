# See LICENSE file for full copyright and licensing details
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PropertyType(models.Model):
    _name = "property.type"
    _description = "Property Type"

    name = fields.Char(
        string='Name',
        size=50,
        required=True)


class RentType(models.Model):
    _name = "rent.type"
    _description = "Rent Type"
    _order = 'sequence_in_view'
    _rec_names_search = ['name', 'renttype']

    def _compute_display_name(self):
        for rec in self:
            parts = [p for p in [rec.name, rec.renttype] if p]
            rec.display_name = ' '.join(parts)

    name = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'),
         ('4', '4'), ('5', '5'), ('6', '6'),
         ('7', '7'), ('8', '8'), ('9', '9'),
         ('10', '10'), ('11', '11'), ('12', '12')],
        required=True)
    renttype = fields.Selection(
        [('Monthly', 'Monthly'),
         ('Yearly', 'Yearly'),
         ('Weekly', 'Weekly')],
        string='Rent Type',
        required=True)
    sequence_in_view = fields.Integer(
        string='Sequence')

    @api.constrains('sequence_in_view')
    def _check_value(self):
        for rec in self:
            # 0 means "no explicit sequence"; only enforce real values.
            if rec.sequence_in_view and rec.search_count([
                    ('sequence_in_view', '=', rec.sequence_in_view),
                    ('id', '!=', rec.id)], limit=1):
                raise ValidationError(_('Sequence should be Unique!'))


class RoomType(models.Model):
    _name = "room.type"
    _description = "Room Type"

    name = fields.Char(
        string='Name',
        size=50,
        required=True)


class Utility(models.Model):
    _name = "utility"
    _description = "Utility"

    name = fields.Char(
        string='Name',
        size=50,
        required=True)


class PlaceType(models.Model):
    _name = 'place.type'
    _description = 'Place Type'

    name = fields.Char(
        string='Place Type',
        size=50,
        required=True)


class PropertyPhase(models.Model):
    _name = "property.phase"
    _description = 'Property Phase'
    _rec_name = 'property_id'

    end_date = fields.Date(
        string='End Date')
    start_date = fields.Date(
        string='Beginning Date')
    commercial_tax = fields.Float(
        string='Commercial Tax (in %)')
    occupancy_rate = fields.Float(
        string='Occupancy Rate (in %)')
    lease_price = fields.Float(
        string='Sales/lease Price Per Month')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')
    company_income = fields.Float(
        string='Company Income Tax CIT (in %)')


class PropertyPhoto(models.Model):
    _name = "property.photo"
    _description = 'Property Photo'
    _rec_name = 'doc_name'

    photos = fields.Binary(
        string='Photos')
    doc_name = fields.Char(
        string='Filename')
    photos_description = fields.Char(
        string='Description')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')


class PropertyFloorPlans(models.Model):
    _name = "property.floor.plans"
    _description = 'Floor Plans'
    _rec_name = 'doc_name'

    photos = fields.Binary(
        string='Photos')
    doc_name = fields.Char(
        string='Filename')
    photos_description = fields.Char(
        string='Description')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')


class PropertyRoom(models.Model):
    _name = "property.room"
    _description = 'Property Room'

    note = fields.Text(
        string='Notes')
    width = fields.Float(
        string='Width')
    height = fields.Float(
        string='Height')
    length = fields.Float(
        string='Length')
    image = fields.Binary(
        string='Picture')
    name = fields.Char(
        string='Name',
        size=60)
    attach = fields.Boolean(
        string='Attach Bathroom')
    type_id = fields.Many2one(
        comodel_name='room.type',
        string='Room Type')
    assets_ids = fields.One2many(
        comodel_name='room.assets',
        inverse_name='room_id',
        string='Assets')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')


class NearbyProperty(models.Model):
    _name = 'nearby.property'
    _description = 'Nearby Property'

    distance = fields.Float(
        string='Distance (Km)')
    name = fields.Char(
        string='Name',
        size=100)
    type = fields.Many2one(
        comodel_name='place.type',
        string='Type')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')


class RoomAssets(models.Model):
    _name = "room.assets"
    _description = "Room Assets"

    date = fields.Date(
        string='Date')
    name = fields.Char(
        string='Description',
        size=60)
    type = fields.Selection(
        [('fixed', 'Fixed Assets'),
         ('movable', 'Movable Assets'),
         ('other', 'Other Assets')],
        string='Type')
    qty = fields.Float(
        string='Quantity')
    room_id = fields.Many2one(
        comodel_name='property.room',
        string='Property')


class PropertyInsurance(models.Model):
    _name = "property.insurance"
    _description = "Property Insurance"

    premium = fields.Float(
        string='Premium')
    end_date = fields.Date(
        string='End Date')
    doc_name = fields.Char(
        string='Filename')
    contract = fields.Binary(
        string='Contract')
    start_date = fields.Date(
        string='Start Date')
    name = fields.Char(
        string='Description',
        size=60)
    policy_no = fields.Char(
        string='Policy Number',
        size=60)
    contact = fields.Many2one(
        comodel_name='res.company',
        string='Insurance Company')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Related Company')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')
    payment_mode_type = fields.Selection(
        [('monthly', 'Monthly'),
         ('semi_annually', 'Semi Annually'),
         ('yearly', 'Annually')],
        string='Payment Term')

    @api.constrains('start_date', 'end_date')
    def _constraint_date_limit(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date >= rec.end_date:
                    raise ValidationError(_(
                        'In Property Insurance Start Date Should be '
                        'less than the End Date!'))


class PropertyUtility(models.Model):
    _name = "property.utility"
    _description = 'Property Utility'

    note = fields.Text(
        string='Remarks')
    ref = fields.Char(
        string='Reference',
        size=60)
    expiry_date = fields.Date(
        string='Expiry Date')
    issue_date = fields.Date(
        string='Issuance Date')
    utility_id = fields.Many2one(
        comodel_name='utility',
        string='Utility')
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')
    contact_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Contact',
        domain="[('tenant', '=', True)]")


class PropertySafetyCertificate(models.Model):
    _name = "property.safety.certificate"
    _description = 'Property Safety Certificate'

    ew = fields.Boolean('EW')
    weeks = fields.Integer('Weeks')
    ref = fields.Char('Reference', size=60)
    expiry_date = fields.Date(string='Expiry Date')
    name = fields.Char(
        string='Certificate',
        size=60,
        required=True)
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')
    contact_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Contact',
        domain="[('tenant', '=', True)]")


class PropertyAttachment(models.Model):
    _name = 'property.attachment'
    _description = 'Property Attachment'

    doc_name = fields.Char(string='Filename')
    expiry_date = fields.Date(string='Expiry Date')
    contract_attachment = fields.Binary(string='Attachment')
    name = fields.Char(
        string='Description',
        size=64,
        required=True)
    property_id = fields.Many2one(
        comodel_name='account.asset',
        string='Property')
