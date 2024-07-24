# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class WizradNPE_Unfix(models.TransientModel):
    _name = "npe.unfixed.insert"

    def load_button(self):
        sql ='''
            DELETE FROM npe_unfixed_master;
            -- DELETE FROM npe_unfixed_detail;

            INSERT into npe_unfixed_master (partner_ids, qty_contract, qty_received, to_receive, name, qty_fixed, unfixed, mc, fm, black,
                            broken, brown, mold, cherry, excelsa, screen20, screen19, screen18, screen16, screen13, greatersc12, belowsc12, burned, eaten)
            (SELECT pc.partner_id partner_ids, sum(pc.qty_contract) qty_contract, sum(pc.qty_received) qty_received, 
                sum(pc.to_receive) to_receive, concat(rp.name,' (',count(*),')') as name  , sum(fix_qty.qty_fixed) qty_fixed, 
                sum(pc.qty_received - fix_qty.qty_fixed) unfixed, 
                sum(kcs.mc * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) mc, 
                sum(kcs.fm * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) fm, 
                sum(kcs.black * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) black, 
                sum(kcs.broken * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) broken, 
                sum(kcs.brown * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) brown, 
                sum(kcs.mold * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) mold, 
                sum(kcs.cherry * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) cherry, 
                sum(kcs.excelsa * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) excelsa, 
                sum(kcs.screen20 * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) screen20, 
                sum(kcs.screen19 * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) screen19, 
                sum(kcs.screen18 * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) screen18, 
                sum(kcs.screen16 * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) screen16, 
                sum(kcs.screen13 * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) screen13, 
                sum(kcs.greatersc12 * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) greatersc12, 
                sum(kcs.belowsc12 * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) belowsc12, 
                sum(kcs.burned * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) burned, 
                sum(kcs.eaten * (pc.qty_received - fix_qty.qty_fixed))/sum(pc.qty_received - fix_qty.qty_fixed) eaten
            From (SELECT A.id npe_id, B.partner_id, B.qty_contract, A.qty_received, B.npe, B.date_order,
            B.qty_contract - A.qty_received AS to_receive From
            (SELECT pc.id, sum(sa.qty_allocation) qty_received from purchase_contract pc
            JOIN stock_allocation sa ON pc.id=sa.contract_id Group by pc.id) A Join
            (SELECT pc.id, pc.partner_id, pc.name npe, pc.date_order, pcl.product_qty qty_contract from purchase_contract pc
            JOIN purchase_contract_line pcl ON pc.id=pcl.contract_id) B ON A.id=B.id) pc
            JOIN (SELECT pc.id npe_nvp_id, case when sum(npe_nvp.product_qty) is null then 0 else sum(npe_nvp.product_qty) End AS qty_fixed 
                  from purchase_contract pc Left Join npe_nvp_relation npe_nvp ON pc.id=npe_nvp.npe_contract_id Group by pc.id) fix_qty
                ON pc.npe_id=fix_qty.npe_nvp_id
            JOIN (SELECT pc.id pc_id, sum(rkl.mc)/count(pc.id) mc, sum(rkl.fm)/count(pc.id) fm, sum(rkl.black)/count(pc.id) black,
                sum(rkl.broken)/count(pc.id) broken, sum(rkl.brown)/count(pc.id) brown, sum(rkl.mold)/count(pc.id) mold, sum(rkl.screen20)/count(pc.id) screen20,
                sum(rkl.cherry)/count(pc.id) cherry, sum(rkl.excelsa)/count(pc.id) excelsa, sum(rkl.screen19)/count(pc.id) screen19, sum(rkl.screen18)/count(pc.id) screen18, 
                sum(rkl.screen16)/count(pc.id) screen16, sum(rkl.screen13)/count(pc.id) screen13, sum(rkl.greatersc12)/count(pc.id) greatersc12,
                sum(rkl.belowsc12)/count(pc.id) belowsc12, sum(rkl.burned)/count(pc.id) burned, sum(rkl.eaten)/count(pc.id) eaten
                From purchase_contract pc
                JOIN stock_allocation sa ON pc.id=sa.contract_id
                JOIN stock_picking sp ON sa.picking_id=sp.id
                JOIN request_kcs_line rkl ON sp.id=rkl.picking_id
                Group by pc.id order by pc.id desc) kcs ON pc.npe_id=kcs.pc_id
            JOIN res_partner rp ON pc.partner_id=rp.id
            Where left(pc.npe,3)='NPE' And pc.qty_received - fix_qty.qty_fixed>0 
            Group by pc.partner_id, rp.name)
            RETURNING id, partner_ids
        '''
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            sql_detail = '''
                INSERT into npe_unfixed_detail (npe_unfix_id, partner_id, name, partner, qty_contract, qty_received, to_receive, qty_fixed, unfixed, mc, fm, black,
                            broken, brown, mold, cherry, excelsa, screen20, screen19, screen18, screen16, screen13, greatersc12, belowsc12, burned, eaten)
                SELECT %s as npe_unfix_id, pc.partner_id, pc.name, rp.name partner, pc.qty_contract, pc.qty_received, pc.to_receive,
                    fix_qty.qty_fixed, pc.qty_received - fix_qty.qty_fixed unfixed, kcs.mc, kcs.fm, kcs.black, kcs.broken, kcs.brown, kcs.mold, 
                    kcs.cherry, kcs.excelsa, kcs.screen20, kcs.screen19, kcs.screen18, kcs.screen16, kcs.screen13, kcs.greatersc12, kcs.belowsc12, kcs.burned, kcs.eaten
                FROM (SELECT A.id npe_id, B.partner_id, B.qty_contract, A.qty_received, B.name, B.date_order,
                B.qty_contract - A.qty_received AS to_receive FROM
                (SELECT pc.id, sum(sa.qty_allocation) qty_received FROM purchase_contract pc
                JOIN stock_allocation sa ON pc.id=sa.contract_id GROUP BY pc.id) A Join
                (SELECT pc.id, pc.partner_id, pc.name as name, pc.date_order, pcl.product_qty qty_contract from purchase_contract pc
                JOIN purchase_contract_line pcl ON pc.id=pcl.contract_id) B ON A.id=B.id) pc
                JOIN (SELECT pc.id npe_nvp_id, case when sum(npe_nvp.product_qty) is null then 0 else sum(npe_nvp.product_qty) End AS qty_fixed 
                      from purchase_contract pc Left Join npe_nvp_relation npe_nvp ON pc.id=npe_nvp.npe_contract_id Group by pc.id) fix_qty
                    ON pc.npe_id=fix_qty.npe_nvp_id
                JOIN (SELECT sum(rkl.mc)/count(pc.id) mc, sum(rkl.fm)/count(pc.id) fm, sum(rkl.black)/count(pc.id) black,
                    sum(rkl.broken)/count(pc.id) broken, sum(rkl.brown)/count(pc.id) brown, sum(rkl.mold)/count(pc.id) mold, sum(rkl.screen20)/count(pc.id) screen20,
                    sum(rkl.cherry)/count(pc.id) cherry, sum(rkl.excelsa)/count(pc.id) excelsa, sum(rkl.screen19)/count(pc.id) screen19, sum(rkl.screen18)/count(pc.id) screen18, 
                    sum(rkl.screen16)/count(pc.id) screen16, sum(rkl.screen13)/count(pc.id) screen13, sum(rkl.greatersc12)/count(pc.id) greatersc12,
                    sum(rkl.belowsc12)/count(pc.id) belowsc12, sum(rkl.burned)/count(pc.id) burned, sum(rkl.eaten)/count(pc.id) eaten, pc.id pc_id
                    From purchase_contract pc
                    JOIN stock_allocation sa ON pc.id=sa.contract_id
                    JOIN stock_picking sp ON sa.picking_id=sp.id
                    JOIN request_kcs_line rkl ON sp.id=rkl.picking_id
                    Group by pc.id order by pc.id desc) kcs ON pc.npe_id=kcs.pc_id
                JOIN res_partner rp ON pc.partner_id=rp.id
                Where left(pc.name,3)='NPE' And pc.qty_received - fix_qty.qty_fixed>0 AND pc.partner_id = '%s';
            '''%(line['id'], line['partner_ids'])
            self.env.cr.execute(sql_detail)
        
        action = self.env.ref('sd_report.action_npe_unfixed_master')
        result = action.read()[0]
        return result
        
    	

