# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _name = 'sucden.syn.config'
    _description = 'Sucden  Syn Config'
    
    name = fields.Char(string="Name")
    host = fields.Char(string="Host")
    user = fields.Char(string="User Name")
    password = fields.Char(string="password") 
    db_name = fields.Char(string="db Name") 
    server_db_link = fields.Char(string="Server Db Link") 
    result = fields.Char(string="Result" , readonly="1")
    
    def sys_compute(self):
        # self.compute_scontract_line()
        # self.compute_scontract()
        # self.compute_shipping_instruction()
        
        self.compute_sale_contract_line()
        self.compute_sale_contract()
    
    def sys_compute_data(self):
        # self.sys_produ()
        # self.sys_sys_sys()
        # self.sys_produ()
        # self.sys_partner()
        self.compute_account_journal()
        # self.syz_sale_contract()
        
    def syn_config(self):
        self.env.cr.execute('''
                CREATE EXTENSION dblink;
            ''')
        
        sql ='''
        SELECT dblink_connect('host=%s user=%s password=%s dbname=%s');
        '''%(self.host, self.user,self.password, self.db_name)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            result = line['dblink_connect'] or 'False'
        
        if result =='OK':
            self.env.cr.execute('''
                CREATE FOREIGN DATA WRAPPER dbrnd VALIDATOR postgresql_fdw_validator;
            ''')
            
            sql ='''
                CREATE SERVER %s FOREIGN DATA WRAPPER dbrnd OPTIONS (hostaddr '%s', dbname '%s');
            '''%(self.server_db_link, self.host, self.db_name)
            self.env.cr.execute(sql)
            self.env.cr.execute('''
                CREATE USER MAPPING FOR CURRENT_USER SERVER sucdendblink  OPTIONS (user 'odoo', password '1');
            ''')
            sql ='''
                SELECT dblink_connect('%s');
            '''%(self.server_db_link)
            
            self.env.cr.execute(sql)
            for line in self.env.cr.dictfetchall():
                sql = line['dblink_connect'] or 'False'
            
            self.result = sql
    
    def syn_config1(self):
        # self.env.cr.execute('''
        #         CREATE EXTENSION dblink;
        #     ''')
        
        sql ='''
        SELECT dblink_connect('host=%s user=%s password=%s dbname=%s');
        '''%(self.host, self.user,self.password, self.db_name)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            result = line['dblink_connect'] or 'False'
        
        if result =='OK':
            # self.env.cr.execute('''
            #     CREATE FOREIGN DATA WRAPPER dbrnd VALIDATOR postgresql_fdw_validator;
            # ''')
            
            sql ='''
                CREATE SERVER %s FOREIGN DATA WRAPPER dbrnd OPTIONS (hostaddr '%s', dbname '%s');
            '''%(self.server_db_link, self.host, self.db_name)
            self.env.cr.execute(sql)
            sql = '''
                CREATE USER MAPPING FOR CURRENT_USER SERVER %s  OPTIONS (user '%s', password '%s');
            '''%(self.server_db_link, self.user, self.password )
            self.env.cr.execute(sql)
            sql = '''
                SELECT dblink_connect('%s');
            ''' %(self.server_db_link)
            self.env.cr.execute(sql)
            for line in self.env.cr.dictfetchall():
                sql = line['dblink_connect'] or 'False'
            
            self.result = sql
                
       
  

            


        
    