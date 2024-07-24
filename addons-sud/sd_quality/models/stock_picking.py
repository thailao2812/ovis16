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
    
    
    def load_qc_gip(self):
        for this in self:
            # if this.kcs_line.zone_id.hopper != True:
            #     raise UserError(_('You can only load QC from GRN Hopper.'))
            # Anh Tuấn chi đem wa v16 --> vấn đề 1
            # if this.product_id.default_code != 'FAQ':
            #     raise UserError(_('You can only load QC from GRN FAQ.'))
            # ko cho đem wa  đối với sản phẩm là FAQ -> V16 có nên bỏ điểu kiện này ko   vấn đề 2
            if not this.kcs_line:
                this.btt_loads()
                
            # kcs_line_id = self.env['request.kcs.line'].search([('stack_id','=', this.kcs_line.stack_id.id),('zone_id','=',this.kcs_line.zone_id.id)],limit = 1)
            # if not kcs_line_id:
            #     raise UserError(_('KCS of GRN reference not found.'))
            
            
            
            mc_degree = this.kcs_line.stack_id.mc /(1- (0.01* this.kcs_line.stack_id.mc))
            
            if this.kcs_line:
                this.kcs_line.update({
                    'sample_weight': 100,
                    'bb_sample_weight': 100,
                    # 'mc_degree': False,
                    'mc_degree': this.zone_id.hopper == True and mc_degree or False,
                    # 'mc': this.kcs_line.stack_id.mc,
                    #'mc_deduct': this.kcs_line.stack_id.mc_deduct,
                    'fm_gram': this.kcs_line.stack_id.fm,
                    # 'fm': this.kcs_line.stack_id.fm,
                    #'fm_deduct': this.kcs_line.stack_id.fm_deduct,
                    'black_gram': this.kcs_line.stack_id.black,
                    # 'black': this.kcs_line.stack_id.black,
                    'broken_gram': this.kcs_line.stack_id.broken,
                    # 'broken': this.kcs_line.stack_id.broken,
                    #'broken_deduct': this.kcs_line.stack_id.broken_deduct,
                    'brown_gram': this.kcs_line.stack_id.brown,
                    # 'brown': this.kcs_line.stack_id.brown,
                    #'brown_deduct': this.kcs_line.stack_id.brown_deduct,
                    # 'bbb': this.kcs_line.stack_id.bbb,
                    'mold_gram': this.kcs_line.stack_id.mold,
                    # 'mold': this.kcs_line.stack_id.mold,
                    #'mold_deduct': this.kcs_line.stack_id.mold_deduct,
                    'cherry_gram': this.kcs_line.stack_id.cherry,
                    # 'cherry': this.kcs_line.stack_id.cherry,
                    'excelsa_gram': this.kcs_line.stack_id.excelsa,
                    # 'excelsa': this.kcs_line.stack_id.excelsa,
                    #'excelsa_deduct': this.kcs_line.stack_id.excelsa_deduct,
                    'screen20_gram': this.kcs_line.stack_id.screen20,
                    # 'screen20': this.kcs_line.stack_id.screen20,
                    'screen19_gram': this.kcs_line.stack_id.screen19,
                    # 'screen19': this.kcs_line.stack_id.screen19,
                    'screen18_gram': this.kcs_line.stack_id.screen18,
                    # 'screen18': this.kcs_line.stack_id.screen18,
                    'screen17_gram': this.kcs_line.stack_id.screen17,
                    
                    # 'oversc18': this.kcs_line.stack_id.oversc18,
                    'screen16_gram': this.kcs_line.stack_id.screen16,
                    'screen15_gram': this.kcs_line.stack_id.screen15,
                    
                    'screen14_gram': this.kcs_line.stack_id.screen14,
                    'screen13_gram': this.kcs_line.stack_id.screen13,
                    
                    # 'screen16': this.kcs_line.stack_id.screen16,
                    # 'oversc16': this.kcs_line.stack_id.oversc16,
                    # 'screen13_gram': this.kcs_line.stack_id.screen13_gram,
                    # 'screen13': this.kcs_line.stack_id.screen13,
                    # 'oversc13': this.kcs_line.stack_id.oversc13,
                    'greatersc12_gram': this.kcs_line.stack_id.greatersc12,
                    # 'greatersc12': this.kcs_line.stack_id.greatersc12,
                    'belowsc12_gram': this.kcs_line.stack_id.screen12,
                    # 'belowsc12': this.kcs_line.stack_id.belowsc12,
                    # 'oversc12': this.kcs_line.stack_id.oversc12,
                    'burned_gram': this.kcs_line.stack_id.burn,
                    # 'burned': this.kcs_line.stack_id.burned,
                    #'burned_deduct': this.kcs_line.stack_id.burned_deduct,
                    'eaten_gram': this.kcs_line.stack_id.eaten,
                    # 'eaten': this.kcs_line.stack_id.eaten,
                    'immature_gram': this.kcs_line.stack_id.immature,
                    # 'immature': this.kcs_line.stack_id.immature,
                    #'insect_bean_deduct': this.kcs_line.stack_id.insect_bean_deduct,
                    'sampler': False,
                    'stone_count': this.kcs_line.stack_id.stone_count,
                    'stick_count': this.kcs_line.stack_id.stick_count
            })
        return True
    
    def btt_change_product(self):
        return
        for pick in self:
            if pick.state =='done' and pick.state_kcs == 'approved':
                raise UserError(_('You much select Stack'))
            
            if pick.change_product_id:
                #Change cho KCs
                for kcs_line in pick.kcs_line:
                    kcs_line.product_id = pick.change_product_id.id
                #Change cho Stock Move
                for move in pick.move_lines:
                    move.prduct_id = pick.change_product_id.id
                    move.product_uom_qty = move.init_qty
                pick.product_id = pick.change_product_id.id
                if pick.state =='draft':
                    pick.action_confirm()   
                 
                #Change cho san xuat
                sql ='''
                    select id from mrp_operation_result_produced_product where picking_id =%s
                '''%(pick.id)
                self.env.cr.execute(sql)
                for line in self.env.cr.dictfetchall():
                    result = self.env['mrp.operation.result.produced.product'].browse(line['id'])
                    result.product_id = pick.change_product_id.id
                     
                pick.note = '''Change %s'''%(pick.change_product_id.default_code)
            
        return
    
    contract_no = fields.Char(string="Contract no")
    date_sent = fields.Datetime('Date Sent',default= time.strftime(DATETIME_FORMAT))
    change_product_id = fields.Many2one('product.product','Change Product')
    fix_done = fields.Boolean('FIX')
    cuptest = fields.Char(related='kcs_line.cuptest', string="Cuptest")
    kcs_sample_ids = fields.Many2many('kcs.sample','kcs_sample_stock_picking_rel','picking_id','kcs_sample_id', string="Intake Quality Average")
    use_sample = fields.Boolean(string='Use Sample', )
    picking_type_code = fields.Selection(related="picking_type_id.code", string="Picking Type code",  store= True)
    
    def print_kcs_sample(self):
        for this in self:
            if not this.kcs_sample_ids:
                raise UserError(_('Intake Quality Average is not define.'))
            else:
                return {'type': 'ir.actions.report.xml','report_name':'report_kcs_quality_sample_details'}
            
    @api.onchange('use_sample')
    def onchange_use_sample(self):
        for this in self:
            if this.use_sample != True:
                for line in this.kcs_line:
                    line.update({'deduction_manual': 0})
    
