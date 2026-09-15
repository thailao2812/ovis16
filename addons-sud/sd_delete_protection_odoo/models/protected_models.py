# -*- coding: utf-8 -*-
"""Delete protection for the standard Odoo documents OVIS runs on.

Two different rules apply here, and the split is deliberate.

**Document heads** -- picking, journal entry, payment, manufacturing order, lot
-- are never deleted, in any state. Not "once numbered" and not "once posted":
a draft journal entry here may be called "Draft", "INV-00019" or
"BYP/93/2026-27" depending on how it was raised, so a rule keyed on the number
would let some through and refuse others for reasons that are not true. The
policy is simply that these documents get cancelled, never removed, and
`_protect_never_delete` says exactly that. Force Delete remains the way out
when a record really has to go, and it records who and why.

**Lines** -- stock moves, move lines, journal items -- get the parent rule and
nothing else: they may be removed while their document is still in draft, and
not afterwards. Their own state is deliberately left unchecked, because Odoo
itself deletes and recreates them constantly during normal work: reserving and
unreserving stock, editing a draft invoice, recomputing a picking. A line can
sit in state ``done`` while its picking is still being assembled, so judging a
line by its own state would refuse operations the system performs on itself.
Counted in the Odoo 16 source: 23 places delete an account.move, 12 a
stock.move, 6 a stock.move.line. Every one of those has to keep working.
"""
from odoo import models


# ---------------------------------------------------------------------------
# Document heads -- never deleted, in any state
# ---------------------------------------------------------------------------
class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'sd.delete.protection.mixin']

    _protect_never_delete = True


class AccountMove(models.Model):
    """``status`` on this model is an OVIS addition holding something else, so
    only ``state`` is consulted."""
    _name = 'account.move'
    _inherit = ['account.move', 'sd.delete.protection.mixin']

    _protect_never_delete = True
    _protect_state_fields = ('state',)


class AccountPayment(models.Model):
    """``name`` and ``state`` are delegated to the journal entry through
    ``_inherits``. They are not columns on this table, but the ORM resolves them
    on read, which is all the protection needs."""
    _name = 'account.payment'
    _inherit = ['account.payment', 'sd.delete.protection.mixin']

    _protect_never_delete = True
    _protect_state_fields = ('state',)


class MrpProduction(models.Model):
    _name = 'mrp.production'
    _inherit = ['mrp.production', 'sd.delete.protection.mixin']

    _protect_never_delete = True


class StockLot(models.Model):
    """No workflow state of its own; the never-delete policy is the whole rule."""
    _name = 'stock.lot'
    _inherit = ['stock.lot', 'sd.delete.protection.mixin']

    _protect_never_delete = True
    _protect_state_fields = ()


# ---------------------------------------------------------------------------
# Lines -- judged only by the state of the document they belong to
# ---------------------------------------------------------------------------
class StockMove(models.Model):
    _name = 'stock.move'
    _inherit = ['stock.move', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_state_fields = ()
    _protect_parent_field = 'picking_id'


class StockMoveLine(models.Model):
    """Pointed at the picking rather than at the move: it is the picking whose
    state a user recognises, and it gives a message they can act on."""
    _name = 'stock.move.line'
    _inherit = ['stock.move.line', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_state_fields = ()
    _protect_parent_field = 'picking_id'


class AccountMoveLine(models.Model):
    _name = 'account.move.line'
    _inherit = ['account.move.line', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_state_fields = ()
    _protect_parent_field = 'move_id'
