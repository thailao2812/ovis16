# -*- coding: utf-8 -*-
from datetime import datetime
import time
from openerp.osv import osv
from openerp.report import report_sxw
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
from openerp import SUPERUSER_ID

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.from_date = False
        self.to_date = False
        self.localcontext.update({
            'get_date':self.get_date,
            'get_line_traffic':self.get_line_traffic,
            'get_destart':self.get_destart,
            'get_line_stack':self.get_line_stack,
            'get_destrt':self.get_destrt,
            'get_line_p_contract':self.get_line_p_contract,
            'get_real_qty_gdn':self.get_real_qty_gdn
        })
        
    def get_line_traffic(self):
        self.get_header()
        traffic_contract = self.pool.get('traffic.contract').search(self.cr,1, [('start_of_ship_period','>=',self.from_date),('start_of_ship_period','<=',self.to_date)])
        traffic_obj = self.pool.get('traffic.contract').browse(self.cr,1,traffic_contract)
        return traffic_obj
    
    def get_line_p_contract(self):
        self.get_header()
        traffic_contract = self.pool.get('s.contract').search(self.cr,1, [('type','=','p_contract'),('date','>=',self.from_date),('date','<=',self.to_date)])
        traffic_obj = self.pool.get('s.contract').browse(self.cr,1,traffic_contract)
        return traffic_obj
    
    def get_line_stack(self):
        traffic_contract = self.pool.get('stock.lot').search(self.cr,1, [('is_bonded','=',True),('date','>=',self.from_date),('date','<=',self.to_date)])
        traffic_obj = self.pool.get('stock.lot').browse(self.cr,1,traffic_contract)
        return traffic_obj
        
    def get_destart(self):
        self.get_header()
        return self.get_date(self.from_date)
    
    def get_destrt(self):
        self.get_header()
        return self.get_date(self.to_date)
    
    def get_real_qty_gdn(self,p_contract_id):
        qty = 0
        if not p_contract_id:
            return 0.0
        else:
            [('shipping_id','!=',False),('type','=','export')]
            contract_id = self.pool.get('sale.contract').search(self.cr,1,[('shipping_id','!=',False),('type','=','export'),('contract_p_id','=',p_contract_id.id)])
            contract = self.pool.get('sale.contract').browse(self.cr,1,contract_id)
            for i in contract:
                if i.picking_id:
                    qty += i.picking_id.total_qty
            return qty

    def get_date(self, date):
        try:
            if not date:
                date = time.strftime(DATE_FORMAT)
            date = datetime.strptime(date, DATE_FORMAT)
            return date.strftime('%d/%m/%Y')
        except Exception as e:
            date = time.strftime(DATE_FORMAT)
            date = datetime.strptime(date, DATE_FORMAT)
            return date.strftime('%m/%d/%Y')
        
    
    def get_datetime(self, date):
        if not date:
            date = time.strftime(DATETIME_FORMAT)
        date = datetime.strptime(date, DATETIME_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        self.from_date = wizard_data['date_from'] or False
        self.to_date = wizard_data['date_to'] or False
        return True
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
