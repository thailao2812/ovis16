# -*- coding: utf-8 -*-
{
    'name': 'REACH SEQUENCE',
    'category': 'REACH ERP BASE',
    'version' : '16.0.1.0',
    'author': 'REACH TECHNOLOGY',
    'website': 'https://www.reach.com.vn',
    'description': """
    """,
    'depends': ['base','sd_master'], #THANH depend sale & purchase to change odoo sequence (using sql to change)
    'data': [
        "security/ir.model.access.csv",
        "views/ir_sequence_view.xml",
    ],
    'assets': {
        "web.assets_backend": [
            "reach_sequence/static/src/js/no_delete_one2many.js",
            "reach_sequence/static/src/js/no_delete_list_renderer.js",
            "reach_sequence/static/src/xml/no_delete_list_renderer.xml",
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