#     request_kcs_id = fields.Many2one("request.kcs", "Request KCS", 
#          states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    state_kcs = fields.Selection(selection=[('draft', 'New'),('approved', 'Approved'),('waiting', 'Waiting Another Operation'),
        ('rejected', 'Rejected'),('cancel', 'Cancel')],string='KCS Status', readonly=True, copy=False, index=True, default='draft', tracking=True,)
    
    
    date_kcs = fields.Datetime(string="KCS Date")
    
    kcs_line = fields.One2many('request.kcs.line','picking_id',string="KCS Line")
    approve_id = fields.Many2one("res.users",string= "Approved")
    kcs_criterions_id = fields.Many2one("kcs.criterions",string= "Rule KCS")
    special = fields.Boolean(string="Special")
    
    def btt_loads(self):
        self.env.cr.execute('''
                    DELETE FROM request_kcs_line WHERE picking_id = %(picking_id)s;''' % ({'picking_id': self.id}))
        
        for pick in self:
            if not pick.date_kcs:
                pick.date_kcs = datetime.now()
            if pick.picking_type_id.kcs != True:
                raise UserError(_('Quy trinh khong KCS'))
                continue
            for move in pick.move_line_ids_without_package:
                #Kiet ko thay sai
                # if move.product_id.product_kcs == True:
                #     raise UserError(_('Products %s khong can KCS.')%(move.product_id.name))
                
                kcs_criterions_id = False
                if pick.picking_type_id.code == 'incoming' and pick.warehouse_id:
                    sql ='''
                    SELECT id
                    FROM kcs_criterions kc join kcs_rule_warehouse_rel krwr ON kc.id = krwr.rule_id
                    WHERE date(timezone('UTC','%s'::timestamp)) between kc.from_date and kc.to_date
                        and kc.product_id =%s
                        and kc.state not in ('draft','cancel') 
                        and krwr.warehouse_id = %s 
                        and kc.type_warehouse !='processing'
                        and kc.active = true
                    ORDER BY id DESC
                    LIMIT 1
                    '''%(pick.date_kcs,move.product_id.id, pick.warehouse_id.id)

                elif pick.picking_type_id.code in ('production_in','production_out','transfer_in') and pick.warehouse_id:
                    sql ='''
                    SELECT id
                    FROM kcs_criterions kc join kcs_rule_warehouse_rel krwr ON kc.id = krwr.rule_id
                    WHERE date(timezone('UTC','%s'::timestamp)) between from_date and to_date
                        and state not in ('draft','cancel')
                        and krwr.warehouse_id = %s 
                        and kc.type_warehouse = 'processing'
                        and kc.active = true
                    ORDER BY id DESC
                    LIMIT 1
                    '''%(pick.date_kcs,  pick.warehouse_id.id)
                self.env.cr.execute(sql)
                for criterions in self.env.cr.dictfetchall():
                    kcs_criterions_id = criterions['id'] or False
                
                if not kcs_criterions_id:
                    if pick.picking_type_id.code == 'incoming' and pick.warehouse_id:
                        sql ='''
                        SELECT id
                        FROM kcs_criterions kc join kcs_rule_warehouse_rel krwr ON kc.id = krwr.rule_id
                        WHERE date(timezone('UTC','%s'::timestamp)) between kc.from_date and kc.to_date
                            and kc.categ_id =%s and kc.product_id is null
                            and kc.state not in ('draft','cancel') 
                            and krwr.warehouse_id = %s 
                            and kc.type_warehouse !='processing'
                            and kc.active = true
                        ORDER BY id DESC
                        LIMIT 1
                    '''%(pick.date_kcs, move.product_id.categ_id.id, pick.warehouse_id.id)
                    
                    elif pick.picking_type_id.code in ('production_in','production_out'):
                        sql ='''
                        SELECT id
                        FROM kcs_criterions kc join kcs_rule_warehouse_rel krwr ON kc.id = krwr.rule_id
                        WHERE date(timezone('UTC','%s'::timestamp)) between from_date and to_date
                            and state not in ('draft','cancel')
                            and krwr.warehouse_id = %s 
                            and kc.type_warehouse = 'processing'
                            and kc.active = true
                        ORDER BY id DESC
                        LIMIT 1
                    '''%(pick.date_kcs, pick.warehouse_id.id)

                self.env.cr.execute(sql)
                for criterions in self.env.cr.dictfetchall():
                    kcs_criterions_id = criterions['id'] or False
                
                if not kcs_criterions_id:
                    raise UserError(_('You must define rule KCS.'))
                
                pick.kcs_criterions_id = kcs_criterions_id
                
                
                
                var = {'picking_id': pick.id, 
                        'name': move.picking_id.name or False,
                        'product_id': move.product_id.id or False, 
                        'categ_id': move.product_id.product_tmpl_id.categ_id.id,  
                        'product_qty': move.init_qty or 0.0,
                        'qty_reached': move.init_qty or 0.0,
                        'criterions_id': False,  
                        'product_uom': move.product_uom_id.id or False,
                        'move_id': move.id or False,
                        'packing_id':move.packing_id and move.packing_id.id or False,
                        'bag_no':move.bag_no or 0.0,
                        'state': 'draft'}
                self.env['request.kcs.line'].create(var)

                self.env.cr.execute(''' update request_kcs_line set x_warehouse_id = 
                                            (SELECT warehouse_id 
                                            FROM stock_picking where request_kcs_line.picking_id = stock_picking.id)
                                            WHERE request_kcs_line.x_warehouse_id is NULL; ''')
                
            if pick.picking_type_id.code =='production_out':
                pick.kcs_line.refresh()
                pick.load_qc_gip()
    
    def btt_approved(self):
        for pick in self:
            if not pick.kcs_line:
                raise UserError(_('You cannot approve a Request KCS without any Request KCS Line.'))
            
            for line in pick.kcs_line:
                if line.bb_sample_weight == 0 or line.sample_weight == 0 :
                    raise UserError(_('You input bb sample weigh or sample weight before Approved '))
                
            if pick.kcs_criterions_id.reject_rule:
                for line in pick.kcs_line:
                    if (line.reject_mc or line.reject_foreign or line.reject_bb or line.reject_brown or line.reject_mold or line.reject_excelsa or line.reject_burned or line.reject_insect_bean):
                        raise UserError(_('Check Reject'))
            
        
        if self.picking_type_id.code == 'production_out':
            self.state_kcs = 'approved'
            for pick in self:
                for line in pick.kcs_line:
                    if line.state != 'draft':
                        continue
                    line.state = 'approved'
                    if pick.picking_type_id.deduct:
                        line.move_id.write({'qty_done': line.basis_weight or 0.0})
                    else:
                        line.move_id.write({'qty_done': line.product_qty or 0.0})
                        # line.move_id.write({'reserved_uom_qty':line.product_qty or 0.0,'qty_done': line.product_qty or 0.0})
                    #Minh update QC transfer in and transfer out
                    # if line.stack_id:
                    #     for pick_in in line.stack_id.move_line_ids.filtered(lambda x: x.picking_id.picking_type_id.code =='transfer_in').mapped('picking_id'):
                    #         pick_in.kcs_line.write({'state':'draft'})
                    #         pick_in.kcs_line.unlink()
                    #         for move_in in pick_in.move_lines:
                    #             pick.kcs_line.filtered(lambda x: x.product_id == move_in.product_id).copy({'picking_id':pick_in.id,
                    #                                 'move_id':move_in.id})
                    #         if pick_in.backorder_id:
                    #             pick_in.backorder_id.kcs_line.write({'state':'draft'})
                    #             pick_in.backorder_id.kcs_line.unlink()
                    #             for move_out in pick_in.backorder_id.move_lines:
                    #                 pick.kcs_line.filtered(lambda x: x.product_id == move_out.product_id).copy({'picking_id':pick_in.backorder_id.id,
                    #                                     'move_id':move_out.id})
