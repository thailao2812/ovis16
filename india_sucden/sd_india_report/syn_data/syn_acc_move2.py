from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re

DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
        
                       
    
    def run_acc_move_final(self):
        self.sys_account_payment_final()
    
    
    def sys_account_payment_final(self):
        sql ='''
        INSERT INTO 
            account_payment 
            (
                id, 
                create_date, create_uid, 
                write_date,   write_uid, 
                --move_id  ,
                partner_bank_id ,
                --paired_internal_transfer_payment_id ,
                --payment_method_line_id ,
                --DATA.payment_method_id ,
                currency_id ,
                partner_id ,
                --outstanding_account_id ,
                --destination_account_id ,
                --destination_journal_id ,
                payment_type   ,
                partner_type  ,
                payment_reference  ,
                amount ,
                --amount_company_currency_signed ,
                --is_reconciled ,
                --is_matched ,
                --is_internal_transfer ,
                --payment_transaction_id ,
                --payment_token_id ,
                --source_payment_id ,
                request_payment_id ,
                purchase_contract_id ,
                extend_payment  ,
                payment_date ,
                --payment_refunded ,
                --open_advance ,
                allocated ,
                company_analytic_account_id ,
                account_analytic_id ,
                invoice_currency_id ,
                conversion_currency_id ,
                responsible  ,
                communication  ,
                invoice_reference  ,
                conversion_currency_amount ,
                currency_rate ,
                conversion_currency_rate                    
            )        
        
        
        SELECT * 
        from 
        (
        SELECT 
            
            DATA.id, 
            DATA.create_date,  DATA.create_uid, 
            DATA.write_date,  DATA.write_uid, 
            --move_id  ,
            partner_bank_id ,
            --paired_internal_transfer_payment_id ,
            --payment_method_line_id ,
            --DATA.payment_method_id ,
            currency_id ,
            partner_id ,
            --outstanding_account_id ,
            --destination_account_id ,
            --destination_journal_id ,
            payment_type   ,
            COALESCE(partner_type,'customer') as partner_type    ,
            payment_reference  ,
            amount ,
            --amount_company_currency_signed ,
            --is_reconciled ,
            --is_matched ,
            --is_internal_transfer ,
            --payment_transaction_id ,
            --payment_token_id ,
            --source_payment_id ,
            request_payment_id ,
            purchase_contract_id ,
            extend_payment  ,
            payment_date ,
            --payment_refunded ,
            --open_advance ,
            allocated ,
            company_analytic_account_id ,
            account_analytic_id ,
            invoice_currency_id ,
            conversion_currency_id ,
            responsible  ,
            communication  ,
            invoice_reference  ,
            conversion_currency_amount ,
            currency_rate ,
            conversion_currency_rate 
            
            
            FROM public.dblink
            ('%s',
             'SELECT 
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                --move_id  ,
                partner_bank_id ,
                --paired_internal_transfer_payment_id ,
                --payment_method_line_id ,
                payment_method_id ,
                currency_id ,
                partner_id ,
                --outstanding_account_id ,
                --destination_account_id ,
                destination_journal_id ,
                payment_type   ,
                partner_type   ,
                payment_reference  ,
                amount ,
                --amount_company_currency_signed ,
                --is_reconciled ,
                --is_matched ,
                --is_internal_transfer ,
                --payment_transaction_id ,
                --payment_token_id ,
                --source_payment_id ,
                request_payment_id ,
                purchase_contract_id ,
                extend_payment  ,
                payment_date date,
                --payment_refunded ,
                --open_advance ,
                allocated ,
                company_analytic_account_id ,
                account_analytic_id ,
                invoice_currency_id ,
                conversion_currency_id ,
                responsible  ,
                communication  ,
                invoice_reference  ,
                conversion_currency_amount ,
                currency_rate ,
                conversion_currency_rate 
                
            FROM public.account_payment 
            WHERE purchase_contract_id is not null') 
            
            AS DATA(id INTEGER,
                create_date timestamp without time zone,
                create_uid integer,
                write_date timestamp without time zone,
                write_uid integer,  
                
                --move_id integer ,
                partner_bank_id integer,
                --paired_internal_transfer_payment_id integer,
                --payment_method_line_id integer,
                payment_method_id integer,
                currency_id integer,
                partner_id integer,
                --outstanding_account_id integer,
                destination_account_id integer,
                --destination_journal_id integer,
                payment_type character varying  ,
                partner_type character varying  ,
                payment_reference character varying ,
                amount numeric,
                --amount_company_currency_signed numeric,
                --is_reconciled boolean,
                --is_matched boolean,
                --is_internal_transfer boolean,
                --payment_transaction_id integer,
                --payment_token_id integer,
                --source_payment_id integer,
                request_payment_id integer,
                purchase_contract_id integer,
                extend_payment character varying ,
                payment_date date,
                --payment_refunded numeric,
                --open_advance numeric,
                allocated boolean,
                company_analytic_account_id integer,
                account_analytic_id integer,
                invoice_currency_id integer,
                conversion_currency_id integer,
                responsible character varying ,
                communication character varying ,
                invoice_reference character varying ,
                conversion_currency_amount numeric,
                currency_rate double precision,
                conversion_currency_rate double precision
            ) ) xx
            where xx.id not in (select id from account_payment)
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_payment_id_seq', (select max(id) + 1 from  account_payment));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    