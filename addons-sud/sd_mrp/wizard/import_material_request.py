# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import float_round
import time
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta, datetime, date
import calendar
import xlrd
from lxml import etree
import base64
from xlrd import open_workbook


class SImportFile(models.Model):
    _name = "s.import.file"
    
    im_file = fields.Binary('Import')
    name = fields.Char('PIC', size=128)
    error = fields.Text('Error')
    
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
    
    def get_mrp_id(self):
        mrp_id = 0
        try:
            if  self._context.get('active_model', False) != 'traffic.contract':
                mrp_id = self.env['mrp.production'].browse(self._context.get('active_id'))
        except:
            pass
        return mrp_id
    
    mrp_id = fields.Many2one('mrp.production', 'Manufacturing Order', default=get_mrp_id)
    
    def convert_date(self, ddate):
        if not ddate:
            return ''
        tmp = str(ddate)
        tmp = tmp.split('-')
        day = tmp[0]
        month = tmp[1]
        year = tmp[2]
        if len(year) < 4:
            year = '20%s'%year
        return '%s-%s-%s' %(year, month, day)
    
    def import_material_request(self):
        mrp_obj = self.env['mrp.production']
        ware_obj = self.env['stock.warehouse']
        product_obj = self.env['product.product']
        wz_request = self.env['wizard.request.materials']
        wz_line = self.env['wizard.request.materials.line']
        stk_stack = self.env['stock.lot']
        
        for record in self:
            if record.im_file:
                filecontent = base64.b64decode(record.im_file)
                temp_path = '/tmp/import_material_request_%s.xls' % str(datetime.now())
                with open(temp_path, 'wb') as f:
                    f.write(filecontent)

                wb = open_workbook(temp_path)
                for sheet in wb.sheets():
                    number_of_rows = sheet.nrows
                    number_of_columns = sheet.ncols
                    items = []
                    rows = []
                    nrow = 0
                    idd = 0
                    for row in range(1, number_of_rows):
                        vals = {
                            'production_id': record.mrp_id and record.mrp_id.id or 0,
                            'request_user_id':self.env.uid,
                            'state':'draft'
                        }
                        nrow += 1
                                
                        if sheet.cell(row, 0).value:
                            warehouse_id = ware_obj.search([('code', '=', sheet.cell(row, 0).value)], limit=1)
                            warehouse_id = warehouse_id and warehouse_id.id or 0
                            if warehouse_id:
                                vals.update({'warehouse_id': warehouse_id})
                        if not idd:
                            idd = self.env['request.materials'].create(vals)
                            
                        vall = {'request_id': idd.id}
                        if sheet.cell(row, 1).value:
                            stack_id = stk_stack.search([('name', '=', sheet.cell(row, 1).value)], limit=1)
                            stack_id = stack_id and stack_id.id or 0
                            if stack_id:
                                vall.update({'stack_id': stack_id})

                        if sheet.cell(row, 2).value:
                            product_id = product_obj.search([('name', '=', sheet.cell(row, 2).value)], limit=1)
                            product_id = product_id and product_id.id or 0
                            prod_uom = product_id and product_obj.browse(product_id).uom_id.id or 0,
                            if product_id:
                                vall.update({'product_id': product_id, 'product_uom': prod_uom})
                        
                        if sheet.cell(row, 3).value:
                            vall.update({'product_qty': sheet.cell(row, 3).value})
                            
                        self.env['request.materials.line'].create(vall)
        return 1     
    
