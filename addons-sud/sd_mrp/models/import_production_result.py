# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError
import time
from datetime import timedelta
import xlrd
import base64
from xlrd import open_workbook

from datetime import datetime
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"
from odoo.exceptions import UserError, ValidationError


class WizardImportProductionResult(models.Model):
    _name = "wizard.import.production.result"
    
    @api.depends('import_result_ids','state')
    def _compute_result(self):
        for mrp in self:
            mrp.result_count = len(mrp.import_result_ids) or 0.0
    
    result_count = fields.Integer(compute='_compute_result', string='Receptions', default=0)
    
    name = fields.Char(string="Name")
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('wizard.import.production.result')
        return super(WizardImportProductionResult, self).create(vals)
    
    def action_view_result(self):
        result_ids = self.mapped('import_result_ids')
        result = {
            
            "type": "ir.actions.act_window",
            "res_model": "mrp.operation.result",
            "domain": [('id', 'in', result_ids.ids)],
            "context": {"create": False},
            "name": "Production Result",
            'view_mode': 'tree,form',
            }
        return result
    
    state= fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ], 'Status', readonly=True, default='draft')
    
    
    def update_qc(self, kcs_line , j):
        if  kcs_line:
            kcs_line.update({
                    'sample_weight': 100,
                    'bb_sample_weight': 100,
                    'mc_degree': j.mc,
                    # 'mc': j.mc,
                    # 'mc_deduct': j.mc_deduct,
                    'fm_gram': j.fm,
                    # 'fm': j.fm,
                    # 'fm_deduct': j.fm_deduct,
                    'black_gram': j.black,
                    # 'black': j.black,
                    'broken_gram': j.broken,
                    # 'broken': j.broken,
                    # 'broken_deduct': j.broken_deduct,
                    'brown_gram': j.brown,
                    # 'brown': j.brown,
                    # 'brown_deduct': j.brown_deduct,
                    # 'bbb': j.bbb,
                    'mold_gram': j.mold,
                    # 'mold': j.mold,
                    # 'mold_deduct': j.mold_deduct,
                    'cherry_gram': j.cherry,
                    # 'cherry': j.cherry,
                    'excelsa_gram': j.excelsa,
                    # 'excelsa': j.excelsa,
                    # 'excelsa_deduct': j.excelsa_deduct,
                    'screen20_gram': j.screen20,
                    # 'greatersc12_gram': j.screen20,
                    # 'screen20': j.screen20,
                    'screen19_gram': j.screen19,
                    # 'screen19': j.screen19,
                    'screen18_gram': j.screen18,
                    # 'screen18': j.screen18,
                    # 'oversc18': j.oversc18,
                    'screen17_gram': j.screen17,
                    'screen16_gram': j.screen16,
                    
                    'screen15_gram': j.screen15,
                    'screen14_gram': j.screen14,
                    
                    'screen13_gram': j.screen13,
                    'greatersc12_gram':j.screen12,
                    # 'screen16': j.screen16,
                    # 'oversc16': j.oversc16,
                    # 'screen13': j.screen13,
                    # 'oversc13': j.oversc13,
                    # 'greatersc12_gram': j.greatersc12_gram,
                    # 'greatersc12': j.greatersc12,
                    # 'belowsc12_gram': j.belowsc12_gram,
                    'belowsc12_gram': j.below_screen12,
                    # 'oversc12': j.oversc12,
                    'burned_gram': j.burn,
                    
                    # 'insect_bean_deduct': j.insect_bean_deduct,
                    # 'burned': j.burned,
                    # 'burned_deduct': j.burned_deduct,
                    'eaten_gram': j.insect,
                    # 'eaten': j.eaten,
                    'immature_gram': j.immature,
                    'sampler': j.sampler,
                    'stone_count': j.stone,
                    'stick_count': j.stick 
                    
                    #Bulk Density  -> chưa thây có
            })
            kcs_line._percent_mc()
            kcs_line._percent_fm()
            kcs_line._percent_black()
            kcs_line._percent_broken()
            kcs_line._percent_brown()
            kcs_line._percent_mold()
            kcs_line._percent_cherry()
            kcs_line._percent_excelsa()
            kcs_line._percent_screen20()
            kcs_line._percent_screen19()
            kcs_line._percent_screen18()
            kcs_line._percent_screen17()
            kcs_line._percent_screen16()
            kcs_line._percent_screen15()
            kcs_line._percent_screen14()
            kcs_line._percent_screen13()
            kcs_line._greatersc12_gram()
            kcs_line._percent_greatersc12()
            kcs_line._percent_belowsc12()
            kcs_line._screen12_deduct()
            kcs_line._percent_burned()
            kcs_line._percent_eaten()
            kcs_line._percent_immature()
            
        return
    
    
    file =  fields.Binary('File', help='Choose file Excel', copy=False)
    file_name =  fields.Char('Filename', size=100, readonly=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    date_result = fields.Date(string="Date result", default= datetime.now())
    result_id = fields.Many2one('mrp.operation.result')
    
    def _default_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)])
        # default with user only working 1 company account analytic
        if warehouse_ids:
            return warehouse_ids[0]
    
    @api.model
    def _domain_warehouse(self):
        return "[('id', 'in', %s)]" % self.env.user._warehouses_domain()
    
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", default=_default_warehouse, domain=lambda self: self._domain_warehouse())
    production_shift =fields.Selection([
                        ('1','Ca 1'),
                        ('2','Ca 2'),
                        ('3','Ca 3'),], 'Ca', required=True, default="1" )
    
    production_id = fields.Many2one('mrp.production')
    # resource_calendar_id = fields.Many2one('mrp.resource.calendar','Working Time')
    user_id = fields.Many2one('res.users', string='User',copy=False, default=lambda self: self._uid)
    import_result_ids = fields.One2many('mrp.operation.result','import_result_id', string="Operation result")
    
    failure = fields.Integer('Error(s)', default=0, copy=False)
    warning_mess = fields.Text('Message', copy=False)
    
    def button_confirm(self):
        for i in self.import_result_ids:
            i.btt_confirm()
        
        self.state ='confirmed'
        warehouse_id = self.warehouse_id
        #Kiệt: xử lý cho hoạt động tự động của kho Đồng nai
        if self.warehouse_id.x_auto_done == True:
            for i in self.import_result_ids:
                for j in i.produced_products:
                    if j.picking_id:
                        j.create_kcs()
                        j.picking_id.btt_loads()
                        self.update_qc(j.picking_id.kcs_line , j)
                        
                        #Kiệt done Phiếu chất lượng
                        j.picking_id.btt_approved()
                        
                        #Tạo stack phiếu kho
                        
                        for move_live in j.picking_id.move_line_ids_without_package:
                            if not move_live.lot_id:
                                var = {
                                    'product_id':move_live.product_id.id,
                                    'company_id':warehouse_id.company_id.id or False,
                                    'zone_id': j.zone_id.id,
                                    'date':self.date_result,
                                    'name':'/',
                                    # 'stack_type':this.stack_type,
                                  }
                            # if pick_info.warehouse_id.x_is_bonded:
                            #     var.update({'is_bonded': True})
                            lot_id = self.env['stock.lot'].create(var)
                            
                            move_live.lot_id = lot_id and lot_id.id or False
                        j.picking_id.date_done = self.date_result
                        j.picking_id.button_sd_validate()
                        
                        #Cập nhật chất lượng cho nghiệp vụ 
                    # for j in i.picking_id.request_kcs_line:
                    #     j.
                    
            
    
    def report_kqsx(self):
        self.import_file()
    
    def report_summary_production(self):
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = 'wizard.import.production.result'
        data['form'] = self.read([])[0]
        return {'type': 'ir.actions.report.xml', 'report_name': 'report_summary_production' , 'datas': data}
    
    def unlinknk_production_result(self):
        self.import_result_ids.unlink()
                      
    def import_file(self):
        flag = flag_finish = False
