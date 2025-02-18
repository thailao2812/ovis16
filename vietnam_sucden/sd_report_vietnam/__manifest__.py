# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN VIETNAM REPORT',
    'category': 'SUCDEN VIETNAM REPORT',
    'version' : '16.0.1.0',
    'author': 'SUCDEN VIETNAM',
    'website': 'https://www.sucden.com',
    'depends': ['base', 'sd_report', 'sd_master_vietnam'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/shipment_view.xml',
        'views/production_analysis_view.xml',
        'views/fob_weight_franchise_view.xml',
        'views/production_analysis_line_output_view.xml',
    ],
    'assets': {

    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
