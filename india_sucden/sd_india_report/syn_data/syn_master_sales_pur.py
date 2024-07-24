from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re

DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    
    def sys_masterdata_sales_purchase_run(self):
        self.env.cr.execute('''
            delete from shipping_line; ;
            delete from delivery_place;
            DELETE FROM market_price;
            DELETE FROM packing_terms;
            DELETE FROM ned_fumigation;
            DELETE FROM packing_terms;
            DELETE FROM ned_crop;
            DELETE FROM ned_certificate;
            DELETE FROM ned_packing;
        ''')
        
        self.sys_shipping_line()
        self.sys_delivery()
        self.sys_market_price()
        self.sys_packing_terms()
        self.sys_ned_fumigation()
        self.sys_ned_crop()
        self.sys_ned_certificate()
        self.sys_ned_packing()
        
    def sys_shipping_line(self):
        sql ='''
            INSERT INTO 
            shipping_line (
                id,
                create_date,create_uid,
                write_date, write_uid, 
                name, active)
             
            SELECT *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                     id, 
                     create_date, create_uid, 
                     write_date,  write_uid, 
                     name, active
                 
                FROM public.shipping_line') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name CHARACTER VARYING,
                        active boolean
                       );
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('shipping_line_id_seq', (select max(id) + 1 from  shipping_line));
        ''')
        
    def sys_delivery(self):
        sql ='''
        INSERT INTO 
            delivery_place (
                id,
                create_date,create_uid,
                write_date, write_uid, 
                name, description, type,
                partner_id, transit_cost, 
                currency_id, active, 
                phone, fax,
                address, recipient)
             
            SELECT *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    name, description, type,
                    partner_id, transit_cost,
                    currency_id, active,
                    phone, fax, address, recipient
                 
                FROM public.delivery_place') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,
                        name CHARACTER VARYING,
                        description CHARACTER VARYING,
                        type character varying,
                        partner_id integer,
                        transit_cost double precision,
                        currency_id integer,
                        active boolean,
                        phone CHARACTER VARYING,
                        fax CHARACTER VARYING,
                        address CHARACTER VARYING,
                        recipient CHARACTER VARYING);
        '''
        self.env.cr.execute(sql)
        
        self.env.cr.execute('''
            SELECT setval('delivery_place_id_seq', (select max(id) + 1 from  delivery_place));
        ''')
            
    def sys_market_price(self):
        sql ='''
        INSERT INTO 
            market_price (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                mdate , interbankrate , price,
                bankceiling ,note , bank_floor ,eximbank, 
                techcombank , acb_or_vietinbank, commercialrate ,
                exporter_faq_price , 
                privateDealer_faq_price ,
                liffe_month ,liffe , g2difflocal ,
                g2difffob , g2_replacement ,
                faq_price ,fob_price ,
                grade_price )
             
            SELECT *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid,  mdate , 
                    interbankrate ,price, bankceiling ,
                    note ,bank_floor , eximbank, 
                    techcombank , acb_or_vietinbank , commercialrate ,
                    exporter_faq_price , privateDealer_faq_price ,
                    liffe_month , liffe , g2difflocal ,
                    g2difffob , g2_replacement , faq_price ,
                    fob_price , grade_price 
                     
                 
                FROM public.market_price' ) 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                         mdate date,  
                    interbankrate double precision,
                    price double precision,
                    bankceiling double precision,
                    note  CHARACTER VARYING,
                    bank_floor double precision,
                    eximbank double precision,
                    techcombank double precision,
                    acb_or_vietinbank double precision,
                    commercialrate  double precision,
                    exporter_faq_price double precision,
                    privateDealer_faq_price double precision,
                    liffe_month CHARACTER VARYING,
                    liffe CHARACTER VARYING,
                    g2difflocal double precision,
                    g2difffob double precision,
                    g2_replacement double precision,
                    faq_price double precision,
                    fob_price double precision,
                    grade_price double precision)
        '''
        self.env.cr.execute(sql)
        
        self.env.cr.execute('''
            SELECT setval('market_price_id_seq', (select max(id) + 1 from market_price));
        ''')     

    def sys_packing_terms(self):
        sql ='''
        delete from packing_terms; 
        INSERT INTO 
            packing_terms (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name, vietnamese, english )
             
            SELECT *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                     id, 
                     create_date, create_uid, 
                     write_date, write_uid, 
                    name, vietnamese, english
                FROM public.packing_terms' ) 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name CHARACTER VARYING,  
                        vietnamese CHARACTER VARYING,
                        english CHARACTER VARYING
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('packing_terms_id_seq', (select max(id) + 1 from packing_terms));
        ''')
    
    def sys_ned_fumigation(self):
        sql ='''
        INSERT INTO 
            ned_fumigation (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name)
             
            SELECT *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                     id, 
                     create_date, create_uid, 
                     write_date, write_uid, 
                    name
                FROM public.ned_fumigation' ) 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name CHARACTER VARYING
                        
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('ned_fumigation_id_seq', (select max(id) + 1 from ned_fumigation));
        ''')
        
    def sys_ned_crop(self):
        sql ='''
        delete from ned_crop; 
        INSERT INTO 
            ned_crop (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name, 
                short_name,
                start_date,
                to_date,
                description,
                state    )
             
            SELECT *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                     id, 
                     create_date, create_uid, 
                     write_date, write_uid, 
                    name, 
                     short_name,
                 start_date,
                 to_date,
                 description,
                 state                 
                 
                FROM public.ned_crop' ) 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name CHARACTER VARYING,
                        short_name CHARACTER VARYING,
                        start_date date, 
                        to_date date , 
                        description CHARACTER VARYING,
                        state CHARACTER VARYING
                    );
        '''
        self.env.cr.execute(sql)
        
        self.env.cr.execute('''
            SELECT setval('ned_crop_id_seq', (select max(id) + 1 from  ned_crop));
        ''')
    
    
    def sys_ned_certificate(self):
        sql ='''
        DELETE FROM ned_certificate;
        INSERT INTO 
            ned_certificate (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name, 
                code,
                premium,
                currency_id,
                description,
                active,
                name_print,
                combine)
             
            SELECT *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    name, 
                    code,
                    premium,
                    currency_id, -- USD = id = 2
                    description,
                    active,
                    name_print,
                    combine     
                                    
                FROM public.ned_certificate' ) 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name CHARACTER VARYING,
                        code CHARACTER VARYING,
                        premium double precision,
                        currency_id integer, 
                        description CHARACTER VARYING, 
                        active Boolean,
                        name_print CHARACTER VARYING,
                        combine Boolean
                    )
        '''
        self.env.cr.execute(sql)
        
        self.env.cr.execute('''
            SELECT setval('ned_certificate_id_seq', (select max(id) + 1 from  ned_certificate));
        ''')   
    
    def sys_ned_packing(self):
        sql ='''
        INSERT INTO 
            ned_packing (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                
                name ,
        vn_description ,
        en_description ,
        capacity,
        tare_weight,
        price ,
        "Premium" ,
        active 
            )
            SELECT *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                     id, 
                     create_date, create_uid, 
                     write_date, write_uid, 
                    name, 
                     vn_description ,
        en_description ,
        capacity,
        tare_weight,
        price ,
        "Premium" ,
        active                      
                FROM public.ned_packing' ) 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name CHARACTER VARYING,
                        vn_description CHARACTER VARYING,
                        en_description CHARACTER VARYING,
                        capacity double precision, 
                        tare_weight double precision, 
                        price double precision,
                        "Premium"  numeric,
                        active Boolean
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('ned_packing_id_seq', (select max(id) + 1 from  ned_packing));
        ''')  
            


        
    