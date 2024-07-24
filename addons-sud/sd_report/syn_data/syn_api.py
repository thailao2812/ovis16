from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
# from pip._vendor.pygments.lexer import _inherit
DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    
    
    def sys_api_v14(self):
        self.env.cr.execute('''
            alter table api_synchronize_data_config_line alter fields_id drop not null;
            
            DELETE FROM api_synchronize_data_config;
            DELETE FROM api_synchronize_data_config_line;
            DELETE FROM api_synchronize_data;
            DELETE FROM api_synchronize_data_line;
        
        
        ''')
        
        self.sys_api_synchronize_data_config()
        self.sys_api_synchronize_data_config_line()
        self.compute_fields()
        self.sys_api_synchronize_data()
        self.sys_api_synchronize_data_line()
        
    
    def sys_api_synchronize_data_line(self):
        sql ='''
        INSERT INTO 
            api_synchronize_data_line 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                synchronize_id ,
                slc_method,
                state  ,
                payload  ,
                result  
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    synchronize_id ,
                    slc_method,
                    state   ,
                    payload  ,
                    result  
                    
                FROM public.api_synchronize_data_line') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        synchronize_id integer,
                        slc_method character varying ,
                        state character varying ,
                        payload text ,
                        result text 
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('api_synchronize_data_line_id_seq', (select max(id) + 1 from  api_synchronize_data_line));
        ''')   
        
        return
    
    
    def compute_fields(self):
        obj = self.env['api.synchronize.data.config'].search([])
        for i in obj:
            model = self.env['ir.model'].search([('model','=',i.model)])
            for line in i.line_ids:
                irs = self.env['ir.model.fields'].search([('model_id','=',model.id),('name','=',line.fields_sys)])
                line.fields_id = irs and irs.id or False
    
    def sys_api_synchronize_data_config(self):
        sql ='''
        INSERT INTO 
            api_synchronize_data_config 
            (
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                model    ,
                new_model    ,
                state   ,
                is_change 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    model    ,
                    new_model    ,
                    state   ,
                    is_change 
                    
                FROM public.api_synchronize_data_config') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        model character varying  ,
                        new_model character varying  ,
                        state character varying ,
                        is_change boolean
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('api_synchronize_data_config_id_seq', (select max(id) + 1 from  api_synchronize_data_config));
        ''')   
        
        return
        
        
    def sys_api_synchronize_data_config_line(self):
        sql ='''
        INSERT INTO 
            api_synchronize_data_config_line 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                config_id ,
                --fields_id  ,
                config_sys_id ,
                fields_name ,
                ttype ,
                fields_sys ,
                model_sys ,
                value_sys ,
                relation ,
                is_sync 
            )        
        
        SELECT 
            id, 
            create_date, create_uid, 
            write_date, write_uid, 
            config_id ,
            --fields_id  ,
            config_sys_id ,
            fields_name ,
            ttype ,
            fields_sys ,
            model_sys ,
            value_sys ,
            relation ,
            is_sync
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    config_id ,
                    fields_id  ,
                    config_sys_id ,
                    fields_name ,
                    ttype ,
                    fields_sys ,
                    model_sys ,
                    value_sys ,
                    relation ,
                    is_sync 
                        
                FROM public.api_synchronize_data_config_line') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        config_id integer,
                        fields_id integer,
                        config_sys_id integer,
                        fields_name character varying ,
                        ttype character varying ,
                        fields_sys character varying ,
                        model_sys character varying ,
                        value_sys character varying ,
                        relation character varying ,
                        is_sync boolean
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('api_synchronize_data_config_line_id_seq', (select max(id) + 1 from  api_synchronize_data_config_line));
        ''')   
        
        return
    
    def sys_api_synchronize_data(self):
        sql ='''
        INSERT INTO 
            api_synchronize_data 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                res_id ,
                res_id_syn ,
                number_of_retries ,
                name  ,
                model  ,
                name_syn  ,
                model_syn  ,
                state  ,
                slc_method  ,
                type  ,
                result  ,
                is_delete ,
                is_run ,
                is_write 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    res_id ,
                    res_id_syn ,
                    number_of_retries ,
                    name  ,
                    model  ,
                    name_syn  ,
                    model_syn  ,
                    state  ,
                    slc_method  ,
                    type  ,
                    result  ,
                    is_delete ,
                    is_run ,
                    is_write 
                    
                FROM public.api_synchronize_data') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        res_id integer,
                        res_id_syn integer,
                        number_of_retries integer,
                        name character varying ,
                        model character varying ,
                        name_syn character varying ,
                        model_syn character varying ,
                        state character varying ,
                        slc_method character varying ,
                        type character varying ,
                        result text ,
                        is_delete boolean,
                        is_run boolean,
                        is_write boolean
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('api_synchronize_data_id_seq', (select max(id) + 1 from  api_synchronize_data));
        ''')   
        
        return
