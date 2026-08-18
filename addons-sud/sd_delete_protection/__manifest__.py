# -*- coding: utf-8 -*-
{
    'name': 'OVIS Delete Protection',
    'version': '16.0.1.0.0',
    'category': 'Sucden/Tools',
    'summary': 'Delete protection mixin and system-wide deletion audit log',
    'description': """
Delete Protection
=================

A record can no longer be deleted once either is true:

* it has been issued a sequence number, or
* its state / status has moved past draft.

The rule is carried by ``sd.delete.protection.mixin`` and applied to the shared
transaction models. Everything past draft must be cancelled instead of deleted,
so that document numbering stays complete and auditable.

Members of *Force Delete Records* may still delete, but only from a session
that explicitly sets ``sd_force_delete`` in the context -- the group alone is
not enough, and the context flag alone is not enough.

Deletion Audit Log
==================

Separately from the protection, every deletion on the system is recorded in
``sd.delete.log``: which model and record, who deleted it, when, the number and
status it carried, and a snapshot of its stored values. Deletions that only
succeeded because the protection was bypassed are flagged, so they can be
reviewed on their own.

The log is append-only. It cannot be edited by anyone, and only a system
administrator can purge it, deliberately.

Tuning, via System Parameters:

* ``sd_delete_log.excluded_models`` -- comma separated models to leave out, on
  top of the built-in technical denylist.
* ``sd_delete_log.max_snapshot_records`` -- above this many records in a single
  deletion, entries are written without a snapshot (default 200).
* ``sd_delete_log.log_uninstall`` -- set to log module-uninstall deletions too;
  off by default because uninstalling produces thousands of rows.
""",
    'author': 'Sucden Coffee',
    # Nothing but base on purpose. The audit log is a system-wide facility and
    # must never be blocked by a business module that is absent or broken.
    # Business-model registrations live in sd_delete_protection_core and
    # sd_india_delete_protection.
    'depends': ['base'],
    'data': [
        'security/delete_protection_security.xml',
        'security/ir.model.access.csv',
        'views/delete_log_views.xml',
        'wizard/force_delete_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
