# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re

import base64
import xlrd
from datetime import datetime
from xlrd import open_workbook

class WizardPssManagementNestle(models.TransientModel):
    _name = "wizard.pss.management.nestle"

    file = fields.Binary('File', help='Choose file Excel')
    file_name = fields.Char('Filename', readonly=True)
    
    def map_datetime(self, ddate=False, datemode=False):
        result = False
        try:
            if ddate:
                tmp = xlrd.xldate_as_tuple(ddate, datemode)
                
                result = datetime(int(tmp[0]), int(tmp[1]), int(tmp[2]))
        except:
            if ddate and datemode:
                try:
                    result = datetime(*xlrd.xldate_as_tuple(ddate, datemode))
                except:
                    pass
        return result
    
    def import_pss_management(self):
        pss_management_ids = []
        result = False
        for this in self:

            try:
                recordlist = base64.decodestring(this.file)
                excel = xlrd.open_workbook(file_contents=recordlist)
                #wb = open_workbook(temp_path)
                sh = excel.sheet_by_index(0)
                warehouse_id = False
                si_no_id = False
                customer_id = False
                product_id = False

            except Exception as e:
                raise UserError(_('Warning !!!'))
            if sh:
                for row in range(sh.nrows):
                    if row > 0:
                        # Đọc thông tin file
                        warehouse = sh.cell(row, 0).value or False
                        pss_name = sh.cell(row, 1).value or False
                        si_no = sh.cell(row, 2).value or False
                        date_pss = sh.cell(row, 3).value or False
                        date_sent = sh.cell(row, 4).value or False
                        pss_status = sh.cell(row, 5).value or False
                        date_result = sh.cell(row, 6).value or False
                        buyer_ref = sh.cell(row, 7).value or False
                        quantity = sh.cell(row, 8).value or False
                        cont_qty = sh.cell(row, 9).value or False
                        mc = sh.cell(row, 10).value or False
                        fm = sh.cell(row, 11).value or False
                        black = sh.cell(row, 12).value or False
                        broken = sh.cell(row, 13).value or False
                        brown = sh.cell(row, 14).value or False
                        moldy = sh.cell(row, 15).value or False
                        burned = sh.cell(row, 16).value or False
                        sc20 = sh.cell(row, 17).value or False
                        sc19 = sh.cell(row, 18).value or False
                        sc18 = sh.cell(row, 19).value or False
                        sc16 = sh.cell(row, 20).value or False
                        sc13 = sh.cell(row, 21).value or False
                        bel_sc12 = sh.cell(row, 22).value or False
                        bulk = sh.cell(row, 23).value or False
                        cuptaste = sh.cell(row, 24).value or False
                        inspector = sh.cell(row, 25).value or False
                        buyer_com = sh.cell(row, 26).value or False
                        our_com = sh.cell(row, 27).value or False
                        staff = sh.cell(row, 28).value or False

                        if warehouse:
                            warehouse_id = self.env['stock.warehouse'].search([('code', '=', warehouse.strip())])
                        if si_no:
                            si_no_id = self.env['shipping.instruction'].search([('name', '=', si_no.strip())])
                        if date_pss:
                            date_pss = self.map_datetime(date_pss, excel.datemode)
                        #     date_pss = self.map_datetime(ddate, datemode)
                        #     date_pss = (date_pss - 25569) * 86400.0
                        #     date_pss = datetime.utcfromtimestamp(date_pss).date()
                        # if date_sent:
                        #     date_sent = (date_sent - 25569) * 86400.0
                        #     date_sent = datetime.utcfromtimestamp(date_sent).date()
                        # if date_result:
                        #     date_result = (date_result - 25569) * 86400.0
                        #     date_result = datetime.utcfromtimestamp(date_result).date()
                        if si_no_id:
                            customer_id = si_no_id.partner_id.id if si_no_id.partner_id else False
                            product_id = si_no_id.shipping_ids[0].product_id.id if si_no_id.shipping_ids else False
                        val = {
                            'name': pss_name,
                            'x_ex_warehouse_id': warehouse_id.id if warehouse_id else False,
                            'shipping_id': si_no_id.id if si_no_id else False,
                            'partner_id': customer_id or False,
                            'product_id': product_id or False,
                            'created_date': date_pss,
                            'date_sent': date_sent,
                            'pss_status': pss_status,
                            'date_result': date_result,
                            'buyer_ref': buyer_ref,
                            'lot_quantity': quantity,
                            'cont_quantity': cont_qty,
                            'mc': mc,
                            'fm': fm,
                            'black': black,
                            'broken': broken,
                            'brown': brown,
                            'moldy': moldy,
                            'burned': burned,
                            'scr20': sc20,
                            'scr19': sc19,
                            'scr18': sc18,
                            'scr16': sc16,
                            'scr13': sc13,
                            'blscr12': bel_sc12,
                            'x_bulk_density': bulk,
                            'note': cuptaste,
                            'inspector': inspector,
                            'buyer_comment': buyer_com,
                            'our_comment': our_com,
                            'qc_staff': staff,
                            'is_nestle': True,

                        }
                        new_id = self.env['pss.management'].create(val)
                        pss_management_ids.append(new_id.id)
        if pss_management_ids:
            imd = self.env['ir.model.data']
            action = imd.xmlid_to_object('sd_quality.action_wizard_pss_management')
            list_view_id = imd.xmlid_to_res_id('sd_quality.view_pss_management_nestle')
            result = {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'views': [[list_view_id, 'tree']],
                'target': action.target,
                'context': action.context,
                'res_model': action.res_model,
                'domain': "[('id','in',%s)]" % pss_management_ids
            }
        return result



