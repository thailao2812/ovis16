# -*- coding: utf-8 -*-
{
    'name': 'OVIS India Delete Protection',
    'version': '16.0.1.0.0',
    'category': 'Sucden/Tools',
    'summary': 'Prevents deletion of committed transactions on the India models',
    'description': """
Extends *OVIS Delete Protection* to the India-specific transaction models.

Same rule: once a record carries a sequence number, or its state has moved past
draft, it must be cancelled rather than deleted. Several India models open in
``new`` or ``requested`` rather than ``draft``, which is declared per model.

This module also registers ``production.plan``, which ships in both
``sd_report`` and ``sd_india_report``. It is claimed here so that the India
deployment -- which installs only ``sd_india_report`` -- gets the protection
without having to install ``sd_report``.

Depends on ``sd_delete_protection`` for the mixin only, not on
``sd_delete_protection_core``: the two sets of registrations are independent
and either can be installed without the other.
""",
    'author': 'Sucden Coffee',
    'depends': [
        'sd_delete_protection',
        'sd_india_report',
        'sd_india_contract',
        'sd_india_master',
        'sd_india_mrp',
        'sd_india_quality_control',
        'sd_india_security_gate',
        'sd_india_traffic',
    ],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