#                     line.move_id.write({'product_uom_qty': line.product_qty or 0.0})
            return True
        
        for pick in self:
            pick.state_kcs = 'approved'
            if all(x.zone_id for x in pick.kcs_line) and pick.picking_type_id.code == 'production_out':
            #SON: thêm sự kiện tìm và gán số STACK WIP tương ứng ZONE cho GRP khi KCS approve
                sql ='''
                    SELECT id FROM stock_stack 
                    WHERE zone_id = %s 
                        and name like '%%%s%%'
                '''%(self.zone_id.id,'WIP-')
                self.env.cr.execute(sql)
                for stack_obj in self.env.cr.dictfetchall():
                    stack_line = self.env['stock.lot'].browse(stack_obj['id'])
                    pick.stack_id = stack_line['id'] or 'null'

            for line in pick.kcs_line:
                if line.state != 'draft':
                    continue
                line.state = 'approved'
                
                if pick.picking_type_id.deduct:
                    line.move_id.write({'qty_done': line.basis_weight or 0.0})
                    # Đây là nghiệp vụ hàng mua
                    
#                     pick.create_itr()
                else:
                    line.move_id.write({'qty_done': line.product_qty or 0.0})
                
                # Err phần sản xuất
                # produced_product = self.env['mrp.operation.result.produced.product'].search([('picking_id','=',pick.id)])
                # if produced_product:
                #     produced_product.kcs_notes = pick.note or 'null'
        self.write({'state_kcs': 'approved', 'approve_id': self.env.uid,
            'date_kcs': time.strftime(DATETIME_FORMAT)})

    # Đồng thời ghi nhận trọng lượng vào stock.stack
        for linekcs in self.kcs_line:
            for linestack in linekcs.stack_id:
                if linestack:
                    linestack.write({'net_qty':linekcs.product_qty,'basis_qty':linekcs.basis_weight,'init_qty':linekcs.product_qty,'remaining_qty':linekcs.basis_weight,'bag_qty':self.total_bag})
        
        #Không dùng GRP tạm Áp dụng 30/04/2023
        # if self.picking_type_code == 'production_in':
        #     name_seq =  self.picking_type_id.sequence_id.with_context(ir_sequence_date=str(self.date_kcs)[0:10]).next_by_id()
        #     if pick.crop_id.short_name:
        #         crop = '-' + pick.crop_id.short_name +'-'
        #         name_seq = name_seq.replace("-", crop, 1)
        #         pick.name = name_seq
        #     else:
        #         pick.name = name_seq
            
        if self.picking_type_id.kcs_approved:
            operation = self.env['stock.move.line'].search([('picking_id','=',self.id)])
            for i in self.kcs_line:
                if i.product_id == operation.product_id:
                    operation.write({'reserved_uom_qty':0,'qty_done':i.basis_weight})
            self.button_sd_validate()
            
    
    def btt_draft(self):
        for pick in self:
