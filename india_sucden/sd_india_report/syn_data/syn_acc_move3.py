from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re

DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    def sys_run_move_interest_line(self):
        self.sys_account_move_line_relate_interest()
        self.sys_account_move_line_relate_interest_1()
    
    def sys_run_move_interest(self):
        sql ='''
            DELETE FROM account_move_line where move_id in (
                    SELECT 
                        interest_move_id
                        FROM public.dblink
                                    ('%s',
                                     'SELECT p.id contract_id, 
                                         am.id as interest_move_id
                                    FROM account_move am 
                                        join purchase_contract p on p.interest_move_id = am.id') 
                                    AS DATA(
                                            contract_id integer,
                                            interest_move_id integer                           
                                        ));
            
            DELETE   
            FROM  account_move
            WHERE id in (
                    SELECT 
                        interest_move_id
                        FROM public.dblink
                                    ('%s',
                                     'SELECT p.id contract_id, 
                                         am.id as interest_move_id
                                    FROM account_move am 
                                        join purchase_contract p on p.interest_move_id = am.id') 
                                    AS DATA(
                                            contract_id integer,
                                            interest_move_id integer                           
                                        ));
            
            
            DELETE FROM account_move_line where move_id in (
                    SELECT 
                        interest_move_entries_id
                        FROM public.dblink
                                    ('%s',
                                     'SELECT p.id contract_id, 
                                         am.id as interest_move_entries_id
                                    FROM account_move am 
                                        join purchase_contract p on p.interest_move_entries_id = am.id') 
                                    AS DATA(
                                            contract_id integer,
                                            interest_move_entries_id integer                           
                                        ));
            
            DELETE FROM account_move where id in (
                    SELECT 
                        interest_move_entries_id
                        FROM public.dblink
                                    ('%s',
                                     'SELECT p.id contract_id, 
                                         am.id as interest_move_entries_id
                                    FROM account_move am 
                                        join purchase_contract p on p.interest_move_entries_id = am.id') 
                                    AS DATA(
                                            contract_id integer,
                                            interest_move_entries_id integer                           
                                        ));
            
           
        '''%(self.server_db_link,self.server_db_link, self.server_db_link, self.server_db_link)
        self.env.cr.execute(sql)
        self.sys_account_move_relate_interest()
        self.update_relate_interest()

        self.sys_account_move_relate_interest_1()
        self.update_relate_interest_1()
    
    
    def update_relate_interest(self):
        sql ='''
        UPDATE purchase_contract set interest_move_id = xoo.interest_move_id
            from
            (
                SELECT 
                    *
                    FROM public.dblink
                                ('%s',
                                 'SELECT p.id contract_id, 
                                     am.id as interest_move_id
                                FROM account_move am 
                                    join purchase_contract p on p.interest_move_id = am.id') 
                                AS DATA(
                                        contract_id integer,
                                        interest_move_id integer                           
                                    )
                ) xoo
                where purchase_contract.id = xoo.contract_id
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        return
    
    def sys_account_move_relate_interest(self):
        sql ='''
        INSERT INTO 
            account_move 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                journal_id  ,
                    company_id ,
                    --payment_id ,
                    statement_line_id ,
                    --tax_cash_basis_rec_id ,
                    --tax_cash_basis_origin_move_id ,
                    --auto_post_origin_id ,
                    --secure_sequence_number ,
                   -- invoice_payment_term_id ,
                    partner_id ,
                    --commercial_partner_id ,
                    --partner_shipping_id ,
                    --partner_bank_id ,
                    --fiscal_position_id ,
                    currency_id  ,
                    --reversed_entry_id ,
                    --invoice_user_id ,
                    --invoice_incoterm_id ,
                    --invoice_cash_rounding_id ,
                    --sequence_prefix  ,
                    --access_token  ,
                    name  ,
                    ref  ,
                    state   ,
                    move_type   ,
                    auto_post   ,
                    --inalterable_hash  ,
                    --payment_reference  ,
                    --qr_code_method  ,
                    --payment_state  ,
                    --invoice_source_email  ,
                    --invoice_partner_display_name  ,
                    --invoice_origin  ,
                    date  ,
                    --auto_post_until ,
                    invoice_date ,
                    --invoice_date_due ,
                    narration  ,
                    --amount_untaxed ,
                    --amount_tax ,
                    --amount_total ,
                    --amount_residual ,
                    --amount_untaxed_signed ,
                    --amount_tax_signed ,
                    --amount_total_signed ,
                    --amount_total_in_currency_signed ,
                    --amount_residual_signed ,
                    --quick_edit_total_amount ,
                    --is_storno ,
                    --always_tax_exigible ,
                    --to_check ,
                    --posted_before ,
                    --is_move_sent ,
                    --edi_state  ,
                    --stock_move_id ,
                    --sale_contract_id ,
                    --purchase_contract_id ,
                    --contract_id ,
                    --supplier_inv_date date,
                    account_analytic_id 
                    --l10n_in_state_id ,
                    --l10n_in_shipping_port_code_id ,
                    --l10n_in_reseller_partner_id ,
                    --l10n_in_gst_treatment  ,
                    --l10n_in_gstin  ,
                    --l10n_in_shipping_bill_number  ,
                    --l10n_in_shipping_bill_date
            )        
        
        SELECT 
            
            id,
                create_date,create_uid,
                write_date, write_uid,                     
                journal_id  ,
                    company_id ,
                    --payment_id ,
                    statement_line_id ,
                    --tax_cash_basis_rec_id ,
                    --tax_cash_basis_origin_move_id ,
                    --auto_post_origin_id ,
                    --secure_sequence_number ,
                   -- invoice_payment_term_id ,
                    partner_id ,
                    --commercial_partner_id ,
                    --partner_shipping_id ,
                    --partner_bank_id ,
                    --fiscal_position_id ,
                    currency_id  ,
                    --reversed_entry_id ,
                    --invoice_user_id ,
                    --invoice_incoterm_id ,
                    --invoice_cash_rounding_id ,
                    --sequence_prefix  ,
                    --access_token  ,
                    name|| 'xxxx' ||id as name  ,
                    ref  ,
                    state   ,
                    'entry' as move_type   ,
                    'no' as auto_post   ,
                    --inalterable_hash  ,
                    --payment_reference  ,
                    --qr_code_method  ,
                    --payment_state  ,
                    --invoice_source_email  ,
                    --invoice_partner_display_name  ,
                    --invoice_origin  ,
                    date  ,
                    --auto_post_until ,
                    invoice_date ,
                    --invoice_date_due ,
                    narration  ,
                    --amount_untaxed ,
                    --amount_tax ,
                    --amount_total ,
                    --amount_residual ,
                    --amount_untaxed_signed ,
                    --amount_tax_signed ,
                    --amount_total_signed ,
                    --amount_total_in_currency_signed ,
                    --amount_residual_signed ,
                    --quick_edit_total_amount ,
                    --is_storno ,
                    --always_tax_exigible ,
                    --to_check ,
                    --posted_before ,
                    --is_move_sent ,
                    --edi_state  ,
                    --stock_move_id ,
                    --sale_contract_id ,
                    --purchase_contract_id ,
                    --contract_id ,
                    --supplier_inv_date date,
                    account_analytic_id 
                    --l10n_in_state_id ,
                    --l10n_in_shipping_port_code_id ,
                    --l10n_in_reseller_partner_id ,
                    --l10n_in_gst_treatment  ,
                    --l10n_in_gstin  ,
                    --l10n_in_shipping_bill_number  ,
                    --l10n_in_shipping_bill_date
            
            
            FROM public.dblink
                ('%s',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date,  write_uid, 
                    --sequence_number ,
                    journal_id  ,
                    company_id ,
                    --payment_id ,
                    statement_line_id ,
                    --tax_cash_basis_rec_id ,
                    --tax_cash_basis_origin_move_id ,
                    --auto_post_origin_id ,
                    --secure_sequence_number ,
                   -- invoice_payment_term_id ,
                    partner_id ,
                    --commercial_partner_id ,
                    --partner_shipping_id ,
                    --partner_bank_id ,
                    --fiscal_position_id ,
                    currency_id  ,
                    --reversed_entry_id ,
                    --invoice_user_id ,
                    --invoice_incoterm_id ,
                    --invoice_cash_rounding_id ,
                    --sequence_prefix  ,
                    --access_token  ,
                    name  ,
                    ref  ,
                    state   ,
                    --move_type   ,
                    --auto_post   ,
                    --inalterable_hash  ,
                    --payment_reference  ,
                    --qr_code_method  ,
                    --payment_state  ,
                    --invoice_source_email  ,
                    --invoice_partner_display_name  ,
                    --invoice_origin  ,
                    date date ,
                    --auto_post_until ,
                    invoice_date ,
                    --invoice_date_due ,
                    narration  ,
                    --amount_untaxed ,
                    --amount_tax ,
                    --amount_total ,
                    --amount_residual ,
                    --amount_untaxed_signed ,
                    --amount_tax_signed ,
                    --amount_total_signed ,
                    --amount_total_in_currency_signed ,
                    --amount_residual_signed ,
                    --quick_edit_total_amount ,
                    --is_storno ,
                    --always_tax_exigible ,
                    --to_check ,
                    --posted_before ,
                    --is_move_sent ,
                    --edi_state  ,
                    --stock_move_id ,
                    --sale_contract_id ,
                    --purchase_contract_id ,
                    --contract_id ,
                    --supplier_inv_date date,
                    account_analytic_id 
                    --l10n_in_state_id ,
                    --l10n_in_shipping_port_code_id ,
                    --l10n_in_reseller_partner_id ,
                    --l10n_in_gst_treatment  ,
                    --l10n_in_gstin  ,
                    --l10n_in_shipping_bill_number  ,
                    --l10n_in_shipping_bill_date
                    
                    
                FROM public.account_move
                WHERE
                    id in (Select am.id 
                            FROM account_move am join purchase_contract p on p.interest_move_id = am.id)
                 ') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        --sequence_number integer,
                        journal_id integer ,
                        company_id integer,
                        --payment_id integer,
                        statement_line_id integer,
                        --tax_cash_basis_rec_id integer,
                        --tax_cash_basis_origin_move_id integer,
                        --auto_post_origin_id integer,
                        --secure_sequence_number integer,
                        --invoice_payment_term_id integer,
                        partner_id integer,
                        --commercial_partner_id integer,
                        --partner_shipping_id integer,
                        --partner_bank_id integer,
                        --fiscal_position_id integer,
                        currency_id integer ,
                        --reversed_entry_id integer,
                        --invoice_user_id integer,
                        --invoice_incoterm_id integer,
                        --invoice_cash_rounding_id integer,
                        --sequence_prefix character varying ,
                        --access_token character varying ,
                        name character varying ,
                        ref character varying ,
                        state character varying  ,
                        --move_type character varying  ,
                        --auto_post character varying  ,
                        --inalterable_hash character varying ,
                        --payment_reference character varying ,
                        --qr_code_method character varying ,
                        --payment_state character varying ,
                        --invoice_source_email character varying ,
                        --invoice_partner_display_name character varying ,
                        --invoice_origin character varying ,
                        date date ,
                        --auto_post_until date,
                        invoice_date date,
                        --invoice_date_due date,
                        narration text ,
                        --amount_untaxed numeric,
                        --amount_tax numeric,
                        --amount_total numeric,
                        --amount_residual numeric,
                        --amount_untaxed_signed numeric,
                        --amount_tax_signed numeric,
                        --amount_total_signed numeric,
                        --amount_total_in_currency_signed numeric,
                        --amount_residual_signed numeric,
                        --quick_edit_total_amount numeric,
                        --is_storno boolean,
                        --always_tax_exigible boolean,
                        --to_check boolean,
                        --posted_before boolean,
                        --is_move_sent boolean,
                        --edi_state character varying ,
                        --stock_move_id integer,
                        --sale_contract_id integer,
                        --purchase_contract_id integer,
                        --contract_id integer,
                        --supplier_inv_date date,
                        account_analytic_id integer
                        --l10n_in_state_id integer,
                        --l10n_in_shipping_port_code_id integer,
                        --l10n_in_reseller_partner_id integer,
                        --l10n_in_gst_treatment character varying ,
                        --l10n_in_gstin character varying ,
                        --l10n_in_shipping_bill_number character varying ,
                        --l10n_in_shipping_bill_date date  
                    )
        
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_move_id_seq', (select max(id) + 1 from  account_move));
        ''')  
    
    def sys_account_move_line_relate_interest(self):
        sql ='''
        INSERT INTO 
            account_move_line 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,     
                move_id  ,
                journal_id ,
                company_id ,
                company_currency_id ,
                --sequence ,
                account_id ,
                currency_id  ,
                partner_id ,
                --reconcile_model_id ,
                payment_id ,
                --statement_line_id ,
                statement_id ,
                --group_tax_id ,
                tax_line_id ,
                --tax_group_id ,
                --tax_repartition_line_id ,
                --full_reconcile_id ,
                --account_root_id ,
                product_id ,
                product_uom_id ,                       
                --move_name  ,
                --parent_state  ,
                ref  ,
                name  ,
                --tax_audit  ,
                --matching_number  ,
                display_type   ,           
                
                date ,
                date_maturity ,
                --discount_date ,
                --analytic_distribution ,
                debit ,
                credit ,
                balance ,
                amount_currency ,
                --tax_base_amount ,
                amount_residual ,
                amount_residual_currency ,
                quantity ,
                --price_unit ,
                --price_subtotal ,
                --price_total ,
                --discount ,
                --discount_amount_currency ,
                --discount_balance ,
                --tax_tag_invert ,
                reconciled ,
                blocked ,
                --discount_percentage ,
                second_currency_id ,
                rate_type  ,
                currency_ex_rate ,
                second_ex_rate ,
                second_amount ,
                price_unit,
                price_subtotal
            )        
        
    SELECT  *
     from (
         SELECT 
            
            id,
            create_date,create_uid,
            write_date, write_uid,     
            move_id  ,
            journal_id ,
            company_id ,
            company_currency_id ,
            --sequence ,
            account_id ,
            currency_id  ,
            partner_id ,
            --reconcile_model_id ,
            payment_id ,
            --statement_line_id ,
            statement_id ,
            --group_tax_id ,
            tax_line_id ,
            --tax_group_id ,
            --tax_repartition_line_id ,
            --full_reconcile_id ,
            --account_root_id ,
            product_id ,
            product_uom_id ,                       
            --move_name  ,
            --parent_state  ,
            ref  ,
            name  ,
            --tax_audit  ,
            --matching_number  ,
            
            CASE WHEN aa_type in('liability_payable','asset_receivable') THEN 'payment_term'::text
                  else 'product'::text                                     
                END AS display_type,
            --display_type   ,           
            
            
            date date,
            date_maturity ,
            --discount_date ,
            --analytic_distribution ,
            debit ,
            credit ,
            balance ,
            amount_currency ,
            --tax_base_amount ,
            amount_residual ,
            amount_residual_currency ,
            quantity ,
            --price_unit ,
            --price_subtotal ,
            --price_total ,
            --discount ,
            --discount_amount_currency ,
            --discount_balance ,
            --tax_tag_invert ,
            reconciled ,
            blocked ,
            --discount_percentage ,
            second_currency_id ,
            rate_type  ,
            currency_ex_rate ,
            second_ex_rate ,
            second_amount,
            
            CASE
                  WHEN currency_id is not null and quantity !=0 THEN abs(amount_currency) / quantity
                  WHEN currency_id is null and debit !=0 and quantity !=0  THEN  debit/ quantity
                  WHEN currency_id is null and credit !=0 and quantity !=0  THEN  credit/ quantity                       
            END AS price_unit,
            
            CASE
                  WHEN currency_id is not null and quantity !=0 THEN abs(amount_currency)
                  WHEN currency_id is null and debit !=0 THEN  debit
                  WHEN currency_id is null and credit !=0 THEN  credit                     
            END AS price_subtotal
        
        FROM public.dblink
            ('%s',
             'SELECT 
                aml.id, 
                aml.create_date, aml.create_uid, 
                aml.write_date, aml.write_uid, 
                
                aml.move_id  ,
                aml.journal_id ,
                aml.company_id ,
                company_currency_id ,
                --sequence ,
                aml.account_id ,
                COALESCE(aml.currency_id ,am.currency_id) as currency_id ,
                aml.partner_id ,
                --reconcile_model_id ,
                payment_id ,
                --statement_line_id ,
                statement_id ,
                --group_tax_id ,
                tax_line_id ,
                --tax_group_id ,
                --tax_repartition_line_id ,
                --full_reconcile_id ,
                --account_root_id ,
                aml.product_id ,
                product_uom_id ,                       
                --move_name  ,
                --parent_state  ,
                aml.ref  ,
                aml.name  ,
                --tax_audit  ,
                --matching_number  ,
                --display_type   ,
                aml.date date,
                date_maturity ,
                --discount_date ,
                --analytic_distribution ,
                debit ,
                credit ,
                balance ,
                amount_currency ,
                --tax_base_amount ,
                amount_residual ,
                amount_residual_currency ,
                quantity ,
                --price_unit ,
                --price_subtotal ,
                --price_total ,
                --discount ,
                --discount_amount_currency ,
                --discount_balance ,
                --tax_tag_invert ,
                aml.reconciled ,
                blocked ,
                --discount_percentage ,
                aml.second_currency_id ,
                rate_type  ,
                currency_ex_rate ,
                aml.second_ex_rate ,
                aml.second_amount ,                
                aa.type aa_type
                
                    
            FROM public.account_move_line aml 
                join account_move am on aml.move_id = am.id               
                join account_account aa on aml.account_id = aa.id
            where aml.id not in (553365, 553366, 553370, 553369, 553362, 553361, 553363, 553364, 553357, 553357)
            ') 
            AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,  
                                              
                    move_id integer ,
                    journal_id integer,
                    company_id integer,
                    company_currency_id integer,
                    --sequence integer,
                    account_id integer,
                    currency_id integer ,
                    partner_id integer,
                    --reconcile_model_id integer,
                    payment_id integer,
                    --statement_line_id integer,
                    statement_id integer,
                    --group_tax_id integer,
                    tax_line_id integer,
                    --tax_group_id integer,
                    --tax_repartition_line_id integer,
                    --full_reconcile_id integer,
                    --account_root_id integer,
                    product_id integer,
                    product_uom_id integer,
                    
                    --move_name character varying ,
                    --parent_state character varying ,
                    ref character varying ,
                    name character varying ,
                    --tax_audit character varying ,
                    --matching_number character varying ,
                    --display_type character varying  ,
                    date date,
                    date_maturity date,
                    --discount_date date,
                    --analytic_distribution jsonb,
                    debit numeric,
                    credit numeric,
                    balance numeric,
                    amount_currency numeric,
                    --tax_base_amount numeric,
                    amount_residual numeric,
                    amount_residual_currency numeric,
                    quantity numeric,
                    --price_unit numeric,
                    --price_subtotal numeric,
                    --price_total numeric,
                    --discount numeric,
                    --discount_amount_currency numeric,
                    --discount_balance numeric,
                    --tax_tag_invert boolean,
                    reconciled boolean,
                    blocked boolean,
                    --discount_percentage double precision,
                    second_currency_id integer,
                    rate_type character varying ,
                    currency_ex_rate double precision,
                    second_ex_rate double precision,
                    second_amount double precision,                    
                    aa_type character varying
                   
                )) f
        WHERE move_id in (Select am.id 
                            FROM account_move am join purchase_contract p on p.interest_move_id = am.id)
            
                 
        ''' %(self.server_db_link)
        self.env.cr.execute(sql)
        
        self.env.cr.execute('''
            SELECT setval('account_move_line_id_seq', (select max(id) + 1 from  account_move_line));
        ''') 
        
        return
    
    def update_relate_interest_1(self):
        sql ='''
        UPDATE purchase_contract set interest_move_entries_id = xoo.interest_move_entries_id
            from
            (
                SELECT 
                    *
                    FROM public.dblink
                                ('%s',
                                 'SELECT p.id contract_id, 
                                     am.id as interest_move_entries_id
                                FROM account_move am 
                                    join purchase_contract p on p.interest_move_entries_id = am.id') 
                                AS DATA(
                                        contract_id integer,
                                        interest_move_entries_id integer                           
                                    )
                ) xoo
                where purchase_contract.id = xoo.contract_id
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        return
    
    def sys_account_move_relate_interest_1(self):
        sql ='''
        INSERT INTO 
            account_move 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                journal_id  ,
                    company_id ,
                    --payment_id ,
                    statement_line_id ,
                    --tax_cash_basis_rec_id ,
                    --tax_cash_basis_origin_move_id ,
                    --auto_post_origin_id ,
                    --secure_sequence_number ,
                   -- invoice_payment_term_id ,
                    partner_id ,
                    --commercial_partner_id ,
                    --partner_shipping_id ,
                    --partner_bank_id ,
                    --fiscal_position_id ,
                    currency_id  ,
                    --reversed_entry_id ,
                    --invoice_user_id ,
                    --invoice_incoterm_id ,
                    --invoice_cash_rounding_id ,
                    --sequence_prefix  ,
                    --access_token  ,
                    name  ,
                    ref  ,
                    state   ,
                    move_type   ,
                    auto_post   ,
                    --inalterable_hash  ,
                    --payment_reference  ,
                    --qr_code_method  ,
                    --payment_state  ,
                    --invoice_source_email  ,
                    --invoice_partner_display_name  ,
                    --invoice_origin  ,
                    date  ,
                    --auto_post_until ,
                    invoice_date ,
                    --invoice_date_due ,
                    narration  ,
                    --amount_untaxed ,
                    --amount_tax ,
                    --amount_total ,
                    --amount_residual ,
                    --amount_untaxed_signed ,
                    --amount_tax_signed ,
                    --amount_total_signed ,
                    --amount_total_in_currency_signed ,
                    --amount_residual_signed ,
                    --quick_edit_total_amount ,
                    --is_storno ,
                    --always_tax_exigible ,
                    --to_check ,
                    --posted_before ,
                    --is_move_sent ,
                    --edi_state  ,
                    --stock_move_id ,
                    --sale_contract_id ,
                    --purchase_contract_id ,
                    --contract_id ,
                    --supplier_inv_date date,
                    account_analytic_id 
                    --l10n_in_state_id ,
                    --l10n_in_shipping_port_code_id ,
                    --l10n_in_reseller_partner_id ,
                    --l10n_in_gst_treatment  ,
                    --l10n_in_gstin  ,
                    --l10n_in_shipping_bill_number  ,
                    --l10n_in_shipping_bill_date
            )        
        
        SELECT 
            
            id,
                create_date,create_uid,
                write_date, write_uid,                     
                journal_id  ,
                    company_id ,
                    --payment_id ,
                    statement_line_id ,
                    --tax_cash_basis_rec_id ,
                    --tax_cash_basis_origin_move_id ,
                    --auto_post_origin_id ,
                    --secure_sequence_number ,
                   -- invoice_payment_term_id ,
                    partner_id ,
                    --commercial_partner_id ,
                    --partner_shipping_id ,
                    --partner_bank_id ,
                    --fiscal_position_id ,
                    currency_id  ,
                    --reversed_entry_id ,
                    --invoice_user_id ,
                    --invoice_incoterm_id ,
                    --invoice_cash_rounding_id ,
                    --sequence_prefix  ,
                    --access_token  ,
                    name|| 'xxxx' ||id as name  ,
                    ref  ,
                    state   ,
                    'entry' as move_type   ,
                    'no' as auto_post   ,
                    --inalterable_hash  ,
                    --payment_reference  ,
                    --qr_code_method  ,
                    --payment_state  ,
                    --invoice_source_email  ,
                    --invoice_partner_display_name  ,
                    --invoice_origin  ,
                    date  ,
                    --auto_post_until ,
                    invoice_date ,
                    --invoice_date_due ,
                    narration  ,
                    --amount_untaxed ,
                    --amount_tax ,
                    --amount_total ,
                    --amount_residual ,
                    --amount_untaxed_signed ,
                    --amount_tax_signed ,
                    --amount_total_signed ,
                    --amount_total_in_currency_signed ,
                    --amount_residual_signed ,
                    --quick_edit_total_amount ,
                    --is_storno ,
                    --always_tax_exigible ,
                    --to_check ,
                    --posted_before ,
                    --is_move_sent ,
                    --edi_state  ,
                    --stock_move_id ,
                    --sale_contract_id ,
                    --purchase_contract_id ,
                    --contract_id ,
                    --supplier_inv_date date,
                    account_analytic_id 
                    --l10n_in_state_id ,
                    --l10n_in_shipping_port_code_id ,
                    --l10n_in_reseller_partner_id ,
                    --l10n_in_gst_treatment  ,
                    --l10n_in_gstin  ,
                    --l10n_in_shipping_bill_number  ,
                    --l10n_in_shipping_bill_date
            
            
            FROM public.dblink
                ('%s',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date,  write_uid, 
                    --sequence_number ,
                    journal_id  ,
                    company_id ,
                    --payment_id ,
                    statement_line_id ,
                    --tax_cash_basis_rec_id ,
                    --tax_cash_basis_origin_move_id ,
                    --auto_post_origin_id ,
                    --secure_sequence_number ,
                   -- invoice_payment_term_id ,
                    partner_id ,
                    --commercial_partner_id ,
                    --partner_shipping_id ,
                    --partner_bank_id ,
                    --fiscal_position_id ,
                    currency_id  ,
                    --reversed_entry_id ,
                    --invoice_user_id ,
                    --invoice_incoterm_id ,
                    --invoice_cash_rounding_id ,
                    --sequence_prefix  ,
                    --access_token  ,
                    name  ,
                    ref  ,
                    state   ,
                    --move_type   ,
                    --auto_post   ,
                    --inalterable_hash  ,
                    --payment_reference  ,
                    --qr_code_method  ,
                    --payment_state  ,
                    --invoice_source_email  ,
                    --invoice_partner_display_name  ,
                    --invoice_origin  ,
                    date date ,
                    --auto_post_until ,
                    invoice_date ,
                    --invoice_date_due ,
                    narration  ,
                    --amount_untaxed ,
                    --amount_tax ,
                    --amount_total ,
                    --amount_residual ,
                    --amount_untaxed_signed ,
                    --amount_tax_signed ,
                    --amount_total_signed ,
                    --amount_total_in_currency_signed ,
                    --amount_residual_signed ,
                    --quick_edit_total_amount ,
                    --is_storno ,
                    --always_tax_exigible ,
                    --to_check ,
                    --posted_before ,
                    --is_move_sent ,
                    --edi_state  ,
                    --stock_move_id ,
                    --sale_contract_id ,
                    --purchase_contract_id ,
                    --contract_id ,
                    --supplier_inv_date date,
                    account_analytic_id 
                    --l10n_in_state_id ,
                    --l10n_in_shipping_port_code_id ,
                    --l10n_in_reseller_partner_id ,
                    --l10n_in_gst_treatment  ,
                    --l10n_in_gstin  ,
                    --l10n_in_shipping_bill_number  ,
                    --l10n_in_shipping_bill_date
                    
                    
                FROM public.account_move
                WHERE
                    id in (Select am.id 
                            FROM account_move am join purchase_contract p on p.interest_move_entries_id = am.id)
                 ') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        --sequence_number integer,
                        journal_id integer ,
                        company_id integer,
                        --payment_id integer,
                        statement_line_id integer,
                        --tax_cash_basis_rec_id integer,
                        --tax_cash_basis_origin_move_id integer,
                        --auto_post_origin_id integer,
                        --secure_sequence_number integer,
                        --invoice_payment_term_id integer,
                        partner_id integer,
                        --commercial_partner_id integer,
                        --partner_shipping_id integer,
                        --partner_bank_id integer,
                        --fiscal_position_id integer,
                        currency_id integer ,
                        --reversed_entry_id integer,
                        --invoice_user_id integer,
                        --invoice_incoterm_id integer,
                        --invoice_cash_rounding_id integer,
                        --sequence_prefix character varying ,
                        --access_token character varying ,
                        name character varying ,
                        ref character varying ,
                        state character varying  ,
                        --move_type character varying  ,
                        --auto_post character varying  ,
                        --inalterable_hash character varying ,
                        --payment_reference character varying ,
                        --qr_code_method character varying ,
                        --payment_state character varying ,
                        --invoice_source_email character varying ,
                        --invoice_partner_display_name character varying ,
                        --invoice_origin character varying ,
                        date date ,
                        --auto_post_until date,
                        invoice_date date,
                        --invoice_date_due date,
                        narration text ,
                        --amount_untaxed numeric,
                        --amount_tax numeric,
                        --amount_total numeric,
                        --amount_residual numeric,
                        --amount_untaxed_signed numeric,
                        --amount_tax_signed numeric,
                        --amount_total_signed numeric,
                        --amount_total_in_currency_signed numeric,
                        --amount_residual_signed numeric,
                        --quick_edit_total_amount numeric,
                        --is_storno boolean,
                        --always_tax_exigible boolean,
                        --to_check boolean,
                        --posted_before boolean,
                        --is_move_sent boolean,
                        --edi_state character varying ,
                        --stock_move_id integer,
                        --sale_contract_id integer,
                        --purchase_contract_id integer,
                        --contract_id integer,
                        --supplier_inv_date date,
                        account_analytic_id integer
                        --l10n_in_state_id integer,
                        --l10n_in_shipping_port_code_id integer,
                        --l10n_in_reseller_partner_id integer,
                        --l10n_in_gst_treatment character varying ,
                        --l10n_in_gstin character varying ,
                        --l10n_in_shipping_bill_number character varying ,
                        --l10n_in_shipping_bill_date date  
                    )
        
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_move_id_seq', (select max(id) + 1 from  account_move));
        ''')  
    
    def sys_account_move_line_relate_interest_1(self):
        sql ='''
        INSERT INTO 
            account_move_line 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,     
                move_id  ,
                journal_id ,
                company_id ,
                company_currency_id ,
                --sequence ,
                account_id ,
                currency_id  ,
                partner_id ,
                --reconcile_model_id ,
                payment_id ,
                --statement_line_id ,
                statement_id ,
                --group_tax_id ,
                tax_line_id ,
                --tax_group_id ,
                --tax_repartition_line_id ,
                --full_reconcile_id ,
                --account_root_id ,
                product_id ,
                product_uom_id ,                       
                --move_name  ,
                --parent_state  ,
                ref  ,
                name  ,
                --tax_audit  ,
                --matching_number  ,
                display_type   ,           
                
                date ,
                date_maturity ,
                --discount_date ,
                --analytic_distribution ,
                debit ,
                credit ,
                balance ,
                amount_currency ,
                --tax_base_amount ,
                amount_residual ,
                amount_residual_currency ,
                quantity ,
                --price_unit ,
                --price_subtotal ,
                --price_total ,
                --discount ,
                --discount_amount_currency ,
                --discount_balance ,
                --tax_tag_invert ,
                reconciled ,
                blocked ,
                --discount_percentage ,
                second_currency_id ,
                rate_type  ,
                currency_ex_rate ,
                second_ex_rate ,
                second_amount ,
                price_unit,
                price_subtotal
            )        
    SELECT  *
     from (
         SELECT 
            
            id,
            create_date,create_uid,
            write_date, write_uid,     
            move_id  ,
            journal_id ,
            company_id ,
            company_currency_id ,
            --sequence ,
            account_id ,
            currency_id  ,
            partner_id ,
            --reconcile_model_id ,
            payment_id ,
            --statement_line_id ,
            statement_id ,
            --group_tax_id ,
            tax_line_id ,
            --tax_group_id ,
            --tax_repartition_line_id ,
            --full_reconcile_id ,
            --account_root_id ,
            product_id ,
            product_uom_id ,                       
            --move_name  ,
            --parent_state  ,
            ref  ,
            name  ,
            --tax_audit  ,
            --matching_number  ,
            
            CASE
                  WHEN aa_type in('liability_payable','asset_receivable') THEN 'payment_term'::text
                  else 'product'::text                                             
                END AS display_type,
            --display_type   ,           
            
            
            date date,
            date_maturity ,
            --discount_date ,
            --analytic_distribution ,
            debit ,
            credit ,
            balance ,
            amount_currency ,
            --tax_base_amount ,
            amount_residual ,
            amount_residual_currency ,
            quantity ,
            --price_unit ,
            --price_subtotal ,
            --price_total ,
            --discount ,
            --discount_amount_currency ,
            --discount_balance ,
            --tax_tag_invert ,
            reconciled ,
            blocked ,
            --discount_percentage ,
            second_currency_id ,
            rate_type  ,
            currency_ex_rate ,
            second_ex_rate ,
            second_amount,
            
            CASE
                  WHEN currency_id is not null and quantity !=0 THEN abs(amount_currency) / quantity
                  WHEN currency_id is null and debit !=0 and quantity !=0  THEN  debit/ quantity
                  WHEN currency_id is null and credit !=0 and quantity !=0  THEN  credit/ quantity                       
            END AS price_unit,
            
            CASE
                  WHEN currency_id is not null and quantity !=0 THEN abs(amount_currency)
                  WHEN currency_id is null and debit !=0 THEN  debit
                  WHEN currency_id is null and credit !=0 THEN  credit                     
            END AS price_subtotal
        
        FROM public.dblink
            ('%s',
             'SELECT 
                aml.id, 
                aml.create_date, aml.create_uid, 
                aml.write_date, aml.write_uid, 
                
                aml.move_id  ,
                aml.journal_id ,
                aml.company_id ,
                company_currency_id ,
                --sequence ,
                aml.account_id ,
                COALESCE(aml.currency_id ,am.currency_id) as currency_id ,
                aml.partner_id ,
                --reconcile_model_id ,
                payment_id ,
                --statement_line_id ,
                statement_id ,
                --group_tax_id ,
                tax_line_id ,
                --tax_group_id ,
                --tax_repartition_line_id ,
                --full_reconcile_id ,
                --account_root_id ,
                aml.product_id ,
                product_uom_id ,                       
                --move_name  ,
                --parent_state  ,
                aml.ref  ,
                aml.name  ,
                --tax_audit  ,
                --matching_number  ,
                --display_type   ,
                aml.date date,
                date_maturity ,
                --discount_date ,
                --analytic_distribution ,
                debit ,
                credit ,
                balance ,
                amount_currency ,
                --tax_base_amount ,
                amount_residual ,
                amount_residual_currency ,
                quantity ,
                --price_unit ,
                --price_subtotal ,
                --price_total ,
                --discount ,
                --discount_amount_currency ,
                --discount_balance ,
                --tax_tag_invert ,
                aml.reconciled ,
                blocked ,
                --discount_percentage ,
                aml.second_currency_id ,
                rate_type  ,
                currency_ex_rate ,
                aml.second_ex_rate ,
                aml.second_amount ,                
                aa.type aa_type
                
                    
            FROM public.account_move_line aml 
                join account_move am on aml.move_id = am.id               
                join account_account aa on aml.account_id = aa.id
            WHERE 
                aml.id not in (553357,553358)
            ') 
            AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,  
                                              
                    move_id integer ,
                    journal_id integer,
                    company_id integer,
                    company_currency_id integer,
                    --sequence integer,
                    account_id integer,
                    currency_id integer ,
                    partner_id integer,
                    --reconcile_model_id integer,
                    payment_id integer,
                    --statement_line_id integer,
                    statement_id integer,
                    --group_tax_id integer,
                    tax_line_id integer,
                    --tax_group_id integer,
                    --tax_repartition_line_id integer,
                    --full_reconcile_id integer,
                    --account_root_id integer,
                    product_id integer,
                    product_uom_id integer,
                    
                    --move_name character varying ,
                    --parent_state character varying ,
                    ref character varying ,
                    name character varying ,
                    --tax_audit character varying ,
                    --matching_number character varying ,
                    --display_type character varying  ,
                    date date,
                    date_maturity date,
                    --discount_date date,
                    --analytic_distribution jsonb,
                    debit numeric,
                    credit numeric,
                    balance numeric,
                    amount_currency numeric,
                    --tax_base_amount numeric,
                    amount_residual numeric,
                    amount_residual_currency numeric,
                    quantity numeric,
                    --price_unit numeric,
                    --price_subtotal numeric,
                    --price_total numeric,
                    --discount numeric,
                    --discount_amount_currency numeric,
                    --discount_balance numeric,
                    --tax_tag_invert boolean,
                    reconciled boolean,
                    blocked boolean,
                    --discount_percentage double precision,
                    second_currency_id integer,
                    rate_type character varying ,
                    currency_ex_rate double precision,
                    second_ex_rate double precision,
                    second_amount double precision,                    
                    aa_type character varying
                   
                )) fx
        WHERE move_id in (Select am.id 
                            FROM account_move am join purchase_contract p on p.interest_move_entries_id = am.id)
                 
        ''' %(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_move_line_id_seq', (select max(id) + 1 from  account_move_line));
        ''') 
        
        return
    