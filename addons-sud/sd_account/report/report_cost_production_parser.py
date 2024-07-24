# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser

import datetime
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

import datetime
from datetime import datetime
from pytz import timezone
import time
from datetime import datetime, timedelta

class Parser(models.AbstractModel):
    _name = 'report.report_cost_productions'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_cost_productions'
    

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        global case_sql
        case_sql =False
        
        localcontext.update({
            'get_line':self.get_line,
            'get_total_qty':self.get_total_qty,
            'getmo_name':self.getmo_name
        })
        return localcontext
    
    def get_line(self,this):
        vark =[]
        for line in this.production_order_ids:
            varGrp =[]
            varGrn =[]
            
            tm= {
                'grp_default_code':'',
                'grp_mo_name':'',
                'grn_mo_name':'',
                'grp':'',
                'grp_init_qty':'',
                'grp_product_uom_qty':'',
                'grp_date':'',
                'grn':'',
                'grn_init_qty':'',
                'grn_product_uom_qty':'',
                'grn_date':'',
                'grn_default_code':''
            }
            vark.append(tm)
            
            sql='''
                SELECT sp.date_done grn_date,pp.default_code,
                    sp.name grn,sm.init_qty grn_init_qty,sm.qty_done grn_product_uom_qty
                    FROM stock_move_line  sm
                        join stock_picking sp on sm.picking_id = sp.id
                        join stock_picking_type spt on sp.picking_type_id = spt.id
                        join product_product pp on pp.id = sm.product_id
                    where 
                        sm.material_id = %s
                        and spt.code ='production_out'
                        and sm.state ='done'
                        and qty_done !=0
                        and init_qty !=0
                        and pp.default_code not in ('FR','GTR-13B2','GTR-13B3','GTR-16B2','GTR-16B3','GTR-18B2','GTR-18B3','HUSKS','PCR','STONES','WP Dust')
                    order by sp.date_done asc
            '''%(line['id'])
            self.env.cr.execute(sql)
            for i in self.env.cr.dictfetchall():
                varGrn.append({
                    'grn_mo_name':line['name'],
                    'grn':i['grn'],
                    'grn_init_qty':i['grn_init_qty'],
                    'grn_product_uom_qty':i['grn_product_uom_qty'],
                    'grn_date':self.get_date(i['grn_date']),
                    'grn_default_code':i['default_code']
                })
            
            
            sql='''
                SELECT sp.name picking_name, init_qty grp_init_qty,qty_done grp_product_uom_qty,sm.date grp_date,pp.default_code
                FROM stock_move_line sm 
                    join stock_picking sp on sm.picking_id = sp.id
                    join stock_picking_type spt on sp.picking_type_id = spt.id
                    join product_product pp on sm.product_id = pp.id
                where sm.finished_id = %s
                    and sm.state ='done'
                    and qty_done !=0
                    and init_qty !=0
                    and spt.code ='production_in'
                    and pp.default_code not in ('FR','GTR-13B2','GTR-13B3','GTR-16B2','GTR-16B3','GTR-18B2','GTR-18B3','HUSKS','PCR','STONES','WP Dust')
                order by sp.date_done asc
            '''%(line['id'])
            self.env.cr.execute(sql)
            for i in self.env.cr.dictfetchall():
                varGrp.append({
                    'grp_default_code':i['default_code'],
                    'grp_mo_name':line['name'],
                    'grp':i['picking_name'],
                    'grp_init_qty':i['grp_init_qty'],
                    'grp_product_uom_qty':i['grp_product_uom_qty'],
                    'grp_date':self.get_date(i['grp_date'])
                })
            if len(varGrn) > len(varGrp):
                for i in varGrn:
                    if varGrp:
                        i.update(varGrp.pop())
                        vark.append(i)
                    else:
                        Grn_tm ={
                            'grp_default_code':'',
                            'grp_mo_name':line['name'],
                            'grp':'',
                            'grp_init_qty':'',
                            'grp_product_uom_qty':'',
                            'grp_date':''
                        }
                        i.update(Grn_tm)
                        vark.append(i)
            else:
                for i in varGrp:
                    if varGrn:
                        i.update(varGrn.pop())
                        vark.append(i)
                    else:
                        Grn_tm ={
                            'grn_mo_name':line['name'],
                            'grn':'',
                            'grn_init_qty':'',
                            'grn_product_uom_qty':'',
                            'grn_date':'',
                            'grn_default_code':''
                        }
                        i.update(Grn_tm)
                        vark.append(i)
                    
        
        return vark
    
    
    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        
        date = date_user_tz.strftime('%d/%m/%Y')
        
        return date

    
    def get_total_qty(self,this):
        
        total_qty = 0
        for i in this.premium_ids:
            total_qty += i.product_qty 
        
        return total_qty
    
    def getmo_name(self,grn_mo,grp_mo):
        if grn_mo:
            return grn_mo
        else:
            return grp_mo
    
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
