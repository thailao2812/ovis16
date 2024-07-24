{

    'name': 'REACH RESTFUL API',
    "version": "16.0",
    'author': 'reach',
    'category': 'REACH',
    'website': '',
    'summary': """
        REACH RESTFUL API
    """,
    "depends": [
        # 'ned_stock_vn',
        # 'ned_contract_vn',
        'base',
        'account',
    ],

    'description': """
        
    """,
    "data": [
        'security/ir.model.access.csv',
        'security/api_security.xml',
        'data/api_restful_data.xml',
        # 'view/res_partner_views.xml',
        'view/account_invoice_views.xml',
        'view/stock_picking_type_views.xml',
        'view/stock_picking_views.xml',
        'view/ir_cron_views.xml',
        'view/account_journal_views.xml',
        'view/api_synchronize_data_views.xml',
        'view/api_synchronize_data_config_views.xml',
        'view/menu.xml',
    ],
    "license": "",

    'installable': True,
}
