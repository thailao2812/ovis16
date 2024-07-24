from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
# from pip._vendor.pygments.lexer import _inherit
DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    def sys_report_production_pnl(self):
        self.env.cr.execute('''
            DELETE FROM production_analysis_line_output;
            DELETE FROM production_analysis_line_daily_confirmation;
            DELETE FROM production_analysis_line_input_quantity;
            DELETE FROM production_analysis_line_input_value;
            DELETE FROM production_analysis;
        ''')
        self.env.cr.commit()
        
        self.sys_production_pnl()
        self.sys_production_analysis_line_daily_confirmation_pnl()
        self.sys_production_analysis_line_input_quantity_pnl()
        self.sys_production_analysis_line_input_quantity_pnl2()
        self.sys_production_analysis_line_input_value()
        self.sys_production_analysis_line_output()
        
    
    def sys_production_pnl(self):
        sql ='''
        INSERT INTO 
            production_analysis 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                production_id ,
                failure ,
                crop_id  ,
                week ,
                note_fail  ,
                production_state  ,
                name  ,
                type  ,
                warning_mess  ,
                notes  ,
                exchange_rate ,
                premium_utz ,
                premium_4c ,
                trucking_cost ,
                input_quantity ,
                input_value ,
                output_quantity ,
                output_value ,
                payment_weight ,
                total_pnl ,
                pnl_per_ton ,
                ra_input ,
                sml_quantity ,
                sml_value ,
                liffe ,
                diff ,
                cost_price ,
                premium ,
                premium_total ,
                real_extraction ,
                price_premium ,
                sale_to_ams 
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
                    failure ,
                    crop_id  ,
                    week ,
                    note_fail  ,
                    production_state  ,
                    name  ,
                    type  ,
                    warning_mess  ,
                    notes  ,
                    exchange_rate ,
                    premium_utz ,
                    premium_4c ,
                    trucking_cost ,
                    input_quantity ,
                    input_value ,
                    output_quantity ,
                    output_value ,
                    payment_weight ,
                    total_pnl ,
                    pnl_per_ton ,
                    ra_input ,
                    sml_quantity ,
                    sml_value ,
                    liffe ,
                    diff ,
                    cost_price ,
                    premium ,
                    premium_total ,
                    real_extraction ,
                    price_premium ,
                    sale_to_ams 
                FROM public.production_analysis') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        production_id integer,
                        failure integer,
                        crop_id integer ,
                        week integer,
                        note_fail character varying ,
                        production_state character varying ,
                        name character varying ,
                        type character varying ,
                        warning_mess text ,
                        notes text ,
                        exchange_rate numeric,
                        premium_utz numeric,
                        premium_4c numeric,
                        trucking_cost numeric,
                        input_quantity numeric,
                        input_value numeric,
                        output_quantity numeric,
                        output_value numeric,
                        payment_weight numeric,
                        total_pnl numeric,
                        pnl_per_ton numeric,
                        ra_input double precision,
                        sml_quantity double precision,
                        sml_value double precision,
                        liffe double precision,
                        diff double precision,
                        cost_price double precision,
                        premium double precision,
                        premium_total double precision,
                        real_extraction double precision,
                        price_premium double precision,
                        sale_to_ams double precision
                    )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('production_analysis_id_seq', (select max(id) + 1 from  production_analysis));
        ''')   
        
    def sys_production_analysis_line_daily_confirmation_pnl(self):
        sql ='''
        INSERT INTO 
            production_analysis_line_daily_confirmation 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                analysis_id ,
                contract_id ,
                liffe  ,
                diff  ,
                diff_price  ,
                exchange_rate  
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date,  write_uid, 
            analysis_id ,
            contract_id ,
            liffe double ,
            diff double ,
            diff_price  ,
            exchange_rate  
            
            FROM public.dblink
                ('%s',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    analysis_id ,
                    contract_id ,
                    liffe ,
                    diff ,
                    diff_price  ,
                    exchange_rate  
                    
                    
                FROM public.production_analysis_line_daily_confirmation') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    analysis_id integer,
                    contract_id integer,
                    liffe double precision,
                    diff double precision,
                    diff_price double precision,
                    exchange_rate double precision
                    )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('production_analysis_line_daily_confirmation_id_seq', (select max(id) + 1 from  production_analysis_line_daily_confirmation));
        ''')   
        
    
    def sys_production_analysis_line_input_quantity_pnl(self):
        sql ='''
        INSERT INTO 
            production_analysis_line_input_quantity 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                analysis_id ,
                stack_id ,
                picking_id ,
                production_id ,
                product_id ,
                zone_id ,
                packing_id ,
                analysis_upgrade_id ,
                exportale  ,
                date ,
                net_qty ,
                real_qty ,
                bag_no ,
                mc_discount ,
                value_input ,
                mc ,
                fm ,
                black ,
                broken ,
                brown ,
                mold ,
                cherry ,
                excelsa ,
                screen18 ,
                screen16 ,
                screen13 ,
                screen12 ,
                greatersc12 ,
                burn ,
                eaten ,
                immature ,
                --stone_count ,
                --stick_count ,
                value_low_grade ,
                premium_discount ,
                required_mc ,
                excess_mc  
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date,  write_uid, 
            analysis_id ,
            stack_id ,
            picking_id ,
            production_id ,
            product_id ,
            zone_id ,
            packing_id ,
            analysis_upgrade_id ,
            exportale  ,
            date ,
            net_qty ,
            real_qty ,
            bag_no ,
            mc_discount ,
            value_input ,
            mc ,
            fm ,
            black ,
            broken ,
            brown ,
            mold ,
            cherry ,
            excelsa ,
            screen18 ,
            screen16 ,
            screen13 ,
            screen12 ,
            greatersc12 ,
            burn ,
            eaten ,
            immature ,
            --stone_count ,
            --stick_count ,
            value_low_grade ,
            premium_discount ,
            required_mc ,
            excess_mc  
            
            FROM public.dblink
                ('%s',
                 'SELECT 
                    r.id, 
                    r.create_date, r.create_uid, 
                    r.write_date, r.write_uid, 
                    analysis_id ,
                    r.stack_id ,
                    r.picking_id ,
                    r.production_id ,
                    r.product_id ,
                    r.zone_id ,
                    l.packing_id ,
                    analysis_upgrade_id ,
                    exportale  ,
                    r.date date,
                    r.net_qty ,
                    r.real_qty ,
                    r.bag_no ,
                    mc_discount ,
                    value_input ,
                    r.mc ,
                    r.fm ,
                    r.black ,
                    r.broken ,
                    r.brown ,
                    r.mold ,
                    r.cherry ,
                    r.excelsa ,
                    r.screen18 ,
                    r.screen16 ,
                    r.screen13 ,
                    r.screen12 ,
                    r.greatersc12 ,
                    r.burn ,
                    r.eaten ,
                    r.immature ,
                    --s.stone_count ,
                    --s.stick_count ,
                    value_low_grade ,
                    premium_discount ,
                    required_mc ,
                    excess_mc 
                    
                FROM public.production_analysis_line_input_quantity r join stock_picking p on r.picking_id = p.id
                    join stock_move l on p.id = l.picking_id') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    analysis_id integer,
                    stack_id integer,
                    picking_id integer,
                    production_id integer,
                    product_id integer,
                    zone_id integer,
                    packing_id integer,
                    analysis_upgrade_id integer,
                    exportale character ,
                    date date,
                    net_qty numeric,
                    real_qty numeric,
                    bag_no numeric,
                    mc_discount numeric,
                    value_input numeric,
                    mc double precision,
                    fm double precision,
                    black double precision,
                    broken double precision,
                    brown double precision,
                    mold double precision,
                    cherry double precision,
                    excelsa double precision,
                    screen18 double precision,
                    screen16 double precision,
                    screen13 double precision,
                    screen12 double precision,
                    greatersc12 double precision,
                    burn double precision,
                    eaten double precision,
                    immature double precision,
                    --stone_count double precision,
                    --stick_count double precision,
                    value_low_grade double precision,
                    premium_discount double precision,
                    required_mc double precision,
                    excess_mc double precision
                    
                    )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('production_analysis_line_input_quantity_id_seq', (select max(id) + 1 from  production_analysis_line_input_quantity));
        ''')  
    
    def sys_production_analysis_line_input_quantity_pnl2(self):
        sql ='''
        INSERT INTO 
            production_analysis_line_input_quantity 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                analysis_id ,
                stack_id ,
                picking_id ,
                production_id ,
                product_id ,
                zone_id ,
                --packing_id ,
                analysis_upgrade_id ,
                exportale  ,
                date ,
                net_qty ,
                real_qty ,
                bag_no ,
                mc_discount ,
                value_input ,
                mc ,
                fm ,
                black ,
                broken ,
                brown ,
                mold ,
                cherry ,
                excelsa ,
                screen18 ,
                screen16 ,
                screen13 ,
                screen12 ,
                greatersc12 ,
                burn ,
                eaten ,
                immature ,
                --stone_count ,
                --stick_count ,
                value_low_grade ,
                premium_discount ,
                required_mc ,
                excess_mc  
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date,  write_uid, 
            analysis_id ,
            stack_id ,
            picking_id ,
            production_id ,
            product_id ,
            zone_id ,
            --packing_id ,
            analysis_upgrade_id ,
            exportale  ,
            date ,
            net_qty ,
            real_qty ,
            bag_no ,
            mc_discount ,
            value_input ,
            mc ,
            fm ,
            black ,
            broken ,
            brown ,
            mold ,
            cherry ,
            excelsa ,
            screen18 ,
            screen16 ,
            screen13 ,
            screen12 ,
            greatersc12 ,
            burn ,
            eaten ,
            immature ,
            --stone_count ,
            --stick_count ,
            value_low_grade ,
            premium_discount ,
            required_mc ,
            excess_mc  
            
            FROM public.dblink
                ('%s',
                 'SELECT 
                    r.id, 
                    r.create_date, r.create_uid, 
                    r.write_date, r.write_uid, 
                    analysis_id ,
                    r.stack_id ,
                    r.picking_id ,
                    r.production_id ,
                    r.product_id ,
                    r.zone_id ,
                    --l.packing_id ,
                    analysis_upgrade_id ,
                    exportale  ,
                    r.date date,
                    r.net_qty ,
                    r.real_qty ,
                    r.bag_no ,
                    mc_discount ,
                    value_input ,
                    r.mc ,
                    r.fm ,
                    r.black ,
                    r.broken ,
                    r.brown ,
                    r.mold ,
                    r.cherry ,
                    r.excelsa ,
                    r.screen18 ,
                    r.screen16 ,
                    r.screen13 ,
                    r.screen12 ,
                    r.greatersc12 ,
                    r.burn ,
                    r.eaten ,
                    r.immature ,
                    --s.stone_count ,
                    --s.stick_count ,
                    value_low_grade ,
                    premium_discount ,
                    required_mc ,
                    excess_mc 
                    
                FROM public.production_analysis_line_input_quantity r where picking_id is null ') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    analysis_id integer,
                    stack_id integer,
                    picking_id integer,
                    production_id integer,
                    product_id integer,
                    zone_id integer,
                    --packing_id integer,
                    analysis_upgrade_id integer,
                    exportale character ,
                    date date,
                    net_qty numeric,
                    real_qty numeric,
                    bag_no numeric,
                    mc_discount numeric,
                    value_input numeric,
                    mc double precision,
                    fm double precision,
                    black double precision,
                    broken double precision,
                    brown double precision,
                    mold double precision,
                    cherry double precision,
                    excelsa double precision,
                    screen18 double precision,
                    screen16 double precision,
                    screen13 double precision,
                    screen12 double precision,
                    greatersc12 double precision,
                    burn double precision,
                    eaten double precision,
                    immature double precision,
                    --stone_count double precision,
                    --stick_count double precision,
                    value_low_grade double precision,
                    premium_discount double precision,
                    required_mc double precision,
                    excess_mc double precision
                    )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('production_analysis_line_input_quantity_id_seq', (select max(id) + 1 from  production_analysis_line_input_quantity));
        ''')   
        

    def sys_production_analysis_line_input_value(self):
        sql ='''
        INSERT INTO 
            production_analysis_line_input_value 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                analysis_id ,
                stack_id ,
                picking_id ,
                contract_id ,
                source_contract_id ,
                qty_allocation ,
                premium ,
                trucking_cost ,
                raw_coffee_cost ,
                factory_price ,
                total_paid ,
                liffe ,
                diff ,
                exchange_rate ,
                premium_total ,
                diff_price ,
                subsidy ,
                contract_price ,
                sale_to_ams ,
                factory_price_premium ,
                payment 
            )        
        
        SELECT 
                id,
                create_date, create_uid, 
                write_date,  write_uid, 
                analysis_id ,
                stack_id ,
                picking_id ,
                contract_id ,
                source_contract_id ,
                qty_allocation ,
                premium ,
                trucking_cost ,
                raw_coffee_cost ,
                factory_price ,
                total_paid ,
                liffe ,
                diff ,
                exchange_rate ,
                premium_total ,
                diff_price ,
                subsidy ,
                contract_price ,
                sale_to_ams ,
                factory_price_premium ,
                payment 
            FROM public.dblink
                ('%s',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    analysis_id ,
                    stack_id ,
                    picking_id ,
                    contract_id ,
                    source_contract_id ,
                    qty_allocation ,
                    premium ,
                    trucking_cost ,
                    raw_coffee_cost ,
                    factory_price ,
                    total_paid ,
                    liffe ,
                    diff ,
                    exchange_rate ,
                    premium_total ,
                    diff_price ,
                    subsidy ,
                    contract_price ,
                    sale_to_ams ,
                    factory_price_premium ,
                    payment 
                    
                FROM public.production_analysis_line_input_value') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        analysis_id integer,
                        stack_id integer,
                        picking_id integer,
                        contract_id integer,
                        source_contract_id integer,
                        qty_allocation numeric,
                        premium numeric,
                        trucking_cost numeric,
                        raw_coffee_cost numeric,
                        factory_price numeric,
                        total_paid numeric,
                        liffe numeric,
                        diff numeric,
                        exchange_rate numeric,
                        premium_total numeric,
                        diff_price numeric,
                        subsidy numeric,
                        contract_price double precision,
                        sale_to_ams double precision,
                        factory_price_premium double precision,
                        payment double precision
                    )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('production_analysis_line_input_value_id_seq', (select max(id) + 1 from  production_analysis_line_input_value));
        ''')   
        return
        
    def sys_production_analysis_line_output(self):
        sql ='''
        INSERT INTO 
            production_analysis_line_output 
            (
                id,
                create_date,create_uid,
                write_date, write_uid, 
                analysis_id,                    
                stack_id ,
                picking_id ,
                product_id ,
                categ_id ,
                zone_id ,
                --packing_id ,
                exportale ,
                date ,
                net_qty ,
                real_qty ,
                bag_no ,
                mc_discount ,
                value_output ,
                mc ,
                fm ,
                bb ,
                black ,
                broken ,
                brown ,
                mold ,
                cherry ,
                excelsa ,
                screen18 ,
                screen16 ,
                screen13 ,
                screen12 ,
                greatersc12 ,
                burn ,
                eaten ,
                immature ,
                --stone_count ,
                --stick_count ,
                value_low_grade ,
                premium_discount ,
                required_mc ,
                excess_mc 
            )        
        
        SELECT 
            id,
                create_date,create_uid,
                write_date, write_uid,   
                analysis_id,                  
                stack_id ,
                picking_id ,
                product_id ,
                categ_id ,
                zone_id ,
                --packing_id ,
                exportale ,
                date ,
                net_qty ,
                real_qty ,
                bag_no ,
                mc_discount ,
                value_output ,
                mc ,
                fm ,
                bb ,
                black ,
                broken ,
                brown ,
                mold ,
                cherry ,
                excelsa ,
                screen18 ,
                screen16 ,
                screen13 ,
                screen12 ,
                greatersc12 ,
                burn ,
                eaten ,
                immature ,
                --stone_count ,
                --stick_count ,
                value_low_grade ,
                premium_discount ,
                required_mc ,
                excess_mc 
                
            FROM public.dblink
                ('%s',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    analysis_id ,
                    stack_id ,
                    picking_id ,
                    product_id ,
                    categ_id ,
                    zone_id ,
                    --packing_id ,
                    exportale ,
                    date ,
                    net_qty ,
                    real_qty ,
                    bag_no ,
                    mc_discount ,
                    value_output ,
                    mc ,
                    fm ,
                    bb ,
                    black ,
                    broken ,
                    brown ,
                    mold ,
                    cherry ,
                    excelsa ,
                    screen18 ,
                    screen16 ,
                    screen13 ,
                    screen12 ,
                    greatersc12 ,
                    burn ,
                    eaten ,
                    immature ,
                    --stone_count ,
                    --stick_count ,
                    value_low_grade ,
                    premium_discount ,
                    required_mc ,
                    excess_mc 
                        
                FROM public.production_analysis_line_output') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        analysis_id integer,
                        stack_id integer,
                        picking_id integer,
                        product_id integer,
                        categ_id integer,
                        zone_id integer,
                        --packing_id integer,
                        exportale character varying,
                        date date,
                        net_qty numeric,
                        real_qty numeric,
                        bag_no numeric,
                        mc_discount numeric,
                        value_output numeric,
                        mc double precision,
                        fm double precision,
                        bb double precision,
                        black double precision,
                        broken double precision,
                        brown double precision,
                        mold double precision,
                        cherry double precision,
                        excelsa double precision,
                        screen18 double precision,
                        screen16 double precision,
                        screen13 double precision,
                        screen12 double precision,
                        greatersc12 double precision,
                        burn double precision,
                        eaten double precision,
                        immature double precision,
                        --stone_count double precision,
                        --stick_count double precision,
                        value_low_grade double precision,
                        premium_discount double precision,
                        required_mc double precision,
                        excess_mc double precision
                    )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('production_analysis_line_output_id_seq', (select max(id) + 1 from  production_analysis_line_output));
        ''')   
        
        return