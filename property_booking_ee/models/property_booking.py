# See LICENSE file for full copyright and licensing details

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from string import ascii_lowercase


class PropertyCreated(models.Model):
    _name = "property.created"
    _description = 'Property Created'

    @api.depends('asset_id.child_ids')
    def _compute_total_prop_tower(self):
        for rec in self:
            rec.total_prop_tower = len(rec.child_ids)

    @api.depends('child_ids', 'child_ids.state')
    def _compute_no_avl(self):
        for rec in self:
            rec.no_avl = len([
                c for c in rec.child_ids if c.state != 'book'])

    tower_num = fields.Char(string='Tower No.')
    floor_number = fields.Char(string='Floor No.')
    asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset',
        delegate=True,
        required=True,
        ondelete='cascade')
    prefix3 = fields.Selection(
        [('1', 'ABCD'), ('2', '101'), ('3', '1001'), ('4', '10001')],
        string='Prefix For Property',
        default='2',
        help='Prefix or Label For Property.')
    is_sub_property = fields.Boolean(
        string='Sub Property',
        help='Select if your property is a Sub Property.')
    change_lable = fields.Boolean(string='Change Label')
    prop_number = fields.Char(string='Property Number')
    lable_bool = fields.Boolean(string='Label Boolean')
    parent_related = fields.Many2one(
        comodel_name='account.asset',
        string='Parent Property (Related)',
        related='asset_id.property_parent_id',
        ondelete='restrict')
    parent_property_rel = fields.Many2one(
        comodel_name='account.asset',
        string='Parent Property Relation',
        related='parent_related.property_parent_id',
        ondelete='restrict')
    total_prop_tower = fields.Float(
        compute='_compute_total_prop_tower',
        string='Total Tower',
        readonly=True)
    no_avl = fields.Integer(
        string='Available',
        compute='_compute_no_avl',
        store=True)
    image = fields.Binary(
        string="Image",
        attachment=True)

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if 'name' not in default:
            for rec, vals in zip(self, vals_list):
                vals['name'] = _("%s (Copy)", rec.name)
        return vals_list

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        context = self._context
        new_property_id = context.get('booking_new_prop_id')
        main_property_id = context.get('booking_main_property_id')
        extra = []
        if new_property_id:
            asset_id = self.browse(new_property_id).asset_id
            extra += [('property_parent_id', '=', asset_id.id), ('state', '=', 'draft')]
        if main_property_id and new_property_id:
            extra += [('id', '!=', main_property_id)]
        if extra:
            domain = list(domain) + extra
        return super()._search(
            domain, offset=offset, limit=limit, order=order)

    def create_property(self):
        create_obj = self.env['property.created']
        tower_list = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for property_rec in self:
            if property_rec.is_sub_property and (
                    property_rec.no_of_property == 0 or property_rec.floor == 0):
                raise ValidationError(_(
                    'Property per floor and number of floors should not be zero!'))
            base_values = {
                'original_value': property_rec.original_value,
                'furnished': property_rec.furnished,
                'type_id': property_rec.type_id.id,
                'property_parent_id': property_rec.asset_id.id,
                'is_property': True,
                'ground_rent': property_rec.ground_rent,
                'floor': property_rec.floor,
                'no_of_property': 1,
                'state': 'draft',
                'color': 4,
                'lable_bool': True,
                'is_sub_property': True,
                'street': property_rec.street,
                'street2': property_rec.street2,
                'township': property_rec.township,
                'city': property_rec.city,
                'state_id': property_rec.state_id.id,
                'country_id': property_rec.country_id.id,
                'zip': property_rec.zip,
                'image': property_rec.image,
                'property_manager': property_rec.property_manager.id,
            }
            if property_rec.prefix3 != '1':
                for floor_rec in range(1, int(property_rec.floor) + 1):
                    for pro_rec in range(
                            1, int(property_rec.no_of_property) + 1):
                        fmt = "%." + str(property_rec.prefix3) + "d"
                        values = dict(base_values, **{
                            'name': '%s-%s%s' % (
                                property_rec.name, floor_rec, fmt % pro_rec),
                            'tower_num': property_rec.name,
                            'prop_number': fmt % pro_rec,
                            'floor_number': str(floor_rec),
                        })
                        create_obj.create(values)
                property_rec.write({'state': 'new_draft'})
            else:
                labels = list(ascii_lowercase) + [
                    a + b for a in ascii_lowercase for b in ascii_lowercase]
                for floor_rec in range(1, int(property_rec.floor) + 1):
                    for counter in range(int(property_rec.no_of_property)):
                        if counter < len(labels):
                            label = labels[counter % len(labels)]
                        else:
                            label = (tower_list[counter % len(tower_list)]
                                     + str(counter // 26))
                        values = dict(base_values, **{
                            'name': '%s-%s%s' % (
                                property_rec.name, floor_rec, label),
                            'tower_num': property_rec.name,
                            'prop_number': label,
                            'floor_number': str(floor_rec),
                        })
                        create_obj.create(values)
                property_rec.write({'state': 'new_draft'})
        return True

    @api.onchange('property_parent_id')
    def parent_prop_change(self):
        if self.property_parent_id:
            p = self.property_parent_id
            self.street = p.street or False
            self.street2 = p.street2 or False
            self.township = p.township or False
            self.city = p.city or False
            self.state_id = p.state_id.id or False
            self.zip = p.zip or False
            self.country_id = p.country_id.id or False
            self.type_id = p.type_id.id or False

    def property_unlink(self):
        for property_rec in self:
            draft_children = self.env['account.asset'].search([
                ('id', 'in', property_rec.child_ids.ids),
                ('state', '=', 'draft'),
            ])
            property_rec.child_ids = [(5, 0, 0)]
            draft_children.unlink()
            property_rec.write({'state': 'draft'})
        return True

    def unlink(self):
        for property_rec in self:
            draft_children = self.env['account.asset'].search([
                ('id', 'in', property_rec.child_ids.ids),
                ('state', '=', 'draft'),
            ])
            property_rec.child_ids = [(5, 0, 0)]
            draft_children.unlink()
        return super().unlink()

    def write(self, vals):
        rec = super().write(vals)
        for property_rec in self:
            if property_rec.child_ids:
                child_vals = {
                    'original_value': property_rec.original_value,
                    'furnished': property_rec.furnished,
                    'ground_rent': property_rec.ground_rent,
                    'type_id': property_rec.type_id.id,
                }
                property_rec.child_ids.write(child_vals)
        return rec

    def edit_prop_wizzard(self):
        floor = []
        tower = []
        for res in self:
            prop_ids = self.search([('property_parent_id', '=', res.asset_id.id)])
            for rec in prop_ids:
                floor.append(str(rec.floor_number))
                tower.append(str(rec.tower_num))
            return {
                'name': _('Filter Wizard'),
                'res_model': 'property.wizard',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_property_id': res.id,
                    'default_floor_count': list(set(floor)),
                    'default_newtower': list(set(tower)),
                },
            }

    def split_property(self):
        for rec in self:
            if rec.state != 'cancel':
                continue
            proplist = rec.name.split('->Merge->')
            if len(proplist) > 1:
                rec.write({
                    'state': 'draft',
                    'property_manager': False,
                    'name': proplist[0],
                })
                to_update = rec.search([('name', '=', proplist[1])])
                for cur in to_update:
                    new_label_val = int(cur.label_id.name) - rec.label_id.name
                    label = self.env['property.label'].search(
                        [('name', '=', new_label_val)])
                    cur.write({'label_id': label.id or False})
            else:
                raise ValidationError(_(
                    'Please select a Property that has been Merged!'))
        return True

    def merge_prop_wizzard(self):
        self.ensure_one()
        return {
            'name': _('Merge Property'),
            'res_model': 'property.parent.merge.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_new_prop_id': self.id},
        }


class PropertyLabel(models.Model):
    _name = "property.label"
    _description = 'Property Label'
    _rec_names_search = ['name', 'code']

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s%s' % (
                str(rec.name) if rec.name else '',
                rec.code or '')

    name = fields.Integer(
        string='Number of BHK',
        required=True,
        help='Number of BHK')
    code = fields.Char(
        string='Code',
        default='BHK',
        help='Code For BHK')


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset'

    @api.depends('child_ids', 'child_ids.state')
    def _compute_available_property(self):
        for prop in self:
            prop.available_property = len([
                c for c in prop.child_ids if c.state == 'draft'])

    @api.depends('child_ids', 'child_ids.state')
    def _compute_book_property(self):
        for prop in self:
            prop.book_property = len([
                c for c in prop.child_ids if c.state == 'book'])

    label_id = fields.Many2one(
        comodel_name='property.label',
        string='Label',
        help='Label e.g. 1-BHK, 2-BHK.')
    available_property = fields.Float(
        string='Available Properties',
        compute='_compute_available_property')
    book_property = fields.Float(
        string='Booked Properties',
        compute='_compute_book_property')
    new_child_ids = fields.One2many(
        comodel_name='account.asset',
        inverse_name='property_parent_id',
        string='Child Assets')
