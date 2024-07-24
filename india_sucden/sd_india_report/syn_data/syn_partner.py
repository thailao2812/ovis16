from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re

DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    
    def sys_partner_run(self):
        self.env.cr.execute('''
            delete from audit_log;
            delete from mail_tracking_value;
            delete from res_partner_bank;
            delete from ned_security_gate_queue;
            delete from res_bank;
            
            alter table account_tax alter country_id drop not null;
            
            update account_tax set country_id = null;
            update res_partner set state_id = null, country_id = null;
            delete from res_country_state;
            delete from res_district;
            delete from res_country;
        ''')
        
        
        self.sys_res_country()
        self.sys_res_country_state()
        self.sys_res_district()
        
        self.sys_res_partner()
        self.sys_res_users()
        self.sys_res_company_users_rel()
        
        self.sys_res_bank()
        self.sys_res_partner_bank()
    
    def compute_payable_receive(self):
        for i in self.env['res.partner'].search([]):
            i.property_account_payable_id = 1622
            i.property_account_receivable_id = 1514
            i.property_vendor_advance_acc_id = 1623
            i.property_customer_advance_acc_id = 1512
    
    def sys_res_company_users_rel(self):
        sql ='''
            INSERT INTO 
                res_company_users_rel 
                (
                    cid  ,           
                    user_id
                )        
            
            SELECT 
                *
                FROM public.dblink
                    ('sucdendblink',
                     'SELECT 
                        cid,
                        user_id
                     
                    FROM public.res_company_users_rel') 
                    AS DATA(
                            cid integer,
                            user_id integer                            
                        )
                where user_id not in (1,2,3,4,5)
        '''
        self.env.cr.execute(sql)
        
    def sys_res_users(self):
        sql ='''
        INSERT INTO 
            res_users 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                company_id  ,
                partner_id  ,
                active  ,
                login   ,
                password  ,
                action_id ,
                signature  ,
                share ,
                notification_type
            )        
        
        SELECT 
            id, 
            create_date, create_uid, 
            write_date, write_uid, 
            company_id  ,
            partner_id  ,
            active  ,
            login   ,
            password  ,
            action_id ,
            signature  ,
            share ,
             
            --totp_secret  ,
            'email' as  notification_type   
            --odoobot_state  ,
            --odoobot_failed ,
            --warehouses_dom  ,
            --warehouses_allow_dom  ,
            --working_all_warehouse ,
            --follow_all_warehouse 
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    company_id  ,
                    partner_id  ,
                    active  ,
                    login   ,
                    password  ,
                    action_id ,
                    signature  ,
                    share 
                     
                    --totp_secret  ,
                    --notification_type   ,
                    --odoobot_state  ,
                    --odoobot_failed ,
                    --warehouses_dom  ,
                    --warehouses_allow_dom  ,
                    --working_all_warehouse ,
                    --follow_all_warehouse 
                    
                FROM public.res_users') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,  
                                                  
                        company_id integer ,
                        partner_id integer ,
                        active boolean ,
                        login character varying  ,
                        password character varying ,
                        action_id integer,
                        signature text ,
                        share boolean
                        
                        --totp_secret character varying ,
                        --notification_type character varying  ,
                        --odoobot_state character varying ,
                        --odoobot_failed boolean,
                        --warehouses_dom character varying ,
                        --warehouses_allow_dom character varying ,
                       -- working_all_warehouse boolean,
                        --follow_all_warehouse boolean
                    )
                where id not in (1,2,3,4,5)
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('res_users_id_seq', (select max(id) + 1 from  res_users));
        ''')   
    
    def sys_res_bank(self):
        sql ='''
        INSERT INTO 
            res_bank 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                state ,
                country ,
                name  ,
                street  ,
                street2  ,
                zip  ,
                city  ,
                email  ,
                phone  ,
                bic  ,
                active ,
                sync_id
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date,  create_uid, 
                    write_date, write_uid, 
                    state ,
                    country ,
                    name  ,
                    street  ,
                    street2  ,
                    zip  ,
                    city  ,
                    email  ,
                    phone  ,
                    bic  ,
                    active ,
                    sync_id
                 
                FROM public.res_bank') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    state integer,
                    country integer,
                    name character varying ,
                    street character varying ,
                    street2 character varying ,
                    zip character varying ,
                    city character varying ,
                    email character varying ,
                    phone character varying ,
                    bic character varying ,
                    active boolean,
                    sync_id integer
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('res_bank_id_seq', (select max(id) + 1 from  res_bank));
        ''')   
        
        return
    
    def sys_res_partner_bank(self):
        sql ='''
        INSERT INTO 
            res_partner_bank 
            (
                id, 
                create_date,  create_uid, 
                write_date,  write_uid, 
                partner_id  ,
                bank_id ,
                sequence ,
                currency_id ,
                company_id ,
                acc_number   ,
                sanitized_acc_number  ,
                --acc_holder_name  ,
                active ,
                sync_id
                --allow_out_payment 
            )        
        
        SELECT 
            id, 
                create_date, create_uid, 
                write_date, write_uid, 
                COALESCE(partner_id, 1) as partner_id,  
                bank_id ,
                sequence ,
                currency_id ,
                company_id ,
                acc_number   ,
                sanitized_acc_number  ,
                --acc_holder_name  ,
                active ,
                sync_id
                --allow_out_payment 
            FROM public.dblink
            ('sucdendblink',
             'SELECT 
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                partner_id  ,
                bank_id ,
                sequence ,
                currency_id ,
                company_id ,
                acc_number   ,
                sanitized_acc_number  ,
                --acc_holder_name  ,
                active ,
                sync_id
                --allow_out_payment 
             
            FROM public.res_partner_bank') 
            AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    partner_id integer ,
                    bank_id integer,
                    sequence integer,
                    currency_id integer,
                    company_id integer,
                    acc_number character varying  ,
                    sanitized_acc_number character varying ,
                    --acc_holder_name character varying ,
                    active boolean,
                    sync_id integer
                    --allow_out_payment boolean
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('res_partner_bank_id_seq', (select max(id) + 1 from  res_partner_bank));
        ''')   
        
        return
        
    def sys_res_partner(self):
        sql ='''
        INSERT INTO res_partner 
        (
            id,
            create_date,create_uid,
            write_date, write_uid,    
            name,
            parent_id ,
            user_id ,
            state_id ,
            country_id ,
            
            color ,
            commercial_partner_id ,                                
            display_name   ,
            ref   ,
            lang   ,                                
            vat   ,
            --company_registry   ,
            website   ,
            function  ,
            type   ,
            street   ,
            street2  ,
            zip   ,
            city   ,
            email   ,
            phone   ,
            mobile   ,
            --commercial_company_name   ,
            --company_name   ,
            date ,
            comment  ,
            --partner_latitude ,
            --partner_longitude ,
            active ,
            employee ,
            is_company ,
            --partner_share ,    
            supplier_rank,
            customer_rank ,                                
            district_id ,
            --position_en   ,
            type_ned   ,
            repperson1   ,
            repperson2   ,
            goods   ,
            partner_code   ,
            fax   ,
            transfer ,
            is_customer_coffee ,
            is_supplier_coffee ,
            ppkg  ,
            estimated_annual_volume  ,
            purchase_undelivered_limit  ,
            property_evaluation  ,
            m2mlimit  ,            
            shortname ,
            sync_id      
        )        

        SELECT 
            id, 
            create_date,1 as create_uid, 
            write_date,1 as write_uid, 
            name,
            parent_id ,
            user_id ,
            state_id ,
            --CASE WHEN country_id = 105 THEN 104 ELSE country_id END as country_id,
            country_id,
            color ,
            commercial_partner_id ,                                
            display_name   ,
            ref   ,
            lang   ,                                
            vat   ,
            --company_registry   ,
            website   ,
            function  ,
            type   ,
            street   ,
            street2  ,
            zip   ,
            city   ,
            email   ,
            phone   ,
            mobile   ,
            --commercial_company_name   ,
            --company_name   ,
            date ,
            comment  ,
            --partner_latitude ,
            --partner_longitude ,
            active ,
            employee ,
            is_company ,
            --partner_share ,    
             
            CASE WHEN supplier = True
                THEN 1 ELSE 0 END as supplier_rank,
            CASE WHEN customer = True
                THEN 1 ELSE 0 END as customer_rank,
                    district_id ,
                    --position_en   ,
                    type_ned   ,
                    repperson1   ,
                    repperson2   ,
                    goods   ,
                    partner_code   ,
                    fax   ,
                    transfer ,
                    is_customer_coffee ,
                    is_supplier_coffee ,
                    ppkg  ,
                    estimated_annual_volume  ,
                    purchase_undelivered_limit  ,
                    property_evaluation  ,
                    m2mlimit  ,            
                    shortname ,
                    sync_id  
            
                FROM public.dblink
                    ('sucdendblink',
                     'SELECT 
                        id, 
                        create_date, create_uid, 
                        write_date, write_uid, 
                        name,
                        parent_id ,
                        user_id ,
                        state_id ,
                        country_id ,
                        
                        color ,
                        commercial_partner_id ,                                
                        display_name   ,
                        ref   ,
                        lang   ,                                
                        vat   ,
                        --company_registry   ,
                        website   ,
                        function  ,
                        type   ,
                        street   ,
                        street2  ,
                        zip   ,
                        city   ,
                        email   ,
                        phone   ,
                        mobile   ,
                        --commercial_company_name   ,
                        --company_name   ,
                        date ,
                        comment  ,
                        --partner_latitude ,
                        --partner_longitude ,
                        active ,
                        employee ,
                        is_company ,
                        --partner_share ,    
                         
                        CASE WHEN supplier = True
                            THEN 1 ELSE 0 END as supplier_rank,
                        CASE WHEN customer = True
                            THEN 1 ELSE 0 END as customer_rank,
                        district_id ,
                        --position_en   ,
                        type_ned   ,
                        repperson1   ,
                        repperson2   ,
                        goods   ,
                        partner_code   ,
                        fax   ,
                        transfer ,
                        is_customer_coffee ,
                        is_supplier_coffee ,
                        ppkg  ,
                        estimated_annual_volume  ,
                        purchase_undelivered_limit  ,
                        property_evaluation  ,
                        m2mlimit  ,            
                        shortname,
                        sync_id                                       
                         
                        FROM public.res_partner where id not in (select partner_id from res_users where id in (1,2,3,4,5)) and id != 1
                        
                        ') 
                        AS DATA(id INTEGER,
                            create_date timestamp without time zone,
                            create_uid integer,
                            write_date timestamp without time zone,
                            write_uid integer, 
                            name character varying,
                            --title integer,
                            parent_id integer,
                            user_id integer,
                            state_id integer,
                            country_id integer,
                            --industry_id integer,
                            color integer,
                            commercial_partner_id integer,                                
                            display_name character varying ,
                            ref character varying ,
                            lang character varying ,                                
                            vat character varying ,
                            --company_registry character varying ,
                            website character varying ,
                            function character varying,
                            type character varying ,
                            street character varying ,
                            street2 character varying,
                            zip character varying ,
                            city character varying ,
                            email character varying ,
                            phone character varying ,
                            mobile character varying ,
                            --commercial_company_name character varying ,
                            --company_name character varying ,
                            date date,
                            comment text ,
                            --partner_latitude numeric,
                            --partner_longitude numeric,
                            active boolean,
                            employee boolean,
                            is_company boolean,
                            --partner_share boolean,    
                            supplier boolean,
                            customer boolean,                                
                            district_id integer,
                            --position_en character  ,
                            type_ned character varying ,
                            repperson1 character varying ,
                            repperson2 character varying ,
                            goods character varying ,
                            partner_code character varying ,
                            fax character varying ,
                            transfer boolean,
                            is_customer_coffee boolean,
                            is_supplier_coffee boolean,
                            ppkg double precision,
                            estimated_annual_volume double precision,
                            purchase_undelivered_limit double precision,
                            property_evaluation double precision,
                            m2mlimit double precision,    
                            shortname character varying    ,
                            sync_id   integer               
                        )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('res_partner_id_seq', (select max(id) + 1 from  res_partner));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
         
    def sys_res_country(self):
        sql ='''
            INSERT INTO 
                    res_country (
                        id,
                        create_date,create_uid,
                        write_date, write_uid,                     
                        
                        phone_code ,                   
                        code ,
                        name,
                        sync_id
                        )
       
            SELECT  id, 
                        create_date, 1 as create_uid, 
                        write_date, 1 as write_uid, 
                        phone_code ,                   
                        code  ,
                        jsonb_build_object('en_US', name ) as name,
                        sync_id
                        
                FROM public.dblink
                    ('sucdendblink',
                     'SELECT 
                        id, 
                        create_date, create_uid, 
                        write_date, write_uid, 
                        
                        phone_code ,                   
                        code  ,
                        name ,
                        sync_id                      
                     
                    FROM public.res_country' ) 
                    AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,   
                        phone_code integer,                   
                        code character varying,
                        name character varying,
                        sync_id integer)
                        --where id !=104 and code not in('IN')
        
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('res_country_id_seq', (select max(id) + 1 from  res_country));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_res_country_state(self):
        sql ='''
            INSERT INTO 
                res_country_state (
                    id,
                    create_date, create_uid,
                    write_date, write_uid, 
                    country_id ,
                    code ,name,
                    sync_id)
       
            SELECT  *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, 1 as  write_uid, 
                    country_id ,
                    code  ,
                    name ,
                    sync_id 
                 
                FROM public.res_country_state') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,   
                    country_id integer,
                    code character varying,
                    name character varying,
                    sync_id integer
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('res_country_state_id_seq', (select max(id) + 1 from  res_country_state));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_res_district(self):
        sql ='''
            INSERT INTO 
                res_district (
                    id,
                    create_date,create_uid,
                    write_date, write_uid, 
                    state_id ,
                    name ,
                    active,
                    sync_id)
            SELECT  *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, 1 as write_uid, 
                    state_id ,
                    name   ,
                    active  ,
                    sync_id
                 
                FROM public.res_district') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,   
                    state_id integer,
                    name character varying,
                    active boolean,
                    sync_id integer
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('res_district_id_seq', (select max(id) + 1 from  res_district));
        ''')   
        
        return
    
   
            


        
    