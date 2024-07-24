from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re

DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    def sys_report_batch(self):
        self.env.cr.execute('''
            DELETE FROM batch_report_output;
            DELETE FROM batch_report_input;
            DELETE FROM batch_report_instore;
            DELETE FROM batch_report;
        ''')
        self.env.cr.commit()
        
        self.sys_batch_report()
        self.sys_batch_report_input()
        self.sys_batch_report_output()
        self.batch_report_instore()
    
    def batch_report_instore(self):
        sql ='''
        
        INSERT INTO 
            batch_report_instore 
            (
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                stack_id ,
                product_id ,
                batch_id ,
                date ,
                mc ,
                fm ,
                black ,
                broken ,
                brown ,
                mold ,
                cherry ,
                screen20 ,
                screen19 ,
                screen18 ,
                screen16 ,
                screen13 ,
                screen12 ,
                greatersc12 ,
                burn ,
                eaten ,
                immature ,
                net_qty ,
                excelsa 
            )        
        SELECT 
            *
            FROM public.dblink
                ('%s',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    
                    stack_id ,
                    product_id ,
                    batch_id ,
                    date ,
                    mc ,
                    fm ,
                    black ,
                    broken ,
                    brown ,
                    mold ,
                    cherry ,
                    screen20 ,
                    screen19 ,
                    screen18 ,
                    screen16 ,
                    screen13 ,
                    screen12 ,
                    greatersc12 ,
                    burn ,
                    eaten ,
                    immature ,
                    net_qty ,
                    excelsa 
                    
                FROM public.batch_report_instore') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer, 
                    stack_id integer,
                    product_id integer,
                    batch_id integer,
                    date date,
                    mc numeric,
                    fm numeric,
                    black numeric,
                    broken numeric,
                    brown numeric,
                    mold numeric,
                    cherry numeric,
                    screen20 numeric,
                    screen19 numeric,
                    screen18 numeric,
                    screen16 numeric,
                    screen13 numeric,
                    screen12 numeric,
                    greatersc12 numeric,
                    burn numeric,
                    eaten numeric,
                    immature numeric,
                    net_qty double precision,
                    excelsa double precision
                )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('batch_report_instore_id_seq', (select max(id) + 1 from  batch_report_instore));
        ''')   
    
    
    def sys_batch_report_output(self):
        sql ='''
        INSERT INTO 
            batch_report_output 
            (
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                stack_id ,
                picking_id ,
                zone_id ,
                product_id ,
                categ_id ,
                batch_id ,
                date ,
                net_qty ,
                real_qty ,
                bag_no ,
                mc ,
                fm ,
                black ,
                broken ,
                brown ,
                mold ,
                cherry ,
                excelsa ,
                screen20 ,
                screen19 ,
                screen18 ,
                screen16 ,
                screen13 ,
                screen12 ,
                greatersc12 ,
                burn ,
                eaten ,
                immature 
                --stone_count ,
                --stick_count 
            )        
        SELECT 
            id, 
                create_date, create_uid, 
                write_date,  write_uid, 
                stack_id ,
                picking_id ,
                zone_id ,
                product_id ,
                categ_id ,
                batch_id ,
                date date,
                net_qty ,
                real_qty ,
                bag_no ,
                mc ,
                fm ,
                black ,
                broken ,
                brown ,
                mold ,
                cherry ,
                excelsa ,
                screen20 ,
                screen19 ,
                screen18 ,
                screen16 ,
                screen13 ,
                screen12 ,
                greatersc12 ,
                burn ,
                eaten ,
                immature 
                --stone_count ,
                --stick_count 
            FROM public.dblink
                ('%s',
                 'SELECT 
                    r.id, 
                    r.create_date, r.create_uid, 
                    r.write_date, r.write_uid, 
                    r.stack_id ,
                    r.picking_id ,
                    r.zone_id ,
                    r.product_id ,
                    r.categ_id ,
                    r.batch_id ,
                    r.date date,
                    r.net_qty ,
                    r.real_qty ,
                    r.bag_no ,
                    r.mc ,
                    r.fm ,
                    r.black ,
                    r.broken ,
                    r.brown ,
                    r.mold ,
                    r.cherry ,
                    r.excelsa ,
                    r.screen20 ,
                    r.screen19 ,
                    r.screen18 ,
                    r.screen16 ,
                    r.screen13 ,
                    r.screen12 ,
                    r.greatersc12 ,
                    r.burn ,
                    r.eaten ,
                    r.immature ,
                    ss.stone_count ,
                    ss.stick_count 
                FROM public.batch_report_output r left join stock_stack ss on r.stack_id = ss.id') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        stack_id integer,
                        picking_id integer,
                        zone_id integer,
                        product_id integer,
                        categ_id integer,
                        batch_id integer,
                        date date,
                        net_qty double precision,
                        real_qty double precision,
                        bag_no double precision,
                        mc double precision,
                        fm double precision,
                        black double precision,
                        broken double precision,
                        brown double precision,
                        mold double precision,
                        cherry double precision,
                        excelsa double precision,
                        screen20 double precision,
                        screen19 double precision,
                        screen18 double precision,
                        screen16 double precision,
                        screen13 double precision,
                        screen12 double precision,
                        greatersc12 double precision,
                        burn double precision,
                        eaten double precision,
                        immature double precision,
                        stone_count character varying,
                        stick_count character varying
                    )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('batch_report_output_id_seq', (select max(id) + 1 from  batch_report_output));
        ''')   
        
    def sys_batch_report(self):
        sql ='''
        INSERT INTO 
            batch_report 
            (
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                production_id ,
                name  ,
                in_mc ,
                in_fm ,
                in_black ,
                in_broken ,
                in_brown ,
                in_mold ,
                in_cherry ,
                in_excelsa ,
                in_screen20 ,
                in_screen19 ,
                in_screen18 ,
                in_screen16 ,
                in_screen13 ,
                in_screen12 ,
                in_greatersc12 ,
                in_burn ,
                in_immature ,
                total_in_qty ,
                total_real_qty ,
                total_bag ,
                ins_mc ,
                ins_fm ,
                ins_black ,
                ins_broken ,
                ins_brown ,
                ins_mold ,
                ins_cherry ,
                ins_excelsa ,
                ins_screen20 ,
                ins_screen19 ,
                ins_screen18 ,
                ins_screen16 ,
                ins_screen13 ,
                ins_screen12 ,
                ins_greatersc12 ,
                ins_burn ,
                ins_eaten ,
                ins_immature ,
                out_mc ,
                out_fm ,
                out_black ,
                out_broken ,
                out_brown ,
                out_mold ,
                out_cherry ,
                out_excelsa ,
                out_screen20 ,
                out_screen19 ,
                out_screen18 ,
                out_screen16 ,
                out_screen13 ,
                out_screen12 ,
                out_greatersc12 ,
                out_burn ,
                out_immature ,
                total_out_qty ,
                total_instore_qty 
            )        
        SELECT 
            *
            FROM public.dblink
                ('%s',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    production_id ,
                        name  ,
                        in_mc ,
                        in_fm ,
                        in_black ,
                        in_broken ,
                        in_brown ,
                        in_mold ,
                        in_cherry ,
                        in_excelsa ,
                        in_screen20 ,
                        in_screen19 ,
                        in_screen18 ,
                        in_screen16 ,
                        in_screen13 ,
                        in_screen12 ,
                        in_greatersc12 ,
                        in_burn ,
                        in_immature ,
                        total_in_qty ,
                        total_real_qty ,
                        total_bag ,
                        ins_mc ,
                        ins_fm ,
                        ins_black ,
                        ins_broken ,
                        ins_brown ,
                        ins_mold ,
                        ins_cherry ,
                        ins_excelsa ,
                        ins_screen20 ,
                        ins_screen19 ,
                        ins_screen18 ,
                        ins_screen16 ,
                        ins_screen13 ,
                        ins_screen12 ,
                        ins_greatersc12 ,
                        ins_burn ,
                        ins_eaten ,
                        ins_immature ,
                        out_mc ,
                        out_fm ,
                        out_black ,
                        out_broken ,
                        out_brown ,
                        out_mold ,
                        out_cherry ,
                        out_excelsa ,
                        out_screen20 ,
                        out_screen19 ,
                        out_screen18 ,
                        out_screen16 ,
                        out_screen13 ,
                        out_screen12 ,
                        out_greatersc12 ,
                        out_burn ,
                        out_immature ,
                        total_out_qty ,
                        total_instore_qty 
                        
                FROM public.batch_report') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        production_id integer,
                        name character varying ,
                        in_mc numeric,
                        in_fm numeric,
                        in_black numeric,
                        in_broken numeric,
                        in_brown numeric,
                        in_mold numeric,
                        in_cherry numeric,
                        in_excelsa numeric,
                        in_screen20 numeric,
                        in_screen19 numeric,
                        in_screen18 numeric,
                        in_screen16 numeric,
                        in_screen13 numeric,
                        in_screen12 numeric,
                        in_greatersc12 numeric,
                        in_burn numeric,
                        in_immature numeric,
                        total_in_qty numeric,
                        total_real_qty numeric,
                        total_bag numeric,
                        ins_mc numeric,
                        ins_fm numeric,
                        ins_black numeric,
                        ins_broken numeric,
                        ins_brown numeric,
                        ins_mold numeric,
                        ins_cherry numeric,
                        ins_excelsa numeric,
                        ins_screen20 numeric,
                        ins_screen19 numeric,
                        ins_screen18 numeric,
                        ins_screen16 numeric,
                        ins_screen13 numeric,
                        ins_screen12 numeric,
                        ins_greatersc12 numeric,
                        ins_burn numeric,
                        ins_eaten numeric,
                        ins_immature numeric,
                        out_mc numeric,
                        out_fm numeric,
                        out_black numeric,
                        out_broken numeric,
                        out_brown numeric,
                        out_mold numeric,
                        out_cherry numeric,
                        out_excelsa numeric,
                        out_screen20 numeric,
                        out_screen19 numeric,
                        out_screen18 numeric,
                        out_screen16 numeric,
                        out_screen13 numeric,
                        out_screen12 numeric,
                        out_greatersc12 numeric,
                        out_burn numeric,
                        out_immature numeric,
                        total_out_qty numeric,
                        total_instore_qty double precision
                    )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('batch_report_id_seq', (select max(id) + 1 from  batch_report));
        ''')   
    
    def sys_batch_report_input(self):
        sql ='''
        INSERT INTO 
            batch_report_input 
            (
                id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    stack_id ,
                    picking_id ,
                    zone_id ,
                    product_id ,
                    categ_id ,
                    packing_id ,
                    batch_id ,
                    date ,
                    net_qty ,
                    real_qty ,
                    bag_no ,
                    mc ,
                    fm ,
                    black ,
                    broken ,
                    brown ,
                    mold ,
                    cherry ,
                    excelsa ,
                    screen20 ,
                    screen19 ,
                    screen18 ,
                    screen16 ,
                    screen13 ,
                    screen12 ,
                    greatersc12 ,
                    burn ,
                    eaten ,
                    immature 
                    --stone_count ,
                    --stick_count 
            )        
        SELECT 
            *
            FROM public.dblink
                ('%s',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    stack_id ,
                    picking_id ,
                    zone_id ,
                    product_id ,
                    categ_id ,
                    packing_id ,
                    batch_id ,
                    date date,
                    net_qty ,
                    real_qty ,
                    bag_no ,
                    mc ,
                    fm ,
                    black ,
                    broken ,
                    brown ,
                    mold ,
                    cherry ,
                    excelsa ,
                    screen20 ,
                    screen19 ,
                    screen18 ,
                    screen16 ,
                    screen13 ,
                    screen12 ,
                    greatersc12 ,
                    burn ,
                    eaten ,
                    immature 
                    --stone_count ,
                    --stick_count 
                        
                FROM public.batch_report_input') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        stack_id integer,
                        picking_id integer,
                        zone_id integer,
                        product_id integer,
                        categ_id integer,
                        packing_id integer,
                        batch_id integer,
                        date date,
                        net_qty double precision,
                        real_qty double precision,
                        bag_no double precision,
                        mc double precision,
                        fm double precision,
                        black double precision,
                        broken double precision,
                        brown double precision,
                        mold double precision,
                        cherry double precision,
                        excelsa double precision,
                        screen20 double precision,
                        screen19 double precision,
                        screen18 double precision,
                        screen16 double precision,
                        screen13 double precision,
                        screen12 double precision,
                        greatersc12 double precision,
                        burn double precision,
                        eaten double precision,
                        immature double precision
                        --stone_count double precision,
                        --stick_count double precision
                    )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('batch_report_input_id_seq', (select max(id) + 1 from  batch_report_input));
        ''')   
        
    
        