# -*- coding: utf-8 -*-
"""Applies the delete protection to the India-specific transaction models.

The behaviour comes from ``sd.delete.protection.mixin`` in
``sd_delete_protection``; these classes only declare configuration.

Note the draft state is not always called "draft" here -- several India models
open in ``new`` or ``requested``, so ``_protect_draft_states`` is set per model.
"""
from odoo import models


# ---------------------------------------------------------------------------
# Documents that generate a sequence into `name`
# ---------------------------------------------------------------------------
class SaleContractIndia(models.Model):
    _name = 'sale.contract.india'
    _inherit = ['sale.contract.india', 'sd.delete.protection.mixin']


class FobManagementIndia(models.Model):
    _name = 'fob.management.india'
    _inherit = ['fob.management.india', 'sd.delete.protection.mixin']


class SupplierAdjustment(models.Model):
    _name = 'supplier.adjustment'
    _inherit = ['supplier.adjustment', 'sd.delete.protection.mixin']


class ProductionPlan(models.Model):
    """Ships in both sd_report and sd_india_report. Registered here rather than
    in the shared module so that sd_report need not be installed."""
    _name = 'production.plan'
    _inherit = ['production.plan', 'sd.delete.protection.mixin']


# ---------------------------------------------------------------------------
# Documents without a generated sequence -- protected by state only
# ---------------------------------------------------------------------------
class ContractPricePurchase(models.Model):
    _name = 'contract.price.purchase'
    _inherit = ['contract.price.purchase', 'sd.delete.protection.mixin']

    _protect_sequence_field = None


class MoistureConfiguration(models.Model):
    _name = 'moisture.configuration'
    _inherit = ['moisture.configuration', 'sd.delete.protection.mixin']

    _protect_sequence_field = None


class TruckQualityProduction(models.Model):
    _name = 'truck.quality.production'
    _inherit = ['truck.quality.production', 'sd.delete.protection.mixin']

    _protect_sequence_field = None


# `reject.purchase.contract` and `reject.delivery.registration` are deliberately
# absent: both are TransientModel wizards holding a rejection reason, not
# documents. Odoo's vacuum deletes transient rows on a schedule, so protecting
# them would stop the vacuum and let the tables grow without bound. The audit
# hook skips transient models for the same reason.


class ReturnGoodsCsContract(models.Model):
    _name = 'return.goods.cs.contract'
    _inherit = ['return.goods.cs.contract', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_draft_states = ('requested',)


class AnalysisBatchReport(models.Model):
    _name = 'analysis.batch.report'
    _inherit = ['analysis.batch.report', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_draft_states = ('new',)


class FinancialYear(models.Model):
    _name = 'financial.year'
    _inherit = ['financial.year', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_draft_states = ('new',)


class InterestConfiguration(models.Model):
    _name = 'interest.configuration'
    _inherit = ['interest.configuration', 'sd.delete.protection.mixin']

    _protect_sequence_field = None
    _protect_draft_states = ('new',)
