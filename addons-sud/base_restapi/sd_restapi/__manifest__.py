# -*- coding: utf-8 -*-
{
    'name': 'SUCDEN REST API BASE',
    'version': '1.0',
    'description': 'This module create API and Swagger Docs for SUCDEN',
    'category': 'REST API',
    'summary': "Develop your organization's own high-level REST APIs for Odoo thanks to this add-on. At the same time publish API documentation according to the Swagger structure.",
    'author': 'DEVELOP IT TEAM - SUCDEN COFFEE VN',
    "website": "https://github.com/anhsonnt/Sucden-Smart-Factory",
    'licence': 'SDC-1',
    'depends': [
        'base_rest',
    ],
    "external_dependencies": {
        "python": [
            "cachetools",
            "cerberus",
            "pyquerystring",
            "parse-accept-language",
            "apispec"
        ]
    },
    'data':[
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': True,
}
