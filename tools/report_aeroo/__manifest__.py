# -*- encoding: utf-8 -*-
{
    'name': 'Aeroo Reports',
    'category': 'Besco Tool',
    'description': '''
        Module này điều chỉnh lại từ module gốc của aeroo report trên version 11. 
        Nội dung điều chỉnh bao gồm fix lỗi của aeroo và bỏ sung thêm tính năng mới.
        Để sử dụng các chức năng mới càn đảm bảo 2 module report_pdf_preview và web_utils đã được cài đặt.
    ''',
    'depends': ['base'],
    'external_dependencies': {
        'python': [
            'tempfile',
            'subprocess'
        ],
    },
    'data': [
        "security/ir.model.access.csv",
        "data/report_aeroo_data.xml",
        "views/report_view.xml",
        "views/report_print_by_action.xml",
    ],
    'assets': {
        "web.assets_backend": ["report_aeroo/static/src/js/action_manager_report.js"],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
