# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta, datetime, date


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    stack_type = fields.Selection(related='lot_id.stack_type', store=True)
    shipping_instruction_id = fields.Many2one('shipping.instruction', string='SI No.')
    
    state_kcs = fields.Selection(
        selection=[('draft', 'New'), ('approved', 'Approved'), ('waiting', 'Waiting Another Operation'),
                   ('rejected', 'Rejected'), ('cancel', 'Cancel')], string='KCS Status', readonly=True, copy=False,
        index=True, default='draft', tracking=True, )
    tare_weight = fields.Float(string='Tare Weight', related='move_line_ids_without_package.tare_weight', store=True)

    cost = fields.Float(string="VND/Kg", compute='compute_cost', store=True, readonly=False)

    # zone_id = fields.Many2one(related='lot_id.zone_id', string='Zone', store=True, tracking=True)

    def button_sd_validate(self):
        for record in self:
            if record.picking_type_id.code == 'incoming' and record.picking_type_id.operation == 'factory':
                net_qty = record.total_init_qty
                basis_qty = 0
                if record.state_kcs == 'approved':
                    for line in record.kcs_line:
                        line.product_qty = net_qty
                        line._compute_deduction()
                        basis_qty = line.basis_weight
                    for ml in record.move_line_ids_without_package:
                        ml.qty_done = basis_qty
        return super(StockPicking, self).button_sd_validate()

    def button_qc_assigned(self):
        for record in self:
            if record.picking_type_id.code == 'incoming' and record.picking_type_id.operation == 'station':
                bag = sum(record.move_line_ids_without_package.mapped('bag_no'))
                if bag <= 0:
                    raise UserError(_("You have to input bag number"))

        return super(StockPicking, self).button_qc_assigned()

    def load_qc_gip_merge(self):
        for this in self:
            if not this.kcs_line:
                this.btt_loads()
            mc_degree = this.kcs_line.stack_id.mc / (1 - (0.01 * this.kcs_line.stack_id.mc))

            if this.kcs_line:
                this.kcs_line.update({
                    'sample_weight': 100,
                    'bb_sample_weight': 100,
                    'mc_degree': mc_degree or False,
                    'mc': this.kcs_line.stack_id.mc,
                    # 'mc_deduct': this.kcs_line.stack_id.mc_deduct,
                    'fm_gram': this.kcs_line.stack_id.fm,
                    'fm': this.kcs_line.stack_id.fm,
                    # 'fm_deduct': this.kcs_line.stack_id.fm_deduct,
                    'black_gram': this.kcs_line.stack_id.black,
                    'black': this.kcs_line.stack_id.black,
                    'broken_gram': this.kcs_line.stack_id.broken,
                    'broken': this.kcs_line.stack_id.broken,
                    # 'broken_deduct': this.kcs_line.stack_id.broken_deduct,
                    'brown_gram': this.kcs_line.stack_id.brown,
                    'brown': this.kcs_line.stack_id.brown,
                    # 'brown_deduct': this.kcs_line.stack_id.brown_deduct,
                    # 'bbb': this.kcs_line.stack_id.bbb,
                    'mold_gram': this.kcs_line.stack_id.mold,
                    'mold': this.kcs_line.stack_id.mold,
                    # 'mold_deduct': this.kcs_line.stack_id.mold_deduct,
                    'cherry_gram': this.kcs_line.stack_id.cherry,
                    'cherry': this.kcs_line.stack_id.cherry,
                    'excelsa_gram': this.kcs_line.stack_id.excelsa,
                    'excelsa': this.kcs_line.stack_id.excelsa,
                    # 'excelsa_deduct': this.kcs_line.stack_id.excelsa_deduct,
                    'screen20_gram': this.kcs_line.stack_id.screen20,
                    'screen20': this.kcs_line.stack_id.screen20,
                    'screen19_gram': this.kcs_line.stack_id.screen19,
                    'screen19': this.kcs_line.stack_id.screen19,
                    'screen18_gram': this.kcs_line.stack_id.screen18,
                    'screen18': this.kcs_line.stack_id.screen18,
                    'screen17_gram': this.kcs_line.stack_id.screen17,
                    'screen17': this.kcs_line.stack_id.screen17,

                    # 'oversc18': this.kcs_line.stack_id.oversc18,
                    'screen16_gram': this.kcs_line.stack_id.screen16,
                    'screen16': this.kcs_line.stack_id.screen16,
                    'screen15_gram': this.kcs_line.stack_id.screen15,
                    'screen15': this.kcs_line.stack_id.screen15,

                    'screen14_gram': this.kcs_line.stack_id.screen14,
                    'screen14': this.kcs_line.stack_id.screen15,
                    'screen13_gram': this.kcs_line.stack_id.screen13,
                    'screen13': this.kcs_line.stack_id.screen13,

                    'greatersc12_gram': this.kcs_line.stack_id.greatersc12,
                    'greatersc12': this.kcs_line.stack_id.greatersc12,
                    'belowsc12_gram': this.kcs_line.stack_id.screen12,
                    # 'belowsc12': this.kcs_line.stack_id.belowsc12,
                    'burned_gram': this.kcs_line.stack_id.burn,
                    # 'burned': this.kcs_line.stack_id.burned,
                    'eaten_gram': this.kcs_line.stack_id.eaten,
                    'eaten': this.kcs_line.stack_id.eaten,
                    'immature_gram': this.kcs_line.stack_id.immature,
                    'immature': this.kcs_line.stack_id.immature,
                    # 'insect_bean_deduct': this.kcs_line.stack_id.insect_bean_deduct,
                    'sampler': False,
                    'stone_count': this.kcs_line.stack_id.stone_count,
                    'stick_count': this.kcs_line.stack_id.stick_count
                })
        return True
