# See LICENSE file for full copyright and licensing details

{
    'name': 'Property Maintenance EE',
    'version': '18.0.1.0.0',
    'category': 'Real Estate',
    'author': 'Geronimo',
    'summary': """
            You can manage maintenance of property
            maintenance management
            building maintenance
            maintenance schedule
            maintenance calendar
            maintenance process
            maintenance statistics
    """,
    'license': 'LGPL-3',
    'website': 'mailto:peterkamere@gmail.com',
    'depends': ['property_management_ee', 'maintenance'],
    'data': [
        'security/maint_security.xml',
        'security/ir.model.access.csv',
        'data/maintenanse_data_stage.xml',
        'data/mail_maintenance_template.xml',
        'views/asset_management_view.xml',
        'views/maintenance_view.xml',
    ],
    'images': ['static/description/icon.png'],
    'auto_install': False,
    'installable': True,
    'application': True,
    'price' : 49,
    'currency': 'EUR',
}
