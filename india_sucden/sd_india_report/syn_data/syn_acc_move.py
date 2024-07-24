from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re

DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    
    def run_acc_move(self):
        self.sys_account_move_inv_sales()
        self.sys_account_move_line_inv_sales()
    
    def run_acc_move2(self):
        self.create_move_line_for_draft()
    
    def sys_compute_for_inv_type(self):
        sql = '''
            UPDATE account_move set inv_type = xoo.trans_type
            from
            (
                SELECT 
                    *
                    FROM public.dblink
                        ('%s',
                         'SELECT 
                            acc.id, 
                             aat.name
                         
                        FROM public.account_invoice acc 
                             join account_account_type aat on acc.user_type_id = aat.id') 
                        AS DATA(
                                id integer,
                                name character varying                           
                            )
                ) xoo
                where account_account.id = xoo.id and account_account.id != 1466
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        return
    
    def sys_compute_type_acc(self):
        sql = '''
            UPDATE account_account set account_type = xoo.name
            from
            (
                SELECT 
                    *
                    FROM public.dblink
                        ('%s',
                         'SELECT 
                            acc.id, 
                             aat.name
                         
                        FROM public.account_account acc 
                             join account_account_type aat on acc.user_type_id = aat.id') 
                        AS DATA(
                                id integer,
                                name character varying                           
                            )
                ) xoo
                where account_account.id = xoo.id and account_account.id != 1466
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        return
    
    def sys_account_move_inv_sales(self):
        sql ='''
        INSERT INTO 
            account_move 
            (
                id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    
                    --sequence_number ,
                        journal_id  ,
                        company_id ,
                        --payment_id ,
                        --statement_line_id ,
                        --tax_cash_basis_rec_id ,
                        --tax_cash_basis_origin_move_id ,
                        --auto_post_origin_id ,
                        --secure_sequence_number ,
                        --invoice_payment_term_id ,
                        partner_id ,
                        commercial_partner_id ,
                        --partner_shipping_id ,
                        partner_bank_id ,
                        fiscal_position_id ,
                        currency_id  ,
                        --reversed_entry_id ,
                        --invoice_user_id ,
                        --invoice_incoterm_id ,
                        --invoice_cash_rounding_id ,
                        --sequence_prefix  ,
                        --access_token  ,
                        name  ,
                        reference_description, 
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
                        --narration  ,
                        amount_untaxed ,
                        amount_tax ,
                        amount_total ,
                        --amount_residual ,
                        amount_untaxed_signed ,
                        amount_tax_signed ,
                        amount_total_signed ,
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
                        sale_contract_id ,
                        purchase_contract_id ,
                        contract_id ,
                        supplier_inv_date ,
                        account_analytic_id ,
                        ref_id  ,
                        origin  ,
                        transaction_id  ,
                        invoice_number  ,
                        status  ,
                        --base64_pdf  ,
                        ref_type  ,
                        org_ref_id  ,
                        org_invoice_number  ,
                        type_invoice  ,
                        --reference_description  ,
                        invoice_issue_date ,
                        org_invoice_issued_date,
                        trans_type
            )        
        
        SELECT 
            id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    
                    --sequence_number ,
                        journal_id  ,
                        company_id ,
                        --payment_id ,
                        --statement_line_id ,
                        --tax_cash_basis_rec_id ,
                        --tax_cash_basis_origin_move_id ,
                        --auto_post_origin_id ,
                        --secure_sequence_number ,
                        --invoice_payment_term_id ,
                        partner_id ,
                        commercial_partner_id ,
                        --partner_shipping_id ,
                        partner_bank_id ,
                        fiscal_position_id ,
                        currency_id  ,
                        --reversed_entry_id ,
                        --invoice_user_id ,
                        --invoice_incoterm_id ,
                        --invoice_cash_rounding_id ,
                        --sequence_prefix  ,
                        --access_token  ,
                        name ||'xx' || id as name ,
                        name,
                        reference  ,
                        CASE
                          WHEN state ='cancel' THEN 'cancel'::text
                          WHEN state  in ('open','paid') THEN 'posted'::text
                          WHEN state ='draft' THEN 'draft'::text                          
                        END AS state,
                        type   ,
                        'no' as auto_post   ,
                        --inalterable_hash  ,
                        --payment_reference  ,
                        --qr_code_method  ,
                        --payment_state  ,
                        --invoice_source_email  ,
                        --invoice_partner_display_name  ,
                        --invoice_origin  ,
                        COALESCE(date ,date_invoice) as date,
                        --auto_post_until ,
                        date_invoice as invoice_date ,
                        --invoice_date_due ,
                        --narration  ,
                        amount_untaxed ,
                        amount_tax ,
                        amount_total ,
                        --amount_residual ,
                        amount_untaxed_signed ,
                        amount_tax_signed ,
                        amount_total_signed ,
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
                        sale_contract_id ,
                        purchase_contract_id ,
                        contract_id ,
                        supplier_inv_date ,
                        account_analytic_id ,
                        ref_id  ,
                        origin  ,
                        transaction_id  ,
                        invoice_number  ,
                        status  ,
                        --base64_pdf  ,
                        ref_type  ,
                        org_ref_id  ,
                        org_invoice_number  ,
                        type_invoice  ,
                        --reference_description  ,
                        invoice_issue_date ,
                        org_invoice_issued_date,
                        trans_type
                        
            FROM public.dblink
                ('%s',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    
                    --sequence_number ,
                        journal_id  ,
                        company_id ,
                        --payment_id ,
                        --statement_line_id ,
                        --tax_cash_basis_rec_id ,
                        --tax_cash_basis_origin_move_id ,
                        --auto_post_origin_id ,
                        --secure_sequence_number ,
                        --invoice_payment_term_id ,
                        partner_id ,
                        commercial_partner_id ,
                        --partner_shipping_id ,
                        partner_bank_id ,
                        fiscal_position_id ,
                        currency_id  ,
                        --reversed_entry_id ,
                        --invoice_user_id ,
                        --invoice_incoterm_id ,
                        --invoice_cash_rounding_id ,
                        --sequence_prefix  ,
                        --access_token  ,
                        name  ,
                        reference,
                        --ref  ,
                        state   ,
                        type   ,
                        --auto_post   ,
                        --inalterable_hash  ,
                        --payment_reference  ,
                        --qr_code_method  ,
                        --payment_state  ,
                        --invoice_source_email  ,
                        --invoice_partner_display_name  ,
                        --invoice_origin  ,
                        date ,
                        --auto_post_until ,
                        date_invoice ,
                        --invoice_date_due ,
                        --narration  ,
                        amount_untaxed ,
                        amount_tax ,
                        amount_total ,
                        --amount_residual ,
                        amount_untaxed_signed ,
                        amount_tax_signed ,
                        amount_total_signed ,
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
                        sale_contract_id ,
                        purchase_contract_id ,
                        contract_id ,
                        supplier_inv_date ,
                        account_analytic_id ,
                        ref_id  ,
                        origin  ,
                        transaction_id  ,
                        invoice_number  ,
                        status  ,
                        --base64_pdf  ,
                        ref_type  ,
                        org_ref_id  ,
                        org_invoice_number  ,
                        type_invoice  ,
                        --reference_description  ,
                        invoice_issue_date ,
                        org_invoice_issued_date,
                        trans_type
                         
                    
                FROM public.account_invoice') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,
                                                    
                        --sequence_number integer,
                        journal_id integer ,
                        company_id integer,
                        --payment_id integer,
                        --statement_line_id integer,
                        --tax_cash_basis_rec_id integer,
                        --tax_cash_basis_origin_move_id integer,
                        --auto_post_origin_id integer,
                        --secure_sequence_number integer,
                        --invoice_payment_term_id integer,
                        partner_id integer,
                        commercial_partner_id integer,
                        --partner_shipping_id integer,
                        partner_bank_id integer,
                        fiscal_position_id integer,
                        currency_id integer ,
                        --reversed_entry_id integer,
                        --invoice_user_id integer,
                        --invoice_incoterm_id integer,
                        --invoice_cash_rounding_id integer,
                        --sequence_prefix character varying ,
                        --access_token character varying ,
                        name character varying ,
                        reference character varying,
                        --ref character varying ,
                        state character varying  ,
                        type character varying  ,
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
                        date_invoice date,
                        --invoice_date_due date,
                        --narration text ,
                        amount_untaxed numeric,
                        amount_tax numeric,
                        amount_total numeric,
                        --amount_residual numeric,
                        amount_untaxed_signed numeric,
                        amount_tax_signed numeric,
                        amount_total_signed numeric,
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
                        sale_contract_id integer,
                        purchase_contract_id integer,
                        contract_id integer,
                        supplier_inv_date date,
                        account_analytic_id integer,
                        ref_id character varying ,
                        origin character varying ,
                        transaction_id character varying ,
                        invoice_number character varying ,
                        status character varying ,
                        --base64_pdf character varying ,
                        ref_type character varying ,
                        org_ref_id character varying ,
                        org_invoice_number character varying ,
                        type_invoice character varying ,
                        --reference_description character varying ,
                        invoice_issue_date date,
                        org_invoice_issued_date date,
                        trans_type character varying
                        
                    )
            WHERE type in ('out_invoice','out_refund')
        ''' %(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_move_id_seq', (select max(id) + 1 from  account_move));
        ''')   
        return
   
    def create_move_line_for_draft(self):
        sql ='''
            SELECT *
                FROM public.dblink
                    ('%s',
                     'SELECT 
                        
                        ai.id invoice_id,
                        ail.name,
                        ail.product_id,
                        ail.account_id,
                        ail.price_unit,
                        ail.quantity,
                        ail.uom_id,
                        ai.type,
                        ai.state 
                        
                    FROM public.account_invoice ai
                        join account_invoice_line ail on ai.id = ail.invoice_id') 
                    AS DATA(
                            invoice_id integer,                            
                            name CHARACTER VARYING,
                            product_id integer,
                            account_id integer,
                            price_unit numeric,
                            quantity numeric,
                            product_uom_id integer,
                            type CHARACTER VARYING,
                            state CHARACTER VARYING
                        )
            WHERE state in ('draft','cancel')
                and type in ('out_invoice','out_refund')
        ''' %(self.server_db_link)
        self.env.cr.execute(sql)
        count = 0
        for i in self.env.cr.dictfetchall():
            count+= 1
            # print(count)
            self._prepare_invoice_line(i)
        return

    def sys_account_move_line_inv_sales(self):
        sql ='''
        INSERT INTO 
            account_move_line 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,     
               -- move_id  ,
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
                move_id,
                price_unit,
                price_subtotal
            )        
        
         SELECT 
            
            id,
            create_date,create_uid,
            write_date, write_uid,     
            --move_id  ,
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
                  WHEN aa_type in('receivable','payable') THEN 'payment_term'::text
                  WHEN aa_type in ('other') THEN 'product'::text                                            
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
            invoice_id as move_id,
            
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
                ai.type,
                aa.type aa_type,
                ai.id invoice_id
                    
            FROM public.account_move_line aml 
                 join account_move am on aml.move_id = am.id
                 join account_invoice ai on ai.move_id = am.id
                 join account_account aa on aml.account_id = aa.id') 
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
                    type  character varying,
                    aa_type character varying,
                    invoice_id integer
                )
                where type in ('out_invoice','out_refund')
                 
        ''' %(self.server_db_link)
        self.env.cr.execute(sql)
        
        self.env.cr.execute('''
            SELECT setval('account_move_line_id_seq', (select max(id) + 1 from  account_move_line));
        ''') 
        # for line in self.env.cr.dictfetchall():
        #     self._prepare_invoice_line(line)
        
        return
    
    def _prepare_invoice_line(self,  move_line):
        self.env['account.move.line'].create({ 
            'name': move_line['name'], 
                 #'origin': origin,
            'move_id': move_line['invoice_id'], 
            'product_id': move_line['product_id'],
            'account_id': move_line['account_id'], 
            'price_unit': move_line['price_unit'], 
            'quantity': move_line['quantity'],
            'product_uom_id':move_line['product_uom_id']
            })
    
    