class WizradNPE_Unfix(models.Model):
    _name = "npe.unfixed.master"
    _description = 'NPE Unfixed - Quality'

    link_to_detail = fields.One2many('npe.unfixed.detail', 'npe_unfix_id', ondelete='cascade', string = 'NPE Unfixed detail')
    partner_ids = fields.Char(string = 'Supplier ID')
    name = fields.Char(string = 'Supplier')
    qty_contract = fields.Float(string = 'Qty Contract', digits=(12, 0))
    qty_received = fields.Float(string = 'Qty Received', digits=(12, 0))
    to_receive = fields.Float(string = 'To Receive', digits=(12, 0))
    qty_fixed = fields.Float(string = 'Fixed', digits=(12, 0))
    unfixed = fields.Float(string = 'Unfixed', digits=(12, 0))
    mc = fields.Float(string = 'MC', digits=(12, 2))
    fm = fields.Float(string = 'FM', digits=(12, 2))
    black = fields.Float(string = 'Black', digits=(12, 2))
    broken = fields.Float(string = 'Broken', digits=(12, 2))
    brown = fields.Float(string = 'Brown', digits=(12, 2))
    mold = fields.Float(string = 'Mold', digits=(12, 2))
    cherry = fields.Float(string = 'Cherry', digits=(12, 2))
    excelsa = fields.Float(string = 'Excelsa', digits=(12, 2))
    screen20 = fields.Float(string = 'Screen20', digits=(12, 2))
    screen19 = fields.Float(string = 'Screen19', digits=(12, 2))
    screen18 = fields.Float(string = 'Screen18', digits=(12, 2))
    screen16 = fields.Float(string = 'Screen16', digits=(12, 2))
    screen13 = fields.Float(string = 'Screen13', digits=(12, 2))
    greatersc12 = fields.Float(string = 'Screen12', digits=(12, 2))
    belowsc12 = fields.Float(string = 'Below Sc12', digits=(12, 2))
    burned = fields.Float(string = 'Burn', digits=(12, 2))
    eaten = fields.Float(string = 'Insect', digits=(12, 2))

