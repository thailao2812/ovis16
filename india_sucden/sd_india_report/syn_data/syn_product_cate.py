from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re

DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    
    def sys_product_run(self):
        
        self.env.cr.execute('''
            DELETE FROM s_contract;
            DELETE FROM s_contract_line;
            DELETE FROM stock_valuation_layer;
            DELETE FROM mrp_bom;
            DELETE FROM kcs_criterions;
            DELETE FROM product_product;
            DELETE FROM product_template;
            DELETE FROM uom_uom;
            DELETE FROM uom_category;
        ''')
        
        self.sys_product_category()
        self.sys_uom_category()
        self.sys_uom_uom()
        self.sys_product_template()
        self.sys_product_product()
    
    def compute_category_acc(self):
        for i in self.env['product.category'].search([]):
            i.property_account_income_categ_id = 1707
        
    def sys_uom_uom(self):
        sql ='''
        INSERT INTO 
            uom_uom 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                category_id,
                uom_type,
                name,
                factor,
                rounding,
                active,
                sync_id
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date, write_uid, 
            category_id,
            uom_type,
            jsonb_build_object('en_US', name ) as name,
            factor,
            rounding,
            active,
            sync_id
            
            FROM public.dblink
                        ('sucdendblink',
                         'SELECT 
                            id, 
                            create_date, create_uid, 
                            write_date, write_uid, 
                            category_id,
                            uom_type,
                            name,
                            factor,
                            rounding,
                            active,
                            sync_id
                         
                        FROM public.product_uom') 
                        AS DATA(id INTEGER,
                                create_date timestamp without time zone,
                                create_uid integer,
                                write_date timestamp without time zone,
                                write_uid integer,                            
                                category_id integer,
                                uom_type CHARACTER VARYING ,
                                name CHARACTER VARYING ,
                                factor numeric,
                                rounding numeric,
                                active boolean ,
                                sync_id integer
                            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('uom_uom_id_seq', (select max(id) + 1 from  uom_uom));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
         
    def sys_uom_category(self):
        sql ='''
        INSERT INTO 
            uom_category 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name,
                sync_id
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date,  write_uid, 
            jsonb_build_object('en_US', name ) as name,
            sync_id
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    name,
                    sync_id
                FROM public.product_uom_categ') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name CHARACTER VARYING,
                        sync_id integer
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('uom_category_id_seq', (select max(id) + 1 from  uom_category));
        ''')   
        
        sql ='''
        INSERT INTO 
            pss_sent 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                s_contract_id ,
                t_contract_id ,
                x_sequence ,
                awb   ,
                ref_no   ,
                signed_by   ,
                x_type   ,
                courier   ,
                x_remark   ,
                date_sent ,
                aproved_date ,
                rejected_date ,
                delivered_date ,
                kgs  
            )        
        
        SELECT 
           *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    s_contract_id ,
                    t_contract_id ,
                    x_sequence ,
                    awb   ,
                    ref_no   ,
                    signed_by   ,
                    x_type   ,
                    courier   ,
                    x_remark   ,
                    date_sent ,
                    aproved_date ,
                    rejected_date ,
                    delivered_date ,
                    kgs  
                    
                FROM public.pss_sent') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        quality integer,
                        
                        s_contract_id integer,
                        t_contract_id integer,
                        x_sequence integer,
                        awb character varying COLLATE pg_catalog."default",
                        ref_no character varying COLLATE pg_catalog."default",
                        signed_by character varying COLLATE pg_catalog."default",
                        x_type character varying COLLATE pg_catalog."default",
                        courier character varying COLLATE pg_catalog."default",
                        x_remark character varying(256) COLLATE pg_catalog."default",
                        date_sent date,
                        aproved_date date,
                        rejected_date date,
                        delivered_date date,
                        kgs double precision
                    )
        '''
        
        return
    
    def sys_product_product(self):
        sql ='''
        INSERT INTO 
                    product_product (
                        id,
                        create_date,create_uid,
                        write_date, write_uid,                     
                        product_tmpl_id, 
                            default_code,                       
                            barcode,
                            active)
        
        SELECT 
            id, 
            create_date,  create_uid, 
            write_date, write_uid, 
            product_tmpl_id, 
            default_code,                       
            barcode,
            true as active
                    
        FROM public.dblink
            ('sucdendblink',
             'SELECT 
                id, 
                create_date,  create_uid, 
                write_date, write_uid, 
                product_tmpl_id, 
                default_code,                       
                barcode 
                                                            
             
            FROM public.product_product' ) 
            AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    product_tmpl_id integer,                            
                    default_code CHARACTER VARYING,
                    barcode CHARACTER VARYING                
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('product_product_id_seq', (select max(id) + 1 from  product_product));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_product_template(self):
        sql ='''
        INSERT INTO 
            product_template (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name,
                sequence,                       
                description,                                                
                description_purchase,                 
                description_sale,                  
                type,   
                detailed_type,                    
                categ_id,   
                list_price,
                sale_ok,
                purchase_ok,
                uom_id,
                uom_po_id,
                company_id,
                active,                     
                hide_report,
                tracking,
                sync_id,
                contract_commodity_vn,
                contract_quality_vn,
                contract_commodity_en,
                contract_quality_en
            )
                    
        SELECT 
                id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    jsonb_build_object('en_US', name ) as name, 
                    sequence,                       
                    jsonb_build_object('en_US', description ) as description,                                                 
                    jsonb_build_object('en_US', description_purchase ) as description_purchase, 
                    jsonb_build_object('en_US', description_sale ) as description_sale,                    
                    type,  
                    type as detailed_type,                       
                    categ_id,   
                    list_price,
                    sale_ok,
                    purchase_ok,
                    uom_id,
                    uom_po_id,
                    company_id,
                    active,                     
                    hide_report,
                    tracking,
                    sync_id,
                    contract_commodity_vn,
                    contract_quality_vn,
                    contract_commodity_en,
                    contract_quality_en
    
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date,  write_uid, 
                    name, 
                    sequence,                       
                    description,                                                
                    description_purchase,                 
                    description_sale,                  
                    type,                       
                    categ_id,   
                    list_price,
                    sale_ok,
                    purchase_ok,
                    uom_id,
                    uom_po_id,
                    company_id,
                    active,                     
                    hide_report,
                    tracking,
                    sync_id,
                    contract_commodity_vn,
                    contract_quality_vn,
                    contract_commodity_en,
                    contract_quality_en
                 
                FROM public.product_template') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name CHARACTER VARYING,                            
                        sequence integer,
                        description CHARACTER VARYING,                           
                        description_purchase CHARACTER VARYING,
                        description_sale CHARACTER VARYING, 
                        type CHARACTER VARYING,                       
                        categ_id integer,   
                        list_price numeric,
                        sale_ok boolean,
                        purchase_ok boolean,
                        uom_id integer,
                        uom_po_id integer,
                        company_id integer,
                        active boolean,    
                        hide_report boolean,
                        tracking CHARACTER VARYING,
                        sync_id integer,
                        contract_commodity_vn CHARACTER VARYING,
                        contract_quality_vn CHARACTER VARYING,
                        contract_commodity_en CHARACTER VARYING,
                        contract_quality_en CHARACTER VARYING
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('product_template_id_seq', (select max(id) + 1 from  product_template));
        ''')   
        
            
    def sys_product_category(self):
        sql ='''
        INSERT INTO 
            product_category (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name, 
                    code,                       
                    parent_id,                                                
                    removal_strategy_id ,
                    active,
                    sync_id )
             
            SELECT 
                id, 
                create_date,  create_uid, 
                write_date, write_uid, 
                name, 
                code,                       
                parent_id,                                                
                removal_strategy_id ,
                true as active,
                sync_id   
                    
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date,  create_uid, 
                    write_date, write_uid, 
                    name, 
                    code,                       
                    parent_id,                                                
                    removal_strategy_id ,
                    sync_id                    
                 
                FROM public.product_category' ) 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name CHARACTER VARYING,                            
                        code CHARACTER VARYING,
                        parent_id double precision,                           
                        removal_strategy_id integer ,
                        sync_id integer                                         
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('product_category_id_seq', (select max(id) + 1 from  product_category));
        ''')   
        
        for catg in self.env['product.category'].search([]):
            catg._compute_complete_name()
            


        
    