class WizardKcsGlyphosat(models.TransientModel):
    _name = "wizard.kcs.glyphosat"
    
    file = fields.Binary('File', help='Choose file Excel')
    file_name =  fields.Char('Filename', readonly=True)
    user_id = fields.Many2one('res.users', string = "Create By")
    date = fields.Date(string="Create Date")

    def import_glyphosat(self):
        glyphosate_ids = []
        result =False
        for this in self:
            
            try:
                recordlist = base64.decodestring(this.file)
                excel = xlrd.open_workbook(file_contents = recordlist)
                sh = excel.sheet_by_index(0)
                warehouse_id = False
                si_no_id = False
                customer_id =False
                product_id = False
                stack_id = False
                
            except Exception:
                raise UserError(_('Warning !!!'))
            if sh:
                for row in range(sh.nrows):
                    if row > 0:
                        #Đọc thông tin file
                        pss_name = sh.cell(row,0).value or False
                        warehouse = sh.cell(row,1).value or False
                        si_no = sh.cell(row,2).value or False
                        customer = sh.cell(row,3).value or False
                        product = sh.cell(row,4).value or False
                        test_requirement = sh.cell(row,5).value or False
                        date_sent = sh.cell(row,6).value or False
                        pss_status = sh.cell(row,7).value or False
                        date_result = sh.cell(row,8).value or False
                        quantity = sh.cell(row,9).value or False
                        cont_qty = sh.cell(row,10).value or False
                        stack_no = sh.cell(row,11).value or False
                        original = sh.cell(row,12).value or False
                        our_comment = sh.cell(row,13).value or False
                        analysis_by = sh.cell(row,14).value or False
                        results    = sh.cell(row,15).value or False
                        inspector_by = sh.cell(row,16).value or False
                        qc_staff = sh.cell(row,17).value or False
                        remark = sh.cell(row,18).value or False
                        
                        if warehouse:
                            warehouse_id = self.env['stock.warehouse'].search([('code','=',warehouse.strip())])
                        if si_no:
                            si_no_id = self.env['shipping.instruction'].search([('name','=',si_no.strip())])
                        if customer:
                            customer_id = self.env['res.partner'].search([('name','=',customer.strip())])
                        if product:
                            product_id = self.env['product.product'].search([('default_code','=',product.strip())])
                        if stack_no:
                            stack_id = self.env['stock.lot'].search(['|',('name','=',stack_no.strip()),('code','=',stack_no.strip())])
                        if date_sent:
                            date_sent = (date_sent - 25569) * 86400.0
                            date_sent = datetime.utcfromtimestamp(date_sent).date()
                        if date_result:
                            date_result = (date_result - 25569) * 86400.0
                            date_result = datetime.utcfromtimestamp(date_result).date()
                        val ={
                            'name':pss_name,
                            'warehouse_id':warehouse_id and warehouse_id.id or False,
                            'si_id': si_no_id and si_no_id.id or False,
                            'customer_id':customer_id and customer_id.id or False,
                            'product_id':product_id and product_id.id or False,
                            'test_requirement':test_requirement,
                            'date_sent': date_sent,
                            'pss_status':pss_status,
                            'date_result': date_result,
                            'quantity':quantity,
                            'cont_qty':cont_qty,
                            'stack_no':stack_id and stack_id.id or False,
                            'original':original,
                            'our_comment':our_comment,
                            'analysis_by':analysis_by,
                            'results':results,
                            'inspector_by':inspector_by,
                            'qc_staff':qc_staff,
                            'remark':remark,
                        }
                        new_id = self.env['kcs.glyphosate'].create(val)
                        glyphosate_ids.append(new_id.id)
        result = False           
        if glyphosate_ids:
            action = self.env.ref('sd_quality.action_kcs_glyphosate')
            result = action.read()[0]
            if len(glyphosate_ids) > 1:
                result['domain'] = "[('id','in',[" + ','.join(map(str, glyphosate_ids)) + "])]"
            elif len(glyphosate_ids) == 1:
                res = self.env.ref('sd_quality.view_kcs_glyphosate_tree', False)
                result['context'] = {}
                result['views'] = [(res and res.id or False, 'tree')]
                result['res_id'] = glyphosate_ids and glyphosate_ids[0] or False
            
            
        return result
    
    
        