class WizradNPE_Unfix(models.Model):
    _name = "npe.unfixed.detail"
    _description = 'NPE Unfixed - Quality detail'

    npe_unfix_id = fields.Many2one('npe.unfixed.master', ondelete='cascade', string = 'NPE Unfixed')
    partner_id = fields.Char(string = 'Supplier ID')
    name = fields.Char(string = 'NPE')
    partner = fields.Char(string = 'Supplier')
    date_order = fields.Date(string = 'Date Contract')
    qty_contract = fields.Float(string = 'Qty Contract', digits=(12, 0))
    qty_received = fields.Float(string = 'Qty Received', digits=(12, 0))
    to_receive = fields.Float(string = 'To Receive', digits=(12, 0))
    qty_fixed = fields.Float(string = 'Fixed', digits=(12, 0))
    unfixed = fields.Float(string = 'Unfixed', digits=(12, 0))
    mc = fields.Float(string = 'MC', digits=(12, 2))
    fm = fields.Float(string = 'FM', digits=(12, 2))
    black = fields.Float(string = 'Black', digits=(12, 2))
    broken = fields.Float(string = 'Broken', digits=(12, 2))
    brown = fields.Float(string = 'Brown', digits=(12, 2))
    mold = fields.Float(string = 'Mold', digits=(12, 2))
    cherry = fields.Float(string = 'Cherry', digits=(12, 2))
    excelsa = fields.Float(string = 'Excelsa', digits=(12, 2))
    screen20 = fields.Float(string = 'Screen20', digits=(12, 2))
    screen19 = fields.Float(string = 'Screen19', digits=(12, 2))
    screen18 = fields.Float(string = 'Screen18', digits=(12, 2))
    screen16 = fields.Float(string = 'Screen16', digits=(12, 2))
    screen13 = fields.Float(string = 'Screen13', digits=(12, 2))
    greatersc12 = fields.Float(string = 'Screen12', digits=(12, 2))
    belowsc12 = fields.Float(string = 'Below Sc12', digits=(12, 2))
    burned = fields.Float(string = 'Burn', digits=(12, 2))
    eaten = fields.Float(string = 'Insect', digits=(12, 2))