# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError
import time
from datetime import timedelta
from lxml import etree
import base64
import xlrd
from odoo.exceptions import UserError, ValidationError

class wizard_import_production_result(models.Model):
    _name = "wizard.import.production.result"
    
    file =  fields.Binary('File', help='Choose file Excel', copy=False)
    file_name =  fields.Char('Filename', size=100, readonly=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    result_id = fields.Many2one('mrp.operation.result')
    production_shift =fields.Selection([
                        ('1','Ca 1'),
                        ('2','Ca 2'),
                        ('3','Ca 3'),], 'Ca', required=True, default="1" )
    
    production_id = fields.Many2one('mrp.production')
    # resource_calendar_id = fields.Many2one('mrp.resource.calendar','Working Time')
    user_id = fields.Many2one('res.users', string='User',copy=False)
    
    
    def report_kqsx(self):
        self.import_file()
    
    def report_summary_production(self):
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = 'wizard.import.production.result'
        data['form'] = self.read([])[0]
        return {'type': 'ir.actions.report.xml', 'report_name': 'report_summary_production' , 'datas': data}
        
                      
    def import_file(self):
        flag = flag_finish = False
#         supplierinfo = self.env['product.supplierinfo']
#         pricelist_ids = []
#         success = failure = 0
#         warning = False
        mrp_pro_temp = []
        for this in self:
            try:
                recordlist = base64.decodestring(this.file)
                excel = xlrd.open_workbook(file_contents = recordlist)
                sh = excel.sheet_by_index(0)
                  
            except Exception as e:
                raise UserError("Error while importing the file: {}".format(str(e)))
            if sh:
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
                      
                    if sh.cell(row,0).value == u'BT Code Mẻ Sản Xuất':
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
                            zone = self.env['stock.zone'].search([
                                ('name', '=', sh.cell(row, 6).value),
                                ('warehouse_id', '=', production_id.warehouse_id.id)
                            ])
                        if sh.cell(row, 38).value:
                            inspector = self.env['x_inspectors.kcs'].search([
                                ('x_name', '=', sh.cell(row, 38).value)
                            ])
                            if not inspector:
                                inspector = self.env['x_inspectors.kcs'].create({
                                    'x_name': sh.cell(row, 38).value
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
                                
                                tmp = {'product_id': product_obj.id,
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
                for row in range(sh.nrows):
                    production_name = sh.cell(row, 0).value
                    production_name = production_name.strip()
                    mrp_pro_obj = self.env['mrp.production'].search([('name','=', production_name)])
                    for workcenter_line in mrp_pro_obj.workcenter_lines:
                        if mrp_pro_obj.id in mrp_pro_temp:
                            continue
                        else:
                            mrp_pro_temp.append(mrp_pro_obj.id)
                        list =  ['message_follower_ids', 'create_date', 'resource_id', 'write_uid', 'create_uid', 
                                 'direct_labour', 'message_ids', 'note', 'state', 'start_date', 'produced_products', 'end_date', 'hours', 
                                 'write_date', 'calendar_id', 'name', 'consumed_products', 'operation_id'
                                ]
                        vals = self.env['mrp.operation.result'].default_get(list)
                        vals['operation_id'] = workcenter_line.id
                        vals['resource_id'] = workcenter_line.workcenter_id.id
                        vals['end_date'] = vals['start_date']
                        vals['production_shift']= self.production_shift
                        vals['user_import_id']= self.env.user.id
                        vals['resource_calendar_id']= self.resource_calendar_id and self.resource_calendar_id.id or False
                        result_id = self.env['mrp.operation.result'].create(vals)
                        temp.append(result_id.id)
                          
                        for i in empl_ids:
                            i.update({'result_id': result_id.id})
                            self.env['direct.labour'].create(i)
                              
                        production_id = self.env['mrp.production'].search([('name','=', production_name)])
                        for i in finish_ids[production_id.id]:
                            i.update({'operation_result_id': result_id.id, 'state_kcs': 'draft'})
                            self.env['mrp.operation.result.produced.product'].create(i)
          
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('general_mrp_operations.action_mrp_operation_result')
        list_view_id = imd.xmlid_to_res_id('general_mrp_operations.view_mrp_operation_result_tree')
        form_view_id = imd.xmlid_to_res_id('general_mrp_operations.view_mrp_operation_result_form')
  
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(temp) > 1:
            result['domain'] = "[('id','in',%s)]" % temp
        elif len(temp) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = temp[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result