# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang

from collections import defaultdict
from itertools import groupby
import json
import time


class WizardPrintInventory(models.TransientModel):
    _name = "wizard.print.inventory"
    _description = "Print Inventory"
                    
    # def print_report(self, cr, uid, ids, context=None): 
    #     datas = {'ids': context.get('active_ids', [])}
    #     datas['model'] = 'stock.picking'
    #     datas['form'] = {'active_ids':context.get('active_ids', [])}
    #     return {'type': 'ir.actions.report.xml', 'report_name': 'report_pending_grp' , 'datas': datas}
    

        
class WizardPrintRequestMaterials(models.TransientModel):
    _name = "wizard.print.request.materials"
    _description = "Print Request Materials"
    
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    production_id = fields.Many2one('mrp.production',string="Production")
    production_ids = fields.Many2many('mrp.production',string="Production")
                    
    def print_report(self): 
        return self.env.ref(
                'sd_inventory.report_print_request_materials').report_action(self)
                
        # datas = {'ids': context.get('active_ids', [])}
        # datas['model'] = 'wizard.print.request.materials'
        # datas['form'] = self.read(cr, uid, ids)[0]
        # return {'type': 'ir.actions.report.xml', 'report_name': 'report_print_request_materials' , 'datas': datas}
    #
    def print_request(self): 
        return self.env.ref(
                'sd_inventory.report_material_request_reports').report_action(self)
        # datas = {'ids': context.get('active_ids', [])}
        # datas['model'] = 'wizard.print.request.materials'
        # datas['form'] = self.read(cr, uid, ids)[0]
        # return {'type': 'ir.actions.report.xml', 'report_name': 'report_material_request_Reports' , 'datas': datas}
    
    
    
    
