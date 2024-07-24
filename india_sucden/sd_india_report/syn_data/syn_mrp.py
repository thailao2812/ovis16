from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re

DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    
    def sys_mrp_master11(self):
        self.env.cr.execute('''
            delete from mrp_production;
            delete from mrp_bom;
            delete from master_code;
            delete from processing_loss_aproval;
            
            delete from mrp_bom_premium;
            delete from mrp_bom_premium_line;
        ''')
        
        self.sys_master_code()
        self.sys_mrp_bom()
        self.sys_mrp_bom_premium()
        self.sys_mrp_bom_premium_line()
        self.sys_mrp_production()
    
    
    def sys_mrp_bom_premium(self):
        sql ='''
        INSERT INTO 
            mrp_bom_premium 
            (
                id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    crop_id ,
                    company_id ,
                    bom_id ,
                    name   ,
                    file_name   ,
                    standard_cost ,
                    active 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    crop_id ,
                    company_id ,
                    bom_id ,
                    name   ,
                    file_name   ,
                    standard_cost ,
                    active 
                    
                FROM public.mrp_bom_premium') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        crop_id integer,
                        company_id integer,
                        bom_id integer,
                        name character varying ,
                        file_name character varying ,
                        standard_cost numeric,
                        active boolean
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('mrp_bom_premium_id_seq', (select max(id) + 1 from  mrp_bom_premium));
        ''')   
        
        return
    
    def sys_mrp_bom_premium_line(self):
        sql ='''
        INSERT INTO 
            mrp_bom_premium_line 
            (
                id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    prem_id ,
                    product_id  ,
                    product_uom ,
                    flag ,
                    premium ,
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
                    belowsc12 ,
                    burned ,
                    eaten ,
                    immature 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    prem_id ,
                    product_id  ,
                    product_uom ,
                    flag ,
                    premium ,
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
                    belowsc12 ,
                    burned ,
                    eaten ,
                    immature 
                    
                FROM public.mrp_bom_premium_line') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        prem_id integer,
                        product_id integer ,
                        product_uom integer,
                        flag boolean,
                        premium double precision,
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
                        belowsc12 double precision,
                        burned double precision,
                        eaten double precision,
                        immature double precision
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('mrp_bom_premium_line_id_seq', (select max(id) + 1 from  mrp_bom_premium_line));
        ''')   
        
        return
    
    
    def sys_update_production_to_lot(self):
        self.env.cr.execute('''
            UPDATE stock_lot set production_id = xoo.production_id
            from
            (
               
                SELECT 
                    *
                    FROM public.dblink
                                ('sucdendblink',
                                 'SELECT 
                                    id,
                                    production_id
                                 
                                FROM public.stock_stack') 
                                AS DATA(
                                        id integer,
                                        production_id integer                           
                                    )
                ) xoo
                where stock_lot.id = xoo.id
        ''')
    
    def sys_mrp_master12(self):
        self.env.cr.execute('''
            
            alter table mrp_operation_result disable trigger all;
            delete from mrp_operation_result;
            alter table mrp_operation_result enable trigger all;
            alter sequence mrp_operation_result_id_seq minvalue 0 start with 1;
            SELECT setval('mrp_operation_result_id_seq', 0);
            
            
            alter table mrp_operation_result_produced_product disable trigger all;
            delete from mrp_operation_result_produced_product;
            alter table mrp_operation_result_produced_product enable trigger all;
            alter sequence mrp_operation_result_produced_product_id_seq minvalue 0 start with 1;
            SELECT setval('mrp_operation_result_produced_product_id_seq', 0);
            
            
            delete from processing_loss_aproval;
        ''')
        
        self.sys_mrp_operation_result()
        self.sys_mrp_operation_result_produced_product()
        self.sys_processing_loss_aproval()
    
    def sys_processing_loss_aproval(self):
        sql ='''
        INSERT INTO 
            processing_loss_aproval 
            (
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                
                --emp_id  ,
               -- job_id ,
               -- department_id ,
               -- result_id ,
                production_id  ,
                picking_id  ,
                warehouse_id ,
                batch_type  ,
                state  ,
                product_issued ,
                product_received ,
                mc_in ,
                mc_out ,
                weight_loss ,
                physical_weight ,
                mc_loss ,
                physical_loss ,
                invisible_loss ,
                start_date ,
                end_date 
               -- hour_nbr  ,
              -- ot_hour 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    
                    --emp_id  ,
                   -- job_id ,
                   -- department_id ,
                   -- result_id ,
                    production_id  ,
                    picking_id  ,
                    warehouse_id ,
                    batch_type  ,
                    state  ,
                    product_issued ,
                    product_received ,
                    mc_in ,
                    mc_out ,
                    weight_loss ,
                    physical_weight ,
                    mc_loss ,
                    physical_loss ,
                    invisible_loss ,
                    start_date ,
                    end_date 
                   -- hour_nbr  ,
                  -- ot_hour  
                    
                FROM public.processing_loss_aproval') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        --emp_id integer ,
                        --job_id integer,
                        --department_id integer,
                       -- result_id integer,
                        production_id integer ,
                        picking_id integer ,
                        warehouse_id integer,
                        batch_type character varying ,
                        state character varying ,
                        product_issued numeric,
                        product_received numeric,
                        mc_in numeric,
                        mc_out numeric,
                        weight_loss numeric,
                        physical_weight numeric,
                        mc_loss numeric,
                        physical_loss numeric,
                        invisible_loss numeric,
                        start_date timestamp without time zone,
                        end_date timestamp without time zone
                      --  hour_nbr double precision ,
                      --  ot_hour double precision 
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('processing_loss_aproval_id_seq', (select max(id) + 1 from  processing_loss_aproval));
        ''')   
        
        return
    
    def sys_mrp_operation_result_produced_product(self):
        sql ='''
        INSERT INTO 
            mrp_operation_result_produced_product 
            (
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                product_id  ,
                product_uom  ,
                operation_result_id ,
                si_id ,
                --lot_id ,
                production_id ,
                packing_id ,
                picking_id ,
                zone_id ,
                lot_id ,
                x_inspector ,
                notes  ,
                pending_grn  ,
                kcs_notes  ,
                zone  ,
                stack  ,
                product  ,
                packing  ,
                source  ,
                bag  ,
                stone  ,
                stick  ,
                remarks  ,
                remark_note  ,
                sampler  ,
                x_bulk_density  ,
                qty_bags ,
                production_weight ,
                product_qty ,
                --start_date ,
                --end_date ,
                qty_packing ,
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
                screen17 ,
                screen16 ,
                screen15 ,
                screen14 ,
                screen13 ,
                screen12 ,
                below_screen12 ,
                immature ,
                burn ,
                insect 
            )        
        
        SELECT 
            id, 
            create_date, create_uid, 
            write_date, write_uid, 
            product_id  ,
            product_uom  ,
            operation_result_id ,
            si_id ,
            --lot_id ,
            production_id ,
            packing_id ,
            picking_id ,
            zone_id ,
            stack_id as lot_id ,
            x_inspector ,
            notes  ,
            pending_grn  ,
            kcs_notes  ,
            zone  ,
            stack  ,
            product  ,
            packing  ,
            source  ,
            bag  ,
            stone  ,
            stick  ,
            remarks  ,
            remark_note  ,
            sampler  ,
            x_bulk_density  ,
            qty_bags ,
            production_weight ,
            product_qty ,
            --start_date ,
            --end_date ,
            qty_packing ,
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
            screen17 ,
            screen16 ,
            screen15 ,
            screen14 ,
            screen13 ,
            screen12 ,
            below_screen12 ,
            immature ,
            burn ,
            insect 
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    product_id  ,
                    product_uom  ,
                    operation_result_id ,
                    si_id ,
                    --lot_id ,
                    production_id ,
                    packing_id ,
                    picking_id ,
                    zone_id ,
                    stack_id ,
                    x_inspector ,
                    notes  ,
                    pending_grn  ,
                    kcs_notes  ,
                    zone  ,
                    stack  ,
                    product  ,
                    packing  ,
                    source  ,
                    bag  ,
                    stone  ,
                    stick  ,
                    remarks  ,
                    remark_note  ,
                    sampler  ,
                    x_bulk_density  ,
                    qty_bags ,
                    production_weight ,
                    product_qty ,
                    --start_date ,
                    --end_date ,
                    qty_packing ,
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
                    screen17 ,
                    screen16 ,
                    screen15 ,
                    screen14 ,
                    screen13 ,
                    screen12 ,
                    below_screen12 ,
                    immature ,
                    burn ,
                    insect 
                    
                    
                FROM public.mrp_operation_result_produced_product') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        product_id integer ,
                        product_uom integer ,
                        operation_result_id integer,
                        si_id integer,
                        --lot_id integer,
                        production_id integer,
                        packing_id integer,
                        picking_id integer,
                        zone_id integer,
                        stack_id integer,
                        x_inspector integer,
                        notes character varying(128) ,
                        pending_grn character varying ,
                        kcs_notes character varying(128) ,
                        zone character varying ,
                        stack character varying ,
                        product character varying ,
                        packing character varying ,
                        source character varying ,
                        bag character varying ,
                        stone character varying ,
                        stick character varying ,
                        remarks character varying ,
                        remark_note character varying ,
                        sampler character varying ,
                        x_bulk_density character varying ,
                        qty_bags numeric,
                        production_weight numeric,
                        product_qty numeric,
                        --start_date timestamp without time zone,
                        --end_date timestamp without time zone,
                        qty_packing double precision,
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
                        screen17 double precision,
                        screen16 double precision,
                        screen15 double precision,
                        screen14 double precision,
                        screen13 double precision,
                        screen12 double precision,
                        below_screen12 double precision,
                        immature double precision,
                        burn double precision,
                        insect double precision 
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('mrp_operation_result_produced_product_id_seq', (select max(id) + 1 from  mrp_operation_result_produced_product));
        ''')   
        
        return
    
    def sys_mrp_operation_result(self):
        sql ='''
        INSERT INTO 
            mrp_operation_result 
            (
                id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                   -- warehouse_id ,
                    --operation_id ,
                    --production_id ,
                    --calendar_id ,
                    --congdoan_id ,
                    product_id ,
                    product_uom ,
                    --resource_id ,
                    --import_result_id ,
                    user_import_id ,
                    resource_calendar_id ,
                    name  ,
                    state  ,
                    production_shift   ,
                    --date_result ,
                    note  ,
                    total_qty ,
                    total_bag ,
                    finished ,
                    start_date  ,
                    end_date  ,
                    hours ,
                    product_qty ,
                    production_id
            )        
        
        SELECT 
            id, 
            create_date, create_uid, 
            write_date, write_uid, 
           -- warehouse_id ,
            --operation_id ,
            --production_id ,
            --calendar_id ,
            --congdoan_id ,
            product_id ,
            product_uom ,
            --resource_id ,
            --import_result_id ,
            user_import_id ,
            resource_calendar_id ,
            name  ,
            state  ,
            production_shift   ,
            --date_result ,
            note  ,
            total_qty ,
            total_bag ,
            finished ,
            start_date  ,
            end_date  ,
            hours ,
            product_qty ,
            production_id
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    m_r.id, 
                    m_r.create_date, m_r.create_uid, 
                    m_r.write_date, m_r.write_uid, 
                   -- warehouse_id ,
                    --operation_id ,
                    --production_id ,
                    --calendar_id ,
                    --congdoan_id ,
                    m_r.product_id ,
                    m_r.product_uom ,
                    resource_id ,
                    --import_result_id ,
                    user_import_id ,
                    resource_calendar_id ,
                    m_r.name  ,
                    m_r.state  ,
                    production_shift   ,
                    --date_result ,
                    m_r.note  ,
                    total_qty ,
                    total_bag ,
                    finished ,
                    start_date  ,
                    end_date  ,
                    hours ,
                    m_r.product_qty ,
                    wl.production_id
                     
                FROM public.mrp_operation_result m_r 
                 join public.mrp_production_workcenter_line wl on m_r.operation_id = wl.id
                 join mrp_production pro on wl.production_id = pro.id
                 ') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        
                       -- warehouse_id integer,
                        --operation_id integer,
                        --production_id integer,
                        --calendar_id integer,
                       -- congdoan_id integer,
                        product_id integer,
                        product_uom integer,
                        resource_id integer,
                        --import_result_id integer,
                        user_import_id integer,
                        resource_calendar_id integer,
                        name character varying ,
                        state character varying ,
                        production_shift character varying  ,
                        --date_result date,
                        note text ,
                        total_qty numeric,
                        total_bag numeric,
                        finished boolean,
                        start_date timestamp without time zone ,
                        end_date timestamp without time zone ,
                        hours double precision,
                        product_qty double precision,
                        production_id integer
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('mrp_operation_result_id_seq', (select max(id) + 1 from  mrp_operation_result));
        ''')   
        
        return
        
    def sys_mrp_production(self):
        sql ='''
        INSERT INTO 
            mrp_production 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,           
                          
                product_id ,
                product_uom_id,
                --lot_producing_id ,
                --picking_type_id  ,
                location_src_id  ,
                location_dest_id  ,
                bom_id ,
                user_id ,
                company_id  ,
                --procurement_group_id ,
                --orderpoint_id ,
                --production_location_id ,
                name  ,
                priority  ,
                origin  ,
                state  ,
                --reservation_state  ,
                --product_description_variants  ,
                consumption   ,
                product_qty  ,
                --qty_producing ,
                --propagate_cancel ,
                --is_locked ,
                --is_planned ,
                --allow_workorder_dependencies ,
                date_planned_start  ,
                --date_planned_finished ,
                --date_deadline ,
                date_start ,
                date_finished ,
                --product_uom_qty ,
                --analytic_account_id ,
                --extra_cost ,
                warehouse_id ,
                grade_id ,
                batch_type  ,
                notes  ,
                product_issued ,
                product_basis_issued ,
                product_received ,
                product_balance ,
                product_received_loss ,
                product_loss_percent ,
                stored_loss
            )        
        
        SELECT 
            id, 
            create_date, create_uid, 
            write_date, write_uid, 
            
            --backorder_sequence ,
            product_id ,
            product_uom as product_uom_id,
            --lot_producing_id ,
            --picking_type_id  ,
            location_src_id  ,
            location_dest_id  ,
            bom_id ,
            user_id ,
            company_id  ,
            --procurement_group_id ,
            --orderpoint_id ,
            --production_location_id ,
            name  ,
            priority  ,
            origin  ,
            
            CASE
                WHEN state in ('draft') THEN 'draft'::text
                WHEN state in ('in_production') THEN 'progress'::text  
                WHEN state in ('done') THEN 'done'::text          
                WHEN state in ('cancel') THEN 'cancel'::text                           
                END AS state,
            
            --reservation_state  ,
            --product_description_variants  ,
            'flexible' as consumption  ,
            product_qty  ,
            --qty_producing ,
            --propagate_cancel ,
            --is_locked ,
            --is_planned ,
            --allow_workorder_dependencies ,
            date_planned as date_planned_start  ,
            --date_planned_finished ,
            --date_deadline ,
            date_start ,
            date_finished ,
            --product_uom_qty ,
            --analytic_account_id ,
            --extra_cost ,
            warehouse_id ,
            grade_id ,
            batch_type  ,
            notes  ,
            product_issued ,
            product_basis_issued ,
            product_received ,
            product_balance ,
            product_received_loss ,
            product_loss_percent ,
            stored_loss
                    
        FROM public.dblink
            ('sucdendblink',
             'SELECT 
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                
                --backorder_sequence ,
                product_id ,
                product_uom ,
                --lot_producing_id ,
                --picking_type_id  ,
                location_src_id  ,
                location_dest_id  ,
                bom_id ,
                user_id ,
                company_id  ,
                --procurement_group_id ,
                --orderpoint_id ,
                --production_location_id ,
                name  ,
                priority  ,
                origin  ,
                state  ,
                --reservation_state  ,
                --product_description_variants  ,
                --consumption   ,
                product_qty  ,
                --qty_producing ,
                --propagate_cancel ,
                --is_locked ,
                --is_planned ,
                --allow_workorder_dependencies ,
                date_planned  ,
                --date_planned_finished ,
                --date_deadline ,
                date_start ,
                date_finished ,
                --product_uom_qty ,
                --analytic_account_id ,
                --extra_cost ,
                warehouse_id ,
                grade_id ,
                batch_type  ,
                notes  ,
                product_issued ,
                product_basis_issued ,
                product_received ,
                product_balance ,
                product_received_loss ,
                product_loss_percent ,
                stored_loss
            
        FROM public.mrp_production') 
        AS DATA(id INTEGER,
            create_date timestamp without time zone,
            create_uid integer,
            write_date timestamp without time zone,
            write_uid integer,   
                                     
           --backorder_sequence integer,
            product_id integer,
            product_uom integer,
            --lot_producing_id integer,
            --picking_type_id integer ,
            location_src_id integer ,
            location_dest_id integer ,
            bom_id integer,
            user_id integer,
            company_id integer ,
            --procurement_group_id integer,
            --orderpoint_id integer,
            --production_location_id integer,
            name character varying ,
            priority character varying ,
            origin character varying ,
            state character varying ,
            --reservation_state character varying ,
            --product_description_variants character varying ,
            --consumption character varying  ,
            product_qty numeric ,
            --qty_producing numeric,
            --propagate_cancel boolean,
            --is_locked boolean,
            --is_planned boolean,
            --allow_workorder_dependencies boolean,
            date_planned timestamp without time zone ,
            --date_planned_finished timestamp without time zone,
            --date_deadline timestamp without time zone,
            date_start timestamp without time zone,
            date_finished timestamp without time zone,
            --product_uom_qty double precision,
            --analytic_account_id integer,
            --extra_cost double precision,
            warehouse_id integer,
            grade_id integer,
            batch_type character varying ,
            notes text ,
            product_issued numeric,
            product_basis_issued numeric,
            product_received numeric,
            product_balance numeric,
            product_received_loss numeric,
            product_loss_percent numeric,
            stored_loss numeric
            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('mrp_production_id_seq', (select max(id) + 1 from  mrp_production));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
        
    def sys_mrp_bom(self):
        sql ='''
        INSERT INTO 
            mrp_bom 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                product_tmpl_id ,
                product_id ,
                product_uom_id ,
                sequence ,
                --picking_type_id ,
                company_id ,
                code  ,
                type   ,
                ready_to_produce   ,
                consumption   ,
                product_qty  ,
                active ,
                --allow_operation_dependencies ,
                master_code_id ,
                crop_id ,
                grade_id ,
                type_code  ,
                batch_code  ,
                last_revised ,
                remarks  ,
                description 
                --detail   
            )        
        
        SELECT 
            id, 
            create_date, create_uid, 
            write_date, write_uid, 
            product_tmpl_id ,
            product_id ,
            product_uom  ,
            sequence ,
            --picking_type_id ,
            company_id ,
            code  ,
            type   ,
            'all_available' as ready_to_produce   ,
            'flexible' as consumption   ,
            product_qty  ,
            active ,
            --allow_operation_dependencies ,
            master_code_id ,
            crop_id ,
            grade_id ,
            type_code  ,
            batch_code  ,
            last_revised ,
            remarks  ,
            description 
            --detail   
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    product_tmpl_id ,
                    product_id ,
                    product_uom  ,
                    sequence ,
                    --picking_type_id ,
                    company_id ,
                    code  ,
                    type   ,
                    --ready_to_produce   ,
                    --consumption   ,
                    product_qty  ,
                    active ,
                    --allow_operation_dependencies ,
                    master_code_id ,
                    crop_id ,
                    grade_id ,
                    type_code  ,
                    batch_code  ,
                    last_revised ,
                    remarks  ,
                    description 
                    --detail   
                      
                FROM public.mrp_bom') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    
                    product_tmpl_id integer,
                    product_id integer,
                    product_uom integer ,
                    sequence integer,
                    --picking_type_id integer,
                    company_id integer,
                    code character varying ,
                    type character varying  ,
                    --ready_to_produce character varying  ,
                    --consumption character varying  ,
                    product_qty numeric ,
                    active boolean,
                    --allow_operation_dependencies boolean,
                    master_code_id integer,
                    crop_id integer,
                    grade_id integer,
                    type_code character varying ,
                    batch_code character varying ,
                    last_revised date,
                    remarks text ,
                    description text 
                    --detail text 
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('mrp_bom_id_seq', (select max(id) + 1 from  mrp_bom));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_master_code(self):
        sql ='''
        INSERT INTO 
            master_code 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name  ,
                type_code  ,
                remarks
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    name  ,
                    type_code  ,
                    remarks
                      
                FROM public.master_code') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name character varying,
                        type_code character varying,
                        remarks text 
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('master_code_id_seq', (select max(id) + 1 from  master_code));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
        
    
    # def sys_mrp_master11(self):
    #     self.env.cr.execute('''
    #         delete from mrp_production;
    #         delete from mrp_bom;
    #         delete from master_code;
    #
    #         alter table mrp_operation_result disable trigger all;
    #         delete from mrp_operation_result;
    #         alter table mrp_operation_result enable trigger all;
    #         alter sequence mrp_operation_result_id_seq minvalue 0 start with 1;
    #         SELECT setval('mrp_operation_result_id_seq', 0);
    #
    #         mrp_operation_result_produced_product
    #
    #         alter table mrp_operation_result_produced_product disable trigger all;
    #         delete from mrp_operation_result_produced_product;
    #         alter table mrp_operation_result_produced_product enable trigger all;
    #         alter sequence mrp_operation_result_produced_product_id_seq minvalue 0 start with 1;
    #         SELECT setval('mrp_operation_result_produced_product_id_seq', 0);
    #
    #
    #         delete from processing_loss_aproval;
    #     ''')
    #
    #     self.sys_master_code()
    #     self.sys_mrp_bom()
    #     self.sys_mrp_production()
    #     self.sys_mrp_operation_result()
    #     self.sys_mrp_operation_result_produced_product()
    #     self.sys_processing_loss_aproval()