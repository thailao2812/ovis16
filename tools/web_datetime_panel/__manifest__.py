# -*- coding: utf-8 -*-
{
    'name': 'Datetime Panel',
    'category': 'REACH Tools',
    'version' : '16.0.1.0',
    'author': 'REACH TECHNOLOGY',
    'website': 'https://reach.com.vn/',
    'description': """
    """,
    'depends': [
        'web',
    ],
    'assets': {
        'web.assets_backend': [
            'web_datetime_panel/static/src/DatetimeFilterItem.js',
            'web_datetime_panel/static/src/DatetimeFilterItem.xml',
            'web_datetime_panel/static/src/DatetimeFilterItem.scss',
            'web_datetime_panel/static/src/DatetimeControlPanel.js',
            'web_datetime_panel/static/src/DatetimeControlPanel.xml',
            'web_datetime_panel/static/src/search_model.js',
            'web_datetime_panel/static/src/utils.js',
        ],
    },
    'data': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
