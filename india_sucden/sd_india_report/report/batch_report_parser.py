# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
from odoo.exceptions import UserError
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
    _name = 'report.batch_report'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.batch_report'
    

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
            'get_qty_faq':self.get_qty_faq,
            'get_date': self.get_date,
            'get_total_out_qty_up': self.get_total_out_qty_up,
            'get_total_out_qty_down': self.get_total_out_qty_down,
            'total_out_qty_up': self.total_out_qty_up,
            'total_out_qty_down': self.total_out_qty_down,
            'get_data_analysis': self.get_data_analysis,
            'get_mill_analysis': self.get_mill_analysis,
            'get_qc_analysis': self.get_qc_analysis,
        })
        return localcontext
    
    def get_date(self, date):
        if date:
            convert_str = date.strftime(DATETIME_FORMAT)
            return_date = str((datetime.strptime(convert_str, DATETIME_FORMAT) + timedelta(hours=5, minutes=30)).date())
            date_convert = datetime.strptime(return_date, '%Y-%m-%d')
            date_convert = date_convert.strftime('%d-%m-%Y')
            return date_convert
    
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
                    pp.default_code,
                    pp.display_wb
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc on pc.id = bo.categ_id
            WHERE batch_id = %s
            GROUP BY bo.product_id,
                    pp.default_code,
                    pp.display_wb,
                    pc.code
            ORDER BY %s
        '''%(batch_id, case_sql)
        self.env.cr.execute(sql)
        for this in self.env.cr.dictfetchall():
            val.append({
                'product_id': this['product_id'],
                'default_code': this['default_code'],
                'display_wb': this['display_wb']
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
            min = self.get_date(line['mindate'])
            max = self.get_date(line['maxdate'])
            var.append({
                'min': min,
                'max': max
            })
        return var

    def get_total_in_date(self, batch_id):
        var = []
        sql = '''
            SELECT bi.date date,
                    pp.display_wb,
                    sum(real_qty) sum_qty
            FROM batch_report_input bi
                JOIN product_product pp ON pp.id = bi.product_id
            WHERE batch_id = %s
            GROUP BY bi.date,
                    pp.display_wb
            ORDER BY bi.date ASC
        '''%(batch_id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'date': line['date'],
                'code': line['display_wb'],
                'qty': line['sum_qty']
            })
        return var

    def get_total_out_qty(self, batch_id, total_qty):
        var = []
        sql= '''
            SELECT pp.display_wb,
                    sum(net_qty) sum_qty
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON pc.id = bo.categ_id
            WHERE batch_id = %s
            GROUP BY pp.display_wb,
                    pc.code
        '''%(batch_id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'name': line['display_wb'],
                'qty': line['sum_qty'],
                'per_qty': total_qty and (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
            })
        return var

    def total_out_qty_up(self, batch_id):
        total_qty = per_qty = 0
        sql = '''
                    SELECT pp.display_wb,
                            sum(net_qty) sum_qty
                    FROM batch_report_output bo
                        JOIN product_product pp ON pp.id = bo.product_id
                        JOIN product_category pc ON pc.id = bo.categ_id
                    WHERE batch_id = %s and (pp.default_code between '13000' AND '14299' and pp.default_code not in ('14101', '14102', '14103', '14104'))
                    GROUP BY pp.display_wb,
                            pc.code
                ''' % (batch_id)
        self.env.cr.execute(sql)
        for tot in self.env.cr.dictfetchall():
            total_qty += tot['sum_qty']
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            per_qty += total_qty and (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
        return total_qty, per_qty

    def total_out_qty_down(self, batch_id):
        total_qty = per_qty = 0
        sql = '''
                            SELECT pp.display_wb,
                                    sum(net_qty) sum_qty
                            FROM batch_report_output bo
                                JOIN product_product pp ON pp.id = bo.product_id
                                JOIN product_category pc ON pc.id = bo.categ_id
                            WHERE batch_id = %s and pp.default_code in ('14101', '14102', '14103', '14104')
                            GROUP BY pp.display_wb,
                                    pc.code
                        ''' % (batch_id)
        self.env.cr.execute(sql)
        for tot in self.env.cr.dictfetchall():
            total_qty += tot['sum_qty']
        return total_qty


    def get_total_out_qty_up(self, batch_id, total_qty):
        var = []
        total_qty = 0
        sql= '''
            SELECT pp.display_wb,
                    sum(net_qty) sum_qty
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON pc.id = bo.categ_id
            WHERE batch_id = %s and (pp.default_code between '13000' AND '14299' and pp.default_code not in ('14101', '14102', '14103', '14104'))
            GROUP BY pp.display_wb,
                    pc.code
            ORDER BY pp.display_wb
        '''%(batch_id)
        self.env.cr.execute(sql)
        for tot in self.env.cr.dictfetchall():
            total_qty += tot['sum_qty']
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'name': line['display_wb'],
                'qty': line['sum_qty'],
                'per_qty': total_qty and (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
            })
        return var

    def get_total_out_qty_down(self, batch_id, total_qty):
        var = []
        sql= '''
            SELECT pp.display_wb,
                    sum(net_qty) sum_qty
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON pc.id = bo.categ_id
            WHERE batch_id = %s and pp.default_code in ('14101','14102','14103','14104')
            GROUP BY pp.display_wb,
                    pc.code
            ORDER BY pp.display_wb
        '''%(batch_id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'name': line['display_wb'],
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
                    pp.display_wb,
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
            uom = line['uom_name']['en_US']
            var.append({
                'date': line['date'],
                'stack': line['stack_name'],
                'qty': line['net_qty'],
                'name': line['display_wb'],
                'uom': uom,
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
                    pp.display_wb
            FROM batch_report_input bi
                JOIN product_product pp ON pp.id = bi.product_id
            WHERE bi.batch_id = %s
            GROUP BY pp.display_wb
        '''%(batch_id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                    'real_qty' : line['real_qty'],
                    'default_code': line['display_wb']
            })
        return var

    def get_main_grade(self, batch_id):
        var = []
        total_qty = self.total_out_qty_up(batch_id)[0]
        sql = '''
            SELECT sum(net_qty) sum_qty,
                    pp.display_wb pc_code
            FROM batch_report_output bo
                JOIN product_product pp ON bo.product_id = pp.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code between '13000' and '13999' and pp.default_code not in ('13005', '13006', '13105', '13106', '13205', '13206', '13305', '13306')
            GROUP BY pp.display_wb
            ORDER BY pp.display_wb
        '''%({'batch_id':batch_id})
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
        total_qty = self.total_out_qty_up(batch_id)[0]
        sql = '''
            SELECT sum(net_qty) sum_qty
            FROM batch_report_output bo
                JOIN product_product pp ON bo.product_id = pp.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code between '13000' and '13999' and pp.default_code not in ('13005', '13006', '13105', '13106', '13205', '13206', '13305', '13306')
        ''' % ({'batch_id': batch_id})
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'qty': line['sum_qty'] if line['sum_qty'] != None else 0.0,
                'per_qty': (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
            })
        return var

    def get_under_grade(self, batch_id, total_qty):
        var = []
        total_qty = self.total_out_qty_up(batch_id)[0]
        sql = '''

            SELECT sum(net_qty) sum_qty,
                    pp.display_wb pc_code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('13005', '13006', '13105', '13106', '13205', '13206', '13305', '13306')
                GROUP BY pp.display_wb
        '''%({'batch_id': batch_id})
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'qty': line['sum_qty'] if line['sum_qty'] != None else 0.0,
                'name': line['pc_code'],
                'per_qty': (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
            })
        return var

    def get_sum_under_grade(self, batch_id, total_qty):
        var = []
        total_qty = self.total_out_qty_up(batch_id)[0]
        sql = '''
            SELECT sum(net_qty) sum_qty
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('13005', '13006', '13105', '13106', '13205', '13206', '13305', '13306')
        '''%({'batch_id': batch_id})
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'qty': line['sum_qty'] if line['sum_qty'] != None else 0.0,
                'per_qty': (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
            })
        return var

    def get_zero_grade(self, batch_id, total_qty):
        var = []
        total_qty = self.total_out_qty_up(batch_id)[0]
        sql = '''

            SELECT sum(net_qty) sum_qty,
                    pp.display_wb pc_code
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
                JOIN product_category pc ON bo.categ_id = pc.id
            WHERE bo.batch_id = %(batch_id)s
                AND pp.default_code in ('14001', '14201', '14205', '14301', '14002', '14202', '14206', '14302', '14003', '14204', '14207', '14303', '14004', '14203', '14208', '14304', '14210', '14209')
                GROUP BY pp.display_wb
        '''%({'batch_id': batch_id})
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            var.append({
                'qty': line['sum_qty'] if line['sum_qty'] != None else 0.0,
                'name': line['pc_code'],
                'per_qty': (line['sum_qty']/total_qty)*100 if line['sum_qty'] != None else 0.0
            })
        return var

    def get_sum_zero_grade(self, batch_id, total_qty):
        var = []
        total_qty = self.total_out_qty_up(batch_id)[0]
        sql = '''
            SELECT sum(net_qty) sum_qty
            FROM batch_report_output bo
                JOIN product_product pp ON pp.id = bo.product_id
            WHERE bo.batch_id = %s
                AND pp.default_code in ('14001', '14201', '14205', '14301', '14002', '14202', '14206', '14302', '14003', '14204', '14207', '14303', '14004', '14203', '14208', '14304', '14210', '14209')
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
            qty = net_qty
        return qty

    # def get_instore(self, batch_id, quality=None):
    #     if batch_id:
    #         for
    
    
    
    def get_data_analysis(self, batch):
        if batch:
            manufacturing = batch.production_id
            grade_of_manu = manufacturing.grade_id
            crop_active = self.env['ned.crop'].search([
                ('state', '=', 'current')
            ])
            analysis_grade_id = self.env['analysis.batch.report'].search([
                ('state', '=', 'approve'),
                ('grade_id', '=', grade_of_manu.id),
                ('crop_id', '=', crop_active.id)
            ])
            if analysis_grade_id:
                return analysis_grade_id.percent, analysis_grade_id.expectation_percent
            else:
                return 0, 0

    def get_mill_analysis(self, batch, quality=False):
        truck_quality = self.env['truck.quality.production'].search([
            ('production_id', '=', batch.production_id.id),
            ('department_stage', '=', 'mill')
        ])
        total_qty = sum(truck_quality.mapped('quantity'))
        total_quality = 0
        if total_qty == 0:
            raise UserError(_("Please check your data MILL in truck quality!!"))
        if quality == 'mc':
            for i in truck_quality:
                total_quality += i.moisture_percent * i.quantity
            return total_quality / total_qty
        if quality == 'aaa':
            for i in truck_quality:
                total_quality += i.aaa_percent * i.quantity
            return total_quality / total_qty
        if quality == 'aa':
            for i in truck_quality:
                total_quality += i.aa_percent * i.quantity
            return total_quality / total_qty
        if quality == 'a':
            for i in truck_quality:
                total_quality += i.a_percent * i.quantity
            return total_quality / total_qty
        if quality == 'b':
            for i in truck_quality:
                total_quality += i.b_percent * i.quantity
            return total_quality / total_qty
        if quality == 'c':
            for i in truck_quality:
                total_quality += i.c_percent * i.quantity
            return total_quality / total_qty
        if quality == 'pb':
            for i in truck_quality:
                total_quality += i.pb_percent * i.quantity
            return total_quality / total_qty
        if quality == 'idb':
            for i in truck_quality:
                total_quality += i.idb_percent * i.quantity
            return total_quality / total_qty
        if quality == 'bleach':
            for i in truck_quality:
                total_quality += i.bleached_percent * i.quantity
            return total_quality / total_qty
        if quality == 'bits':
            for i in truck_quality:
                total_quality += i.bits_percent * i.quantity
            return total_quality / total_qty
        if quality == 'husk':
            for i in truck_quality:
                total_quality += i.hulks_percent * i.quantity
            return total_quality / total_qty
        if quality == 'stone':
            for i in truck_quality:
                total_quality += i.stone_percent * i.quantity
            return total_quality / total_qty
        return 0

    def get_qc_analysis(self, batch, quality=False):
        truck_quality = self.env['truck.quality.production'].search([
            ('production_id', '=', batch.production_id.id),
            ('department_stage', '=', 'qc')
        ])
        total_qty = sum(truck_quality.mapped('quantity'))
        total_quality = 0
        if total_qty == 0:
            raise UserError(_("Please check your data QC in truck quality!!"))
        if quality == 'mc':
            for i in truck_quality:
                total_quality += i.moisture_percent * i.quantity
            return total_quality / total_qty
        if quality == 'aaa':
            for i in truck_quality:
                total_quality += i.aaa_percent * i.quantity
            return total_quality / total_qty
        if quality == 'aa':
            for i in truck_quality:
                total_quality += i.aa_percent * i.quantity
            return total_quality / total_qty
        if quality == 'a':
            for i in truck_quality:
                total_quality += i.a_percent * i.quantity
            return total_quality / total_qty
        if quality == 'b':
            for i in truck_quality:
                total_quality += i.b_percent * i.quantity
            return total_quality / total_qty
        if quality == 'c':
            for i in truck_quality:
                total_quality += i.c_percent * i.quantity
            return total_quality / total_qty
        if quality == 'pb':
            for i in truck_quality:
                total_quality += i.pb_percent * i.quantity
            return total_quality / total_qty
        if quality == 'idb':
            for i in truck_quality:
                total_quality += i.idb_percent * i.quantity
            return total_quality / total_qty
        if quality == 'bleach':
            for i in truck_quality:
                total_quality += i.bleached_percent * i.quantity
            return total_quality / total_qty
        if quality == 'bits':
            for i in truck_quality:
                total_quality += i.bits_percent * i.quantity
            return total_quality / total_qty
        if quality == 'husk':
            for i in truck_quality:
                total_quality += i.hulks_percent * i.quantity
            return total_quality / total_qty
        if quality == 'stone':
            for i in truck_quality:
                total_quality += i.stone_percent * i.quantity
            return total_quality / total_qty
        return 0

