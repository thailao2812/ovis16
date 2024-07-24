# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ProductionAnalysisLineInputValue(models.Model):
    _inherit = "production.analysis.line.input.value"

    @api.depends('contract_price', 'qty_allocation', 'liffe', 'exchange_rate')
    def _compute_raw_cost(self):
        for this in self:
            if this.contract_id:
                if (this.contract_id.name[0:3] == 'NVP' or this.contract_id.name[0:4] == 'SVNP') and this.exchange_rate:
                    this.raw_coffee_cost = this.contract_price / this.exchange_rate * this.qty_allocation
                else:
                    this.raw_coffee_cost = this.qty_allocation * (this.liffe + this.contract_id.diff_price) / 1000
            else:
                this.raw_coffee_cost = 0
            if this.exchange_rate:
                this.factory_price = (this.raw_coffee_cost + (-this.premium * this.qty_allocation + this.trucking_cost * this.qty_allocation) / this.exchange_rate) / this.qty_allocation * 1000