#         supplierinfo = self.env['product.supplierinfo']
#         pricelist_ids = []
        success = failure = 0
#         warning = False
        mrp_pro_temp = []
        self.unlinknk_production_result()
        for this in self:
            try:
                recordlist = base64.decodebytes(this.file)
                excel = xlrd.open_workbook(file_contents = recordlist)
                sh = excel.sheet_by_index(0)
                  
            except  ValidationError:
                raise UserError(('Please select Filesssssss'))
            if sh:
                production_ids =[]
                empl_ids = []
                finish_ids = {}
                for row in range(sh.nrows):
                    if sh.cell(row,0).value == 'CODE':
                        flag = True
                        continue
                    if flag:
                        emp_obj = self.env['hr.employee'].search([('code','=', sh.cell(row,0).value)])
                        if emp_obj:
                            empl_ids.append({'emp_id': emp_obj.id,
                                             'job_id': emp_obj.job_id.id or False,
                                             'department_id': emp_obj.department_id.id or False,
                                             'hour_nbr': sh.cell(row,5).value,
                                             'ot_hour': sh.cell(row,6).value
                                            })
                        else:
#                             raise UserError(_("Employee %s do not exist")%sh.cell(row,0).value)
                            flag = False
                    print(sh.cell(row,0).value)
                    if sh.cell(row,0).value == 'BT Code Mẻ Sản Xuất':
                        flag_finish = True
                        continue
                    if flag_finish:
                        product_code = sh.cell(row,2).value
                        packing = sh.cell(row,7).value
                        pending_grp = sh.cell(row,1).value
                        packing = packing.strip()
                        production_name = sh.cell(row,0).value
                        production_name = production_name.strip()
                        product_obj = self.env['product.product'].search([('default_code','=', product_code.strip())])
                        packing = self.env['ned.packing'].search([('name','=', packing), ('active','=',True)], limit=1)
                        contract_no = self.env['shipping.instruction'].search([('name','=', sh.cell(row,9).value)])
                        production_id = self.env['mrp.production'].search([('name','=', production_name)])
                        qty_bag = sh.cell(row,8).value
                        lot = sh.cell(row,10).value or False
                        inspector = False
                        zone = False
                        if production_id:
                            if production_id not in production_ids:
                                production_ids.append(production_id)
                                
                            zone = self.env['stock.zone'].search([
                                ('name', '=', sh.cell(row, 6).value),
                                ('warehouse_id', '=', self.warehouse_id.id)
                            ])
                        if sh.cell(row, 38).value:
                            inspector = self.env['x_inspectors.kcs'].search([
                                ('name', '=', sh.cell(row, 38).value)
                            ])
                            if not inspector:
                                inspector = self.env['x_inspectors.kcs'].create({
                                    'name': sh.cell(row, 38).value
                                })
                        if product_obj:
                            if production_id.id in finish_ids:
                                tmp = { 'product_id': product_obj.id,
                                        'zone_id': zone.id if zone else False,
                                        'packing_id': packing.id,
                                        'qty_bags': qty_bag,
                                        'product_uom': product_obj.uom_id.id,
                                        'product_qty': sh.cell(row,4).value,
                                        'production_weight': sh.cell(row,5).value,
                                        'si_id': contract_no.id,
                                        'notes':lot,
                                        'production_id':production_id.id,
                                        'pending_grn':pending_grp}
                                try:
                                    tmp.update({
                                        'mc': sh.cell(row,11).value or False,
                                        'fm': sh.cell(row,12).value or False,
                                        'black': sh.cell(row,13).value or False,
                                        'broken':sh.cell(row,14).value or False,
                                        'brown' :sh.cell(row,15).value or False,
                                        'mold': sh.cell(row,16).value or False,
                                        'cherry':sh.cell(row,17).value or False,
                                        'excelsa': sh.cell(row,18).value or False,
                                        'screen20': sh.cell(row,19).value or False,
                                        'screen19':sh.cell(row,20).value or False,
                                        'screen18':sh.cell(row,21).value or False,
                                        'screen17':sh.cell(row,22).value or False,
                                        'screen16':sh.cell(row,23).value or False,
                                        'screen15':sh.cell(row,24).value or False,
                                        'screen14':sh.cell(row,25).value or False,
                                        'screen13':sh.cell(row,26).value or False,
                                        'screen12':sh.cell(row,27).value or False,
                                        'below_screen12':sh.cell(row,28).value or False,
                                        'immature':sh.cell(row,29).value or False,
                                        'burn':sh.cell(row,30).value or False,
                                        'insect': sh.cell(row,31).value or False,
                                        'stone':sh.cell(row,32).value or False,
                                        'stick':sh.cell(row,33).value or False,
                                        'remarks':sh.cell(row,34).value or False,
                                        'remark_note':sh.cell(row,35).value or False,
                                        'sampler':sh.cell(row,36).value or False,
                                        'x_bulk_density': sh.cell(row, 37).value or False,
                                        'x_inspector': inspector.id if inspector else False,
                                        'state_kcs': 'approved'
                                        })
                                except:
                                    tmp.update({'state_kcs': 'draft'})
                                finish_ids[production_id.id].append(tmp)

                            else:
                                finish_ids[production_id.id] = []
                                
                                tmp = { 'product_id': product_obj.id,
                                        'zone_id': zone.id if zone else False,
                                        'packing_id': packing.id,
                                        'qty_bags': qty_bag,
                                        'product_uom': product_obj.uom_id.id,
                                        'product_qty': sh.cell(row,4).value,
                                        'production_weight': sh.cell(row,5).value,
                                        'si_id': contract_no.id,
                                        'notes':lot,
                                        'pending_grn':pending_grp}
                                try:
                                    tmp.update({ 'mc': sh.cell(row,11).value or False,
                                                'fm': sh.cell(row,12).value or False,
                                                'black': sh.cell(row,13).value or False,
                                                'broken':sh.cell(row,14).value or False,
                                                'brown' :sh.cell(row,15).value or False,
                                                'mold': sh.cell(row,16).value or False,
                                                'cherry':sh.cell(row,17).value or False,
                                                'excelsa': sh.cell(row,18).value or False,
                                                'screen20': sh.cell(row,19).value or False,
                                                'screen19':sh.cell(row,20).value or False,
                                                'screen18':sh.cell(row,21).value or False,
                                                'screen17':sh.cell(row,22).value or False,
                                                'screen16':sh.cell(row,23).value or False,
                                                'screen15':sh.cell(row,24).value or False,
                                                'screen14':sh.cell(row,25).value or False,
                                                'screen13':sh.cell(row,26).value or False,
                                                'screen12':sh.cell(row,27).value or False,
                                                'below_screen12':sh.cell(row,28).value or False,
                                                'immature':sh.cell(row,29).value or False,
                                                'burn':sh.cell(row,30).value or False,
                                                'insect': sh.cell(row,31).value or False,
                                                'stone':sh.cell(row,32).value or False,
                                                'stick':sh.cell(row,33).value or False,
                                                'remarks':sh.cell(row,34).value or False,
                                                'remark_note':sh.cell(row,35).value or False,
                                                'sampler':sh.cell(row,36).value or False,
                                                'x_bulk_density': sh.cell(row, 37).value or False,
                                                'x_inspector': inspector.id if inspector else False,
                                                'state_kcs': 'approved'
                                                })
                                except:
                                    tmp.update({'state_kcs': 'draft'})
                                finish_ids[production_id.id].append(tmp)
                        else:
