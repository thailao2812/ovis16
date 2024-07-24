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
    _inherit = "wizard.import.production.result"
    
    def import_file(self):
        flag = flag_finish = False
#         supplierinfo = self.env['product.supplierinfo']
#         pricelist_ids = []
        success = failure = 0
#         warning = False
        mrp_pro_temp = []
        # self.unlinknk_production_result()
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
                            ], limit = 1)
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
                        new_id.create_update_stack_wip()
          
