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
    _name = 'report.batch_report_pnl_bta_parser'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.batch_report_pnl_bta_parser'
    

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        global case_sql
        case_sql =False
        
        case_sql = '''
                        CASE 
                        WHEN pp.default_code ilike 'G20%' THEN 1
                        WHEN pp.default_code ilike 'G19%' THEN 2
                        WHEN pp.default_code ilike 'G18%' THEN 3
                        WHEN pp.default_code ilike 'G16%' THEN 4
                        WHEN pp.default_code ilike 'G13%' THEN 5
                        WHEN pp.default_code ilike 'G3%' THEN 6
                        WHEN pc.code = 'Lowgrades' THEN 7
                        WHEN pc.code = 'Reject' THEN 8
                        ELSE 9
                        
                END'''
        
        
        localcontext.update({
            'get_total_inputs':self.get_total_inputs,
            'get_total_outputs':self.get_total_outputs,
            'get_analysis_input_total_outputs':self.get_analysis_input_total_outputs,
            'get_analysis_output_total_outputs':self.get_analysis_output_total_outputs,
            'get_analysis_loss_total_outputs':self.get_analysis_loss_total_outputs,
            'get_ned_crop':self.get_ned_crop,
            'get_product':self.get_product,
            'get_out_qc':self.get_out_qc,
            'get_total_in_qty':self.get_total_in_qty,
            'get_main_grade': self.get_main_grade,
            'get_sum_main_grade': self.get_sum_main_grade,
            'get_under_grade': self.get_under_grade,
            'get_sum_under_grade': self.get_sum_under_grade,
            'get_zero_grade': self.get_zero_grade,
            'get_sum_zero_grade': self.get_sum_zero_grade,
            'get_mimax_date': self.get_mimax_date,
            'get_total_in_date': self.get_total_in_date,
            'get_total_out_qty': self.get_total_out_qty,
            'get_total_stack_in': self.get_total_stack_in,
            'get_loss':self.get_loss,
            'get_loss_total':self.get_loss_total,
            'get_qty_faq':self.get_qty_faq
        })
        return localcontext
    
    def get_date(self, date):
        if not date:
            date = datetime.now()
        date_user_tz = self.env['res.users']._convert_user_datetime(
            fields.Datetime.to_string(date))
        
        date = date_user_tz.strftime('%d/%m/%Y')
        return date
    
    def get_ned_crop(self):
        sql ='''
            SELECT name FROM ned_crop where state ='current' limit 1
        '''
        self.env.cr.execute(sql)
        for i in self.env.cr.dictfetchall():
            return i['name'] or ''
        return ''
    
    def get_analysis_loss_total_outputs(self,o):
        basis = actual = var_usd = var =bom = 0
        val =[]
        for input in o.summary_ids:
            basis += input.basis or 0.0
            bom += input.bom
            var += input.var
            actual += input.actual
        
        val.append({
              'basis':basis,
              'bom':bom,
              'var':var,
              'var_usd':var_usd,
              'actual':actual
            })
        return val
    
    def get_analysis_output_total_outputs(self,o):
        val =[]
        belowsc12= screen13 = screen16 = screen18 = screen19 = screen20 = brown = broken = black = fm = mc = 0
        actual = var_usd = var =bom = basis = count = 0
        for input in o.output_ids:
            mc += input.mc * input.net_qty
            fm += input.fm * input.net_qty or 0.0
            black += input.black * input.net_qty  or 0.0
            broken += input.broken * input.net_qty or 0.0
            brown +=  input.brown * input.net_qty or 0.0
            screen20 += input.screen20 * input.net_qty or 0.0
            screen19 += input.screen19 * input.net_qty or 0.0
            screen18 += input.screen18 * input.net_qty or 0.0
            screen16 += input.screen16 * input.net_qty or 0.0
            screen13 += input.screen13 * input.net_qty or 0.0
            belowsc12 += input.screen12 * input.net_qty or 0.0
            count += input.net_qty or 0.0
            basis += input.basis_qty or 0.0
            bom += input.bom
            var += input.var
            var_usd += input.var_usd
            actual += input.actual
        
        val.append({
              'net_qty': count,
              'basis':basis,
              'deduction': (1- basis/count)*100,
              'mc':count and mc/count or 0.0,
              'fm':count and fm/count or 0.0, 
              'black':count and black/count or 0.0, 
              'broken':count and broken/count or 0.0, 
              'brown':count and brown/count or 0.0, 
              'screen20':count and screen20/count or 0.0, 
              'screen19':count and screen19/count or 0.0, 
              'screen18':count and screen18/count or 0.0, 
              'screen16':count and screen16/count or 0.0, 
              'screen13':count and screen13/count or 0.0, 
              'screen12':count and belowsc12/count or 0.0, 
              'bom':bom,
              'var':var,
              'var_usd':var_usd,
              'actual':actual
            })
        return val
    
    def get_analysis_input_total_outputs(self,o):
        val =[]
        belowsc12= screen13 = screen16 = screen18 = screen19 = screen20 = brown = broken = black = fm = mc = 0
        bom = basis = count = 0
        
        for input in o.input_ids:
            mc += input.mc * input.net_qty
            fm += input.fm * input.net_qty or 0.0
            black += input.black * input.net_qty  or 0.0
            broken += input.broken * input.net_qty or 0.0
            brown +=  input.brown * input.net_qty or 0.0
            screen20 += input.screen20 * input.net_qty or 0.0
            screen19 += input.screen19 * input.net_qty or 0.0
            screen18 += input.screen18 * input.net_qty or 0.0
            screen16 += input.screen16 * input.net_qty or 0.0
            screen13 += input.screen13 * input.net_qty or 0.0
            belowsc12 += input.screen12 * input.net_qty or 0.0
            count += input.net_qty or 0.0
            basis += input.basis_qty or 0.0
            bom += input.bom
        
        val.append({
              'net_qty': count,
              'basis':basis,
              'deduction': (1- basis/count)*100,
              'mc':count and mc/count or 0.0,
              'fm':count and fm/count or 0.0, 
              'black':count and black/count or 0.0, 
              'broken':count and broken/count or 0.0, 
              'brown':count and brown/count or 0.0, 
              'screen20':count and screen20/count or 0.0, 
              'screen19':count and screen19/count or 0.0, 
              'screen18':count and screen18/count or 0.0, 
              'screen16':count and screen16/count or 0.0, 
              'screen13':count and screen13/count or 0.0, 
              'screen12':count and belowsc12/count or 0.0, 
              'bom':bom
            })
        return val

    def get_total_outputs(self,obj):
        cherry = mold = belowsc12= screen13 = screen16 = screen18 = screen19 = screen20 = brown = broken = black = fm = mc = 0
        basis = count = 0
        val=[]
        for input in obj.outputs_ids:
            mc += input.mc * input.net_qty
            fm += input.fm * input.net_qty or 0.0
            black += input.black * input.net_qty  or 0.0
            broken += input.broken * input.net_qty or 0.0
            brown +=  input.brown * input.net_qty or 0.0
            screen20 += input.screen20 * input.net_qty or 0.0
            screen19 += input.screen19 * input.net_qty or 0.0
            screen18 += input.screen18 * input.net_qty or 0.0
            screen16 += input.screen16 * input.net_qty or 0.0
            screen13 += input.screen13 * input.net_qty or 0.0
            belowsc12 += input.screen12 * input.net_qty or 0.0
            cherry += input.cherry * input.net_qty or 0.0
            mold += input.mold * input.net_qty or 0.0
            count += input.net_qty or 0.0
            basis += input.basis_qty or 0.0
            
        val.append({  
              'net_qty': count,
              'basis':basis,
              'deduction': (1- basis/count)*100,
              'mc':count and mc/count or 0.0,
              'fm':count and fm/count or 0.0, 
              'black':count and black/count or 0.0, 
              'broken':count and broken/count or 0.0, 
              'brown':count and brown/count or 0.0, 
              'screen20':count and screen20/count or 0.0, 
              'screen19':count and screen19/count or 0.0, 
              'screen18':count and screen18/count or 0.0, 
              'screen16':count and screen16/count or 0.0, 
              'screen13':count and screen13/count or 0.0, 
              'screen12':count and belowsc12/count or 0.0, 
              'mold':count and mold/count or 0.0, 
              'cherry':count and cherry/count or 0.0, 
              })
        return val
    
    
    def get_total_inputs(self,obj):
        cherry = mold = belowsc12= screen13 = screen16 = screen18 = screen19 = screen20 = brown = broken = black = fm = mc = 0
        basis = count = 0
        val=[]
        for input in obj.input_ids:
            mc += input.mc * input.net_qty
            fm += input.fm * input.net_qty or 0.0
            black += input.black * input.net_qty  or 0.0
            broken += input.broken * input.net_qty or 0.0
            brown +=  input.brown * input.net_qty or 0.0
            screen20 += input.screen20 * input.net_qty or 0.0
            screen19 += input.screen19 * input.net_qty or 0.0
            screen18 += input.screen18 * input.net_qty or 0.0
            screen16 += input.screen16 * input.net_qty or 0.0
            screen13 += input.screen13 * input.net_qty or 0.0
            belowsc12 += input.screen12 * input.net_qty or 0.0
            cherry += input.cherry * input.net_qty or 0.0
            mold += input.mold * input.net_qty or 0.0
            count += input.net_qty or 0.0
            basis += input.basis_qty or 0.0
        val.append({
                'net_qty': count,
                'basis':basis,
                'deduction': (1- basis/count) * 100,
                'mc':count and mc/count or 0.0,
                'fm':count and fm/count or 0.0, 
                'black':count and black/count or 0.0, 
                'broken':count and broken/count or 0.0, 
                'brown':count and brown/count or 0.0, 
                'screen20':count and screen20/count or 0.0, 
                'screen19':count and screen19/count or 0.0, 
                'screen18':count and screen18/count or 0.0, 
                'screen16':count and screen16/count or 0.0, 
                'screen13':count and screen13/count or 0.0, 
                'screen12':count and belowsc12/count or 0.0, 
                'mold':count and mold/count or 0.0, 
                'cherry':count and cherry/count or 0.0, 
            })
        return val

    def get_product(self, batch_id):
        val = []
        sql = '''
            SELECT bo.product_id,
                    pp.default_code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc on pc.id = bo.categ_id
            WHERE batch_id = %s
            GROUP BY bo.product_id,
                    pp.default_code,
                    pc.code
            ORDER BY %s
        '''%(batch_id, case_sql)
        self.env.cr.execute(sql)
        for this in self.env.cr.dictfetchall():
            val.append({
                'product_id': this['product_id'],
                'default_code': this['default_code']
            })
        return val

    def get_mimax_date(self, batch_id):
        var = []
        sql = '''
            SELECT MAX(date) maxdate,
                    MIN(date) mindate
            FROM batch_report_input
            WHERE batch_id = %s
        '''%(batch_id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'min': line['mindate'],
                'max': line['maxdate']
            })
        return var

    def get_total_in_date(self, batch_id):
        var = []
        sql = '''
            SELECT bi.date date,
                    pp.default_code,
                    sum(real_qty) sum_qty
            FROM batch_report_input bi
                JOIN product_product pp ON pp.id = bi.product_id
            WHERE batch_id = %s
            GROUP BY bi.date,
                    pp.default_code
            ORDER BY bi.date ASC
        '''%(batch_id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'date': line['date'],
                'code': line['default_code'],
                'qty': line['sum_qty']
            })
        return var

    def get_total_out_qty(self, batch_id, total_qty):
        var = []
        sql= '''
            SELECT pp.default_code,
                    sum(net_qty) sum_qty
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON pc.id = bo.categ_id
            WHERE batch_id = %s
            GROUP BY pp.default_code,
                    pc.code
            ORDER BY %s
        '''%(batch_id, case_sql)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'name': line['default_code'],
                'qty': line['sum_qty'],
                'per_qty': total_qty and (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
            })
        return var

    def get_total_stack_in(self, batch_id):
        var = []
        sql = '''
            SELECT ss.name stack_name,
                    bi.net_qty,
                    bi.date,
                    pp.default_code,
                    pu.name uom_name,
                    np.name packing_name,
                    bi.bag_no,
                    sz.name zone_name,
                    bi.stack_id stack_id
            FROM batch_report_input bi
                JOIN stock_lot ss ON bi.stack_id = ss.id
                JOIN product_product pp ON pp.id = bi.product_id
                    JOIN product_template tmpl ON tmpl.id = pp.product_tmpl_id
                    JOIN uom_uom pu ON pu.id = tmpl.uom_id
                LEFT JOIN ned_packing np ON np.id = bi.packing_id
                JOIN stock_zone sz ON sz.id = bi.zone_id
            WHERE batch_id = %s
            ORDER BY bi.date ASC
        '''%(batch_id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'date': line['date'],
                'stack': line['stack_name'],
                'qty': line['net_qty'],
                'name': line['default_code'],
                'uom': str(line['uom_name']).upper(),
                'pack': line['packing_name'] or False,
                'bag': line['bag_no'],
                'zone': line['zone_name'],
                'stack_id':line['stack_id']
            })
        return var
    
    def get_out_qc(self, batch_id, product_id):
        var = []
        sql = '''
            SELECT
                SUM(mc*net_qty)/SUM(net_qty) mc,
                sum(fm*net_qty)/sum(net_qty) fm,
                sum(black*net_qty)/sum(net_qty) black,
                sum(broken*net_qty)/sum(net_qty) broken,
                sum(brown*net_qty)/sum(net_qty) brown,
                sum(mold*net_qty)/sum(net_qty) mold,
                sum(cherry*net_qty)/sum(net_qty) cherry,
                sum(excelsa*net_qty)/sum(net_qty) excelsa,
                sum(screen20*net_qty)/sum(net_qty) screen20,
                sum(screen19*net_qty)/sum(net_qty) screen19,
                sum(screen18*net_qty)/sum(net_qty) screen18,
                sum(screen16*net_qty)/sum(net_qty) screen16,
                sum(screen13*net_qty)/sum(net_qty) screen13,
                sum(screen12*net_qty)/sum(net_qty) screen12,
                sum(greatersc12*net_qty)/sum(net_qty) greatersc12,
                sum(burn*net_qty)/sum(net_qty) burn,
                sum(immature*net_qty)/sum(net_qty) immature,
                sum(net_qty) total_out_qty,
                sum(bag_no) bag_no
            FROM batch_report_output
            WHERE batch_id = %s
                AND product_id = %s
            '''%(batch_id, product_id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'mc': line['mc'],
                'fm': line['fm'],
                'black': line['black'],
                'broken': line['broken'],
                'brown': line['brown'],
                'mold': line['mold'],
                'cherry': line['cherry'],
                'excelsa': line['excelsa'],
                'screen20': line['screen20'],
                'screen19': line['screen19'],
                'screen18': line['screen18'],
                'screen16': line['screen16'],
                'screen13': line['screen13'],
                'screen12': line['screen12'],
                'greatersc12': line['greatersc12'],
                'burn': line['burn'],
                'immature': line['immature'],
                'total_out_qty': line['total_out_qty'],
                'bag_no': line['bag_no'],
            })
        return var

    def get_total_in_qty(self,batch_id):
        var = []
        sql='''
            SELECT sum(bi.real_qty) real_qty,
                    pp.default_code
            FROM batch_report_input bi
                JOIN product_product pp ON pp.id = bi.product_id
            WHERE bi.batch_id = %s
            GROUP BY pp.default_code
        '''%(batch_id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                    'real_qty' : line['real_qty'],
                    'default_code': line['default_code']
            })
        return var

    def get_main_grade(self, batch_id, total_qty):
        var = []
        sql = '''
            SELECT sum(sum_qty) sum_qty,
                    pc_code
            FROM(SELECT sum(net_qty) sum_qty,
                    CASE WHEN pp.default_code ilike '%(S20)s'
                    THEN 'Scr 20'
                    ELSE
                    CASE WHEN pp.default_code ilike '%(S19)s'
                    THEN 'Scr 19'
                    ELSE
                    CASE WHEN pp.default_code ilike '%(S18)s'
                    THEN 'Scr 18'
                    ELSE
                    CASE WHEN (pp.default_code ilike '%(S16)s' OR pp.default_code ilike 'Nestle7.1' OR pp.default_code ilike '%(S15)s')
                    THEN 'Scr 16'
                    ELSE 
                    CASE WHEN (pp.default_code ilike '%(S13)s' OR pp.default_code ilike 'Nestle7.2' OR pp.default_code ilike '%(S14)s')
                    THEN 'Scr 13' 
                    ELSE 
                    CASE WHEN pp.default_code ilike '%(G3)s'
                    THEN 'G3' 
                    END END END END END END pc_code
            FROM batch_report_output bo
                JOIN product_product pp ON bo.product_id = pp.id
            WHERE bo.batch_id = %(batch_id)s
                AND (pp.default_code ilike '%(S20)s'
                    OR pp.default_code ilike '%(S19)s'
                    OR pp.default_code ilike '%(S18)s'
                    OR pp.default_code ilike '%(S16)s'
                    OR pp.default_code ilike '%(S13)s'
                    OR pp.default_code ilike '%(G3)s'
                    OR pp.default_code ilike 'Nestle7.1'
                    OR pp.default_code ilike 'Nestle7.2'
                    OR pp.default_code ilike '%(S14)s'
                    OR pp.default_code ilike '%(S15)s')
            GROUP BY pp.default_code
            ORDER BY pp.default_code DESC) su
            WHERE pc_code in ('Scr 20', 'Scr 19', 'Scr 18', 'Scr 16', 'Scr 13','G3')
            GROUP BY pc_code
            ORDER BY pc_code DESC
        '''%({'batch_id':batch_id,
                'S20': 'S20%',
                'S19': 'S19%',
                'S18': 'S18%',
                'S16': 'S16%',
                'S15': 'S15%',
                'S14': 'S14%',
                'S13': 'S13%',
                'G3': 'G3%'})
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'qty': line['sum_qty'] if line['sum_qty'] != None else 0.0,
                'name': line['pc_code'],
                'per_qty': (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
            })
        return var
    
    def get_sum_main_grade(self, batch_id, total_qty):
        var = []
        sql = '''
            SELECT sum(net_qty) sum_qty
            FROM batch_report_output bo
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %s
                AND pc.code in ('G1-S18','G13','G19','G3','G2','G1-S16')
        '''%(batch_id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'qty': line['sum_qty'] if line['sum_qty'] != None else 0.0,
                'per_qty': (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
            })
        return var

    def get_under_grade(self, batch_id, total_qty):
        var = []
        sql = '''

            SELECT sum(net_qty) sum_qty,
                    'Robusta Color Sorter Reject' code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('CSR-G1','CSR-G2','CSR-S18','CSR-S19','CSR-S20','CSR-S16','CSR-16','CSR-18')

            UNION ALL

            SELECT sum(net_qty) sum_qty,
                    'GTR' code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('GTR')

            UNION ALL

            SELECT sum(net_qty) sum_qty,
                    'GTR7' code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('GTR-70')

            UNION ALL

            SELECT sum(net_qty) sum_qty,
                    'Below Sc 12' code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('BL-12','BL-12B')

            UNION ALL

            SELECT sum(net_qty) sum_qty,
                    'Sweepings [Bulk]' code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('SPL')
                
            UNION ALL

            SELECT sum(net_qty) sum_qty,
                    'Sample' code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('SML')
                
            UNION ALL

            SELECT sum(net_qty) sum_qty,
                    'Wet polished reject' code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('WPR')
            
            UNION ALL

            SELECT sum(net_qty) sum_qty,
                    'Various beans received from spillage winnower' code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('BULK')
            
            UNION ALL

            SELECT sum(net_qty) sum_qty,
                    'Destoner reject' code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('DSR')
            
        '''%({'batch_id': batch_id})
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'qty': line['sum_qty'] if line['sum_qty'] != None else 0.0,
                'name': "Robusta Gravity Reject 10% FM" if line['code'] == 'GTR' else 'Robusta Gravity Reject 70% FM' if line['code'] == 'GTR7' else line['code'],
                'per_qty': (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
            })
        return var

    def get_sum_under_grade(self, batch_id, total_qty):
        var = []
        sql = '''
            SELECT sum(net_qty) sum_qty
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
            WHERE bo.batch_id = %s
                AND pp.default_code in ('SPL','BL-12','GTR-70','GTR','CSR-G1','CSR-G2','CSR-S16','SML','WPR','BL-12B','BULK ','DSR','CSR-S18','CSR-S19','CSR-S20','CSR-16','CSR-18')
        '''%(batch_id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'qty': line['sum_qty'] if line['sum_qty'] != None else 0.0,
                'per_qty': (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
            })
        return var

    def get_zero_grade(self, batch_id, total_qty):
        var = []
        sql = '''

            SELECT sum(net_qty) sum_qty,
                    'Robusta Pre Cleaner Reject' code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('PCR')

            UNION ALL

            SELECT sum(net_qty) sum_qty,
                    'Robusta  Husk' code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('HUSKS')

            UNION ALL

            SELECT sum(net_qty) sum_qty,
                    'Robusta Stone' code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('STONES')

            UNION ALL

            SELECT sum(net_qty) sum_qty,
                    'Robusta Dust' code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('Dust','WP Dust')

        '''%({'batch_id': batch_id})
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'qty': line['sum_qty'] if line['sum_qty'] != None else 0.0,
                'name': line['code'],
                'per_qty': (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
            })
        return var

    def get_sum_zero_grade(self, batch_id, total_qty):
        var = []
        sql = '''
            SELECT sum(net_qty) sum_qty
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
            WHERE bo.batch_id = %s
                AND pp.default_code in ('Dust','WP Dust','STONES','HUSKS','PCR')
        '''%(batch_id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'qty': line['sum_qty'] if line['sum_qty'] != None else 0.0,
                'per_qty': (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
            })
        return var
    
    def get_loss(self,product_id,stack_id):
        qty =0
        sql = '''
            SELECT sum(sml.init_qty) loss_qty
                FROM mrp_production mp
                    JOIN stock_move_line sml ON mp.id = sml.finished_id
                    JOIN stock_picking sp on sp.id = sml.picking_id
                    join stock_picking_type spt on sp.picking_type_id = spt.id
                WHERE mp.id =%s 
                AND sml.lot_id =%s
                AND spt.code ='phys_adj';
        '''%(product_id.id,stack_id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            qty = line['loss_qty'] or 0.0
        return qty
        
    def get_loss_total(self,product_id):
        qty =0
        sql = '''
            SELECT sum(sml.init_qty) loss_qty
                FROM mrp_production mp
                    JOIN stock_move_line sml ON mp.id = sml.finished_id
                    JOIN stock_picking sp on sp.id = sml.picking_id
                    join stock_picking_type spt on sp.picking_type_id = spt.id
                WHERE mp.id =%s 
                AND spt.code ='phys_adj';
        '''%(product_id.id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            qty = line['loss_qty'] or 0.0
        return qty
        
    def get_qty_faq(self,product_id,net_qty):
        qty = '' 
        if product_id.default_code =='FAQ':
            qty =net_qty
        return qty
    
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
