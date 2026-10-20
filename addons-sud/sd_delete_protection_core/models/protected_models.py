# -*- coding: utf-8 -*-
"""Applies the delete protection to the shared OVIS transaction models.

Every class below only declares configuration -- the behaviour lives in
``sd.delete.protection.mixin``. Adding a new model is three lines.

Two rules to respect when extending this file:

*  ``_protect_sequence_field`` must only name a field that really receives a
   generated sequence. On models where ``name`` is an ordinary label, leave it
   as ``None`` or the label would be read as a sequence and block every delete.
*  Line models set ``_protect_sequence_field = None`` and point
   ``_protect_parent_field`` at their parent document.
"""
from odoo import models


# ---------------------------------------------------------------------------
# Documents that generate a sequence into `name`
# ---------------------------------------------------------------------------
class PurchaseContract(models.Model):
    _name = 'purchase.contract'
    _inherit = ['purchase.contract', 'sd.delete.protection.mixin']


class SaleContract(models.Model):
    _name = 'sale.contract'
    _inherit = ['sale.contract', 'sd.delete.protection.mixin']


class DeliveryOrder(models.Model):
    _name = 'delivery.order'
    _inherit = ['delivery.order', 'sd.delete.protection.mixin']


class PostShipment(models.Model):
    _name = 'post.shipment'
    _inherit = ['post.shipment', 'sd.delete.protection.mixin']


class RequestMaterials(models.Model):
    _name = 'request.materials'
    _inherit = ['request.materials', 'sd.delete.protection.mixin']


class RequestStockMaterial(models.Model):
    _name = 'request.stock.material'
    _inherit = ['request.stock.material', 'sd.delete.protection.mixin']


class MrpOperationResult(models.Model):
    _name = 'mrp.operation.result'
    _inherit = ['mrp.operation.result', 'sd.delete.protection.mixin']


class LotKcs(models.Model):
    _name = 'lot.kcs'
    _inherit = ['lot.kcs', 'sd.delete.protection.mixin']


class KcsSample(models.Model):
    _name = 'kcs.sample'
    _inherit = ['kcs.sample', 'sd.delete.protection.mixin']


class DailyConfirmation(models.Model):
    _name = 'daily.confirmation'
    _inherit = ['daily.confirmation', 'sd.delete.protection.mixin']


# `production.plan` is registered by sd_india_delete_protection instead: it
# ships in both sd_report and sd_india_report, and the India deployment installs
# only the latter. `import.data` is left out entirely -- it lives in sd_traffic,
# which the India deployment does not install.


class NedSecurityGateQueue(models.Model):
    _name = 'ned.security.gate.queue'
    _inherit = ['ned.security.gate.queue', 'sd.delete.protection.mixin']


# ---------------------------------------------------------------------------
# Document generating its sequence into `reference`
# ---------------------------------------------------------------------------
class ShippingInstruction(models.Model):
    _name = 'shipping.instruction'
    _inherit = ['shipping.instruction', 'sd.delete.protection.mixin']

    _protect_sequence_field = 'reference'


# ---------------------------------------------------------------------------
# Documents without a generated sequence -- protected by state only
# ---------------------------------------------------------------------------
class SContract(models.Model):
    _name = 's.contract'
    _inherit = ['s.contract', 'sd.delete.protection.mixin']

    _protect_sequence_field = None


class StockAllocation(models.Model):
    _name = 'stock.allocation'
    _inherit = ['stock.allocation', 'sd.delete.protection.mixin']

    _protect_sequence_field = None


class InvoicedAllocation(models.Model):
    _name = 'invoiced.allocation'
    _inherit = ['invoiced.allocation', 'sd.delete.protection.mixin']

    _protect_sequence_field = None


class LotStackAllocation(models.Model):
    _name = 'lot.stack.allocation'
    _inherit = ['lot.stack.allocation', 'sd.delete.protection.mixin']

    _protect_sequence_field = None


class KcsCriterions(models.Model):
    _name = 'kcs.criterions'
    _inherit = ['kcs.criterions', 'sd.delete.protection.mixin']

    _protect_sequence_field = None


class ProcessingLossApproval(models.Model):
    _name = 'processing.loss.aproval'
    _inherit = ['processing.loss.aproval', 'sd.delete.protection.mixin']

    _protect_sequence_field = None


class FobManagement(models.Model):
    _name = 'fob.management'
    _inherit = ['fob.management', 'sd.delete.protection.mixin']

    _protect_sequence_field = None


class FobPssManagement(models.Model):
    _name = 'fob.pss.management'
    _inherit = ['fob.pss.management', 'sd.delete.protection.mixin']

    _protect_sequence_field = None


class SaleContractClam(models.Model):
    _name = 'sale.contract.clam'
    _inherit = ['sale.contract.clam', 'sd.delete.protection.mixin']

    _protect_sequence_field = None


class TrafficContract(models.Model):
    """`status` here holds a warehouse category, not a workflow stage --
    only `state` is meaningful for delete protection."""
    _name = 'traffic.contract'
    _inherit = ['traffic.contract', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_state_fields = ('state',)


class RestackManagement(models.Model):
    _name = 'restack.management'
    _inherit = ['restack.management', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_state_fields = ('status',)
    _protect_draft_states = ('pending',)


class VesselRegistration(models.Model):
    _name = 'vessel.registration'
    _inherit = ['vessel.registration', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_state_fields = ('status',)
    _protect_draft_states = ('pending',)


# ---------------------------------------------------------------------------
# Line models -- no sequence of their own, checked against their parent
# ---------------------------------------------------------------------------
class PurchaseContractLine(models.Model):
    _name = 'purchase.contract.line'
    _inherit = ['purchase.contract.line', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_parent_field = 'contract_id'


class SaleContractLine(models.Model):
    _name = 'sale.contract.line'
    _inherit = ['sale.contract.line', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_parent_field = 'contract_id'


class SContractLine(models.Model):
    _name = 's.contract.line'
    _inherit = ['s.contract.line', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_parent_field = 'contract_id'


class ShippingInstructionLine(models.Model):
    _name = 'shipping.instruction.line'
    _inherit = ['shipping.instruction.line', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_parent_field = 'shipping_id'


class DeliveryOrderLine(models.Model):
    _name = 'delivery.order.line'
    _inherit = ['delivery.order.line', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_parent_field = 'delivery_id'


class RequestMaterialsLine(models.Model):
    """No draft stage exists here -- the selection is approved/cancel only, so
    an empty tuple is the honest declaration: any state that is set blocks the
    delete, and only a line whose state was never set can still be removed."""
    _name = 'request.materials.line'
    _inherit = ['request.materials.line', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_draft_states = ()
    _protect_parent_field = 'request_id'


class RequestStockMaterialLine(models.Model):
    _name = 'request.stock.material.line'
    _inherit = ['request.stock.material.line', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_parent_field = 'request_id'