#             if pick.state == 'done':
#                 raise UserError(_(u'Bộ phận kho đã nhập kho, muốn điều chỉnh thông báo với bộ phận kho'))

#SON: khóa set to draft phiếu GIP khi Done
            if pick.state == 'done' and pick.picking_type_code == 'production_out' and not self.user_has_groups('ned_kcs.group_qc_button'):
                raise UserError(_('Unable set to draft for Picking %s.\n\t Please contact with your manager.') % (self.name))
                
            pick.state_kcs = 'draft'
            pick.action_revert_done()
            for line in pick.kcs_line:
                line.write({'state': 'draft'})
            
                
    def btt_reject(self):
        for pick in self:
            pick.state_kcs = 'rejected'
            for line in pick.kcs_line:
                if line.state_kcs != 'draft':
                    continue
                line.state = 'reject'
            if pick.picking_type_id.code == 'production_in':
                if pick.state != 'done' :
                    pick.action_cancel()
                else:
                    raise UserError(_('Unable set State Reject for QC Picking %s. Becase is WH Done') % (pick.name))
        
    def do_new_transfer(self):
        self.ensure_one()
        if self.picking_type_id.kcs == True:
            for move in self.move_lines:
                if move.product_id.product_kcs:
                    if self.state_kcs == 'draft':
                        raise UserError(_('Products %s requiring KCS.')%(move.product_id.name))
        return super(StockPicking, self).do_new_transfer()
    
    
    def btt_qc_modification(self):
        if self.picking_type_id.code == 'production_out':
            self.state_kcs = 'approved'
            for pick in self:
                for line in pick.kcs_line:
                    if line.state != 'draft':
                        continue
                    line.state = 'approved'
                    if pick.picking_type_id.deduct:
                        line.move_id.write({'qty_done': line.basis_weight or 0.0})
                    else:
                        line.move_id.write({'product_uom_qty': line.product_qty or 0.0})
                    #Minh update QC transfer in and transfer out
                    if line.stack_id:
                        for pick_in in line.stack_id.move_ids.filtered(lambda x: x.picking_id.picking_type_id.code =='transfer_in').mapped('picking_id'):
                            pick_in.kcs_line.write({'state':'draft'})
                            pick_in.kcs_line.unlink()
                            for move_in in pick_in.move_line_ids_without_package:
                                pick.kcs_line.filtered(lambda x: x.product_id == move_in.product_id).copy({'picking_id':pick_in.id,
                                                    'move_id':move_in.id})
                            if pick_in.backorder_id:
                                pick_in.backorder_id.kcs_line.write({'state':'draft'})
                                pick_in.backorder_id.kcs_line.unlink()
                                for move_out in pick_in.backorder_id.move_line_ids_without_package:
                                    pick.kcs_line.filtered(lambda x: x.product_id == move_out.product_id).copy({'picking_id':pick_in.backorder_id.id,
                                                        'move_id':move_out.id})
