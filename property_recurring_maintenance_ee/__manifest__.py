# See LICENSE file for full copyright and licensing details
{
    'name': 'Property Recurring Maintenance EE',
    'version': '18.0.1.1.0',
    'category': 'Real Estate',
    'summary': """
This module allows to manage the Recurring Maintenance
maintenance subscription
maintenance management
maintenance charges and invoice
maintenance account
     """,
    'license': 'LGPL-3',
    'author': 'Geronimo',
    'website': 'mailto:peterkamere@gmail.com',
    'depends': ['property_maintenance_ee'],
    'data': [
        'security/ir.model.access.csv',
        'views/property_recuring_maintenance_view.xml'
    ],
    'images': ['static/description/banner.png'],
    'demo': ['data/recurring_maintenance_data.xml', 'demo/demo_recurring.xml'],
    'auto_install': False,
    'installable': True,
    'application': True,
    'price' : 99,
    'currency': 'EUR',
}
