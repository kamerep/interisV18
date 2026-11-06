# See LICENSE file for full copyright and licensing details
from odoo.tests import common


class PropertyManagementSPTestCase(common.TransactionCase):

    def setUp(self):
        super(PropertyManagementSPTestCase, self).setUp()

    def test_property_action(self):
        # Property Created
        self.property_type = self.browse_ref(
            'property_management_ee.property_type1')
        self.partner = self.browse_ref('base.res_partner_2')
        self.property_demo = self.browse_ref("property_management_ee.property1")
        self.rent_type = self.browse_ref("property_management_ee.rent_type1")
        self.payment_term = self.browse_ref(
            'account.account_payment_term_15days')
        self.asset = self.env['account.asset'].sudo().create(
            {
                'name': 'Radhika Recidency',
                'state': self.property_demo.state,
                'street': self.property_demo.street,
                'city': self.property_demo.city,
                'country_id': self.property_demo.country_id.id,
                'state_id': self.property_demo.state_id.id,
                'zip': self.property_demo.zip,
                'original_value': self.property_demo.original_value,
                'ground_rent': self.property_demo.ground_rent,
                'furnished': self.property_demo.furnished,
                'facing': self.property_demo.facing,
                'type_id': self.property_demo.type_id.id,
                'floor': self.property_demo.floor,
                'bedroom': self.property_demo.bedroom,
                'bathroom': self.property_demo.bathroom,
                'gfa_meter': self.property_demo.gfa_meter,
                'gfa_feet': self.property_demo.gfa_feet,
                'parent_id': self.property_demo.parent_id.id,
                'property_manager': self.property_demo.property_manager.id,
                'income_acc_id': self.property_demo.income_acc_id.id,
                'rent_type_id': self.rent_type.id,
                'sale_date': '2017-07-07',
                'sale_price': 2200000.00,
                'payment_term': self.payment_term.id,
                'customer_id': self.partner.id,
                'partner_id': self.partner.id,
                'end_date': '2018-07-17',
                'purchase_price': 3200000.00,
                'recurring_rule_type': 'monthly',
            })
        self.asset.genrate_payment_enteries()
        self.asset.create_purchase_installment()
