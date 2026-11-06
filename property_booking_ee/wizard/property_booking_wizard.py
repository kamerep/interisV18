# See LICENSE file for full copyright and licensing details
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PropertWizard(models.TransientModel):
    _name = "property.wizard"
    _description = 'Property Wizard'

    @api.model
    def get_floor(self):
        """
        This Method is used to show floors from active property.
        """
        context = dict(self._context or {})
        rec = []
        if context.get('default_floor_count', False):
            for floor_rec in range(
                    1, len(context['default_floor_count']) + 1):
                res = (str(floor_rec), str(floor_rec))
                rec.append(res)
        return rec

    @api.model
    def get_tower(self):
        """
        This Method is used to show towers
        from active property.
        """
        context = dict(self._context or {})
        rec = []
        if 'default_newtower' in context:
            for tower_rec in context['default_newtower']:
                res = (str(tower_rec), str(tower_rec))
                rec.append(res)
        return rec

    property_created_ids = fields.Many2many(
        comodel_name='property.created',
        relation='rel_wizz_id',
        column1='wizz_id',
        column2='propert_id',
        string='Property Line')
    property_id = fields.Many2one(
        comodel_name='property.created',
        string='Property')
    tower = fields.Selection(
        'get_tower',
        string='Tower',
        help='Prefix Or First Letter Of Tower.')
    newtower = fields.Char(
        string='Prefix Of Tower')
    floor_count = fields.Char(
        string='Number Of Floor',
        help='Number Of Tower.')
    floor = fields.Selection(
        'get_floor',
        string='Floor No.')

    @api.onchange('property_id')
    def property_change(self):
        """
        This Method is used to set child properties
        on change ofproperty_id.
        """
        if self.property_id:
            property_id2 = self.property_id.asset_id.id
            prop_ids = self.env['property.created'].search(
                [('property_parent_id', '=', property_id2)])
            self.property_created_ids = prop_ids.ids

    def property_method(self):
        res = []
        context = dict(self._context)
        for property_rec in self:
            if property_rec.floor:
                for rec in property_rec.property_created_ids:
                    old_name = rec.name
                    bool_name = old_name.startswith(str(property_rec.tower))
                    if int(rec.floor_number) == int(property_rec.floor) and \
                            bool_name and rec.state != 'cancel':
                        res.append(rec.id)
                    context.update({'result3': res})

        return {
            'name': _('Property Wizard'),
            'res_model': 'sub.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_property_created_merged_ids':
                        context.get('result3')},
        }


class PropertyParentMergeWizard(models.TransientModel):
    _name = "property.parent.merge.wizard"
    _description = 'Property Parent Merge Wizard'

    new_prop_id = fields.Many2one(
        comodel_name='property.created',
        string='Property')
    new_property_created_ids = fields.Many2many(
        comodel_name='property.created',
        relation='rel_new_wizz_id',
        column1='new_wizz_id',
        column2='new_propert_id',
        string='Property Line123')
    main_property_id = fields.Many2one(
        comodel_name='property.created',
        string='Main Property')

    def property_merge_parent(self):
        """
        This method is used to merge child properties
        from property form view.
        """
        data_prop = []
        for rec in self:
            activeids = rec.new_property_created_ids
            mainid = rec.main_property_id

            if mainid.id:
                if len(activeids.ids) == 0:
                    raise ValidationError(
                        _("Please select atleast one property for merge."))
            if activeids.ids:
                for rec_brw in activeids:
                    data_prop += rec_brw.read(['state',
                                               'property_parent_id', 'floor_number'])
                for main_rec_brw in mainid:
                    data_prop += main_rec_brw.read(
                        ['state', 'property_parent_id', 'floor_number'])

                for data in data_prop:
                    if not data['property_parent_id']:
                        raise ValidationError(
                            _("Please select sub properties. \n Not \
                            parent property!"))
                states = [data['state']
                          for data in data_prop if data['state'] != 'draft']
                if states:
                    raise ValidationError(
                        _("Only Available state properties are allowed \
                        to be merged!"))
                parents = list(set([x['property_parent_id'][0] for x in data_prop]))
                if len(parents) != 1:
                    raise ValidationError(
                        _("Please select sub properties from the same Parent \
                        property!"))
                check_property = False
                maxm = 0
                prop_f_no = 0
                prop_p_no = False
                for main_prop in mainid:
                    check_property = main_prop
                    prop_f_no = int(main_prop.floor_number)
                    prop_p_no = str(main_prop.prop_number)
                    if main_prop.label_id:
                        maxm = int(main_prop.label_id.name)
                for prop in activeids:
                    maxm += int(prop.label_id.name)
                    vals = {
                        'name': prop.name + "->" + "Merge" + "->"
                        + check_property.name,
                        'state': 'cancel',
                    }

                    floor_no = list(set(x['floor_number'] or '' for x in data_prop))
                    if len(floor_no) != 1:
                        if int(prop.floor_number) in (prop_f_no + 1,
                                                      prop_f_no - 1) and \
                                str(prop.prop_number)\
                                == prop_p_no:
                            prop.write(vals)
                        else:
                            raise ValidationError(
                                _('Please select sub properties from the same '
                                  'Floors!'))
                    prop.write(vals)
                label = self.env['property.label'].search(
                    [('name', '=', int(maxm))], limit=1)
                if not label:
                    label = self.env['property.label'].create(
                        {'name': maxm, 'code': 'BHK'})
                check_property.write({'label_id': label.id})
                # if len(requ_id.ids) != 1 and int(maxm) != 0:
                #     raise ValidationError(
                #         _('Please Create label of %s ' % (
                #             str(maxm) + " " + str(prop.label_id.code))))

        return {'type': 'ir.actions.act_window_close'}


class SubWizard(models.TransientModel):
    _name = "sub.wizard"
    _description = 'Sub Property Wizard'

    property_created_merged_ids = fields.Many2many(
        comodel_name='property.created',
        relation='rel_wizz_id21',
        column1='wizz_id21',
        column2='propert_id21',
        string='Property Line')
    name_prop_name = fields.Char(
        string='New Name Of Property',
        help='New Name Of Property.')
    is_other = fields.Boolean(
        string='Is Shop',
        help='Check if it is other property.')
    furnish = fields.Selection(
        [('none', 'None'),
         ('semi_furnished', 'Semi Furnished'),
         ('full_furnished', 'Full Furnished')],
        string='Furnishing',
        default='full_furnished',
        help='Furnishing.')

    def sub_method(self):
        """
        This method is used to update property values.
        """
        # if self._context is None:
        #     self._context = {}
        for res in self:
            label_change = False
            for rec in res.property_created_merged_ids:
                if not res.is_other:
                    label_change = rec.label_id.id
                old_name = rec.name
                new_name = old_name.replace(
                    str(rec.tower_num), str(res.name_prop_name))
                stval = {'name': new_name,
                         'tower_num': res.name_prop_name,
                         'furnished': res.furnish,
                         'property_manager': rec.property_manager.id,
                         'state': rec.state,
                         'label_id': label_change,
                         }
                rec.write(stval)
        return True
