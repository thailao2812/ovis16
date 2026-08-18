# -*- coding: utf-8 -*-
{
    'name': 'OVIS India Document Chatter',
    'version': '16.0.1.0.0',
    'category': 'Sucden/Tools',
    'summary': 'Chatter and workflow tracking for the India-side documents',
    'description': """
Extends *OVIS Document Chatter* to the two documents whose form views live in
the India modules: ``production.plan`` (from sd_india_report) and
``stock.allocation`` (model in sd_purchase_contract, form in sd_india_contract).

Same treatment: mail.thread and mail.activity.mixin for the chatter, and
``state`` re-declared with tracking so every change is recorded.
""",
    'author': 'Sucden Coffee',
    'depends': [
        'mail',
        'sd_purchase_contract',
        'sd_india_report',
        'sd_india_contract',
    ],
    'data': [
        'views/document_chatter_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
