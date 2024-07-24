# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    
        # self.compute_scontract_line()
        # self.compute_scontract()
        # self.compute_shipping_instruction()
        
    def sys_run_step1(self):
        self.sys_currency_run_step()
        self.result = "sys_run_step1"
    
    
    def sys_run_step2(self):
        self.sys_partner_run()
        self.result = "sys_run_step2"
    
    def sys_run_step3(self):
        self.sys_masterdata_sales_purchase_run()
        self.sys_product_run()
        self.sys_stock_master_data_run()
        self.result = "sys_run_step3.0"
        
    def sys_run_step3_1(self):
        self.syz_sale_contract()
        self.sys_res_currency_rate()
        self.result = "sys_run_step3.1"
    
    def sys_run_step3_2(self):
        self.syz_sale_contract_1()
        self.result = "sys_run_step3.2"
    
    def sys_run_step3_3(self):
        self.syz_sale_contract_2()
        self.result = "sys_run_step3.3"
    
    def sys_run_step3_4(self):
        self.syz_sale_contract_3()
        self.result = "sys_run_step3.4"
        
    
    def sys_run_step4(self):
        self.sys_stock_master_data2_run()
        self.sys_purchase_run1()
        self.sys_mrp_master11()
        self.sys_kcs1()
        self.result = "sys_run_step4"
        
    def sys_run_step5(self):
        self.sys_stock1_run()
        self.result = "sys_run_step5.1"
        
    def sys_run_step5_1(self):
        self.sys_stock1_1_run()
        self.result = "sys_run_step5.2" 
    
    
    
    def sys_run_step6(self):
        self.sys_stock2_run()
        self.result = "sys_run_step6"
    
    def sys_run_step7(self):
        self.sys_stock3_run()
        self.result = "sys_run_step7"
    
    def sys_run_step8(self):
        self.sys_kcs2()
        self.result = "sys_run_step8"
    
    def sys_run_step9(self):
        self.sys_mrp_master12()
        self.result = "sys_run_step9"
    
    def sys_run_step10(self):
        self.sys_acc1()
        self.sys_purchase_run2()
        self.result = "sys_run_step10"
    
    def sys_run_step11(self):
        self.sys_acc2()
        self.result = "sys_run_step11 _ Setup ACC company"
    
    def sys_run_step12(self):
        self.sys_acc3()
        self.result = "sys_run_step12"
    
    def sys_run_step13(self):
        self.sys_purchase_run3()
        self.result = "sys_run_step13"
    
    def sys_run_step14(self):
        self.sys_api_v14()
        self.result = "sys_run_step14"
    
    def sys_run_step15(self):
        self.sys_purchase_run4()
        # 
        self.sys_update_production_to_lot()
        self.result = "sys_run_step15"
    
    def sys_run_step16(self):
        self.compute_payable_receive()
        self.compute_category_acc()
        self.result = "sys_run_step16"
    
    def sys_run_step17(self):
        self.sys_acc4()
        self.result = "sys_run_step17"
    
    def sys_run_step18(self):
        self.compute_purchase()
        self.sys_compute_type_acc()
        # self.compute_res_comcompany()
        self.result = "sys_run_step18"
    
    def sys_run_step19(self):
        self.run_acc_move()
        self.result = "sys_run_step19"
    
    def sys_run_step20(self):
        self.run_acc_move2()
        self.result = "sys_run_step20"
    
    def sys_run_step21(self):
        self.sys_traffic_run()
        # self.compute_res_comcompany()
        self.result = "sys_run_step21"
    
    def sys_run_step22(self):
        self.sys_report_production_pnl()
        self.result = "sys_run_step22"
    
    def sys_run_step23(self):
        self.run_acc_move_final()
        self.update_fields_acconut_payment()
        self.result = "sys_run_step23"
    
    def sys_run_step24(self):
        self.run_acc_move_final()
        self.sys_report_batch()
        self.result = "sys_run_step24"
    
    def sys_run_step25(self):
        self.sys_run_move_interest()
        self.result = "sys_run_step25"
    
    def sys_run_step26(self):
        self.sys_run_move_interest_line()
        self.update_lot_for_s_contract()
        self.sys_sale_contract_deatail()
        self.result = "sys_run_step26"
    
    def sys_run_step27(self):
        self.sys_certificate_s_contract_ref()
        self.sys_certificate_shipping_instruction_ref()
        self.result = "sys_run_step277"
    
    def sys_run_step28(self):
        self.sys_daily_confirmation()
        self.sys_daily_confirmation_line()
        self.result = "sys_run_step28"
    
    def sys_run_step29(self):
        sql ='''
            update account_move_line set account_id = 1509 
            where id in (
            
            select aml.id from account_move_line aml join account_move am on aml.move_id = am.id
            where 
                am.move_type in ('out_invoice')
                and aml.account_id = 1514
            )
        '''
        self.env.cr.execute(sql)
        count =0
        for i in self.env['res.partner'].search([('property_account_receivable_id','=',1514)]):
            print(count, i.name)
            i.property_account_receivable_id = 1509
            count +=1
            if count > 1000:
                break
        
        
        
        
    
        
    

    
        
        
    
    
                
       
  

            


        
    