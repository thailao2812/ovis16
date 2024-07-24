from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    
    def sys_stock_master_data_run(self):
        self.env.cr.execute('''
            update res_company set internal_transit_location_id = null;
            delete from stock_rule;
            delete from stock_warehouse;
            delete from stock_location;
            delete from stock_picking_type;
        
            delete from stock_stack_transfer;
            delete from stock_storage_condition;
            delete from stock_lot;
            delete from stock_zone;
            delete from stock_rule;
            delete from x_external_warehouse;
        ''')
        
        self.sys_stock_picking_type()
        self.sys_stock_location()
        self.fix_path_location()
        self.sys_stock_warehouse()
        self.sys_stock_zone()
        
        self.sys_stock_storage_condition()
        self.sys_x_external_warehouse()
        self.sys_update_warehouse_to_picknig_type()
        self.compute_ir_seq_picking_type()
    
    
    def compute_ir_seq_picking_type(self):
        for p_type in self.env['stock.picking.type'].search([('sequence_id','=',False)]):
            sequence_id = False
            if p_type.warehouse_id:
                wh = self.env['stock.warehouse'].browse(p_type.warehouse_id.id)
                sequence_id = self.env['ir.sequence'].sudo().create({
                    'name': wh.name + ' ' + _('Sequence') + ' ' + p_type.sequence_code,
                    'prefix': wh.code + '/' + p_type.sequence_code + '/', 'padding': 5,
                    'company_id': wh.company_id.id,
                }).id
                p_type.sequence_id = sequence_id
            else:
                sequence_id = self.env['ir.sequence'].sudo().create({
                    'name': _('Sequence') + ' ' + p_type.sequence_code,
                    'prefix': p_type.sequence_code, 'padding': 5,
                    'company_id': self.env.company.id,
                }).id
                p_type.sequence_id = sequence_id
    
    
    def sys_update_warehouse_to_picknig_type(self):
        self.env.cr.execute('''
            UPDATE stock_picking_type set warehouse_id = xoo.warehouse_id
            from
            (
               
                SELECT 
                    *
                    FROM public.dblink
                                ('sucdendblink',
                                 'SELECT 
                                    id,
                                    warehouse_id
                                 
                                FROM public.stock_picking_type') 
                                AS DATA(
                                        id integer,
                                        warehouse_id integer                           
                                    )
                ) xoo
                where stock_picking_type.id = xoo.id
        ''')
    
    def sys_stock_master_data2_run(self):
        self.env.cr.execute('''
            delete from stock_lot;
            delete from stock_stack_transfer;
        ''')
        self.sys_stock_lot()
        # self.sys_stock_stack_transfer()
        
        
    def sys_x_external_warehouse(self):
        sql ='''
        INSERT INTO 
            x_external_warehouse 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                x_warehouse_id,
                    x_name
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    x_warehouse_id,
                    x_name
                FROM public.x_external_warehouse') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        x_warehouse_id integer,
                        x_name character varying
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('x_external_warehouse_id_seq', (select max(id) + 1 from  x_external_warehouse));
        ''')   
        
        return
    
    def sys_stock_storage_condition(self):
        sql ='''
        INSERT INTO 
            stock_storage_condition 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                zone_id  ,
                inspector_id ,
                name  ,
                time_string  ,
                temperature_unit  ,
                humidity  ,
                temperature  ,
                inspection_time 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    zone_id  ,
                    inspector_id ,
                    name  ,
                    time_string  ,
                    temperature_unit  ,
                    humidity  ,
                    temperature  ,
                    inspection_time 
                    
                FROM public.stock_storage_condition') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,  
                        zone_id integer ,
                        inspector_id integer,
                        name character varying ,
                        time_string character varying ,
                        temperature_unit character varying ,
                        humidity numeric ,
                        temperature numeric ,
                        inspection_time timestamp without time zone 
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('stock_storage_condition_id_seq', (select max(id) + 1 from  stock_storage_condition));
        ''')   
    
    def sys_stock_lot(self):
        sql ='''
        INSERT INTO 
            stock_lot 
            (
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                product_id  ,
                --product_uom_id ,
                company_id  ,
                name   ,
                code,
               -- ref  ,
                --note  ,
                province_id ,
                delivery_place_id ,
                p_contract_id ,
                zone_id ,
                districts_id ,
                warehouse_id ,
                shipper_id ,
                categ_id ,
                product_change_id ,
                stack_type  ,
                pledged  ,
                stack_on_hand  ,
                date ,
                bag_qty ,
                stack_qty ,
                init_qty ,
                out_qty ,
                remaining_qty ,
                lock ,
                active ,
                is_bonded ,
                stack_empty ,
                --production_id ,
                packing_id ,
                maize  ,
                sampler  ,
                
               
                
                --stone_count,
                --stick_count,
                --cast(stone_count as double precision),
                 --cast(stick_count as double precision),
                remarks  ,
                remarks_note  ,
                contract_no  ,
                mc ,
                fm ,
                black ,
                broken ,
                brown ,
                mold ,
                immature ,
                burn ,
                eaten ,
                cherry ,
                screen20 ,
                screen19 ,
                screen18 ,
                screen17 ,
                screen16 ,
                screen15 ,
                screen14 ,
                screen13 ,
                greatersc12 ,
                screen12 ,
                excelsa ,
                net_qty ,
                basis_qty ,
                gdn_basis ,
                gdn_net ,
                gip_net ,
                gip_basis 
                --init_invetory ,
                --init_invetory_qty ,
                --init_invetory_bags ,
                --reason_stack_empty
            )        
        
        SELECT 
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                product_id  ,
                --product_uom_id ,
                1 as company_id  ,
                name   ,
                code,
               -- ref  ,
                --note  ,
                province_id ,
                delivery_place_id ,
                p_contract_id ,
                zone_id ,
                districts_id ,
                warehouse_id ,
                shipper_id ,
                categ_id ,
                product_change_id ,
                stack_type  ,
                pledged  ,
                stack_on_hand  ,
                date date,
                bag_qty ,
                stack_qty ,
                init_qty ,
                out_qty ,
                remaining_qty ,
                lock ,
                active ,
                is_bonded ,
                stack_empty ,
                --production_id ,
                packing_id ,
                maize  ,
                sampler  ,
                --stone_count,
                --stick_count,
                --cast(stone_count as double precision),
                 --cast(stick_count as double precision),
                remarks  ,
                remarks_note  ,
                contract_no  ,
                mc ,
                fm ,
                black ,
                broken ,
                brown ,
                mold ,
                immature ,
                burn ,
                eaten ,
                cherry ,
                screen20 ,
                screen19 ,
                screen18 ,
                screen17 ,
                screen16 ,
                screen15 ,
                screen14 ,
                screen13 ,
                greatersc12 ,
                screen12 ,
                excelsa ,
                net_qty ,
                basis_qty ,
                gdn_basis ,
                gdn_net ,
                gip_net ,
                gip_basis 
                --init_invetory ,
                --init_invetory_qty ,
                --init_invetory_bags ,
                --reason_stack_empty
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    COALESCE(product_id,1399) as product_id  ,
                    --product_uom_id ,
                    --company_id  ,
                    name   ,
                    code,
                   -- ref  ,
                    --note  ,
                    province_id ,
                    delivery_place_id ,
                    p_contract_id ,
                    zone_id ,
                    districts_id ,
                    warehouse_id ,
                    shipper_id ,
                    categ_id ,
                    product_change_id ,
                    stack_type  ,
                    pledged  ,
                    stack_on_hand  ,
                    date date,
                    bag_qty ,
                    stack_qty ,
                    init_qty ,
                    out_qty ,
                    remaining_qty ,
                    lock ,
                    active ,
                    is_bonded ,
                    stack_empty ,
                    --production_id ,
                    packing_id ,
                    maize  ,
                    sampler  ,
                    stone_count ,
                    stick_count ,
                    remarks  ,
                    remarks_note  ,
                    contract_no  ,
                    mc ,
                    fm ,
                    black ,
                    broken ,
                    brown ,
                    mold ,
                    immature ,
                    burn ,
                    eaten ,
                    cherry ,
                    screen20 ,
                    screen19 ,
                    screen18 ,
                    screen17 ,
                    screen16 ,
                    screen15 ,
                    screen14 ,
                    screen13 ,
                    greatersc12 ,
                    screen12 ,
                    excelsa ,
                    net_qty ,
                    basis_qty ,
                    gdn_basis ,
                    gdn_net ,
                    gip_net ,
                    gip_basis 
                    --init_invetory ,
                    --init_invetory_qty ,
                    --init_invetory_bags ,
                    --reason_stack_empty
                 
                FROM public.stock_stack') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        product_id integer ,
                        --product_uom_id integer,
                        --company_id integer ,
                        name character varying  ,
                        code character varying  ,
                        --ref character varying ,
                        --note text ,
                        province_id integer,
                        delivery_place_id integer,
                        p_contract_id integer,
                        zone_id integer,
                        districts_id integer,
                        warehouse_id integer,
                        shipper_id integer,
                        categ_id integer,
                        product_change_id integer,
                        stack_type character varying ,
                        pledged character varying ,
                        stack_on_hand character varying ,
                        date date,
                        bag_qty numeric,
                        stack_qty numeric,
                        init_qty numeric,
                        out_qty numeric,
                        remaining_qty numeric,
                        lock boolean,
                        active boolean,
                        is_bonded boolean,
                        stack_empty boolean,
                       -- production_id integer,
                        packing_id integer,
                        maize character varying ,
                        sampler character varying ,
                        stone_count character varying,
                        stick_count character varying,
                        remarks character varying ,
                        remarks_note character varying ,
                        contract_no character varying ,
                        mc numeric,
                        fm numeric,
                        black numeric,
                        broken numeric,
                        brown numeric,
                        mold numeric,
                        immature numeric,
                        burn numeric,
                        eaten numeric,
                        cherry numeric,
                        screen20 numeric,
                        screen19 numeric,
                        screen18 numeric,
                        screen17 numeric,
                        screen16 numeric,
                        screen15 numeric,
                        screen14 numeric,
                        screen13 numeric,
                        greatersc12 numeric,
                        screen12 numeric,
                        excelsa numeric,
                        net_qty numeric,
                        basis_qty numeric,
                        gdn_basis numeric,
                        gdn_net numeric,
                        gip_net numeric,
                        gip_basis numeric
                        --init_invetory boolean,
                        --init_invetory_qty double precision,
                        --init_invetory_bags double precision,
                        --reason_stack_empty text
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('stock_lot_id_seq', (select max(id) + 1 from  stock_lot));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_stock_stack_transfer(self):
        sql ='''
        INSERT INTO 
            stock_stack_transfer 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                from_zone_id ,
                to_zone_id ,
                stack_id ,
                user_approve_id ,
                user_responsible_id ,
                name  ,
                state  ,
                date_order ,
                date_approve ,
                note  ,
                net_weight ,
                no_of_bag     
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    from_zone_id ,
                    to_zone_id ,
                    stack_id ,
                    user_approve_id ,
                    user_responsible_id ,
                    name  ,
                    state  ,
                    date_order ,
                    date_approve ,
                    note  ,
                    net_weight ,
                    no_of_bag     
                    
                FROM public.stock_stack_transfer') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        from_zone_id integer,
                        to_zone_id integer,
                        stack_id integer,
                        user_approve_id integer,
                        user_responsible_id integer,
                        name character varying(128) ,
                        state character varying ,
                        date_order date,
                        date_approve date,
                        note text ,
                        net_weight double precision,
                        no_of_bag double precision 
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('stock_stack_transfer_id_seq', (select max(id) + 1 from  stock_stack_transfer));
        ''')
      
    def sys_stock_warehouse(self):
        sql ='''
        INSERT INTO 
            stock_warehouse 
            (
                id,
                create_date,create_uid,
                write_date, write_uid, 
                company_id ,                    
                partner_id ,
                view_location_id ,
                lot_stock_id ,
                wh_input_stock_loc_id ,
                wh_qc_stock_loc_id ,
                wh_output_stock_loc_id ,
                wh_pack_stock_loc_id ,
                --mto_pull_id ,
                pick_type_id ,
                pack_type_id ,
                out_type_id ,
                in_type_id ,
                int_type_id ,
                --return_type_id ,
                --crossdock_route_id ,
                --reception_route_id ,
                --delivery_route_id ,
                --sequence ,
                name    ,
                code   ,
                reception_steps   ,
                delivery_steps   ,
                --active ,
                --manufacture_pull_id ,
                --manufacture_mto_pull_id ,
                --pbm_mto_pull_id ,
                --sam_rule_id ,
                --manu_type_id ,
                --pbm_type_id ,
                --sam_type_id ,
                --pbm_route_id ,
                --pbm_loc_id ,
                --sam_loc_id ,
                manufacture_steps ,
                --manufacture_to_resupply ,
                wh_raw_material_loc_id ,
                wh_finished_good_loc_id ,
                wh_production_loc_id ,
                production_in_type_id ,
                production_out_type_id ,
                return_customer_type_id ,
                return_supplier_type_id ,
                other_location_loc_id ,
                wh_npe_id ,
                wh_nvp_id ,
                production_out_type_consu_id ,
                transfer_in_id ,
                transfer_out_id ,
                out_type_local_id ,
                --account_analytic_id ,
                x_is_bonded ,
                active,
                sync_id
                --x_auto_done ,
                --adj_type_id 
            )        
        
        SELECT 
            id, 
                create_date, create_uid, 
                write_date, write_uid, 
                company_id ,                    
                partner_id ,
                view_location_id ,
                lot_stock_id ,
                wh_input_stock_loc_id ,
                wh_qc_stock_loc_id ,
                wh_output_stock_loc_id ,
                wh_pack_stock_loc_id ,
                --mto_pull_id ,
                pick_type_id ,
                pack_type_id ,
                out_type_id ,
                in_type_id ,
                int_type_id ,
                --return_type_id ,
                --crossdock_route_id ,
                --reception_route_id ,
                --delivery_route_id ,
                --sequence ,
                name    ,
                code   ,
                reception_steps   ,
                delivery_steps   ,
                --active ,
                --manufacture_pull_id ,
                --manufacture_mto_pull_id ,
                --pbm_mto_pull_id ,
                --sam_rule_id ,
                --manu_type_id ,
                --pbm_type_id ,
                --sam_type_id ,
                --pbm_route_id ,
                --pbm_loc_id ,
                --sam_loc_id ,
                'mrp_one_step' as manufacture_steps ,
                --manufacture_to_resupply ,
                wh_raw_material_loc_id ,
                wh_finished_good_loc_id ,
                wh_production_loc_id ,
                production_in_type_id ,
                production_out_type_id ,
                return_customer_type_id ,
                return_supplier_type_id ,
                other_location_loc_id ,
                wh_npe_id ,
                wh_nvp_id ,
                production_out_type_consu_id ,
                transfer_in_id ,
                transfer_out_id ,
                out_type_local_id ,
                --account_analytic_id ,
                x_is_bonded ,
                True as active,
                sync_id
                --x_auto_done ,
                --adj_type_id 
                
            FROM public.dblink
            ('sucdendblink',
             'SELECT 
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                company_id ,                    
                partner_id ,
                view_location_id ,
                lot_stock_id ,
                wh_input_stock_loc_id ,
                wh_qc_stock_loc_id ,
                wh_output_stock_loc_id ,
                wh_pack_stock_loc_id ,
                mto_pull_id ,
                pick_type_id ,
                pack_type_id ,
                out_type_id ,
                in_type_id ,
                int_type_id ,
                --return_type_id ,
                crossdock_route_id ,
                reception_route_id ,
                delivery_route_id ,
                --sequence ,
                name    ,
                code   ,
                reception_steps   ,
                delivery_steps   ,
                --active ,
                manufacture_pull_id ,
                --manufacture_mto_pull_id ,
                --pbm_mto_pull_id ,
                --sam_rule_id ,
                --manu_type_id ,
                --pbm_type_id ,
                --sam_type_id ,
                --pbm_route_id ,
                --pbm_loc_id ,
                --sam_loc_id ,
                --manufacture_steps ,
                --manufacture_to_resupply ,
                wh_raw_material_loc_id ,
                wh_finished_good_loc_id ,
                wh_production_loc_id ,
                production_in_type_id ,
                production_out_type_id ,
                return_customer_type_id ,
                return_supplier_type_id ,
                other_location_loc_id ,
                wh_npe_id ,
                wh_nvp_id ,
                production_out_type_consu_id ,
                transfer_in_id ,
                transfer_out_id ,
                out_type_local_id ,
                account_analytic_id ,
                x_is_bonded,
                sync_id
                
                --x_auto_done ,
                --adj_type_id 
                
            FROM public.stock_warehouse') 
            AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,
                    company_id integer ,                    
                    partner_id integer,
                    view_location_id integer ,
                    lot_stock_id integer ,
                    wh_input_stock_loc_id integer,
                    wh_qc_stock_loc_id integer,
                    wh_output_stock_loc_id integer,
                    wh_pack_stock_loc_id integer,
                    mto_pull_id integer,
                    pick_type_id integer,
                    pack_type_id integer,
                    out_type_id integer,
                    in_type_id integer,
                    int_type_id integer,
                    --return_type_id integer,
                    crossdock_route_id integer,
                    reception_route_id integer,
                    delivery_route_id integer,
                    --sequence integer,
                    name character varying  ,
                    code character varying,
                    reception_steps character varying ,
                    delivery_steps character varying ,
                    --active boolean,
                    manufacture_pull_id integer,
                    --manufacture_mto_pull_id integer,
                    --pbm_mto_pull_id integer,
                    --sam_rule_id integer,
                    --manu_type_id integer,
                    --pbm_type_id integer,
                    --sam_type_id integer,
                    --pbm_route_id integer,
                    --pbm_loc_id integer,
                    --sam_loc_id integer,
                    --manufacture_steps character varying ,
                    --manufacture_to_resupply boolean,
                    wh_raw_material_loc_id integer,
                    wh_finished_good_loc_id integer,
                    wh_production_loc_id integer,
                    production_in_type_id integer,
                    production_out_type_id integer,
                    return_customer_type_id integer,
                    return_supplier_type_id integer,
                    other_location_loc_id integer,
                    wh_npe_id integer,
                    wh_nvp_id integer,
                    production_out_type_consu_id integer,
                    transfer_in_id integer,
                    transfer_out_id integer,
                    out_type_local_id integer,
                    account_analytic_id integer,
                    x_is_bonded boolean,
                    sync_id integer
                    --x_auto_done boolean,
                    --adj_type_id integer 
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('stock_warehouse_id_seq', (select max(id) + 1 from  stock_warehouse));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def fix_path_location(self):
        self.env.cr.execute('''
            WITH RECURSIVE __parent_store_compute(id, parent_path) AS (
                SELECT row.id, concat(row.id, '/')
                FROM stock_location row
                WHERE row.location_id IS NULL
            UNION
                SELECT row.id, concat(comp.parent_path, row.id, '/')
                FROM stock_location row, __parent_store_compute comp
                WHERE row.location_id = comp.id
            )
            UPDATE stock_location row SET parent_path = comp.parent_path
            FROM __parent_store_compute comp
            WHERE row.id = comp.id
        ''')
   
    def sys_stock_location(self):
        sql ='''
        INSERT INTO 
            stock_location 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                location_id ,
                        posx ,
                        posy ,
                        posz ,
                        company_id ,
                        removal_strategy_id ,
                        --cyclic_inventory_frequency ,
                        --warehouse_id ,
                        --storage_category_id ,
                        name   ,
                        complete_name   ,
                        usage   ,
                        --parent_path   ,
                        barcode   ,
                        --last_inventory_date ,
                        --next_inventory_date ,
                        comment  ,
                        active ,
                        scrap_location ,
                        return_location ,
                        sync_id
                        --replenish_location ,                        
                        --valuation_in_account_id ,
                        --valuation_out_account_id 
            )        
        
        SELECT 
            id,
                create_date,create_uid,
                write_date, write_uid,                     
                location_id ,
                        posx ,
                        posy ,
                        posz ,
                        company_id ,
                        removal_strategy_id ,
                        --cyclic_inventory_frequency ,
                        --warehouse_id ,
                        --storage_category_id ,
                        name   ,
                        complete_name   ,
                        usage   ,
                        --parent_path   ,
                        barcode   ,
                        --last_inventory_date ,
                        --next_inventory_date ,
                        comment  ,
                        active ,
                        scrap_location ,
                        return_location ,
                        sync_id
                        --replenish_location ,                        
                        --valuation_in_account_id ,
                        --valuation_out_account_id 
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    location_id ,
                        posx ,
                        posy ,
                        posz ,
                        company_id ,
                        removal_strategy_id ,
                        --cyclic_inventory_frequency ,
                        warehouse_id ,
                        --storage_category_id ,
                        name   ,
                        complete_name   ,
                        usage   ,
                        --parent_path   ,
                        barcode   ,
                        --last_inventory_date ,
                        --next_inventory_date ,
                        comment  ,
                        active ,
                        scrap_location ,
                        return_location ,
                        --replenish_location ,                        
                        valuation_in_account_id ,
                        valuation_out_account_id ,
                        sync_id 
                 
                FROM public.stock_location') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        location_id integer,
                        posx integer,
                        posy integer,
                        posz integer,
                        company_id integer,
                        removal_strategy_id integer,
                        --cyclic_inventory_frequency integer,
                        warehouse_id integer,
                        --storage_category_id integer,
                        name character varying ,
                        complete_name character varying ,
                        usage character varying ,
                        --parent_path character varying ,
                        barcode character varying ,
                        --last_inventory_date date,
                        --next_inventory_date date,
                        comment text ,
                        active boolean,
                        scrap_location boolean,
                        return_location boolean,
                        --replenish_location boolean,
                        valuation_in_account_id integer,
                        valuation_out_account_id integer,
                        sync_id integer
            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('stock_location_id_seq', (select max(id) + 1 from  stock_location));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_stock_zone(self):
        sql ='''
        INSERT INTO 
            stock_zone 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                warehouse_id ,
                name  ,
                code ,
                description ,
                active 
                 
            )        
        
        SELECT 
            id,
            create_date,create_uid, 
            write_date, write_uid, 
            warehouse_id ,
            name  ,
            code ,
            description ,
            active 
             
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    warehouse_id ,
                    name  ,
                    code ,
                    description ,
                    active 
                     
                 
                FROM public.stock_zone') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        warehouse_id integer,
                        name character varying(128) ,
                        code character varying(128) ,
                        description character varying(128),
                        active boolean
            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('stock_zone_id_seq', (select max(id) + 1 from  stock_zone));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return

    def sys_stock_picking_type(self):
        sql ='''
        INSERT INTO 
            stock_picking_type 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                color ,
                    sequence ,
                    --sequence_id ,
                    --default_location_src_id ,
                    --default_location_dest_id ,
                    return_picking_type_id ,
                    --warehouse_id ,
                    --reservation_days_before ,
                    --reservation_days_before_priority ,
                    --company_id  ,
                    --sequence_code ,
                    code   ,
                    reservation_method   ,
                    --barcode   ,
                    create_backorder   ,
                    name,
                    show_entire_packs ,
                    active ,
                    use_create_lots ,
                    use_existing_lots ,
                    --print_label ,
                    --show_operations ,
                    --show_reserved ,
                    --auto_show_reception_report ,
                    --use_create_components_lots ,
                    --use_auto_consume_components_lots ,
                    transfer_picking_type_id ,
                    picking_type_npe_id ,
                    picking_type_nvp_id ,
                    operation   ,
                    is_service ,
                    is_product ,
                    is_materials ,
                    is_tools ,
                    is_consignment_agreement ,
                    dashboard_invisible ,
                    fob ,
                    kcs ,
                    deduct ,
                    kcs_approved ,
                    stack ,
                    company_id,
                    sequence_code,
                    sync_id
            )        
        
        SELECT 
            DATA.id, 
                    DATA.create_date, DATA.create_uid, 
                    DATA.write_date, DATA.write_uid, 
                    color ,
                    sequence ,
                    --sequence_id ,
                    --default_location_src_id ,
                    --default_location_dest_id ,
                    return_picking_type_id ,
                    --warehouse_id ,
                    --reservation_days_before ,
                    --reservation_days_before_priority ,
                    --company_id  ,
                    --sequence_code ,
                    code   ,
                    'at_confirm' as reservation_method   ,
                    --barcode   ,
                    'ask' as  create_backorder   ,
                    jsonb_build_object('en_US', name ) as name,
                    show_entire_packs ,
                    active ,
                    use_create_lots ,
                    use_existing_lots ,
                    --print_label ,
                    --show_operations ,
                    --show_reserved ,
                    --auto_show_reception_report ,
                    --use_create_components_lots ,
                    --use_auto_consume_components_lots ,
                    transfer_picking_type_id ,
                    picking_type_npe_id ,
                    picking_type_nvp_id ,
                    operation   ,
                    is_service ,
                    is_product ,
                    is_materials ,
                    is_tools ,
                    is_consignment_agreement ,
                    dashboard_invisible ,
                    fob ,
                    kcs ,
                    deduct ,
                    kcs_approved ,
                    stack ,
                     1 as company_id,
                    prefix,
                    sync_id
                 
                    
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    spt.id, 
                    spt.create_date, spt.create_uid, 
                    spt.write_date, spt.write_uid, 
                    color ,
                    sequence ,
                    sequence_id ,
                    default_location_src_id ,
                    default_location_dest_id ,
                    return_picking_type_id ,
                    warehouse_id ,
                    --reservation_days_before ,
                    --reservation_days_before_priority ,
                    --company_id  ,
                    --sequence_code ,
                    spt.code   ,
                    --reservation_method   ,
                    --barcode   ,
                    --create_backorder   ,
                    spt.name  ,
                    show_entire_packs ,
                    spt.active ,
                    use_create_lots ,
                    use_existing_lots ,
                    --print_label ,
                    --show_operations ,
                    --show_reserved ,
                    --auto_show_reception_report ,
                    --use_create_components_lots ,
                    --use_auto_consume_components_lots ,
                    transfer_picking_type_id ,
                    picking_type_npe_id ,
                    picking_type_nvp_id ,
                    operation   ,
                    is_service ,
                    is_product ,
                    is_materials ,
                    is_tools ,
                    is_consignment_agreement ,
                    dashboard_invisible ,
                    fob ,
                    kcs ,
                    deduct ,
                    kcs_approved ,
                    stack ,
                    i_seq.prefix,
                    spt.sync_id
                    
                 
                FROM public.stock_picking_type spt join ir_sequence i_seq on spt.sequence_id = i_seq.id') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        color integer,
                        sequence integer,
                        sequence_id integer,
                        default_location_src_id integer,
                        default_location_dest_id integer,
                        return_picking_type_id integer,
                        warehouse_id integer,
                        --reservation_days_before integer,
                        --reservation_days_before_priority integer,
                        --company_id integer ,
                        --sequence_code character varying,
                        code character varying ,
                        --reservation_method character varying ,
                        --barcode character varying ,
                        --create_backorder character varying ,
                        name character varying  ,
                        show_entire_packs boolean,
                        active boolean,
                        use_create_lots boolean,
                        use_existing_lots boolean,
                        --print_label boolean,
                        --show_operations boolean,
                        --show_reserved boolean,
                        --auto_show_reception_report boolean,
                        --use_create_components_lots boolean,
                        --use_auto_consume_components_lots boolean,
                        transfer_picking_type_id integer,
                        picking_type_npe_id integer,
                        picking_type_nvp_id integer,
                        operation character varying ,
                        is_service boolean,
                        is_product boolean,
                        is_materials boolean,
                        is_tools boolean,
                        is_consignment_agreement boolean,
                        dashboard_invisible boolean,
                        fob boolean,
                        kcs boolean,
                        deduct boolean,
                        kcs_approved boolean,
                        stack boolean,
                        prefix character varying,
                        sync_id integer
            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('stock_picking_type_id_seq', (select max(id) + 1 from  stock_picking_type));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
        
    