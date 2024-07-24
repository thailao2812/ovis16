# -*- coding: utf-8 -*-

import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
import time
import base64
import xlrd
from base64 import b64encode
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class ImportPContract(models.TransientModel):
    _name = "import.p.contract"

    file = fields.Binary('File', help='Choose file Excel')
    file_name = fields.Char('Filename', readonly=True)

    def import_p_contract(self):
        try:
            recordlist = base64.decodestring(self.file)
            excel = xlrd.open_workbook(file_contents=recordlist)
            lst_sheet = excel.sheet_names()
            sh = excel.sheet_by_index(0)
            if len(lst_sheet) > 1:
                sh2 = excel.sheet_by_index(1)
        except ImportError:
            raise UserError(_('Warning!'), str(ImportError))
        if sh:
            num_of_rows = sh.nrows
            p_contract_ids = []
            for row in range(1, num_of_rows):
                contract = self.env['s.contract']
                line = self.env['s.contract.line']
                mess = ""
                value = {}
                line_value = {}
                name = sh.cell(row, 0).value
                partner_code = (sh.cell(row, 1).value).strip()
                currency = sh.cell(row, 2).value
                product_code = sh.cell(row, 3).value
                quantity = sh.cell(row, 4).value
                market_price = sh.cell(row, 5).value
                p_contract_differencial = sh.cell(row, 6).value
                packing_name = sh.cell(row, 7).value
                entry_date = sh.cell(row, 8).value
                
                if isinstance(entry_date, float):
                    entry_date = sh.cell(row, 8).value and datetime(*xlrd.xldate_as_tuple(sh.cell(row, 8).value, excel.datemode)) or False
                    
                if not packing_name:
                    mess += 'Please input Packing name for P Contract in line %s\n' % (row + 1)
                if packing_name:
                    packing = self.env['ned.packing'].search([
                        ('name', '=', packing_name.strip())
                    ])
                    if not packing:
                        mess += 'Please Check your packing name for P Contract in line %s\n' % (row + 1)
                    if len(packing) > 1:
                        mess += 'Please contact Administrator to check Packing name Duplicate in line %s\n' % (row + 1)
                    else:
                        line_value.update({
                            'packing_id': packing.id
                        })
                if not entry_date:
                    mess += 'Please input Entry Date for P Contract in line %s\n' % (row + 1)
                else:
                    # tes = (entry_date + relativedelta(months=9)).date()
                    date_entry = datetime.strptime(entry_date, '%d/%m/%Y')
                    value.update({
                        'date': date_entry.date(),
                        'shipment_date':  (date_entry + relativedelta(months=9)).date()
                    })
                if not name:
                    mess += 'Please input name for P Contract in line %s\n' % (row + 1)
                value.update({
                    'name': name,
                    'type': 'p_contract'
                })
                line_value.update({
                    'product_qty': quantity,
                    'market_price': market_price,
                    'p_contract_diff': p_contract_differencial
                })
                if partner_code:
                    customer = self.env['res.partner'].search([
                        ('partner_code', '=', partner_code)
                    ])
                    if not customer:
                        mess += 'Customer cannot find, please check again your partner code in line %s\n' % (row + 1)
                    if len(customer) > 1:
                        mess += 'Customer find more than 1, please check again your partner code in line %s\n' % (row + 1)
                    else:
                        value.update({
                            'partner_id': customer.id
                        })
                if not currency:
                    mess += 'Please input Currency name for P Contract in line %s\n' % (row + 1)
                if currency:
                    currency_id = self.env['res.currency'].search([
                        ('name', '=', currency.strip())
                    ])
                    if not currency_id:
                        mess += 'Currency cannot find, please check again your currency name in line %s\n' % (row + 1)
                    if len(currency_id) > 1:
                        mess += 'Currency find more than 1, please check again your currency name in line %s\n' % (row + 1)
                    else:
                        value.update({
                            'currency_id': currency_id.id
                        })
                if not product_code:
                    mess += 'Please input product code for P Contract in line %s\n' % (row + 1)
                if product_code:
                    product = self.env['product.product'].search([
                        ('default_code', '=', product_code.strip())
                    ])
                    if not product:
                        mess += 'Product cannot find, please check again your product code in line %s\n' % (row + 1)
                    if len(product) > 1:
                        mess += 'Product find more than 1, please check again your product code in line %s\n' % (row + 1)
                    else:
                        line_value.update({
                            'product_id': product.id,
                            'product_uom': product.uom_id.id,
                            'name': product.name_get()[0][1]
                        })
                if not mess:
                    p_contract_check = self.env['s.contract'].search([
                        ('name', '=', value['name'].strip())
                    ])
                    if not p_contract_check:
                        p_contract = contract.create(value)
                        p_contract_ids.append(p_contract.id)
                        if p_contract:
                            line_value.update({
                                'p_contract_id': p_contract.id
                            })
                            s_contract_line = line.create(line_value)
                            if s_contract_line:
                                s_contract_line.onchange_bags_qty()
            if p_contract_ids:
                return self.action_view_p_contract(p_contract_ids)
        return True
    
    def action_view_p_contract(self, p_contract_ids):
        
        return  {
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 's.contract',
                'domain': [('id', 'in', p_contract_ids)],
                'target': 'current',
                'context': {}
            }
    
    
    
    