from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re

DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    
    # def sys_stock(self):
    #
    #
    #     self.env.cr.execute('''
    #         delete from ned_security_gate_queue;
    #         delete from request_materials_line;
    #         delete from request_materials;
    #         delete from stock_picking;
    #         delete from stock_stack_transfer;
    #
    #     ''')
    #
    #     self.sys_ned_security_gate_queue()
    #     self.sys_request_materials()
    #     self.sys_request_materials_line()
    #
    #     self.sys_stock_picking()
    #     self.sys_stock_move()
    #     self.sys_stock_move_line()
    #
    #     self.sys_update_link_material()
    #     self.sys_picking_request_move_ref()
    #     self.self.sys_stock_stack_transfer()
    
    
    def sys_stock1_run(self):
        self.env.cr.execute('''
            delete from ned_security_gate_queue;
            delete from request_materials_line;
            delete from request_materials;
            delete from picking_request_move_ref;
            
            
            alter table stock_picking disable trigger all;
            delete from stock_picking;
            alter table stock_picking enable trigger all;
            alter sequence stock_picking_id_seq minvalue 0 start with 1;
            SELECT setval('stock_picking_id_seq', 0);
            
            alter table stock_stack_transfer disable trigger all;
            delete from stock_stack_transfer;
            alter table stock_stack_transfer enable trigger all;
            alter sequence stock_stack_transfer_id_seq minvalue 0 start with 1;
            SELECT setval('stock_stack_transfer_id_seq', 0);
            
        ''')
        self.sys_ned_security_gate_queue()
        self.sys_request_materials()
        self.sys_request_materials_line()
        return
    
    def sys_stock1_1_run(self):
        self.sys_stock_picking()
        self.sys_stock_stack_transfer()
        self.sys_picking_request_move_ref()
        return
    
    def sys_stock2_run(self):
        self.env.cr.execute('''
            
            alter table stock_move_line disable trigger all;
            delete from stock_move_line;
            alter table stock_move_line enable trigger all;
            alter sequence stock_move_line_id_seq minvalue 0 start with 1;
            SELECT setval('stock_move_line_id_seq', 0);
            
            alter table stock_move disable trigger all;
            delete from stock_move;
            alter table stock_move enable trigger all;
            alter sequence stock_move_id_seq minvalue 0 start with 1;
            SELECT setval('stock_move_id_seq', 0);
        ''')
        self.sys_stock_move()
        
        return
    
    def sys_stock3_run(self):
        self.env.cr.execute('''
            
            alter table stock_move_line disable trigger all;
            delete from stock_move_line;
            alter table stock_move_line enable trigger all;
            alter sequence stock_move_line_id_seq minvalue 0 start with 1;
            SELECT setval('stock_move_line_id_seq', 0);
            
        ''')
        self.sys_stock_move_line()
        self.sys_update_link_material()
        return
    
    
    def sys_picking_request_move_ref(self):
        sql ='''
        INSERT INTO 
            picking_request_move_ref 
            (
                picking_id  ,           
                request_id
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    picking_id,
                    request_id
                 
                FROM public.picking_request_move_ref') 
                AS DATA(
                        picking_id integer,
                        request_id integer                            
                    )
        '''
        self.env.cr.execute(sql)
        
    
    def sys_update_link_material(self):
        self.env.cr.execute('''
            update stock_move_line set material_id = xoo.production_id
            from
            (
            select sml.id, sml.move_id, finished_id, foo.production_id, material_id
            from stock_move_line sml join 
            (SELECT 
                        *
                        
                        FROM public.dblink
                                    ('sucdendblink',
                                     'SELECT 
                                        production_id,
                                        move_id
                                     
                                    FROM public.mrp_production_move_ids') 
                                    AS DATA(
                                            production_id integer,
                                            move_id integer                            
                                        )
            ) foo on sml.move_id =foo.move_id) xoo
            where stock_move_line.id = xoo.id
        ''')
        
        self.env.cr.execute('''
            UPDATE stock_move_line set finished_id = null
            FROM (
                SELECT sml.picking_id,sml.id,sml.finished_id,sml.material_id
                FROM stock_move_line sml
                    join stock_picking sp on sp.id = sml.picking_id
                    join stock_picking_type spt on sp.picking_type_id = spt.id
                WHERE
                    spt.code ='production_out'
                    and sml.finished_id is not null) foo
            where stock_move_line.id = foo.id;
        
        ''')
        
        self.env.cr.execute('''
            UPDATE stock_move_line set finished_id = null, material_id = null
            WHERE
                picking_id = null
        
        ''')
    
    def sys_stock_move_line(self):
        sql ='''
        INSERT INTO 
            stock_move_line 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                move_id,
                picking_id ,
                --move_id ,
                company_id  ,
                product_id ,
                product_uom_id  ,
                --package_id ,
                --package_level_id ,                        
                --result_package_id ,
                --owner_id ,
                location_id  ,
                location_dest_id  ,
                --product_category_name  ,
                --lot_name  ,
                state  ,
                reference ,
                --description_picking text ,
                --reserved_qty ,
                --reserved_uom_qty  ,
                --qty_done ,
                date  ,
                --workorder_id ,
                --production_id ,
                lot_id ,
                zone_id ,
                warehouse_id ,
                currency_id ,
                partner_id ,
                packing_id ,
                weight_scale_id  ,
                init_qty ,
                weighbridge  ,
                first_weight ,
                second_weight ,
                bag_no ,
                tare_weight ,
                stack_empty ,
                price_unit ,
                price_currency ,
                gross_weight ,
                reserved_uom_qty,
                qty_done,
                finished_id
            )        
        
        SELECT 
            id, 
                create_date,  create_uid, 
                write_date,  write_uid, 
                
                id as move_id,
                picking_id ,
                --move_id ,
                company_id  ,
                product_id ,
                product_uom as product_uom_id ,
                --package_id ,
                --package_level_id ,                        
                --result_package_id ,
                --owner_id ,
                location_id  ,
                location_dest_id  ,
                --product_category_name  ,
                --lot_name  ,
                state  ,
                name as reference    ,
                --description_picking text ,
                --reserved_qty ,
                --reserved_uom_qty  ,
                --qty_done ,
                date  ,
                --workorder_id ,
                --production_id ,
                stack_id as lot_id,
                zone_id ,
                warehouse_id ,
                currency_id ,
                partner_id ,
                packing_id ,
                weight_scale_id  ,
                init_qty ,
                weighbridge  ,
                first_weight ,
                second_weight ,
                bag_no ,
                tare_weight ,
                stack_empty ,
                price_unit ,
                price_currency ,
                gross_weight ,
                product_qty as reserved_uom_qty,
                product_qty as qty_done,
                production_id as finished_id 
                --material_id   
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date,  create_uid, 
                    write_date,  write_uid, 
                    
                    picking_id ,
                        --move_id ,
                        company_id  ,
                        product_id ,
                        product_uom  ,
                        --package_id ,
                        --package_level_id ,                        
                        --result_package_id ,
                        --owner_id ,
                        location_id  ,
                        location_dest_id  ,
                        --product_category_name  ,
                        --lot_name  ,
                        state  ,
                        name  ,
                        --description_picking text ,
                        --reserved_qty ,
                        --reserved_uom_qty  ,
                        --qty_done ,
                        date  ,
                        --workorder_id ,
                        --production_id ,
                        stack_id ,
                        zone_id ,
                        warehouse_id ,
                        currency_id ,
                        partner_id ,
                        packing_id ,
                        weight_scale_id  ,
                        init_qty ,
                        weighbridge  ,
                        first_weight ,
                        second_weight ,
                        bag_no ,
                        tare_weight ,
                        stack_empty ,
                        price_unit ,
                        price_currency ,
                        gross_weight ,
                        product_qty ,
                        production_id 
                        --material_id    
                    
                FROM public.stock_move') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                                                
                        picking_id integer,
                        --move_id integer,
                        company_id integer ,
                        product_id integer,
                        product_uom integer ,
                        --package_id integer,
                       -- package_level_id integer,                        
                        --result_package_id integer,
                        --owner_id integer,
                        location_id integer ,
                        location_dest_id integer ,
                        --product_category_name character varying ,
                        --lot_name character varying ,
                        state character varying ,
                        name character varying ,
                        --description_picking text ,
                        --reserved_qty numeric,
                        --reserved_uom_qty numeric ,
                        --qty_done numeric,
                        date timestamp without time zone ,
                        --workorder_id integer,
                        --production_id integer,
                        stack_id integer,
                        zone_id integer,
                        warehouse_id integer,
                        currency_id integer,
                        partner_id integer,
                        packing_id integer,
                        weight_scale_id character varying ,
                        init_qty numeric,
                        weighbridge numeric ,
                        first_weight numeric,
                        second_weight numeric,
                        bag_no numeric,
                        tare_weight numeric,
                        stack_empty boolean,
                        price_unit double precision,
                        price_currency double precision,
                        gross_weight double precision,
                        product_qty numeric,
                        production_id integer
                        --material_id integer
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('stock_move_line_id_seq', (select max(id) + 1 from  stock_move_line));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_stock_move(self):
        sql ='''
        INSERT INTO 
            stock_move 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                
                sequence ,
                company_id  ,
                product_id  ,
                product_uom  ,
                location_id  ,
                location_dest_id  ,
                partner_id ,
                picking_id ,
                --group_id ,
                rule_id ,
                picking_type_id ,
                origin_returned_move_id ,
                restrict_partner_id ,
                warehouse_id ,
                --package_level_id ,
                --next_serial_count ,
                --orderpoint_id ,
                --product_packaging_id ,
                name   ,
                priority  ,
                state  ,
                origin  ,
                procure_method   ,
                --reference  ,
                --next_serial  ,
                --reservation_date ,
                --description_picking  ,
                product_qty ,
                product_uom_qty  ,
                quantity_done ,
                --scrapped ,
                --propagate_cancel ,
                --is_inventory ,
                --additional ,
                date  ,
                --date_deadline ,
                --delay_alert_date ,
                --price_unit ,
                --analytic_account_line_id ,
                --to_refund ,
                --is_done ,
                --unit_factor ,
                --created_production_id ,
                --production_id ,
                --raw_material_production_id ,
                --unbuild_id ,
                --consume_unbuild_id ,
                --operation_id ,
                --workorder_id ,
                --bom_line_id ,
                --byproduct_id ,
                --order_finished_lot_id ,
                --cost_share ,
                --manual_consumption ,
                --stack_id ,
                zone_id ,
                packing_id ,
                weight_scale_id  ,
                init_qty ,
                weighbridge  ,
                first_weight ,
                second_weight ,
                bag_no ,
                tare_weight ,
                stack_empty ,
                gross_weight   
            )        
        
        SELECT 
                
            id, 
            create_date, create_uid, 
            write_date,  write_uid, 
                sequence ,
                company_id  ,
                product_id  ,
                product_uom  ,
                location_id  ,
                location_dest_id  ,
                partner_id ,
                picking_id ,
                --group_id ,
                rule_id ,
                picking_type_id ,
                origin_returned_move_id ,
                restrict_partner_id ,
                warehouse_id ,
                --package_level_id ,
                --next_serial_count ,
                --orderpoint_id ,
                --product_packaging_id ,
                name   ,
                priority  ,
                state  ,
                origin  ,
                procure_method   ,
                --reference  ,
                --next_serial  ,
                --reservation_date ,
                --description_picking  ,
                product_qty ,
                product_uom_qty  ,
                product_uom_qty as quantity_done ,
                --scrapped ,
                --propagate_cancel ,
                --is_inventory ,
                --additional ,
                date  ,
                --date_deadline ,
                --delay_alert_date ,
                --price_unit ,
                --analytic_account_line_id ,
                --to_refund ,
                --is_done ,
                --unit_factor ,
                --created_production_id ,
                --production_id ,
                --raw_material_production_id ,
                --unbuild_id ,
                --consume_unbuild_id ,
                --operation_id ,
                --workorder_id ,
                --bom_line_id ,
                --byproduct_id ,
                --order_finished_lot_id ,
                --cost_share ,
                --manual_consumption ,
                --stack_id ,
                zone_id ,
                packing_id ,
                weight_scale_id  ,
                init_qty ,
                weighbridge  ,
                first_weight ,
                second_weight ,
                bag_no ,
                tare_weight ,
                stack_empty ,
                gross_weight  
            
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date,  create_uid, 
                    write_date, write_uid, 
                    
                        sequence ,
                        company_id  ,
                        product_id  ,
                        product_uom  ,
                        location_id  ,
                        location_dest_id  ,
                        partner_id ,
                        picking_id ,
                        group_id ,
                        rule_id ,
                        picking_type_id ,
                        origin_returned_move_id ,
                        restrict_partner_id ,
                        warehouse_id ,
                        --package_level_id ,
                        --next_serial_count ,
                        --orderpoint_id ,
                        --product_packaging_id ,
                        name   ,
                        priority  ,
                        state  ,
                        origin  ,
                        procure_method   ,
                        --reference  ,
                        --next_serial  ,
                        --reservation_date ,
                        --description_picking  ,
                        product_qty ,
                        product_uom_qty  ,
                        --quantity_done ,
                        --scrapped ,
                        --propagate_cancel ,
                        --is_inventory ,
                        --additional ,
                        date  ,
                        --date_deadline ,
                        --delay_alert_date ,
                        --price_unit ,
                        --analytic_account_line_id ,
                        --to_refund ,
                        --is_done ,
                        --unit_factor ,
                        --created_production_id ,
                        --production_id ,
                        --raw_material_production_id ,
                        --unbuild_id ,
                        --consume_unbuild_id ,
                        --operation_id ,
                        --workorder_id ,
                        --bom_line_id ,
                        --byproduct_id ,
                        --order_finished_lot_id ,
                        --cost_share ,
                        --manual_consumption ,
                        stack_id ,
                        zone_id ,
                        packing_id ,
                        weight_scale_id  ,
                        init_qty ,
                        weighbridge  ,
                        first_weight ,
                        second_weight ,
                        bag_no ,
                        tare_weight ,
                        stack_empty ,
                        gross_weight  
                    
                FROM public.stock_move') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,  
                                                  
                        sequence integer,
                        company_id integer ,
                        product_id integer ,
                        product_uom integer ,
                        location_id integer ,
                        location_dest_id integer ,
                        partner_id integer,
                        picking_id integer,
                        group_id integer,
                        rule_id integer,
                        picking_type_id integer,
                        origin_returned_move_id integer,
                        restrict_partner_id integer,
                        warehouse_id integer,
                        --package_level_id integer,
                        --next_serial_count integer,
                        --orderpoint_id integer,
                        --product_packaging_id integer,
                        name character varying  ,
                        priority character varying ,
                        state character varying ,
                        origin character varying ,
                        procure_method character varying  ,
                        --reference character varying ,
                        --next_serial character varying ,
                        --reservation_date date,
                        --description_picking text ,
                        product_qty numeric,
                        product_uom_qty numeric ,
                        --quantity_done numeric,
                        --scrapped boolean,
                        --propagate_cancel boolean,
                        --is_inventory boolean,
                        --additional boolean,
                        date timestamp without time zone ,
                        --date_deadline timestamp without time zone,
                        --delay_alert_date timestamp without time zone,
                        --price_unit double precision,
                        --analytic_account_line_id integer,
                        --to_refund boolean,
                        --is_done boolean,
                        --unit_factor double precision,
                        --created_production_id integer,
                        --production_id integer,
                        --raw_material_production_id integer,
                        --unbuild_id integer,
                        --consume_unbuild_id integer,
                        --operation_id integer,
                        --workorder_id integer,
                        --bom_line_id integer,
                        --byproduct_id integer,
                        --order_finished_lot_id integer,
                        --cost_share numeric,
                        --manual_consumption boolean,
                        stack_id integer,
                        zone_id integer,
                        packing_id integer,
                        weight_scale_id character varying ,
                        init_qty numeric,
                        weighbridge numeric ,
                        first_weight numeric,
                        second_weight numeric,
                        bag_no numeric,
                        tare_weight numeric,
                        stack_empty boolean,
                        gross_weight double precision  
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('stock_move_id_seq', (select max(id) + 1 from  stock_move));
        ''')   
        
    
    def sys_ned_security_gate_queue(self):
        sql ='''
        INSERT INTO 
            ned_security_gate_queue 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                supplier_id  ,
                    picking_type_id  ,
                    certificate_id ,
                    estimated_bags ,
                    user_approve ,
                    parking_order ,
                    security_id ,
                    warehouse_id  ,
                    company_id ,
                    link_fot_id ,
                    districts_id  ,
                    change_warehouse_id ,
                    name   ,
                    license_plate   ,
                    coffee_origins  ,
                    driver_name  ,
                    additional_reference  ,
                    state  ,
                    odor  ,
                    type_transfer  ,
                    date_approve ,
                    remarks  ,
                    approx_quantity  ,
                    sample_weight ,
                    bb_sample_weight ,
                    mc_degree ,
                    mc ,
                    fm_gram ,
                    fm ,
                    black_gram ,
                    black ,
                    broken_gram ,
                    broken ,
                    brown_gram ,
                    brown ,
                    mold_gram ,
                    mold ,
                    cherry ,
                    excelsa_gram ,
                    excelsa ,
                    screen20_gram ,
                    screen20 ,
                    screen19_gram ,
                    screen19 ,
                    screen18_gram ,
                    screen18 ,
                    screen16_gram ,
                    screen16 ,
                    screen13_gram ,
                    screen13 ,
                    greatersc12_gram ,
                    belowsc12_gram ,
                    burned_gram ,
                    burned ,
                    insect_gram ,
                    insect ,
                    immature_gram ,
                    immature ,
                    arrivial_time ,
                    time_in ,
                    time_out ,
                    date ,
                    date_reject ,
                    cherry_gram ,
                    greatersc12 ,
                    belowsc12 ,
                    aprroved_by_quality
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    
                    supplier_id  ,
                    picking_type_id  ,
                    certificate_id ,
                    estimated_bags ,
                    user_approve ,
                    parking_order ,
                    security_id ,
                    warehouse_id  ,
                    company_id ,
                    link_fot_id ,
                    districts_id  ,
                    change_warehouse_id ,
                    name   ,
                    license_plate   ,
                    coffee_origins  ,
                    driver_name  ,
                    additional_reference  ,
                    state  ,
                    odor  ,
                    type_transfer  ,
                    date_approve ,
                    remarks  ,
                    approx_quantity  ,
                    sample_weight ,
                    bb_sample_weight ,
                    mc_degree ,
                    mc ,
                    fm_gram ,
                    fm ,
                    black_gram ,
                    black ,
                    broken_gram ,
                    broken ,
                    brown_gram ,
                    brown ,
                    mold_gram ,
                    mold ,
                    cherry ,
                    excelsa_gram ,
                    excelsa ,
                    screen20_gram ,
                    screen20 ,
                    screen19_gram ,
                    screen19 ,
                    screen18_gram ,
                    screen18 ,
                    screen16_gram ,
                    screen16 ,
                    screen13_gram ,
                    screen13 ,
                    greatersc12_gram ,
                    belowsc12_gram ,
                    burned_gram ,
                    burned ,
                    insect_gram ,
                    insect ,
                    immature_gram ,
                    immature ,
                    arrivial_time ,
                    time_in ,
                    time_out ,
                    date ,
                    date_reject ,
                    cherry_gram ,
                    greatersc12 ,
                    belowsc12 ,
                    aprroved_by_quality
                    
                    
                FROM public.ned_security_gate_queue') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,            
                                        
                        supplier_id integer ,
                        picking_type_id integer ,
                        certificate_id integer,
                        estimated_bags integer,
                        user_approve integer,
                        parking_order integer,
                        security_id integer,
                        warehouse_id integer ,
                        company_id integer,
                        link_fot_id integer,
                        districts_id integer ,
                        change_warehouse_id integer,
                        name character varying  ,
                        license_plate character varying  ,
                        coffee_origins character varying ,
                        driver_name character varying ,
                        additional_reference character varying ,
                        state character varying ,
                        odor character varying ,
                        type_transfer character varying ,
                        date_approve date,
                        remarks text ,
                        approx_quantity numeric ,
                        sample_weight numeric,
                        bb_sample_weight numeric,
                        mc_degree numeric,
                        mc numeric,
                        fm_gram numeric,
                        fm numeric,
                        black_gram numeric,
                        black numeric,
                        broken_gram numeric,
                        broken numeric,
                        brown_gram numeric,
                        brown numeric,
                        mold_gram numeric,
                        mold numeric,
                        cherry numeric,
                        excelsa_gram numeric,
                        excelsa numeric,
                        screen20_gram numeric,
                        screen20 numeric,
                        screen19_gram numeric,
                        screen19 numeric,
                        screen18_gram numeric,
                        screen18 numeric,
                        screen16_gram numeric,
                        screen16 numeric,
                        screen13_gram numeric,
                        screen13 numeric,
                        greatersc12_gram numeric,
                        belowsc12_gram numeric,
                        burned_gram numeric,
                        burned numeric,
                        insect_gram numeric,
                        insect numeric,
                        immature_gram numeric,
                        immature numeric,
                        arrivial_time timestamp without time zone,
                        time_in timestamp without time zone,
                        time_out timestamp without time zone,
                        date timestamp without time zone,
                        date_reject timestamp without time zone,
                        cherry_gram double precision,
                        greatersc12 double precision,
                        belowsc12 double precision,
                        aprroved_by_quality double precision
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('ned_security_gate_queue_id_seq', (select max(id) + 1 from  ned_security_gate_queue));
        ''')   
        
        return
        
    def sys_stock_picking(self):
        sql ='''
        INSERT INTO 
            stock_picking 
            (
                id,
                create_date,create_uid,
                write_date, write_uid, 
                
                backorder_id ,
                --group_id ,
                location_id  ,
                location_dest_id  ,
                picking_type_id  ,
                partner_id ,
                company_id ,
                --user_id ,
                owner_id ,
                name  ,
                origin  ,
                move_type   ,
                state  ,
                priority  ,
                note  ,
                --has_deadline_issue ,
                printed ,
                --is_locked ,
                --immediate_transfer ,
                --scheduled_date ,
                --date_deadline ,
                date ,
                date_done ,
                purchase_contract_id ,
                --allocation_id ,
                allocated_qty ,
                qty_available ,
                allocated ,
                warehouse_id ,
                categ_id ,
                sale_contract_id ,
                delivery_id ,
                pcontract_id ,
                grn_id ,
                delivery_place_id ,
                lot_id ,
                zone_id ,
                packing_id ,
                certificate_id ,
                districts_id ,
                to_picking_type_id ,
                production_id ,
                trucking_id ,
                request_materials_id ,
                cert_type  ,
                vehicle_no  ,
                pledg  ,
                weight_scale_id  ,
                total_qty ,
                total_init_qty ,
                total_weighbridge_qty ,
                total_bag ,
                is_quota_temp ,
                transfer ,
                change_product_id ,
                approve_id ,
                kcs_criterions_id ,
                contract_no  ,
                state_kcs  ,
                fix_done ,
                use_sample ,
                special ,
                date_sent ,
                date_kcs ,
                security_gate_id ,
                link_backorder_id ,
                transfer_picking_type ,
                check_link_backorder ,
                total_print_grn ,
                barcode,
                scheduled_date  ,
                product_id                 
            )        
        
        SELECT 
            id, 
            create_date, create_uid, 
            write_date,  write_uid, 
            
            backorder_id ,
            --group_id ,
            location_id  ,
            location_dest_id  ,
            picking_type_id  ,
            partner_id ,
            company_id ,
            --user_id ,
            owner_id ,
            name  ,
            origin  ,
            move_type   ,
            state  ,
            priority  ,
            note  ,
            --has_deadline_issue ,
            printed ,
            --is_locked ,
            --immediate_transfer ,
            --scheduled_date ,
            --date_deadline ,
            date ,
            date_done ,
            purchase_contract_id ,
            --allocation_id ,
            allocated_qty ,
            qty_available ,
            allocated ,
            warehouse_id ,
            categ_id ,
            sale_contract_id ,
            delivery_id ,
            pcontract_id ,
            grn_id ,
            delivery_place_id ,
            stack_id as lot_id ,
            zone_id ,
            packing_id ,
            certificate_id ,
            districts_id ,
            to_picking_type_id ,
            production_id ,
            trucking_id ,
            request_materials_id ,
            cert_type  ,
            vehicle_no  ,
            pledg  ,
            weight_scale_id  ,
            total_qty ,
            total_init_qty ,
            total_weighbridge_qty ,
            total_bag ,
            is_quota_temp ,
            transfer ,
            change_product_id ,
            approve_id ,
            kcs_criterions_id ,
            contract_no  ,
            state_kcs  ,
            fix_done ,
            use_sample ,
            special ,
            date_sent ,
            date_kcs ,
            security_gate_id ,
            link_backorder_id ,
            transfer_picking_type ,
            check_link_backorder ,
            total_print_grn ,
            barcode,
            min_date,
            product_id
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                        
                    backorder_id ,
                        group_id ,
                        location_id  ,
                        location_dest_id  ,
                        picking_type_id  ,
                        partner_id ,
                        company_id ,
                        --user_id ,
                        owner_id ,
                        name  ,
                        origin  ,
                        move_type   ,
                        state  ,
                        priority  ,
                        note  ,
                        --has_deadline_issue ,
                        printed ,
                        --is_locked ,
                        --immediate_transfer ,
                        --scheduled_date ,
                        --date_deadline ,
                        date ,
                        date_done ,
                        purchase_contract_id ,
                        allocation_id ,
                        allocated_qty ,
                        qty_available ,
                        allocated ,
                        warehouse_id ,
                        categ_id ,
                        sale_contract_id ,
                        delivery_id ,
                        pcontract_id ,
                        grn_id ,
                        delivery_place_id ,
                        stack_id ,
                        zone_id ,
                        packing_id ,
                        certificate_id ,
                        districts_id ,
                        to_picking_type_id ,
                        production_id ,
                        trucking_id ,
                        request_materials_id ,
                        cert_type  ,
                        vehicle_no  ,
                        pledg  ,
                        weight_scale_id  ,
                        total_qty ,
                        total_init_qty ,
                        total_weighbridge_qty ,
                        total_bag ,
                        is_quota_temp ,
                        transfer ,
                        change_product_id ,
                        approve_id ,
                        kcs_criterions_id ,
                        contract_no  ,
                        state_kcs  ,
                        fix_done ,
                        use_sample ,
                        special ,
                        date_sent ,
                        date_kcs ,
                        security_gate_id ,
                        link_backorder_id ,
                        transfer_picking_type ,
                        check_link_backorder ,
                        total_print_grn ,
                        barcode,
                        min_date,
                        product_id
                    
                FROM public.stock_picking') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,   
                        
                        backorder_id integer,
                        group_id integer,
                        location_id integer ,
                        location_dest_id integer ,
                        picking_type_id integer ,
                        partner_id integer,
                        company_id integer,
                        --user_id integer,
                        owner_id integer,
                        name character varying ,
                        origin character varying ,
                        move_type character varying  ,
                        state character varying ,
                        priority character varying ,
                        note text ,
                        --has_deadline_issue boolean,
                        printed boolean,
                        --is_locked boolean,
                        --immediate_transfer boolean,
                        --scheduled_date timestamp without time zone,
                        --date_deadline timestamp without time zone,
                        date timestamp without time zone,
                        date_done timestamp without time zone,
                        purchase_contract_id integer,
                        allocation_id integer,
                        allocated_qty numeric,
                        qty_available numeric,
                        allocated boolean,
                        warehouse_id integer,
                        categ_id integer,
                        sale_contract_id integer,
                        delivery_id integer,
                        pcontract_id integer,
                        grn_id integer,
                        delivery_place_id integer,
                        stack_id integer,
                        zone_id integer,
                        packing_id integer,
                        certificate_id integer,
                        districts_id integer,
                        to_picking_type_id integer,
                        production_id integer,
                        trucking_id integer,
                        request_materials_id integer,
                        cert_type character varying ,
                        vehicle_no character varying(128) ,
                        pledg character varying(128) ,
                        weight_scale_id character varying ,
                        total_qty numeric,
                        total_init_qty numeric,
                        total_weighbridge_qty numeric,
                        total_bag numeric,
                        is_quota_temp boolean,
                        transfer boolean,
                        change_product_id integer,
                        approve_id integer,
                        kcs_criterions_id integer,
                        contract_no character varying ,
                        state_kcs character varying ,
                        fix_done boolean,
                        use_sample boolean,
                        special boolean,
                        date_sent timestamp without time zone,
                        date_kcs timestamp without time zone,
                        security_gate_id integer,
                        link_backorder_id integer,
                        transfer_picking_type boolean,
                        check_link_backorder boolean,
                        total_print_grn integer,
                        barcode character varying,
                        min_date timestamp without time zone,
                        product_id integer         
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('stock_picking_id_seq', (select max(id) + 1 from  stock_picking));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_request_materials(self):
        sql ='''
        INSERT INTO 
            request_materials 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,   
                production_id ,
                warehouse_id ,
                request_user_id ,
                name   ,
                origin   ,
                state   ,
                type   ,
                request_date ,
                notes 
            )        
        
        SELECT 
            *
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    
                    production_id ,
                    warehouse_id ,
                    request_user_id  ,
                    name   ,
                    origin   ,
                    state   ,
                    type   ,
                    request_date ,
                    notes  
                    
                FROM public.request_materials') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,   
                                             
                    production_id integer,
                    warehouse_id integer,
                    request_user_id integer,
                    name character varying ,
                    origin character varying ,
                    state character varying ,
                    type character varying ,
                    request_date date,
                    notes text 
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('request_materials_id_seq', (select max(id) + 1 from  request_materials));
        ''') 
        
    def sys_request_materials_line(self):
        sql ='''
        INSERT INTO 
            request_materials_line 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,   
                product_id ,
                product_uom ,
                request_id ,
                stack_id ,
                state   ,
                product_qty ,
                stack_empty 
            )        
        
        SELECT 
            *
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    
                    product_id ,
                    product_uom ,
                    request_id ,
                    stack_id ,
                    state   ,
                    product_qty ,
                    stack_empty 
                    
                FROM public.request_materials_line') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,   
                                             
                    product_id integer,
                    product_uom integer,
                    request_id integer,
                    stack_id integer,
                    state character varying ,
                    product_qty numeric,
                    stack_empty boolean
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('request_materials_line_id_seq', (select max(id) + 1 from  request_materials_line));
        ''')   
    
    
    
    
    
    
