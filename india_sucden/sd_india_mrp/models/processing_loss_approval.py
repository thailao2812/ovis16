# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta


class ProcessingLossApproval(models.Model):
    _inherit = 'processing.loss.aproval'

    grade_id = fields.Many2one('product.category', related='production_id.bom_id.grade_id', store=True)
    sub_product_id = fields.Many2one('product.product', related='picking_id.sup_product_id', store=True)

    @api.depends('production_id', 'product_issued', 'product_received', 'picking_id.state', 'state')
    def compute_qc(self):
        for this in self:
            if this.production_id:
                sql = '''
                    SELECT SUM(rkl.moisture_percent * rkl.product_qty)/SUM(rkl.product_qty) mc 
                    FROM mrp_production mp
                        JOIN stock_move_line stm ON mp.id = stm.material_id
                        JOIN stock_picking sp ON sp.id = stm.picking_id
                        join stock_picking_type spt on sp.picking_type_id = spt.id
                        JOIN request_kcs_line rkl ON rkl.picking_id = sp.id
                    WHERE mp.id =%s 
                    AND sp.state= 'done'
                    AND spt.code ='production_out';
                    ''' % (this.production_id.id)
                self._cr.execute(sql)
                for line in self._cr.dictfetchall():
                    this.mc_in = line['mc'] or 0.0

                sql = '''
                    SELECT SUM(rkl.moisture_percent * rkl.product_qty)/SUM(rkl.product_qty) mc 
                    FROM mrp_production mp
                        JOIN stock_move_line stm ON mp.id = stm.finished_id
                        JOIN stock_picking sp ON sp.id = stm.picking_id
                        join stock_picking_type spt on sp.picking_type_id = spt.id
                        JOIN request_kcs_line rkl ON rkl.picking_id = sp.id
                    WHERE mp.id =%s 
                    AND spt.code ='production_in'
                    AND stm.state= 'done';
                    ''' % (this.production_id.id)
                self._cr.execute(sql)
                for line in self._cr.dictfetchall():
                    this.mc_out = line['mc'] or 0.0

                this.mc_loss = this.mc_in - this.mc_out
                this.physical_weight = this.product_issued - this.product_received
                this.physical_loss = this.product_issued and (this.physical_weight / this.product_issued * 100) or 0
                this.invisible_loss = this.physical_loss - this.mc_loss

    def button_approve(self):
        for this in self:
            if this.picking_id.state == 'done':
                this.state = 'approved'
            else:
                this.compute_qc()
                this.picking_id.date_done = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                this.picking_id.button_sd_validate()
                this.picking_id.state_kcs = 'approved'
                this.state = 'approved'
        return
