# -*- coding: utf-8 -*-
{
    "name": "MNS Date Search",
    "version": "16.0.1",
    'author': 'Pham Duy Tuong',
    "summary": "Easy search time range in listview, pivot, kanban",
    'license': 'LGPL-3',
    "depends": ['web'],
    "data": [
        # "templates/assets.xml",
    ],
    # 'qweb': ['static/src/xml/'],
    'assets': {
            'web.assets_backend': [
                'mns_date_search/static/src/js/date_range_gm.js',
                'mns_date_search/static/src/js/control_panel.js',
                'mns_date_search/static/src/js/daterangepicker_min.js',
                'mns_date_search/static/src/xml/template.xml',
            ]
        },
    "installable": True,
}
