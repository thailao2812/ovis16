# -*- coding: utf-8 -*-
{
    'name': 'Format Input Number',
    'category': 'REACH TOOLS',
    'version' : '15.0.1.0',
    'author': 'REACH TECHNOLOGY',
    'website': 'https://www.reach.com.vn',
    'summary': 'Auto thousands separator while user typing. Dynamic with user-language.',
    'description': "Thousands separator",
    'depends': ['web'],
    'data': [
    ],
    'images': ['static/description/banner.jpg'],
    'assets': {
        "web.assets_backend": ["format_number/static/src/js/number_widget.js"],
    },
    'installable': True,
    'auto_install': True,
    'application': False,
    'license': 'LGPL-3',
}