#                             raise UserError(_("Product %s do not exist")%(product_code))
                            flag_finish = False
                      
                temp = []
                for production in production_ids:
                    # production_name = sh.cell(row, 0).value
                    # production_name = production_name.strip()
                    # mrp_pro_obj = self.env['mrp.production'].search([('name','=', production_name)])
                    production_id = production
                    
                    # mrp_pro_temp.append(mrp_pro_obj.id)
                    list =  ['message_follower_ids', 'date_result' ,'create_date', 'resource_id', 'write_uid', 'create_uid', 
                             'direct_labour', 'message_ids', 'note', 'state', 'start_date', 'produced_products', 'end_date', 'hours', 
                             'write_date', 'calendar_id', 'name', 'consumed_products', 'operation_id'
                            ]
                    vals = self.env['mrp.operation.result'].default_get(list)
                    # vals['operation_id'] = workcenter_line.id
                    # vals['resource_id'] = workcenter_line.workcenter_id.id
                    vals['end_date'] = vals['start_date']
                    vals['production_shift']= self.production_shift
                    vals['user_import_id']= self.env.user.id
                    vals['date_result'] = self.date_result
                    vals['import_result_id'] = self.id
                    vals['production_id'] =  production_id.id
                    vals['warehouse_id'] = self.warehouse_id.id
                    # vals['resource_calendar_id']= self.resource_calendar_id and self.resource_calendar_id.id or False
                    result_id = self.env['mrp.operation.result'].create(vals)
                    temp.append(result_id.id)
                      
                    for i in empl_ids:
                        i.update({'result_id': result_id.id})
                        self.env['direct.labour'].create(i)
                          
                    # production_id = self.env['mrp.production'].search([('name','=', production_name)])
                    for i in finish_ids[production_id.id]:
                        i.update({'operation_result_id': result_id.id, 'state_kcs': 'draft'})
                        new_id = self.env['mrp.operation.result.produced.product'].create(i)
          
        # imd = self.env['ir.model.data']
        # action = imd.xmlid_to_object('general_mrp_operations.action_mrp_operation_result')
        # list_view_id = imd.xmlid_to_res_id('general_mrp_operations.view_mrp_operation_result_tree')
        # form_view_id = imd.xmlid_to_res_id('general_mrp_operations.view_mrp_operation_result_form')
        #
        # result = {
        #     'name': action.name,
        #     'help': action.help,
        #     'type': action.type,
        #     'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'calendar'], [False, 'pivot']],
        #     'target': action.target,
        #     'context': action.context,
        #     'res_model': action.res_model,
        # }
        # if len(temp) > 1:
        #     result['domain'] = "[('id','in',%s)]" % temp
        # elif len(temp) == 1:
        #     result['views'] = [(form_view_id, 'form')]
        #     result['res_id'] = temp[0]
        # else:
        #     result = {'type': 'ir.actions.act_window_close'}
        # return result