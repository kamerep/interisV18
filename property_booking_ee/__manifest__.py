# See LICENSE file for full copyright and licensing details
{
    'name': 'Property Booking EE',
    'version': '18.0.1.1.0',
    'category': 'Real Estate',
    'summary': """
        Property Management Booking System
        Booking management
        flat booking
        office booking
        apartment booking
    """,
    'description': """
        Property Management Booking System
        Booking management
        flat booking
        office booking
        apartment booking
    """,
    'license': 'LGPL-3',
    'author': 'Geronimo',
    'website': 'mailto:peterkamere@gmail.com',
    'depends': ['property_management_ee'],
    'data': [
        'security/ir.model.access.csv',
        'views/view_property_booking.xml',
        'wizard/view_merge_property_wizard.xml',
        'wizard/view_property_book_wizard.xml',
    ],
    'images': ['static/description/banner.png'],
    'auto_install': False,
    'installable': True,
    'application': True,
    'price' : 49,
    'currency': 'EUR',
}
