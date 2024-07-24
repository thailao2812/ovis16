from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
# from pip._vendor.pygments.lexer import _inherit
DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    
    def sys_currency_run_step(self):
        self.update_res_users_currency()
        self.env.cr.execute('''
            
            delete from audit_log;
            delete from mail_tracking_value;
            delete from res_partner_bank;
            delete from ned_security_gate_queue;
            delete from res_bank;
            
            
            delete from lot_stack_allocation;
            delete from delivery_order;
            delete from delivery_order_line;
            delete from s_contract;
            delete from s_contract_line;
            delete from mail_tracking_value;
            
            delete from shipping_instruction;
            delete from shipping_instruction_line;
            
            delete from daily_confirmation;
            delete from daily_confirmation_line;
            delete from sale_contract;
            delete from sale_contract_line;
            
            delete from post_shipment;
            delete from post_shipment_line;
            
            delete from purchase_contract;
            delete from purchase_contract_line;
            delete from stock_allocation;
            delete from npe_nvp_relation;
            delete from payment_allocation;
            
            delete from request_payment;
            delete from interest_rate;
            
            delete from account_move;
            delete from account_move_line;
            delete from account_payment;
            delete from stock_picking;
            delete from stock_move;
            delete from stock_move_line;
            delete from stock_quant;
            delete from request_kcs_line;
            
            delete from kcs_sample;
            delete from lot_kcs;
            delete from lot_stack_allocation;
            
            delete from pss_management;
            delete from fob_pss_management;
            delete from restack_management;
            delete from kcs_glyphosate;
            
            delete from stock_lot;
            delete from request_materials;
            delete from request_materials_line;
            delete from mrp_production;
            
            delete from res_currency_rate;
            
            delete from mrp_operation_result;
            
            delete from mrp_operation_result_produced_product;
            delete from wizard_import_production_result;
            
            delete from ned_certificate_license;
            delete from ned_certificate;
            
            delete from product_pricelist;
            alter table res_currency disable trigger all;
            delete from res_currency;
            delete from ned_security_gate_queue;
            
            delete from res_company_users_rel where user_id not in (1,2,3,4,5);
            
           --alter table res_partner disable trigger all;
            delete from res_partner where id not in (select  partner_id from res_users  ) and  id != 1;
            --alter table res_partner enable trigger all;
            
            
           -- alter table res_users disable trigger all;
            delete from res_users where id not in (1,2,3,4,5);
          --  alter table res_users enable trigger all;
            
        ''')
        self.env.cr.commit()
        
        self.env.cr.execute('''
            
           --alter table res_partner disable trigger all;
            delete from res_partner where id not in (select  partner_id from res_users where id in (1,2,3,4,5)   ) and  id != 1;
            --alter table res_partner enable trigger all;
            
           -- alter table res_users disable trigger all;
           -- delete from res_users where id not in (1,2,3,4,5);
          --  alter table res_users enable trigger all;
            
        ''')
        
        self.sys_res_currency()
        self.sys_update_res_company_currency()
        
        self.env.cr.execute('''
            alter table res_currency enable trigger all;
        ''')
    
        return
    
    def sys_res_currency_rate(self):
        sql ='''
        INSERT INTO 
            res_currency_rate 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                currency_id ,
                company_id ,
                name  ,
                rate 
            )        
       
        SELECT 
           *
            FROM public.dblink
                ('%s',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    currency_id ,
                    company_id ,
                    name  ,
                    rate 
                    
                FROM public.res_currency_rate') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        currency_id integer,
                        company_id integer,
                        name date ,
                        rate numeric
                    )
                    where id !=455
                        and rate >0
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('res_currency_rate_id_seq', (select max(id) + 1 from  res_currency_rate));
        ''')   
        
        return
    
    def update_res_users_currency(self):
        for users in self.env['res.users'].search([('currency_id','=',2)]):
            users.currency_id = 1
            
    def sys_res_currency(self):
        sql ='''
        INSERT INTO 
            res_currency 
            (
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                name   ,
                symbol   ,
                --decimal_places ,
                --full_name   ,
                "position"   ,
                --currency_unit_label  ,
                --currency_subunit_label  ,
                rounding ,
                active,
                sync_id ,
                currency_type
            )        
        
        SELECT 
            id, 
            create_date, create_uid, 
            write_date, write_uid, 
            name   ,
            COALESCE(symbol,' ') as symbol   ,
            --decimal_places ,
            --full_name   ,
            "position"   ,
            --currency_unit_label  ,
            --currency_subunit_label  ,
            rounding ,
            active ,
            sync_id,
            currency_type
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    name ,
                    symbol   ,
                    --decimal_places ,
                    --full_name ,
                    "position"   ,
                    --currency_unit_label  ,
                    --currency_subunit_label  ,
                    rounding ,
                    active ,
                    sync_id,
                    currency_type
                    
                FROM public.res_currency') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name character varying ,
                        symbol character varying ,
                        --decimal_places integer,
                       
                        --full_name character varying ,
                        "position" character varying ,
                        --currency_unit_label character varying ,
                        --currency_subunit_label character varying ,
                        rounding numeric,
                        active boolean,
                        sync_id integer,
                        currency_type character varying
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('res_currency_id_seq', (select max(id) + 1 from  res_currency));
        ''')   
        return
    
    def sys_update_res_company_currency(self):
        sql ='''
        Update res_company set currency_id = foo.currency_id, second_currency_id = foo.second_currency_id
            from (
                SELECT 
                    id, 
                    currency_id,
                    second_currency_id
                              
                    FROM public.dblink
                        ('sucdendblink',
                         'SELECT 
                            id, 
                            currency_id,
                            second_currency_id
                            
                        FROM public.res_company
                         where id = 1') 
                        AS DATA(id INTEGER,
                                currency_id INTEGER,
                                second_currency_id INTEGER
                            )) foo
                 where res_company.id =foo.id
        '''
        self.env.cr.execute(sql)
        return
    
    
        
        
        

        
    