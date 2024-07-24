from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
# from pip._vendor.pygments.lexer import _inherit
DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    def sys_kcs1(self):
        self.env.cr.execute('''
            delete from kcs_criterions;
            delete from kcs_criterions_line;
            delete from kcs_criterions_mc;
            
            delete from kcs_criterions_mc;
            delete from degree_mc;
            delete from broken_standard;
            delete from brown_standard;
            delete from insect_bean;
            delete from mold_standard;
            delete from foreign_matter;
            delete from excelsa_standard;
            delete from over_screen12;
            delete from x_inspectors_kcs;
            
            alter table request_kcs_line disable trigger all;
            delete from request_kcs_line;
            alter table request_kcs_line enable trigger all;
            alter sequence request_kcs_line_id_seq minvalue 0 start with 1;
            SELECT setval('request_kcs_line_id_seq', 0);
            
            delete from kcs_rule_warehouse_rel;
            
            alter table pss_management disable trigger all;
            delete from pss_management;
            alter table pss_management enable trigger all;
            alter sequence pss_management_id_seq minvalue 0 start with 1;
            SELECT setval('pss_management_id_seq', 0);
            
            alter table fob_management disable trigger all;
            delete from fob_management;
            alter table fob_management enable trigger all;
            alter sequence fob_management_id_seq minvalue 0 start with 1;
            SELECT setval('fob_management_id_seq', 0);
            
            alter table fob_pss_management disable trigger all;
            delete from fob_pss_management;
            alter table fob_pss_management enable trigger all;
            alter sequence fob_pss_management_id_seq minvalue 0 start with 1;
            SELECT setval('fob_pss_management_id_seq', 0);
            
            
            delete from vessel_registration; 
            delete from restack_management;
            delete from kcs_glyphosate;
            
        ''')
        self.env.cr.commit()
        
        self.sys_kcs_criterions()
        self.sys_kcs_criterions_line()
        self.sys_kcs_criterions_mc()
        self.sys_degree_mc()
        self.sys_broken_standard()
        self.sys_brown_standard()
        self.sys_insect_bean()
        self.sys_mold_standard()
        self.sys_excelsa_standard()
        self.sys_foreign_matter()
        self.sys_over_screen12()
        self.sys_kcs_rule_warehouse_rel()
        
        self.sys_pss_management()
        self.sys_fob_pss_management()
        self.sys_vessel_registration()
        self.sys_restack_management()
        self.sys_kcs_glyphosate()
        self.sys_x_inspectors_kcs()
    
    def sys_kcs2(self):
        self.env.cr.execute('''
            
            alter table request_kcs_line disable trigger all;
            delete from request_kcs_line;
            alter table request_kcs_line enable trigger all;
            alter sequence request_kcs_line_id_seq minvalue 0 start with 1;
            SELECT setval('request_kcs_line_id_seq', 0);
            
            delete from kcs_sample_stock_picking_rel;
            delete from kcs_rule_warehouse_rel;
            
            delete from stock_picking_kcs_sample_rel;
            
            alter table kcs_sample disable trigger all;
            delete from kcs_sample;
            alter table kcs_sample enable trigger all;
            alter sequence kcs_sample_id_seq minvalue 0 start with 1;
            SELECT setval('kcs_sample_id_seq', 0);
            
            alter table lot_kcs disable trigger all;
            delete from lot_kcs;
            alter table lot_kcs enable trigger all;
            alter sequence lot_kcs_id_seq minvalue 0 start with 1;
            SELECT setval('lot_kcs_id_seq', 0);
            
            alter table lot_stack_allocation disable trigger all;
            delete from lot_stack_allocation;
            alter table lot_stack_allocation enable trigger all;
            alter sequence lot_stack_allocation_id_seq minvalue 0 start with 1;
            SELECT setval('lot_stack_allocation_id_seq', 0);
            
            alter table fob_management disable trigger all;
            delete from fob_management;
            alter table fob_management enable trigger all;
            alter sequence fob_management_id_seq minvalue 0 start with 1;
            SELECT setval('fob_management_id_seq', 0);
            
            alter table stock_contract_allocation disable trigger all;
            delete from stock_contract_allocation;
            alter table stock_contract_allocation enable trigger all;
            alter sequence stock_contract_allocation_id_seq minvalue 0 start with 1;
            SELECT setval('stock_contract_allocation_id_seq', 0);
            
        ''')
        
        self.env.cr.commit()
        
        self.sys_request_kcs_line()
        self.sys_kcs_sample()
        self.sys_kcs_sample_stock_picking_rel()
        self.sys_stock_picking_kcs_sample_rel()
        self.sys_lot_kcs()
        self.sys_lot_stack_allocation()
        self.sys_stock_contract_allocation()
        self.sys_fob_management()
        
    
    def sys_kcs_glyphosate(self):
        sql ='''
        INSERT INTO 
            kcs_glyphosate 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                warehouse_id ,
                si_id ,
                customer_id ,
                product_id ,
                stack_no ,
                name ,
                test_requirement  ,
                pss_status  ,
                original  ,
                our_comment  ,
                analysis_by  ,
                inspector_by  ,
                qc_staff  ,
                remark  ,
                created_date ,
                date_sent ,
                date_result ,
                quantity ,
                cont_qty ,
                results 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    warehouse_id ,
                    si_id ,
                    customer_id ,
                    product_id ,
                    stack_no ,
                    name ,
                    test_requirement  ,
                    pss_status  ,
                    original  ,
                    our_comment  ,
                    analysis_by  ,
                    inspector_by  ,
                    qc_staff  ,
                    remark  ,
                    created_date ,
                    date_sent ,
                    date_result ,
                    quantity ,
                    cont_qty ,
                    results  
                FROM public.kcs_glyphosate') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    warehouse_id integer,
                    si_id integer,
                    customer_id integer,
                    product_id integer,
                    stack_no integer,
                    name character varying(256) ,
                    test_requirement character varying ,
                    pss_status character varying ,
                    original character varying ,
                    our_comment character varying ,
                    analysis_by character varying ,
                    inspector_by character varying ,
                    qc_staff character varying ,
                    remark character varying ,
                    created_date date,
                    date_sent date,
                    date_result date,
                    quantity double precision,
                    cont_qty double precision,
                    results double precision 
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('kcs_glyphosate_id_seq', (select max(id) + 1 from  kcs_glyphosate));
        ''')   
        
        return
    
    def sys_restack_management(self):
        sql ='''
        INSERT INTO 
            restack_management 
            (
                id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    warehouse_id ,
                    partner_id ,
                    product_id ,
                    packing_id ,
                    name  ,
                    x_p_contract_name  ,
                    buyer_ref  ,
                    payment  ,
                    remark  ,
                    status  ,
                    goods_status  ,
                    type  ,
                    date_request ,
                    finished_date ,
                    date_export ,
                    quantity ,
                    balance_net ,
                    storing_days ,
                    qty_per_contain ,
                    qty_request 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    warehouse_id ,
                    partner_id ,
                    product_id ,
                    packing_id ,
                    name  ,
                    x_p_contract_name  ,
                    buyer_ref  ,
                    payment  ,
                    remark  ,
                    status  ,
                    goods_status  ,
                    type  ,
                    date_request ,
                    finished_date ,
                    date_export ,
                    quantity ,
                    balance_net ,
                    storing_days ,
                    qty_per_contain ,
                    qty_request 
                    
                FROM public.restack_management') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        warehouse_id integer,
                        partner_id integer,
                        product_id integer,
                        packing_id integer,
                        name character varying ,
                        x_p_contract_name character varying(10000) ,
                        buyer_ref character varying ,
                        payment character varying ,
                        remark character varying ,
                        status character varying ,
                        goods_status character varying ,
                        type character varying ,
                        date_request date,
                        finished_date date,
                        date_export date,
                        quantity double precision,
                        balance_net double precision,
                        storing_days double precision,
                        qty_per_contain double precision,
                        qty_request double precision
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('restack_management_id_seq', (select max(id) + 1 from  restack_management));
        ''')   
        
        return
    
    def sys_vessel_registration(self):
        sql ='''
        INSERT INTO 
            vessel_registration 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                shipping_instruction ,
                product_id ,
                delivery_place ,
                from_warehouse ,
                shipping_line ,
                name  ,
                status  ,
                booking_no  ,
                custom_declaration  ,
                quality_staff  ,
                do_date ,
                registration_date ,
                closing_time ,
                si_qty  
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    shipping_instruction ,
                    product_id ,
                    delivery_place ,
                    from_warehouse ,
                    shipping_line ,
                    name  ,
                    status  ,
                    booking_no  ,
                    custom_declaration  ,
                    quality_staff  ,
                    do_date date,
                    registration_date ,
                    closing_time ,
                    si_qty  
                FROM public.vessel_registration') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        shipping_instruction integer,
                        product_id integer,
                        delivery_place integer,
                        from_warehouse integer,
                        shipping_line integer,
                        name character varying ,
                        status character varying ,
                        booking_no character varying ,
                        custom_declaration character varying ,
                        quality_staff character varying ,
                        do_date date,
                        registration_date date,
                        closing_time timestamp without time zone,
                        si_qty double precision
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('vessel_registration_id_seq', (select max(id) + 1 from  vessel_registration));
        ''')   
        
        return
        
    def sys_stock_contract_allocation(self):
        sql ='''
        INSERT INTO 
            stock_contract_allocation 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                stack_no ,
                zone_id ,
                --product_name ,
                shipping_id ,
                partner_id ,
                --factory_etd ,
                stock_balance ,
                allocation_date ,
                allocating_quantity
                --allocation_availabibity
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    stack_no ,
                    zone_id ,
                    --product_name ,
                    shipping_id ,
                    partner_id ,
                    --factory_etd ,
                    stock_balance ,
                    allocation_date ,
                    allocating_quantity
                    --allocation_availabibity
                    
                FROM public.stock_contract_allocation') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    stack_no integer,
                    zone_id integer,
                    --product_name integer,
                    shipping_id integer,
                    partner_id integer,
                    --factory_etd date,
                    stock_balance numeric,
                    allocation_date timestamp without time zone,
                    allocating_quantity double precision
                    --allocation_availabibity double precision
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('stock_contract_allocation_id_seq', (select max(id) + 1 from  stock_contract_allocation));
        ''') 
        
    def sys_fob_pss_management(self):
        sql ='''
        INSERT INTO 
            fob_pss_management 
            (
                id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    product_id ,
                    partner_id ,
                    shipper_id ,
                    warehouse_id ,
                    x_shipper ,
                    x_ex_warehouse ,
                    --x_traffic_contract ,
                    name  ,
                    pss_status  ,
                    date_result  ,
                    buyer_ref  ,
                    ref_no  ,
                    inspector  ,
                    buyer_comment  ,
                    our_comment  ,
                    note  ,
                    qc_staff  ,
                    bulk_density  ,
                    state  ,
                    inspected_by  ,
                    awb_no  ,
                    created_date ,
                    date_sent ,
                    shipment_date ,
                    date_sampling ,
                    lot_quantity ,
                    cont_quantity ,
                    mc ,
                    fm ,
                    black ,
                    broken ,
                    brown ,
                    moldy ,
                    burned ,
                    scr20 ,
                    scr19 ,
                    scr18 ,
                    scr16 ,
                    scr13 ,
                    scr12 ,
                    blscr12 ,
                    x_screen14 ,
                    x_screen15 ,
                    x_screen17 
            )        
        
        SELECT 
            id, 
                create_date, create_uid, 
                write_date, write_uid, 
                product_id ,
                partner_id ,
                shipper_id ,
                warehouse_id ,
                x_shipper ,
                x_ex_warehouse ,
                --x_traffic_contract ,
                name  ,
                pss_status  ,
                date_result  ,
                buyer_ref  ,
                ref_no  ,
                inspector  ,
                buyer_comment  ,
                our_comment  ,
                note  ,
                qc_staff  ,
                bulk_density  ,
                state  ,
                inspected_by  ,
                awb_no  ,
                created_date ,
                date_sent date,
                shipment_date ,
                date_sampling ,
                lot_quantity ,
                cont_quantity ,
                mc ,
                fm ,
                black ,
                broken ,
                brown ,
                moldy ,
                burned ,
                scr20 ,
                scr19 ,
                scr18 ,
                scr16 ,
                scr13 ,
                scr12 ,
                blscr12 ,
                x_screen14 ,
                x_screen15 ,
                x_screen17 
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    product_id ,
                    partner_id ,
                    shipper_id ,
                    warehouse_id ,
                    x_shipper ,
                    x_ex_warehouse ,
                    --x_traffic_contract ,
                    name  ,
                    pss_status  ,
                    date_result  ,
                    buyer_ref  ,
                    ref_no  ,
                    inspector  ,
                    buyer_comment  ,
                    our_comment  ,
                    note  ,
                    qc_staff  ,
                    bulk_density  ,
                    state  ,
                    inspected_by  ,
                    awb_no  ,
                    created_date ,
                    date_sent date,
                    shipment_date ,
                    date_sampling ,
                    lot_quantity ,
                    cont_quantity ,
                    mc ,
                    fm ,
                    black ,
                    broken ,
                    brown ,
                    moldy ,
                    burned ,
                    scr20 ,
                    scr19 ,
                    scr18 ,
                    scr16 ,
                    scr13 ,
                    scr12 ,
                    blscr12 ,
                    x_screen14 ,
                    x_screen15 ,
                    x_screen17 
                FROM public.fob_pss_management') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        product_id integer,
                        partner_id integer,
                        shipper_id integer,
                        warehouse_id integer,
                        x_shipper integer,
                        x_ex_warehouse integer,
                        --x_traffic_contract integer,
                        name character varying ,
                        pss_status character varying ,
                        date_result character varying ,
                        buyer_ref character varying ,
                        ref_no character varying ,
                        inspector character varying ,
                        buyer_comment character varying ,
                        our_comment character varying ,
                        note character varying ,
                        qc_staff character varying ,
                        bulk_density character varying ,
                        state character varying ,
                        inspected_by character varying ,
                        awb_no  character varying ,
                        created_date date,
                        date_sent date,
                        shipment_date date,
                        date_sampling date,
                        lot_quantity double precision,
                        cont_quantity double precision,
                        mc double precision,
                        fm double precision,
                        black double precision,
                        broken double precision,
                        brown double precision,
                        moldy double precision,
                        burned double precision,
                        scr20 double precision,
                        scr19 double precision,
                        scr18 double precision,
                        scr16 double precision,
                        scr13 double precision,
                        scr12 double precision,
                        blscr12 double precision,
                        x_screen14 double precision,
                        x_screen15 double precision,
                        x_screen17 double precision
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('fob_pss_management_id_seq', (select max(id) + 1 from  fob_pss_management));
        ''')   
        
        return
    
    def sys_fob_management(self):
        sql ='''
        INSERT INTO 
            fob_management 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                scontract_id ,
                    pcontract_id ,
                    shipper_id ,
                    dest_id ,
                    --x_traffic_contract_id ,
                    customer_id ,
                    product_id ,
                    packing_id ,
                    name  ,
                    lot_sucden  ,
                    stuff_place  ,
                    bulk_density  ,
                    cup_taste  ,
                    inspect_sampler  ,
                    sup_suc  ,
                    remark  ,
                    x_quality_claim  ,
                    x_reoclaim  ,
                    shiping_line  ,
                    x_p_contract_name  ,
                    contract_no  ,
                    x_fumi  ,
                    state  ,
                    stack_on_hand  ,
                    lot_date ,
                    x_claim_date ,
                    screen20 ,
                    screen19 ,
                    screen17 ,
                    screen18 ,
                    screen16 ,
                    screen15 ,
                    screen14 ,
                    screen13 ,
                    screen12 ,
                    bscreen12 ,
                    burn ,
                    excelsa ,
                    insect ,
                    defects ,
                    net_qty ,
                    mc ,
                    fm ,
                    black ,
                    broken ,
                    brown ,
                    mold ,
                    qty_scontract ,
                    p_on_hand ,
                    real_container ,
                    weight_claim 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    scontract_id ,
                    pcontract_id ,
                    shipper_id ,
                    dest_id ,
                    --x_traffic_contract_id ,
                    customer_id ,
                    product_id ,
                    packing_id ,
                    name  ,
                    lot_sucden  ,
                    stuff_place  ,
                    bulk_density  ,
                    cup_taste  ,
                    inspect_sampler  ,
                    sup_suc  ,
                    remark  ,
                    x_quality_claim  ,
                    x_reoclaim  ,
                    shiping_line  ,
                    x_p_contract_name  ,
                    contract_no  ,
                    x_fumi  ,
                    state  ,
                    stack_on_hand  ,
                    lot_date ,
                    x_claim_date ,
                    screen20 ,
                    screen19 ,
                    screen17 ,
                    screen18 ,
                    screen16 ,
                    screen15 ,
                    screen14 ,
                    screen13 ,
                    screen12 ,
                    bscreen12 ,
                    burn ,
                    excelsa ,
                    insect ,
                    defects ,
                    net_qty ,
                    mc ,
                    fm ,
                    black ,
                    broken ,
                    brown ,
                    mold ,
                    qty_scontract ,
                    p_on_hand ,
                    real_container ,
                    weight_claim 
                FROM public.fob_management') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    scontract_id integer,
                    pcontract_id integer,
                    shipper_id integer,
                    dest_id integer,
                    --x_traffic_contract_id integer,
                    customer_id integer,
                    product_id integer,
                    packing_id integer,
                    name character varying ,
                    lot_sucden character varying(256) ,
                    stuff_place character varying ,
                    bulk_density character varying(256) ,
                    cup_taste character varying ,
                    inspect_sampler character varying(256) ,
                    sup_suc character varying(256) ,
                    remark character varying(256) ,
                    x_quality_claim character varying(128) ,
                    x_reoclaim character varying(256) ,
                    shiping_line character varying(256) ,
                    x_p_contract_name character varying(256) ,
                    contract_no character varying(256) ,
                    x_fumi character varying(256) ,
                    state character varying ,
                    stack_on_hand character varying ,
                    lot_date date,
                    x_claim_date date,
                    screen20 numeric,
                    screen19 numeric,
                    screen17 numeric,
                    screen18 numeric,
                    screen16 numeric,
                    screen15 numeric,
                    screen14 numeric,
                    screen13 numeric,
                    screen12 numeric,
                    bscreen12 numeric,
                    burn numeric,
                    excelsa numeric,
                    insect numeric,
                    defects numeric,
                    net_qty double precision,
                    mc double precision,
                    fm double precision,
                    black double precision,
                    broken double precision,
                    brown double precision,
                    mold double precision,
                    qty_scontract double precision,
                    p_on_hand double precision,
                    real_container double precision,
                    weight_claim double precision
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('fob_management_id_seq', (select max(id) + 1 from  fob_management));
        ''')   
        
        return
    
    def sys_pss_management(self):
        sql ='''
        INSERT INTO 
            pss_management 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                ship_by ,
                shipping_id ,
                product_id ,
                partner_id ,
                x_ex_warehouse_id ,
                shipper_id  ,
                x_stuff_place  ,
                name  ,
                pss_status  ,
                date_result  ,
                buyer_ref  ,
                ref_no  ,
                inspector  ,
                buyer_comment  ,
                our_comment  ,
                note  ,
                qc_staff  ,
                x_bulk_density  ,
                status_nestle  ,
                created_date ,
                date_sent ,
                x_shipment_date ,
                is_nestle ,
                lot_quantity ,
                cont_quantity ,
                mc ,
                fm ,
                black ,
                broken ,
                brown ,
                moldy ,
                burned ,
                scr20 ,
                scr19 ,
                scr18 ,
                scr16 ,
                scr13 ,
                scr12 ,
                blscr12 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    ship_by ,
                    shipping_id ,
                    product_id ,
                    partner_id ,
                    x_ex_warehouse_id ,
                    shipper_id  ,
                    x_stuff_place  ,
                    name  ,
                    pss_status  ,
                    date_result  ,
                    buyer_ref  ,
                    ref_no  ,
                    inspector  ,
                    buyer_comment  ,
                    our_comment  ,
                    note  ,
                    qc_staff  ,
                    x_bulk_density  ,
                    status_nestle  ,
                    created_date ,
                    date_sent ,
                    x_shipment_date ,
                    is_nestle ,
                    lot_quantity ,
                    cont_quantity ,
                    mc ,
                    fm ,
                    black ,
                    broken ,
                    brown ,
                    moldy ,
                    burned ,
                    scr20 ,
                    scr19 ,
                    scr18 ,
                    scr16 ,
                    scr13 ,
                    scr12 ,
                    blscr12 
                    
                FROM public.pss_management') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        ship_by integer,
                        shipping_id integer,
                        product_id integer,
                        partner_id integer,
                        x_ex_warehouse_id integer,
                        shipper_id character varying(256) ,
                        x_stuff_place character varying(256) ,
                        name character varying ,
                        pss_status character varying ,
                        date_result character varying ,
                        buyer_ref character varying ,
                        ref_no character varying ,
                        inspector character varying ,
                        buyer_comment character varying ,
                        our_comment character varying ,
                        note character varying ,
                        qc_staff character varying ,
                        x_bulk_density character varying(256) ,
                        status_nestle character varying ,
                        created_date date,
                        date_sent date,
                        x_shipment_date date,
                        is_nestle boolean,
                        lot_quantity double precision,
                        cont_quantity double precision,
                        mc double precision,
                        fm double precision,
                        black double precision,
                        broken double precision,
                        brown double precision,
                        moldy double precision,
                        burned double precision,
                        scr20 double precision,
                        scr19 double precision,
                        scr18 double precision,
                        scr16 double precision,
                        scr13 double precision,
                        scr12 double precision,
                        blscr12 double precision
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('pss_management_id_seq', (select max(id) + 1 from  pss_management));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_lot_stack_allocation(self):
        sql ='''
        INSERT INTO 
            lot_stack_allocation 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                lot_id ,
                delivery_id ,
                grp_id ,
                stack_id ,
                contract_id ,
                zone_id ,
                gdn_id ,
                product_id ,
                nvs_id ,
                state   ,
                cuptaste  ,
                defects ,
                defects_tcvn ,
                quantity ,
                mc_on_despatch 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    lot_id ,
                    delivery_id ,
                    grp_id ,
                    stack_id ,
                    contract_id ,
                    zone_id ,
                    gdn_id ,
                    product_id ,
                    nvs_id ,
                    state   ,
                    cuptaste  ,
                    defects ,
                    defects_tcvn ,
                    quantity ,
                    mc_on_despatch 
                    
                FROM public.lot_stack_allocation')
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        lot_id integer,
                        delivery_id integer,
                        grp_id integer,
                        stack_id integer,
                        contract_id integer,
                        zone_id integer,
                        gdn_id integer,
                        product_id integer,
                        nvs_id integer,
                        state character varying  ,
                        cuptaste character varying ,
                        defects numeric,
                        defects_tcvn numeric,
                        quantity double precision,
                        mc_on_despatch double precision 
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('lot_stack_allocation_id_seq', (select max(id) + 1 from  lot_stack_allocation));
        ''')   
        
        return
    
    def sys_lot_kcs(self):
        sql ='''
        INSERT INTO 
            lot_kcs 
            (
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                contract_id ,
                product_id ,
                delivery_id ,
                grp_id ,
                stack_id ,
                nvs_id ,
                partner_id ,
                name  ,
                cup_test  ,
                x_bulk_density ,
                maize  ,
                stone  ,
                stick  ,
                sampler  ,
                --stone_count  ,
                --stick_count  ,
                supervisor  ,
                state   ,
                lot_ned  ,
                lot_date ,
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
                fixed_mc ,
                fixed_fm ,
                fixed_black ,
                fixed_broken ,
                fixed_brown ,
                fixed_mold ,
                fixed_immature ,
                fixed_burn ,
                fixed_eaten ,
                fixed_cherry ,
                fixed_screen20 ,
                fixed_screen19 ,
                fixed_screen18 ,
                fixed_screen17 ,
                fixed_screen16 ,
                fixed_screen15 ,
                fixed_screen14 ,
                fixed_screen13 ,
                fixed_greatersc12 ,
                fixed_screen12 ,
                fixed_excelsa ,
                fixed_mc_on_despatch ,
                fixed_defects ,
                mc_on_despatch ,
                defects ,
                lot_quantity ,
                qty_scontract ,
                quantity 
            )        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    contract_id ,
                    product_id ,
                    delivery_id ,
                    grp_id ,
                    stack_id ,
                    nvs_id ,
                    partner_id ,
                    name  ,
                    cup_test  ,
                    x_bulk_density ,
                    maize  ,
                    stone  ,
                    stick  ,
                    sampler  ,
                    --stone_count  ,
                    --stick_count  ,
                    supervisor  ,
                    state   ,
                    lot_ned  ,
                    lot_date ,
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
                    fixed_mc ,
                    fixed_fm ,
                    fixed_black ,
                    fixed_broken ,
                    fixed_brown ,
                    fixed_mold ,
                    fixed_immature ,
                    fixed_burn ,
                    fixed_eaten ,
                    fixed_cherry ,
                    fixed_screen20 ,
                    fixed_screen19 ,
                    fixed_screen18 ,
                    fixed_screen17 ,
                    fixed_screen16 ,
                    fixed_screen15 ,
                    fixed_screen14 ,
                    fixed_screen13 ,
                    fixed_greatersc12 ,
                    fixed_screen12 ,
                    fixed_excelsa ,
                    fixed_mc_on_despatch ,
                    fixed_defects ,
                    mc_on_despatch ,
                    defects ,
                    lot_quantity ,
                    qty_scontract ,
                    quantity 
                    
                FROM public.lot_kcs') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    contract_id integer,
                    product_id integer,
                    delivery_id integer,
                    grp_id integer,
                    stack_id integer,
                    nvs_id integer,
                    partner_id integer,
                    name character varying ,
                    cup_test character varying ,
                    x_bulk_density character varying,
                    maize character varying ,
                    stone character varying ,
                    stick character varying ,
                    sampler character varying ,
                    --stone_count character varying ,
                    --stick_count character varying ,
                    supervisor character varying ,
                    state character varying  ,
                    lot_ned character varying ,
                    lot_date date,
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
                    fixed_mc numeric,
                    fixed_fm numeric,
                    fixed_black numeric,
                    fixed_broken numeric,
                    fixed_brown numeric,
                    fixed_mold numeric,
                    fixed_immature numeric,
                    fixed_burn numeric,
                    fixed_eaten numeric,
                    fixed_cherry numeric,
                    fixed_screen20 numeric,
                    fixed_screen19 numeric,
                    fixed_screen18 numeric,
                    fixed_screen17 numeric,
                    fixed_screen16 numeric,
                    fixed_screen15 numeric,
                    fixed_screen14 numeric,
                    fixed_screen13 numeric,
                    fixed_greatersc12 numeric,
                    fixed_screen12 numeric,
                    fixed_excelsa numeric,
                    fixed_mc_on_despatch numeric,
                    fixed_defects numeric,
                    mc_on_despatch numeric,
                    defects numeric,
                    lot_quantity numeric,
                    qty_scontract numeric,
                    quantity double precision
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('lot_kcs_id_seq', (select max(id) + 1 from  lot_kcs));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
        
    def sys_stock_picking_kcs_sample_rel(self):
        sql ='''
        INSERT INTO 
            stock_picking_kcs_sample_rel 
            (
                kcs_sample_id  ,           
                picking_id
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    kcs_sample_id,
                    picking_id
                 
                FROM public.stock_picking_kcs_sample_rel') 
                AS DATA(
                        kcs_sample_id integer,
                        picking_id integer                            
                    )
        '''
        self.env.cr.execute(sql)
    
    def sys_kcs_rule_warehouse_rel(self):
        sql ='''
        INSERT INTO 
            kcs_rule_warehouse_rel 
            (
                rule_id  ,           
                warehouse_id
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    rule_id,
                    warehouse_id
                 
                FROM public.kcs_rule_warehouse_rel') 
                AS DATA(
                        rule_id integer,
                        warehouse_id integer                            
                    )
        '''
        self.env.cr.execute(sql)
    
    def sys_kcs_sample_stock_picking_rel(self):
        sql ='''
        INSERT INTO  
            kcs_sample_stock_picking_rel 
            (
                picking_id  ,           
                kcs_sample_id
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    picking_id,
                    kcs_sample_id
                 
                FROM public.kcs_sample_stock_picking_rel') 
                AS DATA(
                        picking_id integer,
                        kcs_sample_id integer                            
                    )
        '''
        self.env.cr.execute(sql)
        
    def sys_kcs_sample(self):
        sql ='''
    
        INSERT INTO 
            kcs_sample 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                partner_id  ,
                    product_id  ,
                    categ_id ,
                    criterions_id ,
                    name  ,
                    state  ,
                    sampler  ,
                    maize_yn  ,
                    stone_count ,
                    stick_count ,
                    remark  ,
                    date_kcs ,
                    sample_weight ,
                    bb_sample_weight ,
                    mc_degree ,
                    mc ,
                    mc_deduct ,
                    fm_gram ,
                    fm ,
                    fm_deduct ,
                    black_gram ,
                    black ,
                    broken_gram ,
                    broken ,
                    broken_deduct ,
                    brown_gram ,
                    brown ,
                    brown_deduct ,
                    bbb ,
                    mold_gram ,
                    mold ,
                    mold_deduct ,
                    insect_bean_gram ,
                    insect_bean ,
                    insect_bean_deduct ,
                    cherry ,
                    excelsa_gram ,
                    excelsa ,
                    excelsa_deduct ,
                    screen20_gram ,
                    screen20 ,
                    screen19_gram ,
                    screen19 ,
                    screen18_gram ,
                    screen18 ,
                    oversc18 ,
                    screen17_gram ,
                    screen17 ,
                    screen16_gram ,
                    screen16 ,
                    oversc16 ,
                    screen15_gram ,
                    screen15 ,
                    screen14_gram ,
                    screen14 ,
                    screen13_gram ,
                    screen13 ,
                    oversc13 ,
                    greatersc12_gram ,
                    belowsc12_gram ,
                    oversc12 ,
                    burned_gram ,
                    burned ,
                    burned_deduct ,
                    eaten_gram ,
                    eaten ,
                    immature_gram ,
                    immature ,
                    bb12_gram ,
                    bb12 ,
                    deduction ,
                    deduction_manual ,
                    cherry_gram ,
                    greatersc12 ,
                    belowsc12
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    partner_id  ,
                    product_id  ,
                    categ_id ,
                    criterions_id ,
                    name  ,
                    state  ,
                    sampler  ,
                    maize_yn  ,
                    stone_count ,
                    stick_count ,
                    remark  ,
                    date_kcs ,
                    sample_weight ,
                    bb_sample_weight ,
                    mc_degree ,
                    mc ,
                    mc_deduct ,
                    fm_gram ,
                    fm ,
                    fm_deduct ,
                    black_gram ,
                    black ,
                    broken_gram ,
                    broken ,
                    broken_deduct ,
                    brown_gram ,
                    brown ,
                    brown_deduct ,
                    bbb ,
                    mold_gram ,
                    mold ,
                    mold_deduct ,
                    insect_bean_gram ,
                    insect_bean ,
                    insect_bean_deduct ,
                    cherry ,
                    excelsa_gram ,
                    excelsa ,
                    excelsa_deduct ,
                    screen20_gram ,
                    screen20 ,
                    screen19_gram ,
                    screen19 ,
                    screen18_gram ,
                    screen18 ,
                    oversc18 ,
                    screen17_gram ,
                    screen17 ,
                    screen16_gram ,
                    screen16 ,
                    oversc16 ,
                    screen15_gram ,
                    screen15 ,
                    screen14_gram ,
                    screen14 ,
                    screen13_gram ,
                    screen13 ,
                    oversc13 ,
                    greatersc12_gram ,
                    belowsc12_gram ,
                    oversc12 ,
                    burned_gram ,
                    burned ,
                    burned_deduct ,
                    eaten_gram ,
                    eaten ,
                    immature_gram ,
                    immature ,
                    bb12_gram ,
                    bb12 ,
                    deduction ,
                    deduction_manual ,
                    cherry_gram ,
                    greatersc12 ,
                    belowsc12
                    
                FROM public.kcs_sample') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        partner_id integer ,
                        product_id integer ,
                        categ_id integer,
                        criterions_id integer,
                        name character varying ,
                        state character varying ,
                        sampler character varying ,
                        maize_yn character varying ,
                        stone_count double precision,
                        stick_count double precision,
                        remark character varying ,
                        date_kcs date,
                        sample_weight numeric,
                        bb_sample_weight numeric,
                        mc_degree numeric,
                        mc numeric,
                        mc_deduct numeric,
                        fm_gram numeric,
                        fm numeric,
                        fm_deduct numeric,
                        black_gram numeric,
                        black numeric,
                        broken_gram numeric,
                        broken numeric,
                        broken_deduct numeric,
                        brown_gram numeric,
                        brown numeric,
                        brown_deduct numeric,
                        bbb numeric,
                        mold_gram numeric,
                        mold numeric,
                        mold_deduct numeric,
                        insect_bean_gram numeric,
                        insect_bean numeric,
                        insect_bean_deduct numeric,
                        cherry numeric,
                        excelsa_gram numeric,
                        excelsa numeric,
                        excelsa_deduct numeric,
                        screen20_gram numeric,
                        screen20 numeric,
                        screen19_gram numeric,
                        screen19 numeric,
                        screen18_gram numeric,
                        screen18 numeric,
                        oversc18 numeric,
                        screen17_gram numeric,
                        screen17 numeric,
                        screen16_gram numeric,
                        screen16 numeric,
                        oversc16 numeric,
                        screen15_gram numeric,
                        screen15 numeric,
                        screen14_gram numeric,
                        screen14 numeric,
                        screen13_gram numeric,
                        screen13 numeric,
                        oversc13 numeric,
                        greatersc12_gram numeric,
                        belowsc12_gram numeric,
                        oversc12 numeric,
                        burned_gram numeric,
                        burned numeric,
                        burned_deduct numeric,
                        eaten_gram numeric,
                        eaten numeric,
                        immature_gram numeric,
                        immature numeric,
                        bb12_gram numeric,
                        bb12 numeric,
                        deduction numeric,
                        deduction_manual numeric,
                        cherry_gram double precision,
                        greatersc12 double precision,
                        belowsc12 double precision 
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('kcs_sample_id_seq', (select max(id) + 1 from  kcs_sample));
        ''')   
        return
    
    def sys_request_kcs_line(self):
        sql ='''
        INSERT INTO 
            request_kcs_line 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                product_id ,
                    categ_id ,
                    product_uom ,
                    picking_id ,
                    move_id ,
                    x_inspectator ,
                    x_warehouse_id ,
                    p_contract_id ,
                    --p_contract ,
                    stack_id ,
                    zone_id ,
                    partner_id ,
                    production_id ,
                    picking_type_id ,
                    cuptest  ,
                    inspector  ,
                    x_bulk_density  ,
                    --x_label  ,
                    --state_kcs  ,
                    reference  ,
                    state  ,
                    sampler  ,
                    maize_yn  ,
                    --stone_count ,
                    --stick_count ,
                    picking_type_code  ,
                    name  ,
                    product_qty ,
                    qty_reached ,
                    sample_weight ,
                    bb_sample_weight ,
                    mc_degree ,
                    mc ,
                    mc_deduct ,
                    fm_gram ,
                    fm ,
                    fm_deduct ,
                    black_gram ,
                    black ,
                    broken_gram ,
                    broken ,
                    broken_deduct ,
                    brown_gram ,
                    brown ,
                    brown_deduct ,
                    bbb ,
                    mold_gram ,
                    mold ,
                    mold_deduct ,
                    cherry ,
                    excelsa_gram ,
                    excelsa ,
                    excelsa_deduct ,
                    screen20_gram ,
                    screen20 ,
                    screen19_gram ,
                    screen19 ,
                    screen18_gram ,
                    screen18 ,
                    oversc18 ,
                    screen17_gram ,
                    screen17 ,
                    screen16_gram ,
                    screen16 ,
                    oversc16 ,
                    screen15_gram ,
                    screen15 ,
                    screen14_gram ,
                    screen14 ,
                    screen13_gram ,
                    screen13 ,
                    oversc13 ,
                    greatersc12_gram ,
                    belowsc12_gram ,
                    oversc12 ,
                    burned_gram ,
                    burned ,
                    burned_deduct ,
                    eaten_gram ,
                    eaten ,
                    insect_bean_deduct ,
                    immature_gram ,
                    immature ,
                    bb12_gram ,
                    bb12 ,
                    deduction ,
                    basis_weight ,
                    deduction_manual ,
                    check_deduction ,
                    cherry_gram ,
                    greatersc12 ,
                    belowsc12 
                    --origin_deduction 
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
                    categ_id ,
                    product_uom ,
                    picking_id ,
                    move_id ,
                    x_inspectator ,
                    x_warehouse_id ,
                    p_contract_id ,
                    --p_contract ,
                    stack_id ,
                    zone_id ,
                    partner_id ,
                    production_id ,
                    picking_type_id ,
                    cuptest  ,
                    inspector  ,
                    x_bulk_density  ,
                    --x_label  ,
                    --state_kcs  ,
                    reference  ,
                    state  ,
                    sampler  ,
                    maize_yn  ,
                    --stone_count ,
                    --stick_count ,
                    picking_type_code  ,
                    name  ,
                    product_qty ,
                    qty_reached ,
                    sample_weight ,
                    bb_sample_weight ,
                    mc_degree ,
                    mc ,
                    mc_deduct ,
                    fm_gram ,
                    fm ,
                    fm_deduct ,
                    black_gram ,
                    black ,
                    broken_gram ,
                    broken ,
                    broken_deduct ,
                    brown_gram ,
                    brown ,
                    brown_deduct ,
                    bbb ,
                    mold_gram ,
                    mold ,
                    mold_deduct ,
                    cherry ,
                    excelsa_gram ,
                    excelsa ,
                    excelsa_deduct ,
                    screen20_gram ,
                    screen20 ,
                    screen19_gram ,
                    screen19 ,
                    screen18_gram ,
                    screen18 ,
                    oversc18 ,
                    screen17_gram ,
                    screen17 ,
                    screen16_gram ,
                    screen16 ,
                    oversc16 ,
                    screen15_gram ,
                    screen15 ,
                    screen14_gram ,
                    screen14 ,
                    screen13_gram ,
                    screen13 ,
                    oversc13 ,
                    greatersc12_gram ,
                    belowsc12_gram ,
                    oversc12 ,
                    burned_gram ,
                    burned ,
                    burned_deduct ,
                    eaten_gram ,
                    eaten ,
                    insect_bean_deduct ,
                    immature_gram ,
                    immature ,
                    bb12_gram ,
                    bb12 ,
                    deduction ,
                    basis_weight ,
                    deduction_manual ,
                    check_deduction ,
                    cherry_gram ,
                    greatersc12 ,
                    belowsc12 
                    --origin_deduction
                     
                FROM public.request_kcs_line') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    product_id integer ,
                    categ_id integer,
                    product_uom integer ,
                    picking_id integer,
                    move_id integer,
                    x_inspectator integer,
                    x_warehouse_id integer,
                    p_contract_id integer,
                    --p_contract integer,
                    stack_id integer,
                    zone_id integer,
                    partner_id integer,
                    production_id integer,
                    picking_type_id integer,
                    cuptest character varying ,
                    inspector character varying ,
                    x_bulk_density character varying(256) ,
                    --x_label character varying ,
                    --state_kcs character varying ,
                    reference character varying ,
                    state character varying ,
                    sampler character varying ,
                    maize_yn character varying ,
                    --stone_count double precision,
                    --stick_count double precision,
                    picking_type_code character varying ,
                    name text ,
                    product_qty numeric,
                    qty_reached numeric,
                    sample_weight numeric,
                    bb_sample_weight numeric,
                    mc_degree numeric,
                    mc numeric,
                    mc_deduct numeric,
                    fm_gram numeric,
                    fm numeric,
                    fm_deduct numeric,
                    black_gram numeric,
                    black numeric,
                    broken_gram numeric,
                    broken numeric,
                    broken_deduct numeric,
                    brown_gram numeric,
                    brown numeric,
                    brown_deduct numeric,
                    bbb numeric,
                    mold_gram numeric,
                    mold numeric,
                    mold_deduct numeric,
                    cherry numeric,
                    excelsa_gram numeric,
                    excelsa numeric,
                    excelsa_deduct numeric,
                    screen20_gram numeric,
                    screen20 numeric,
                    screen19_gram numeric,
                    screen19 numeric,
                    screen18_gram numeric,
                    screen18 numeric,
                    oversc18 numeric,
                    screen17_gram numeric,
                    screen17 numeric,
                    screen16_gram numeric,
                    screen16 numeric,
                    oversc16 numeric,
                    screen15_gram numeric,
                    screen15 numeric,
                    screen14_gram numeric,
                    screen14 numeric,
                    screen13_gram numeric,
                    screen13 numeric,
                    oversc13 numeric,
                    greatersc12_gram numeric,
                    belowsc12_gram numeric,
                    oversc12 numeric,
                    burned_gram numeric,
                    burned numeric,
                    burned_deduct numeric,
                    eaten_gram numeric,
                    eaten numeric,
                    insect_bean_deduct numeric,
                    immature_gram numeric,
                    immature numeric,
                    bb12_gram numeric,
                    bb12 numeric,
                    deduction numeric,
                    basis_weight numeric,
                    deduction_manual numeric,
                    check_deduction boolean,
                    cherry_gram double precision,
                    greatersc12 double precision,
                    belowsc12 double precision
                    --origin_deduction double precision
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('request_kcs_line_id_seq', (select max(id) + 1 from  request_kcs_line));
        ''')   
        return
    
    def sys_x_inspectors_kcs(self):
        sql ='''
        INSERT INTO 
            x_inspectors_kcs 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    x_name 
                     
                FROM public.x_inspectors_kcs') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        x_name character varying 
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('x_inspectors_kcs_id_seq', (select max(id) + 1 from  x_inspectors_kcs));
        ''')   
        return
    
    def sys_over_screen12(self):
        sql ='''
        INSERT INTO 
            over_screen12 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                criterion_id ,
                name ,
                compares ,
                range_start ,
                range_end ,
                percent ,
                subtract  
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    criterion_id ,
                    name ,
                    compares ,
                    range_start ,
                    range_end ,
                    percent ,
                    subtract 
                     
                FROM public.over_screen12') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        criterion_id integer,
                        name character varying ,
                        compares character varying ,
                        range_start numeric,
                        range_end numeric,
                        percent numeric,
                        subtract boolean
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('over_screen12_id_seq', (select max(id) + 1 from  over_screen12));
        ''')   
        return
        
    def sys_excelsa_standard(self):
        sql ='''
        INSERT INTO 
            excelsa_standard 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                criterion_id ,
                name ,
                compares ,
                range_start ,
                range_end ,
                percent ,
                subtract  
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    criterion_id ,
                    name ,
                    compares ,
                    range_start ,
                    range_end ,
                    percent ,
                    subtract 
                     
                FROM public.excelsa_standard') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        criterion_id integer,
                        name character varying ,
                        compares character varying ,
                        range_start numeric,
                        range_end numeric,
                        percent numeric,
                        subtract boolean
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('excelsa_standard_id_seq', (select max(id) + 1 from  excelsa_standard));
        ''')   
        return
    
    def sys_foreign_matter(self):
        sql ='''
        INSERT INTO 
            foreign_matter 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                criterion_id ,
                name ,
                compares ,
                range_start ,
                range_end ,
                percent ,
                subtract  
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    criterion_id ,
                    name ,
                    compares ,
                    range_start ,
                    range_end ,
                    percent ,
                    subtract 
                     
                FROM public.foreign_matter') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        criterion_id integer,
                        name character varying ,
                        compares character varying ,
                        range_start numeric,
                        range_end numeric,
                        percent numeric,
                        subtract boolean
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('foreign_matter_id_seq', (select max(id) + 1 from  foreign_matter));
        ''')   
        return
    
    def sys_mold_standard(self):
        sql ='''
        INSERT INTO 
            mold_standard 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                criterion_id ,
                name ,
                compares ,
                range_start ,
                range_end ,
                percent ,
                subtract  
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    criterion_id ,
                    name ,
                    compares ,
                    range_start ,
                    range_end ,
                    percent ,
                    subtract 
                     
                FROM public.mold_standard') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        criterion_id integer,
                        name character varying ,
                        compares character varying,
                        range_start numeric,
                        range_end numeric,
                        percent numeric,
                        subtract boolean
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('mold_standard_id_seq', (select max(id) + 1 from  mold_standard));
        ''')   
        return
    
    def sys_insect_bean(self):
        sql ='''
        INSERT INTO 
            insect_bean 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                criterion_id ,
                name  ,
                range_start ,
                range_end ,
                percent   
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    criterion_id ,
                    name  ,
                    range_start ,
                    range_end ,
                    percent 
                     
                FROM public.insect_bean') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        criterion_id integer,
                        name character varying,
                        range_start numeric,
                        range_end numeric,
                        percent numeric
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('insect_bean_id_seq', (select max(id) + 1 from  insect_bean));
        ''')   
        return
        
    def sys_brown_standard(self):
        sql ='''
        INSERT INTO 
            brown_standard 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                criterion_id ,
                name  ,
                range_start ,
                range_end ,
                percent ,
                "values" ,
                subtract ,
                check_values 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    criterion_id ,
                    name  ,
                    range_start ,
                    range_end ,
                    percent ,
                    "values" ,
                    subtract ,
                    check_values 
                     
                FROM public.brown_standard') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        criterion_id integer,
                        name character varying,
                        range_start numeric,
                        range_end numeric,
                        percent numeric,
                        "values" numeric,
                        subtract boolean,
                        check_values boolean
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('brown_standard_id_seq', (select max(id) + 1 from  brown_standard));
        ''')   
        return
    
    def sys_broken_standard(self):
        sql ='''
        INSERT INTO 
            broken_standard 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                criterion_id ,
                name   ,
                range_start ,
                range_end ,
                percent ,
                subtract  
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    criterion_id ,
                    name   ,
                    range_start ,
                    range_end ,
                    percent ,
                    subtract 
                     
                FROM public.broken_standard') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        criterion_id integer,
                        name character varying ,
                        range_start numeric,
                        range_end numeric,
                        percent numeric,
                        subtract boolean
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('broken_standard_id_seq', (select max(id) + 1 from  broken_standard));
        ''')   
        return
    
    def sys_degree_mc(self):
        sql ='''
        INSERT INTO 
            degree_mc 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                mconkett,
                deduction
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    mconkett,
                    deduction
                     
                FROM public.degree_mc') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        mconkett numeric,
                        deduction numeric
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('degree_mc_id_seq', (select max(id) + 1 from  degree_mc));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_kcs_criterions_mc(self):
        sql ='''
        INSERT INTO 
            kcs_criterions_mc 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                criterion_id ,                   
                name  ,
                percent   
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    
                    criterion_id ,                   
                    name  ,
                    percent    
                    
                FROM public.kcs_criterions_mc') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                                                
                    criterion_id integer,                    
                    name double precision,
                    percent double precision
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('kcs_criterions_mc_id_seq', (select max(id) + 1 from  kcs_criterions_mc));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_kcs_criterions_line(self):
        sql ='''
        INSERT INTO 
            kcs_criterions_line 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                ksc_id ,
                name  ,
                check_indicators ,
                type ,
                description  
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    ksc_id ,
                    name  ,
                    check_indicators ,
                    type ,
                    description  
                    
                FROM public.kcs_criterions_line') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    ksc_id integer,
                    name character varying ,
                    check_indicators character varying  ,
                    type character varying  ,
                    description text 
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('kcs_criterions_line_id_seq', (select max(id) + 1 from  kcs_criterions_line));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_kcs_criterions(self):
        sql ='''
        INSERT INTO 
            kcs_criterions 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                categ_id  ,
                product_id ,
                user_approve ,
                warehouse_id ,
                name   ,
                state  ,
                origin  ,
                from_date  ,
                to_date ,
                date_approve ,
                note  ,
                standard_excelsa ,
                percent_excelsa ,
                standard_screen18_16 ,
                percent_screen18_16 ,
                standard_screen13 ,
                percent_screen13 ,
                standard_screen18 ,
                percent_screen18 ,
                standard_screen19 ,
                percent_screen19 ,
                standard_screen20 ,
                percent_screen20 ,
                standard_burned ,
                percent_burned ,
                percent_fm ,
                degree_mc ,
                special ,
                finished_products
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date,  write_uid, 
                    categ_id  ,
                    product_id ,
                    user_approve ,
                    warehouse_id ,
                    name   ,
                    state  ,
                    origin  ,
                    from_date  ,
                    to_date ,
                    date_approve ,
                    note  ,
                    standard_excelsa ,
                    percent_excelsa ,
                    standard_screen18_16 ,
                    percent_screen18_16 ,
                    standard_screen13 ,
                    percent_screen13 ,
                    standard_screen18 ,
                    percent_screen18 ,
                    standard_screen19 ,
                    percent_screen19 ,
                    standard_screen20 ,
                    percent_screen20 ,
                    standard_burned ,
                    percent_burned ,
                    percent_fm ,
                    degree_mc ,
                    special ,
                    finished_products 
                    
                FROM public.kcs_criterions') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,      
                                              
                        categ_id integer ,
                        product_id integer,
                        user_approve integer,
                        warehouse_id integer,
                        name character varying  ,
                        state character varying ,
                        origin character varying ,
                        from_date date ,
                        to_date date,
                        date_approve date,
                        note text ,
                        standard_excelsa numeric,
                        percent_excelsa numeric,
                        standard_screen18_16 numeric,
                        percent_screen18_16 numeric,
                        standard_screen13 numeric,
                        percent_screen13 numeric,
                        standard_screen18 numeric,
                        percent_screen18 numeric,
                        standard_screen19 numeric,
                        percent_screen19 numeric,
                        standard_screen20 numeric,
                        percent_screen20 numeric,
                        standard_burned numeric,
                        percent_burned numeric,
                        percent_fm numeric,
                        degree_mc numeric,
                        special boolean,
                        finished_products boolean
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('kcs_criterions_id_seq', (select max(id) + 1 from  kcs_criterions));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
        
    