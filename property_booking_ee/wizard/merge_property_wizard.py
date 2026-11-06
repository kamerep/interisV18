# See LICENSE file for full copyright and licensing details

from odoo import _, models
from odoo.exceptions import ValidationError


class MergePropertyWizard(models.TransientModel):
    _name = 'merge.property.wizard'
    _description = 'Merge properties'

    def merge_property(self):
        """
        This Method is used to merge sub properties
        from Sub Properties menu.
        """
        context = dict(self._context or {})
        property_obj = self.env['property.created']
        if context.get('active_ids', []):
            if len(context['active_ids']) <= 1:
                raise ValidationError(_("Please select atleast two properties."))
            data_prop = []
            property_rec = property_obj.browse(context['active_ids'])
            for propert_brw in property_rec:
                data_prop += propert_brw.read(
                    ['state', 'parent_id', 'floor_number'])
            for data in data_prop:
                if not data['parent_id']:
                    raise ValidationError(
                        _("Please select sub properties. \n \
                        Not parent property!"))
            states = [data['state'] for data in data_prop if
                      data['state'] != 'draft']
            if states:
                raise ValidationError(
                    _("Only Available state properties are allowed to be \
                    merged!"))
            parents = list(set([x['parent_id'][0] for x in data_prop]))
            if len(parents) != 1:
                raise ValidationError(
                    _("Please select sub properties from the same Parent \
                    property!"))
            check_property = False
            maxm = 0
            prop_f_no = 0
            prop_p_no = False
            for prop in property_rec:
                if not check_property:
                    check_property = prop
                    prop_f_no = int(prop.floor_number)
                    prop_p_no = str(prop.prop_number)
                    maxm = int(prop.label_id.name)
                    continue
                maxm += int(prop.label_id.name)
                vals = {
                    'name': prop.name + "->" + "Merge" + "->"
                    + check_property.name,
                    'state': 'cancel',
                }
                floor_no = list(set([x['floor_number'][0] for x in data_prop]))
                if len(floor_no) != 1:
                    if int(prop.floor_number) in (prop_f_no + 1,
                                                  prop_f_no - 1) and \
                            str(prop.prop_number) == \
                            prop_p_no:
                        prop.write(vals)
                    else:
                        raise ValidationError(
                            _('Please select sub properties from '
                            'the same Floors!'))
                prop.write(vals)
            requ_id = self.env['property.label'].search(
                [('name', '=', int(maxm))])

            label = False
            if not requ_id:
                label_obj = self.env['property.label']
                vals_label = {
                    'name': maxm,
                    'code': 'BHK'
                }
                label = label_obj.create(vals_label)
                check_property.write({'label_id': label.id})
            # if len(requ_id.ids) != 1 and int(maxm) != 0:
            #     raise ValidationError(
            #         _('Please Create label of %s ' % (
            #             str(maxm) + " " + str(prop.label_id.code)))
            #     )
        return {'type': 'ir.actions.act_window_close'}
