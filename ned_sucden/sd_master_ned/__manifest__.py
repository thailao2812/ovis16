# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN NED EUDR',
    'category': 'SUCDEN NED EUDR',
    'version' : '16.0.1.0',
    'author': 'SCUDEN VIETNAM',
    'website': 'https://www.sucden.com',
    'depends': ['base', 'base_geolocalize', 'sd_master_vietnam', 'contacts_area'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/import_geojson_view.xml',
        'views/res_partner_area_view.xml',
        'views/res_partner_view.xml',
        'views/partner_multiple_point_view.xml',
        'views/supplier_master_data.xml',
        'views/menu.xml',

        'report/report.xml',

        'wizard/wizard_export_error_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
