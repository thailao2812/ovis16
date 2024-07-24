# -*- coding: utf-8 -*-
{
    "name": "Search time range",
    "version": "14.0.1",
    'author': 'Pham Duy Tuong',
    "summary": "Easy search time range in listview, pivot, kanban",
    'license': 'LGPL-3',
    "category": "Gearment",
    "depends": ['web'],
    "data": [
        # "templates/assets.xml",
    ],
    # 'qweb': ['static/src/xml/'],
    'assets': {
            'web.assets_backend': [
                'quick_search_time_range/static/src/js/date_range_gm.js',
                'quick_search_time_range/static/src/js/control_panel.js',
                'quick_search_time_range/static/src/js/daterangepicker_min.js',
                'quick_search_time_range/static/src/xml/template.xml',
            ],
            # 'web.assets': [
            #     'quick_search_time_range/static/src/xml/template.xml',
            # ],
        },
    "installable": True,
}
