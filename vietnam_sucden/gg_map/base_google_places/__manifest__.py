# -*- coding: utf-8 -*-
{
    'name': 'Base Google Places',
    'version': '16.0.2.0.4',
    'author': 'Yopi Angi',
    'license': 'AGPL-3',
    'maintainer': 'Yopi Angi<yopiangi@gmail.com>',
    'support': 'yopiangi@gmail.com',
    'category': 'Hidden',
    'description': ''',
Base of Google Places integration
=================================

A base module for integrating Google Places into Odoo.
This module extends the Google Maps Odoo integration and focuses specifically on integrating with the Google Places service.
    ''',
    'depends': ['web_view_google_map', 'web_widget_google_map'],
    'data': [
        'data/google_places_type.xml',
        'security/ir.model.access.csv',
        'views/google_places_type.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'base_google_places/static/src/views/**/*',
            'base_google_places/static/src/widgets/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'active': True,
    'license': 'AGPL-3',
}
