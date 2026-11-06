# See LICENSE file for full copyright and licensing details
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class PropertyDemoLoader(models.AbstractModel):
    _inherit = 'property.demo.loader'

    @api.model
    def _load_maintenance_demo(self):
        """Team, equipment per property and requests in every stage.

        Shows how maintenance links together: equipment belongs to a
        property, a request on the equipment inherits the property, the
        current tenant is filled in from the running tenancy, and the cost
        feeds the property's Maintenance Cost / Net Income.
        """
        ref = self.env.ref
        core = 'property_management_ee'
        module = 'property_maintenance_ee'
        today = self._today()
        now = fields.Datetime.now()
        Request = self.env['maintenance.request']
        admin = ref('base.user_admin')

        golden = ref('%s.property1' % core)
        grimfield = ref('%s.childproperty1' % core)
        dawson = ref('%s.childproperty2' % core)
        diamond = ref('%s.property2' % core)
        cleveland = ref('%s.childproperty4' % core)
        plazza = ref('%s.childproperty5' % core)
        account = golden.maint_account_id or golden.income_acc_id

        team = self.env['maintenance.team'].create({
            'name': 'Property Maintenance',
            'member_ids': [(6, 0, admin.ids)],
        })
        self._register_xmlid(module, 'demo_team_property', team)
        category = self.env['maintenance.equipment.category'].create({
            'name': 'Building Services',
            'technician_user_id': admin.id,
        })
        self._register_xmlid(module, 'demo_category_building', category)

        Equipment = self.env['maintenance.equipment']
        equipment = {}
        for key, name, prop, model, serial, cost in [
            ('lift', 'Passenger Lift', golden, 'Schindler 3300', 'LFT-0091',
             42000.0),
            ('generator', 'Standby Generator 60 kVA', golden,
             'Perkins 1103A', 'GEN-2207', 18500.0),
            ('pump', 'Borehole Water Pump', diamond, 'Grundfos SP 5A',
             'PMP-1180', 3200.0),
            ('ac', 'Split Air Conditioner', dawson, 'Daikin FTXM35',
             'AC-35-7781', 1100.0),
            ('heater', 'Electric Water Heater', grimfield,
             'Ariston Pro 100L', 'WH-100-342', 450.0),
            ('alarm', 'Smoke Alarm System', cleveland, 'Kidde FireX',
             'SMK-5520', 600.0),
        ]:
            rec = Equipment.create({
                'name': name,
                'category_id': category.id,
                'property_id': prop.id,
                'maintenance_team_id': team.id,
                'technician_user_id': admin.id,
                'model': model,
                'serial_no': serial,
                'cost': cost,
                'effective_date': today - relativedelta(years=2),
                'location': prop.name,
            })
            equipment[key] = rec
            self._register_xmlid(module, 'demo_equipment_%s' % key, rec)

        common = {'maintenance_team_id': team.id, 'account_id': account.id,
                  'user_id': admin.id}

        # Corrective, tenant's fault, repaired and invoiced to the tenant
        done = Request.create(dict(common, **{
            'name': 'Leaking kitchen tap (tenant damage)',
            'property_id': grimfield.id,
            'tenant_id': ref('%s.demo_tenant_alice' % core).id,
            'renters_fault': True,
            'cost': 150.0,
            'request_date': today - relativedelta(days=12),
            'description': 'Tap handle broken by the tenant; replaced.',
        }))
        done.stage_id = ref('maintenance.stage_3')
        done.create_invoice()
        self._register_xmlid(module, 'demo_request_done', done)

        # Corrective on equipment, in progress (property comes from it)
        progress = Request.create(dict(common, **{
            'name': 'Air conditioner service',
            'equipment_id': equipment['ac'].id,
            'cost': 300.0,
            'request_date': today - relativedelta(days=3),
            'schedule_date': now + relativedelta(days=1),
            'duration': 2.0,
        }))
        progress.stage_id = ref('maintenance.stage_1')
        self._register_xmlid(module, 'demo_request_progress', progress)

        # New, unscheduled, on the building itself
        new = Request.create(dict(common, **{
            'name': 'Broken window in lobby',
            'property_id': golden.id,
            'request_date': today,
            'priority': '2',
        }))
        self._register_xmlid(module, 'demo_request_new', new)

        # Preventive and recurring (Odoo creates the next one when done)
        lift = Request.create(dict(common, **{
            'name': 'Quarterly lift inspection',
            'equipment_id': equipment['lift'].id,
            'maintenance_type': 'preventive',
            'recurring_maintenance': True,
            'repeat_interval': 3,
            'repeat_unit': 'month',
            'repeat_type': 'forever',
            'cost': 250.0,
            'request_date': today,
            'schedule_date': now + relativedelta(days=7),
            'duration': 3.0,
        }))
        self._register_xmlid(module, 'demo_request_lift', lift)
        generator = Request.create(dict(common, **{
            'name': 'Monthly generator service',
            'equipment_id': equipment['generator'].id,
            'maintenance_type': 'preventive',
            'recurring_maintenance': True,
            'repeat_interval': 1,
            'repeat_unit': 'month',
            'repeat_type': 'forever',
            'cost': 120.0,
            'request_date': today,
            'schedule_date': now + relativedelta(days=2),
            'duration': 1.5,
        }))
        self._register_xmlid(module, 'demo_request_generator', generator)
        alarm = Request.create(dict(common, **{
            'name': 'Annual smoke alarm test',
            'equipment_id': equipment['alarm'].id,
            'maintenance_type': 'preventive',
            'recurring_maintenance': True,
            'repeat_interval': 1,
            'repeat_unit': 'year',
            'repeat_type': 'forever',
            'cost': 80.0,
            'request_date': today,
            'schedule_date': now + relativedelta(days=20),
            'duration': 1.0,
        }))
        self._register_xmlid(module, 'demo_request_alarm', alarm)

        # Corrective, owner's cost, repaired last month
        pump = Request.create(dict(common, **{
            'name': 'Water pump motor replaced',
            'equipment_id': equipment['pump'].id,
            'cost': 420.0,
            'request_date': today - relativedelta(days=35),
            'schedule_date': now - relativedelta(days=33),
            'duration': 4.0,
        }))
        pump.stage_id = ref('maintenance.stage_3')
        self._register_xmlid(module, 'demo_request_pump', pump)

        # High priority, blocked while waiting for parts
        heater = Request.create(dict(common, **{
            'name': 'Water heater not heating',
            'equipment_id': equipment['heater'].id,
            'cost': 180.0,
            'priority': '3',
            'request_date': today - relativedelta(days=2),
            'schedule_date': now + relativedelta(days=3),
            'duration': 1.5,
            'description': 'Thermostat ordered, waiting for delivery.',
        }))
        heater.stage_id = ref('maintenance.stage_1')
        heater.kanban_state = 'blocked'
        self._register_xmlid(module, 'demo_request_heater', heater)

        # Move-out damage on a closed tenancy, billed and paid
        eva = self.env.ref('%s.demo_tenant_eva' % core)
        moveout = Request.create(dict(common, **{
            'name': 'Repaint walls after move-out',
            'property_id': plazza.id,
            'tenant_id': eva.id,
            'renters_fault': True,
            'cost': 350.0,
            'request_date': today - relativedelta(months=11),
        }))
        moveout.stage_id = ref('maintenance.stage_3')
        moveout.create_invoice()
        self._post_invoice(moveout.invoice_id)
        self._pay_invoice(moveout.invoice_id)
        self._register_xmlid(module, 'demo_request_moveout', moveout)
        return True
