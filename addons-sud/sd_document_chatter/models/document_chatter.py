# -*- coding: utf-8 -*-
"""Gives the shared OVIS documents a chatter and tracks their workflow field.

Each class does two things and nothing else:

*  mixes in ``mail.thread`` and ``mail.activity.mixin`` so the document gains a
   message log, followers and activities;
*  re-declares its workflow field with ``tracking=True``, so every change of
   state is written into that log with the old and new value, by whom and when.

Re-declaring a field with only ``tracking=True`` keeps every other attribute --
selection values, string, default -- from the original definition. Nothing about
the field's behaviour changes; it only becomes tracked.

A note on the two field names. ``state`` is the workflow everywhere. ``status``
on the contract-side models is a different thing entirely: it holds the assigned
warehouse (Paco BWH, MBN BWH, KTN BWH, 3rd party, Ned VN). Both are tracked,
because moving a contract between warehouses is exactly the kind of change worth
a trail, but they should not be read as two versions of the same information.
"""
from odoo import fields, models


class SContract(models.Model):
    """Already carries mail.thread -- only the tracking and the view were missing."""
    _name = 's.contract'
    _inherit = ['s.contract', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)
    status = fields.Selection(tracking=True)


class KcsCriterions(models.Model):
    """Already carries mail.thread -- only the tracking and the view were missing."""
    _name = 'kcs.criterions'
    _inherit = ['kcs.criterions', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class ShippingInstruction(models.Model):
    _name = 'shipping.instruction'
    _inherit = ['shipping.instruction', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)
    status = fields.Selection(tracking=True)


class PostShipment(models.Model):
    _name = 'post.shipment'
    _inherit = ['post.shipment', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class LotKcs(models.Model):
    _name = 'lot.kcs'
    _inherit = ['lot.kcs', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class DailyConfirmation(models.Model):
    _name = 'daily.confirmation'
    _inherit = ['daily.confirmation', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class RequestStockMaterial(models.Model):
    _name = 'request.stock.material'
    _inherit = ['request.stock.material', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class TrafficContract(models.Model):
    _name = 'traffic.contract'
    _inherit = ['traffic.contract', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)
    status = fields.Selection(tracking=True)


# ---------------------------------------------------------------------------
# The two head contracts. Both already carried mail.thread, but their main form
# never rendered the chatter -- only a secondary allocation form did, which is
# why the messages looked absent from the screens people actually use.
# ---------------------------------------------------------------------------
class SaleContract(models.Model):
    """``status`` is deliberately not tracked here: on this model it is a
    non-stored related field reading ``scontract_id.status``, and tracking only
    works on stored fields. The warehouse it mirrors is already tracked at the
    source, on ``s.contract`` above, which is where the change actually happens."""
    _name = 'sale.contract'
    _inherit = ['sale.contract', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class PurchaseContract(models.Model):
    _name = 'purchase.contract'
    _inherit = ['purchase.contract', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


# ---------------------------------------------------------------------------
# Documents and master data that carry a workflow state but had no chatter at
# all. Each gains the mixins and has its state tracked.
# ---------------------------------------------------------------------------
class AccountFiscalyear(models.Model):
    _name = 'account.fiscalyear'
    _inherit = ['account.fiscalyear', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class AccountPeriod(models.Model):
    _name = 'account.period'
    _inherit = ['account.period', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class ByProductDerivable(models.Model):
    _name = 'by.product.derivable'
    _inherit = ['by.product.derivable', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class CertPre(models.Model):
    _name = 'cert.pre'
    _inherit = ['cert.pre', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class FobValue(models.Model):
    _name = 'fob.value'
    _inherit = ['fob.value', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class FxTradeRoot(models.Model):
    _name = 'fx.trade.root'
    _inherit = ['fx.trade.root', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class GradePremiumRoot(models.Model):
    _name = 'grade.premium.root'
    _inherit = ['grade.premium.root', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class MrpPeriodicalProductionCosting(models.Model):
    _name = 'mrp.periodical.production.costing'
    _inherit = ['mrp.periodical.production.costing', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class NedCertificateLicense(models.Model):
    _name = 'ned.certificate.license'
    _inherit = ['ned.certificate.license', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class NedCrop(models.Model):
    _name = 'ned.crop'
    _inherit = ['ned.crop', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class RequestPayment(models.Model):
    _name = 'request.payment'
    _inherit = ['request.payment', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class StoplossConfig(models.Model):
    _name = 'stoploss.config'
    _inherit = ['stoploss.config', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)
