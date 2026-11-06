# See LICENSE file for full copyright and licensing details

{
    'name': 'Commission Management for Property Management System EE',
    'version': '18.0.1.0.0',
    'category': 'Real Estate',
    'summary': """
        property commission
        asset commission
        tenancy commission
        tenant commission
        Commission Management for Property Management
     """,
    'description': """
        property commission
        asset commission
        tenancy commission
        tenant commission
        Commission Management for Property Management
     """,
    'author': 'Geronimo',
    'website': 'mailto:peterkamere@gmail.com',
    'depends': ['property_management_ee'],
    'data': [
            'data/commission_seq.xml',
            'security/res_groups.xml',
            'security/ir.model.access.csv',
            'views/property_commission_view.xml',
            'views/property_res_partner_views.xml',
            'report/commission_report_template2.xml',
            # 'views/report_configuration.xml',

    ],
    'license': 'LGPL-3',
    'auto_install': False,
    'installable': True,
    'application': True,
    'price' : 99,
    'currency': 'EUR',
}
