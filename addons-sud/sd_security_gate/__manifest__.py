# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN Security gate',
    'category': 'REACH SUCDEN',
    'version' : '15.0.1.0',
    'author': 'REACH TECHNOLOGY',
    'website': 'https://www.reach.com.vn',
    'depends': ['sd_master','sd_inventory', 'sd_quality'],
    'description': """
    """,
    'data': [
        'data/ir_sequence.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/security_gate_queue_view.xml',
        'views/security_gate_queue_exstore_view.xml',
        'views/stock_picking.xml',
        'views/res_company_view.xml',
        'views/report_security_gate_qc.xml',
        'views/report_security_gate.xml',
        'views/menu.xml',
        
        #Report
        # 'report/report_security_gate_qc.xml.xml',
        
        #Data
        #'data/ir_sequence.xml'

    ],
    
    'installable': True,
    'auto_install': False,
    'application': False,
}
