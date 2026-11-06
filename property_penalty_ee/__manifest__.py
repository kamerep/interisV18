# See LICENSE file for full copyright and licensing details
{
    'name': 'Property Penalty EE',
    'version': '18.0.1.1.0',
    'category': 'Real Estate',
    'summary': """
        This module will add the Penalty Feature in the Tenancy Rent
        late payment penalty
        late payment charges
        rent penalty
    """,
    'license': 'LGPL-3',
    'author': 'Geronimo',
    'website': 'mailto:peterkamere@gmail.com',
    'depends': ['property_management_ee'],
    'demo': ['demo/demo_penalty.xml'],
    'data': [
        "views/property_penalty_view.xml"
    ],
    'images': ['static/description/banner.png'],
    'auto_install': False,
    'installable': True,
    'application': True,
    'price' : 49,
    'currency': 'EUR',
}
