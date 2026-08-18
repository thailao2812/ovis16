# -*- coding: utf-8 -*-
{
    'name': 'OVIS Delete Protection - Shared Documents',
    'version': '16.0.1.0.0',
    'category': 'Sucden/Tools',
    'summary': 'Applies delete protection to the shared OVIS transaction documents',
    'description': """
Registers the shared addons-sud transaction models with the delete protection
carried by ``sd_delete_protection``.

Kept separate from the mixin on purpose: the mixin and the deletion audit log
depend on nothing but ``base``, so they stay installable even where a business
module is absent or broken. Only this module carries the business dependencies,
so a problem in one of them can never take the audit log down with it.

Deliberately NOT covered here:

* ``production.plan`` -- ships in both ``sd_report`` and ``sd_india_report``;
  registered by the India module instead, so that ``sd_report`` need not be
  installed.
* ``import.data`` -- lives in ``sd_traffic``, which the India deployment does
  not install.
""",
    'author': 'Sucden Coffee',
    'depends': [
        'sd_delete_protection',
        'sd_purchase_contract',
        'sd_sale_contract',
        'sd_inventory',
        'sd_quality',
        'sd_mrp',
        'sd_security_gate',
    ],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
