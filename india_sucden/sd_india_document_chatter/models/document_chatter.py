# -*- coding: utf-8 -*-
"""Chatter and workflow tracking for the two documents whose views are India-side.

``production.plan`` ships in both sd_report and sd_india_report, and this
deployment installs only the latter. ``stock.allocation`` is defined in
sd_purchase_contract but its only form view lives in sd_india_contract, so both
halves are kept here rather than split across two modules.
"""
from odoo import fields, models


class ProductionPlan(models.Model):
    _name = 'production.plan'
    _inherit = ['production.plan', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)


class StockAllocation(models.Model):
    _name = 'stock.allocation'
    _inherit = ['stock.allocation', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(tracking=True)
