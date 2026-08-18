# -*- coding: utf-8 -*-
{
    'name': 'OVIS Document Chatter',
    'version': '16.0.1.0.0',
    'category': 'Sucden/Tools',
    'summary': 'Chatter and workflow tracking on the shared OVIS documents',
    'description': """
Adds a chatter -- message log, followers and activities -- to the shared OVIS
transaction documents that did not have one, and tracks their workflow field so
every change of state is recorded with the old and new value, by whom and when.

Documents covered:

* s.contract, kcs.criterions          (already had mail.thread; the tracking and
                                       the chatter block in the form were missing)
* shipping.instruction, post.shipment, lot.kcs, daily.confirmation,
  request.stock.material, traffic.contract

Fields tracked: ``state`` everywhere, plus ``status`` on the contract-side
models. Note that ``status`` there holds the assigned warehouse rather than a
workflow stage -- it is tracked because reassigning a warehouse is worth a
trail, not because it duplicates ``state``.

This complements the deletion audit log in ``sd_delete_protection``: together
they cover what changed on a document and what was removed outright.
""",
    'author': 'Sucden Coffee',
    'depends': [
        'mail',
        'sd_master',
        'sd_account',
        'sd_pur_sales',
        'sd_sale_contract',
        'sd_purchase_contract',
        'sd_quality',
        'sd_inventory',
        'sd_traffic',
    ],
    'data': [
        'views/document_chatter_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
