from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
# from pip._vendor.pygments.lexer import _inherit
DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    
    def sys_acc1(self):
        self.env.cr.execute('''
            DELETE FROM account_journal;
            DELETE FROM account_account;
            alter table account_payment alter move_id drop not null;
            DELETE FROM account_analytic_account;
            ALTER TABLE account_journal ALTER COLUMN code TYPE character varying;
        ''')
        self.sy_account_account()
        self.sy_account_analytic_account()
        self.sys_account_journal()
        
    
    def sys_acc2(self):
        self.env.cr.execute('''
            
            alter table account_payment disable trigger all;
            delete from account_payment;
            alter table account_payment enable trigger all;
            alter sequence account_payment_id_seq minvalue 0 start with 1;
            SELECT setval('account_payment_id_seq', 0);
            
            alter table account_move disable trigger all;
            delete from account_move;
            alter table account_move enable trigger all;
            alter sequence account_move_id_seq minvalue 0 start with 1;
            SELECT setval('account_move_id_seq', 0);
            
        ''')
        self.compute_account_journal()
        self.sys_compute_type_acc()
        self.sys_account_payment()
        self.sys_account_move()
        self.sys_account_move_relate_payment_allocation()
    
    def sys_acc3(self):
        self.env.cr.execute('''
            alter table account_move_line disable trigger all;
            delete from account_move_line;
            alter table account_move_line enable trigger all;
            alter sequence account_move_line_id_seq minvalue 0 start with 1;
            SELECT setval('account_move_line_id_seq', 0);
        ''')
        
        self.sys_account_move_line()
        self.sys_account_move_line_relate_payment_allocation()
        self.update_fields_acconut_payment()
    
    def sys_acc4(self):
        self.env.cr.execute('''
            alter table account_tax disable trigger all;
            delete from account_tax;
            alter table account_tax enable trigger all;
            
        ''')
        self.sys_account_tax()
    
    def sys_account_tax(self):
        sql ='''
        INSERT INTO 
            account_tax 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name,
                company_id  ,
                sequence  ,
                tax_group_id  ,
                --cash_basis_transition_account_id ,
                --country_id ,
                type_tax_use   ,
                --tax_scope  ,
                amount_type   ,
                description,
                --tax_exigibility  ,
                amount  ,
                active ,
                price_include ,
                include_base_amount ,
                --is_base_affected ,
                analytic ,
                --real_amount ,
                sync_id
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date,  write_uid, 
            jsonb_build_object('en_US', name ) as name,
            company_id  ,
            sequence  ,
            tax_group_id  ,
            --cash_basis_transition_account_id ,
            --country_id ,
            type_tax_use   ,
            --tax_scope  ,
            amount_type   ,
            jsonb_build_object('en_US', description ) as description,
             
            --tax_exigibility  ,
            amount  ,
            active ,
            price_include ,
            include_base_amount ,
            --is_base_affected ,
            analytic ,
            --real_amount ,
            sync_id
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    name ,
                    company_id  ,
                    sequence  ,
                    tax_group_id  ,
                    --cash_basis_transition_account_id ,
                    --country_id ,
                    type_tax_use   ,
                    --tax_scope  ,
                    amount_type   ,
                    description ,
                    --tax_exigibility  ,
                    amount  ,
                    active ,
                    price_include ,
                    include_base_amount ,
                    --is_base_affected ,
                    analytic ,
                    --real_amount ,
                    sync_id
                    
                FROM public.account_tax') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,   
                        
                        name  character varying ,
                        company_id integer ,
                        sequence integer ,
                        tax_group_id integer ,
                        --cash_basis_transition_account_id integer,
                        --country_id integer,
                        type_tax_use character varying  ,
                        --tax_scope character varying ,
                        amount_type character varying  ,
                        description character varying,
                        --tax_exigibility character varying ,
                        amount numeric,
                        active boolean,
                        price_include boolean,
                        include_base_amount boolean,
                        --is_base_affected boolean,
                        analytic boolean,
                        --real_amount double precision,
                        sync_id integer
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_tax_id_seq', (select max(id) + 1 from  account_tax));
        ''')   
        
        return
    
    def update_fields_acconut_payment(self):
        #move_id
        sql ='''
        UPDATE account_payment set move_id = foo.move_id
        FROM 
        (
            SELECT 
                id, move_id, payment_id
               
                FROM public.dblink
                    ('%s',
                     'SELECT 
                        id, 
                        move_id,
                        payment_id
                    FROM public.account_move_line') 
                    AS DATA(id INTEGER,                        
                            move_id integer,                        
                            payment_id integer
                        )
            )foo 
            where account_payment.id = foo.payment_id
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        # payment_method_line_id
        self.env.cr.execute('''
        update account_payment set payment_method_line_id = foo.account_payment_method_line_id
        FROM 
        (
            select apml.journal_id, apml.id account_payment_method_line_id , apm.id account_payment_method_id, apm.payment_type,
                am.id move_id, ap.id payment_id
            from account_payment_method_line apml 
            join account_payment_method apm on apml.payment_method_id = apm.id 
            join account_move am on am.journal_id = apml.journal_id
            join account_payment ap on am.id = ap.move_id and ap.payment_type = apm.payment_type
            order by am.id, apml.journal_id) foo
        WHERE account_payment.id = foo.payment_id
        ''')
        
    def compute_account_journal(self):
        for i in self.env['account.journal'].search([]):
            if not i.inbound_payment_method_line_ids:
                val ={
                    'payment_method_id': 1,
                    'name': 'Manual',
                    'journal_id': i.id
                    }
                self.env['account.payment.method.line'].create(val)
            
            if not i.outbound_payment_method_line_ids:
                val ={
                    'payment_method_id': 2,
                    'name': 'Manual',
                    'journal_id': i.id
                    }
                self.env['account.payment.method.line'].create(val)
    
    def sys_account_move_line(self):
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
                        --move_name ,
                        --parent_state ,
                        ref ,
                        name ,
                        --tax_audit ,
                        --matching_number ,
                        display_type  ,
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
                        blocked 
                        --discount_percentage 
            )        
        
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
                        coalesce(currency_id, 2)  as currency_id ,
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
                        --move_name ,
                        --parent_state ,
                        ref ,
                        name ,
                        --tax_audit ,
                        --matching_number ,
                        'product' as display_type  ,
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
                        blocked 
                        --discount_percentage 
                        
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date,  create_uid, 
                    write_date,   write_uid, 
                    
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
                        --move_name ,
                        --parent_state ,
                        ref ,
                        name ,
                        --tax_audit ,
                        --matching_number ,
                        --display_type  ,
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
                        blocked 
                        --discount_percentage 
                    
                    
                FROM public.account_move_line 
                 WHERE
                     move_id in (Select am.id 
                            FROM account_move_line aml join account_move am on aml.move_id = am.id
                            WHERE aml.payment_id is not null) ') 
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
                        blocked boolean
                        --discount_percentage double precision
                        )
                        where payment_id in (select id from account_payment)
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_move_line_id_seq', (select max(id) + 1 from  account_move_line));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    def sys_account_move_relate_payment_allocation(self):
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
                ('sucdendblink',
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
                            FROM account_move am join payment_allocation pa on pa.move_id = am.id)
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
        
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_move_id_seq', (select max(id) + 1 from  account_move));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    def sys_account_move_line_relate_payment_allocation(self):
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
                        --move_name ,
                        --parent_state ,
                        ref ,
                        name ,
                        --tax_audit ,
                        --matching_number ,
                        display_type  ,
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
                        blocked 
                        --discount_percentage 
            )        
        
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
                        coalesce(currency_id, 2)  as currency_id ,
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
                        --move_name ,
                        --parent_state ,
                        ref ,
                        name ,
                        --tax_audit ,
                        --matching_number ,
                        'product' as display_type  ,
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
                        blocked 
                        --discount_percentage 
                        
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date,  create_uid, 
                    write_date,   write_uid, 
                    
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
                        --move_name ,
                        --parent_state ,
                        ref ,
                        name ,
                        --tax_audit ,
                        --matching_number ,
                        --display_type  ,
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
                        blocked 
                        --discount_percentage 
                    
                    
                FROM public.account_move_line 
                 WHERE
                     move_id in (Select am.id 
                            FROM account_move am join payment_allocation pa on pa.move_id = am.id)
                            
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
                        blocked boolean
                        --discount_percentage double precision
                        )
                       
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_move_line_id_seq', (select max(id) + 1 from  account_move_line));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_account_move(self):
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
                ('sucdendblink',
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
                            FROM account_move_line aml join account_move am on aml.move_id = am.id
                            WHERE aml.payment_id is not null)
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
        
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_move_id_seq', (select max(id) + 1 from  account_move));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sy_account_analytic_account(self):
        sql ='''
        INSERT INTO 
            account_analytic_account 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                plan_id,
                company_id ,
                partner_id ,
                name   ,
                code  ,
                active ,
                sync_id
            )        
        
        SELECT 
           id, 
            create_date, create_uid, 
            write_date,  write_uid, 
            1 as plan_id  ,
            --root_plan_id ,
            company_id ,
            partner_id ,
          
            jsonb_build_object('en_US', name) as name ,
            code  ,
            active ,
            sync_id
                        
        FROM public.dblink
            ('sucdendblink',
             'SELECT 
                id, 
                create_date, create_uid, 
                write_date,  write_uid, 
                
                    --plan_id  ,
                    --root_plan_id ,
                    company_id ,
                    partner_id ,
                  
                    name   ,
                    code  ,
                    active ,
                    sync_id
                    
                    
            FROM public.account_analytic_account') 
            AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    --plan_id integer ,
                    --root_plan_id integer,
                    company_id integer,
                    partner_id integer,
                    name character varying ,
                    code character varying,
                    active boolean,
                    sync_id integer
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_analytic_account_id_seq', (select max(id) + 1 from  account_analytic_account));
        ''')   
        
        return
    def sys_account_payment_for_payment_allocation(self):
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
            ('sucdendblink',
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
            WHERE id in (select pay_id from account_payment) 
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
            ) 
        
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_payment_id_seq', (select max(id) + 1 from  account_payment));
        ''')   
        
        return
    
    def sys_account_payment(self):
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
            ('sucdendblink',
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
            WHERE request_payment_id is not null') 
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
            ) 
        
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_payment_id_seq', (select max(id) + 1 from  account_payment));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
         
    def sys_account_journal(self):
        sql ='''
        INSERT INTO 
            account_journal 
            (
                id, 
                create_date, create_uid, 
                write_date,  write_uid, 
                default_account_id ,                
                --suspense_account_id ,
                sequence ,
                currency_id ,
                company_id  ,
                profit_account_id ,
                loss_account_id ,
                bank_account_id ,
                --sale_activity_type_id ,
                --sale_activity_user_id ,
                --alias_id ,
                --secure_sequence_id ,
                --color ,
                name  ,
                code  ,
                type  ,
                invoice_reference_type  ,
                invoice_reference_model  ,
                bank_statements_source  ,
                --sequence_override_regex  ,
                --sale_activity_note  ,
                --active ,
                --restrict_mode_hash_table ,
                refund_sequence ,
                --payment_sequence ,
                show_on_dashboard ,
                active,
                sync_id,
                is_api
                --l10n_in_gstin_partner_id
            )        
        
        SELECT 
            id, 
                create_date, create_uid, 
                write_date, write_uid, 
                2192 as default_account_id ,                
                --suspense_account_id ,
                sequence ,
                currency_id ,
                company_id  ,
                profit_account_id ,
                loss_account_id ,
                bank_account_id ,
                --sale_activity_type_id ,
                --sale_activity_user_id ,
                --alias_id ,
                --secure_sequence_id ,
                --color ,
                jsonb_build_object('en_US', name) as name  ,
                code || 'xxx' || id as code ,
                type  ,
                'invoice' as invoice_reference_type  ,
                'odoo' as invoice_reference_model  ,
                bank_statements_source  ,
                --sequence_override_regex  ,
                --sale_activity_note  ,
                --active ,
                --restrict_mode_hash_table ,
                refund_sequence ,
                --payment_sequence ,
                show_on_dashboard,
                True as active,
                sync_id,
                is_api
                --l10n_in_gstin_partner_id
                
            FROM public.dblink
            ('sucdendblink',
             'SELECT 
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                 --default_account_id ,                
                --suspense_account_id ,
                sequence ,
                currency_id ,
                company_id  ,
                profit_account_id ,
                loss_account_id ,
                bank_account_id ,
                --sale_activity_type_id ,
                --sale_activity_user_id ,
                --alias_id ,
                --secure_sequence_id ,
                --color ,
                name  ,
                code  ,
                type  ,
                --invoice_reference_type  ,
                --invoice_reference_model  ,
                bank_statements_source  ,
                --sequence_override_regex  ,
                --sale_activity_note  ,
                --active ,
                --restrict_mode_hash_table ,
                refund_sequence ,
                --payment_sequence ,
                show_on_dashboard ,
                sync_id,
                is_api
                --l10n_in_gstin_partner_id
                
            FROM public.account_journal') 
            AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,
                    --default_account_id integer,
                    
                    --suspense_account_id integer,
                    sequence integer,
                    currency_id integer,
                    company_id integer ,
                    profit_account_id integer,
                    loss_account_id integer,
                    bank_account_id integer,
                    --sale_activity_type_id integer,
                    --sale_activity_user_id integer,
                    --alias_id integer,
                    --secure_sequence_id integer,
                    --color integer,
                    name character varying ,
                    code character varying(5) ,
                    type character varying ,
                    --invoice_reference_type character varying ,
                    --invoice_reference_model character varying ,
                    bank_statements_source character varying ,
                    --sequence_override_regex text ,
                    --sale_activity_note text ,
                    --active boolean,
                    --restrict_mode_hash_table boolean,
                    refund_sequence boolean,
                    --payment_sequence boolean,
                    show_on_dashboard boolean,
                    sync_id integer,
                    is_api boolean
                    --l10n_in_gstin_partner_id integer
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_journal_id_seq', (select max(id) + 1 from  account_journal));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sy_account_account(self):
        sql ='''
        INSERT INTO 
            account_account 
            (
                id, 
                create_date, create_uid, 
                write_date,  write_uid, 
                
                currency_id ,
                company_id  ,
                --group_id ,
                --root_id ,
                name,
                code  ,
                account_type   ,
                --internal_group  ,
                note  ,
                deprecated ,
                --include_initial_balance ,
                reconcile ,
                sync_id
                --is_off_balance ,
                --non_trade 
            )        
        
        SELECT 
            id, 
            create_date, create_uid, 
            write_date,  write_uid, 
            
            currency_id ,
            company_id  ,
            --group_id ,
            --root_id ,
            jsonb_build_object('en_US', name) as name  ,
            code  ,
            'asset_receivable' as account_type   ,
            --internal_group  ,
            note  ,
            deprecated ,
            --include_initial_balance ,
            reconcile ,
            sync_id
            --is_off_balance ,
            --non_trade 
            
            FROM public.dblink
                        ('sucdendblink',
                         'SELECT 
                            id, 
                            create_date, create_uid, 
                            write_date,  write_uid, 
                            
                            currency_id ,
                            company_id  ,
                            --group_id ,
                            --root_id ,
                            name   ,
                            code  ,
                            --account_type   ,
                            --internal_group  ,
                            note  ,
                            deprecated ,
                            --include_initial_balance ,
                            reconcile ,
                            sync_id
                            --is_off_balance ,
                            --non_trade 
                                
                        FROM public.account_account') 
                        AS DATA(id INTEGER,
                                create_date timestamp without time zone,
                                create_uid integer,
                                write_date timestamp without time zone,
                                write_uid integer,                            
                                currency_id integer,
                                company_id integer ,
                                --group_id integer,
                                --root_id integer,
                                name character varying  ,
                                code character varying(64)  ,
                                --account_type character varying  ,
                                --internal_group character varying ,
                                note text ,
                                deprecated boolean,
                                --include_initial_balance boolean,
                                reconcile boolean,
                                sync_id integer
                                --is_off_balance boolean,
                                --non_trade boolean
                            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_account_id_seq', (select max(id) + 1 from  account_account));
        ''')   
        
        return
    
   
    # def sy_account_account(self):
        


        
    