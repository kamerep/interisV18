# See LICENSE file for full copyright and licensing details
from dateutil.relativedelta import relativedelta

from odoo import api, models


class PropertyDemoLoader(models.AbstractModel):
    _inherit = 'property.demo.loader'

    @api.model
    def _load_maintenance_demo(self):
        ref = self.env.ref
        core = 'property_management_ee'
        today = self._today()
        Request = self.env['maintenance.request']
        team = self.env['maintenance.team'].search([], limit=1)
        golden = ref('%s.property1' % core)
        account = golden.maint_account_id or golden.income_acc_id
        common = {'maintenance_team_id': team.id, 'account_id': account.id}
        done = Request.create(dict(common, **{
            'name': 'Leaking kitchen tap (tenant damage)',
            'property_id': ref('%s.childproperty1' % core).id,
            'tenant_id': ref('%s.demo_tenant_alice' % core).id,
            'renters_fault': True,
            'cost': 150.0,
            'request_date': today - relativedelta(days=12),
        }))
        done.stage_id = ref('maintenance.stage_3')
        done.create_invoice()
        self._register_xmlid(
            'property_maintenance_ee', 'demo_request_done', done)
        progress = Request.create(dict(common, **{
            'name': 'Air conditioner service',
            'property_id': ref('%s.childproperty2' % core).id,
            'cost': 300.0,
            'request_date': today - relativedelta(days=3),
        }))
        progress.stage_id = ref('maintenance.stage_1')
        self._register_xmlid(
            'property_maintenance_ee', 'demo_request_progress', progress)
        new = Request.create(dict(common, **{
            'name': 'Broken window in lobby',
            'property_id': golden.id,
            'request_date': today,
        }))
        self._register_xmlid(
            'property_maintenance_ee', 'demo_request_new', new)
        return True
