# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"


class StockPicking(models.Model):
    _inherit = "stock.picking"
    order = "id desc"
    
    def btt_reject(self):
        res = super(StockPicking, self).btt_reject()
        for pick in self:
            if pick.picking_type_id.code == 'production_in':
                a = self.env['mrp.operation.result.produced.product'].search([('picking_id','=',pick.id)])
                if a.stack_wip_id:
                    a.stack_wip_id._get_remaining_qty()
            
        return res
    
    def action_cancel(self):
        """ Kiểm tra các điều kiện rùi cập nhật trạng thái cancel """
        if self.state_kcs == 'draft' and self.picking_type_id.code in ('production_in'):
            raise UserError(_('Qc chưa đánh giá chất lượng, Không cho phép Cancel phiếu khokho'))
        #Trường hợp đã tạo git rùi thì ko có tạo phiếu Cancel
        
        return super(StockPicking, self).action_cancel()
            
            
    
        
        