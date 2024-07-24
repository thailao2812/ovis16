# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN SALES CONTRACT',
    'category': 'REACH contract',
    'version' : '15.0.1.0',
    'author': 'REACH TECHNOLOGY',
    'website': 'https://www.reach.com.vn',
    'depends': ['base','stock', 'account','sd_master'],
    'description': """
    """,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        
        'wizard/wizrad_invoice_view.xml',
        #'data/example_users_data.xml',
        
        
        'views/s_contract_view.xml',
        
        'views/s_contract_view.xml',
        'views/shipping_instruction.xml',
        'views/sale_contract_view.xml',
        'views/s_p_allocation_qc.xml',
        'views/delivery_order_view.xml',
        'views/transfer_order.xml',
        
        'views/port_shipment.xml',
        'views/master_data_view.xml',
        'views/daily_confirmation.xml',
        'views/shipping_split.xml',
        #'views/ned_certificate_license_views.xml',
        
        'views/menu.xml',
        
        #Report
        # 'report/report_view.xml',
        
        #Data
        'data/ir_sequence.xml',
        'data/group.xml'

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
