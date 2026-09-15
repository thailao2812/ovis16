# -*- coding: utf-8 -*-
{
    'name': 'OVIS Delete Protection - Odoo Documents',
    'version': '16.0.1.0.0',
    'category': 'Sucden/Tools',
    'summary': 'Delete protection for the standard Odoo documents OVIS runs on',
    'description': """
Extends the delete protection to the standard Odoo documents, which the OVIS
custom models were not covering.

Heads -- never deleted, in any state:

* stock.picking, account.move, account.payment, mrp.production, stock.lot

A draft journal entry may be named "Draft", "INV-00019" or "BYP/93/2026-27"
depending on how it was raised, so the rule is not keyed on the number: these
documents are cancelled, not removed. Force Delete stays available for the
cases that genuinely have to go, and records who and why.

Lines -- removable while the document is in draft, refused afterwards:

* stock.move, stock.move.line, account.move.line

The line rule looks only at the parent's state. Their own state is left alone
because Odoo deletes and recreates lines during ordinary work -- reserving
stock, editing a draft invoice, recomputing a picking -- and blocking that
would break the system on itself.

Kept as its own module so it can be switched off independently of the OVIS
protection if a standard flow turns out to need a deletion this refuses.
""",
    'author': 'Sucden Coffee',
    'depends': [
        'sd_delete_protection',
        'stock',
        'account',
        'mrp',
    ],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