#                     line.move_id.write({'product_uom_qty': line.product_qty or 0.0})
            return True
        
        for pick in self:
            pick.state_kcs = 'approved'
            if all(x.zone_id for x in pick.kcs_line) and pick.picking_type_id.code == 'production_out':
            #SON: thêm sự kiện tìm và gán số STACK WIP tương ứng ZONE cho GRP khi KCS approve
                sql ='''
                    SELECT id FROM stock_lot 
                    WHERE zone_id = %s 
                        and name like '%%%s%%'
                '''%(self.zone_id.id,'WIP-')
                self.env.cr.execute(sql)
                for stack_obj in self.env.cr.dictfetchall():
                    stack_line = self.env['stock.lot'].browse(stack_obj['id'])
                    pick.stack_id = stack_line['id'] or 'null'

            for line in pick.kcs_line:
                if line.state != 'draft':
                    continue
                line.state = 'approved'
                
                if pick.picking_type_id.deduct:
                    line.move_id.write({'qty_done': line.basis_weight or 0.0})
                    # Đây là nghiệp vụ hàng mua
                    
#                     pick.create_itr()
                else:
                    line.move_id.write({'product_uom_qty': line.product_qty or 0.0})
                
                produced_product = self.env['mrp.operation.result.produced.product'].search([('picking_id','=',pick.id)])
                if produced_product:
                    produced_product.kcs_notes = pick.note or 'null'
        self.write({'state_kcs': 'approved', 'approve_id': self.env.uid,
            'date_kcs': time.strftime(DATETIME_FORMAT)})
        for linekcs in self.kcs_line:
            for linestack in linekcs.stack_id:
                if linestack:
                    linestack.write({'net_qty':linekcs.product_qty,'basis_qty':linekcs.basis_weight,'init_qty':linekcs.product_qty,'remaining_qty':linekcs.basis_weight,'bag_qty':self.total_bag})

        if self.picking_type_id.kcs_approved:
            move_line = self.env['stock.move.line'].search([('picking_id','=',self.id)])
            for i in self.kcs_line:
                if i.product_id == move_line.product_id:
                    move_line.write({'qty_done':i.basis_weight})
            
    
    def report_qa_production(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name':'qa_production_report',
            }
    
    def report_qa_gdn(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name':'qa_gdn_report',
            }
    
    def report_qa_grn(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name':'qa_grn_report',
            }
        
    def btt_loads_olds(self):
        for pick in self:
            if not pick.date_kcs:
                pick.date_kcs = datetime.now()
            if pick.picking_type_id.kcs != True:
                raise UserError(_('Quy trinh khong KCS'))
                continue
            for move in pick.move_line_ids_without_package:
                #Kiet ko thay sai
                # if move.product_id.product_kcs == True:
                #     raise UserError(_('Products %s khong can KCS.')%(move.product_id.name))
                
                kcs_criterions_id = False
                sql = ''
                if pick.picking_type_id.code == 'incoming' and pick.warehouse_id:
                    sql ='''
                    SELECT id
                    FROM kcs_criterions kc join kcs_rule_warehouse_rel krwr ON kc.id = krwr.rule_id
                    WHERE '%s' between kc.from_date and kc.to_date
                        and kc.product_id =%s
                        and kc.is_grn = True
                        and (kc.special is null or kc.special =false)
                        and kc.state not in ('draft','cancel') and krwr.warehouse_id = %s 
                    ORDER BY id DESC
                    LIMIT 1
                    '''%(pick.date_kcs,move.product_id.id, pick.warehouse_id.id)

                elif pick.picking_type_id.code == 'production_in':
                    sql ='''
                    SELECT id
                    FROM kcs_criterions 
                    WHERE '%s' between from_date and to_date
                        and product_id =%s 
                        and (special is null or special =false)
                        and is_factory = true
                        and is_grp = True
                        and state not in ('draft','cancel')
                    ORDER BY id DESC
                    LIMIT 1
                    '''%(pick.date_kcs,move.product_id.id)

                else:
                    sql ='''
                    SELECT id
                    FROM kcs_criterions
                    WHERE '%s' between from_date and to_date
                        and product_id =%s
                        and (special is null or special =false)
                        and state not in ('draft','cancel')
                    ORDER BY id DESC
                    LIMIT 1
                '''%(pick.date_kcs,move.product_id.id)
                self.env.cr.execute(sql)
                for criterions in self.env.cr.dictfetchall():
                    kcs_criterions_id = criterions['id'] or False
                if not kcs_criterions_id:
                    if pick.picking_type_id.code == 'incoming' and pick.warehouse_id:
                        sql ='''
                        SELECT id
                        FROM kcs_criterions kc join kcs_rule_warehouse_rel krwr ON kc.id = krwr.rule_id
                        WHERE '%s' between kc.from_date and kc.to_date
                            and kc.categ_id =%s and kc.product_id is null
                            and kc.is_grn = True
                            and (kc.special is null or kc.special = false)
                            and kc.state not in ('draft','cancel') and krwr.warehouse_id = %s
                        ORDER BY id DESC
                        LIMIT 1
                    '''%(pick.date_kcs, move.product_id.categ_id.id, pick.warehouse_id and pick.warehouse_id.id or False)
                    
                    elif pick.picking_type_id.code == 'production_in':
                        sql ='''
                        SELECT id
                        FROM kcs_criterions
                        WHERE '%s' between from_date and to_date
                            and categ_id =%s and product_id is null
                            and (special is null or special = false)
                            and is_factory = true
                            and is_grp = True 
                            and state not in ('draft','cancel')
                        ORDER BY id DESC
                        LIMIT 1
                    '''%(pick.date_kcs, move.product_id.categ_id.id)

                    else:
                        sql ='''
                        SELECT id
                        FROM kcs_criterions
                        WHERE '%s' between from_date and to_date
                            and categ_id =%s and product_id is null
                            and (special is null or special = false)
                            and state not in ('draft','cancel')
                        ORDER BY id DESC
                        LIMIT 1
                    '''%(pick.date_kcs, move.product_id.categ_id.id)
                print(sql)
                self.env.cr.execute(sql)
                for criterions in self.env.cr.dictfetchall():
                    kcs_criterions_id = criterions['id'] or False
                
                if not kcs_criterions_id:
                    raise UserError(_('You must define rule KCS.'))
                
                pick.kcs_criterions_id = kcs_criterions_id
                
                self.env.cr.execute('''
                    DELETE FROM request_kcs_line WHERE picking_id = %(picking_id)s;''' % ({'picking_id': self.id}))
                
                var = {'picking_id': pick.id, 
                        'name': move.picking_id.name or False,
                        'product_id': move.product_id.id or False, 
                        'categ_id': move.product_id.product_tmpl_id.categ_id.id,  
                        'product_qty': sum([x.init_qty for x in pick.move_line_ids_without_package]) or 0.0,
                        'qty_reached': sum([x.init_qty for x in pick.move_line_ids_without_package]) or 0.0,
                        'criterions_id': False,  
                        'product_uom': move.product_uom_id.id or False,
                        'move_id': move.id or False,
                        'packing_id':move.packing_id and move.packing_id.id or False,
                        'bag_no':move.bag_no or 0.0,
                        'state': 'draft'}
                self.env['request.kcs.line'].create(var)

                self.env.cr.execute(''' update request_kcs_line set x_warehouse_id = 
                                            (SELECT warehouse_id 
                                            FROM stock_picking where request_kcs_line.picking_id = stock_picking.id)
                                            WHERE request_kcs_line.x_warehouse_id is NULL; ''')
                
            if pick.picking_type_id.code =='production_out':
                pick.kcs_line.refresh()
                pick.load_qc_gip()
        

        