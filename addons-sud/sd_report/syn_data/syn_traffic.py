from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    def sys_traffic_run(self):
        self.env.cr.execute('''
            DELETE FROM traffic_contract_pcontract_rel;
            DELETE FROM x_fob_management_s_contract_rel;
            DELETE FROM traffic_contract;
        ''')
        
        self.sys_traffic_contract()
        self.sys_traffic_contract_pcontract_rel()
        self.sys_x_fob_management_s_contract_rel()
        self.sys_up_location_for_picking()
        self.sys_ned_origin()
        self.sys_x_unallocated_pcontract()
        # self.update_traffic_contract_mship()
    
    def dada_request_stock_material(self):
        sql='''
            INSERT INTO 
            ir_cron 
            (
                 id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    function character varying ,
                    args  ,
                    name ,
                    interval_type ,
                    numbercall ,
                    nextcall ,
                    priority ,
                    doall ,
                    active ,
                    user_id  ,
                    model ,
                    write_uid ,
                    interval_number ,
                    number_of_retries ,
                    is_api_reach 
            )        
        
        SELECT 
           *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    function character varying ,
                    args  ,
                    name ,
                    interval_type ,
                    numbercall ,
                    nextcall ,
                    priority ,
                    doall ,
                    active ,
                    user_id  ,
                    model ,
                    write_uid ,
                    interval_number ,
                    number_of_retries ,
                    is_api_reach 
                    
                FROM public.ir_cron') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        function character varying ,
                        args text ,
                        name character varying  NOT NULL,
                        interval_type character varying ,
                        numbercall integer,
                        nextcall timestamp without time zone NOT NULL,
                        priority integer,
                        doall boolean,
                        active boolean,
                        user_id integer NOT NULL,
                        model character varying ,
                        write_uid integer,
                        interval_number integer,
                        number_of_retries integer,
                        is_api_reach boolean
                    )
        
        '''
    def update_traffic_contract_mship(self):
        sql ='''
            UPDATE traffic_contract set contract_mship = foo.contract_mship
            FROM 
            (
                SELECT 
                    id, contract_mship
                   
                    FROM public.dblink
                        ('%s',
                         'SELECT 
                            id, 
                            contract_mship                        
                        FROM public.traffic_contract') 
                        AS DATA(id INTEGER,              
                                contract_mship integer
                            )
                )foo 
                where traffic_contract.id = foo.id
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
    
    
    def sys_daily_confirmation(self):
        sql ='''
        INSERT INTO 
            daily_confirmation 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                user_id ,
                failure ,
                name  ,
                state  ,
                file_name  ,
                warning_mess  ,
                exchange_rate ,
                date_create ,
                liffe ,
                diff ,
                cost_price 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('%s',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    
                    user_id ,
                    failure ,
                    name  ,
                    state  ,
                    file_name  ,
                    warning_mess  ,
                    exchange_rate ,
                    date_create ,
                    liffe ,
                    diff ,
                    cost_price 
                    
                    
                FROM public.daily_confirmation') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        user_id integer,
                        failure integer,
                        name character varying ,
                        state character varying ,
                        file_name character varying(100) ,
                        warning_mess text ,
                        exchange_rate numeric,
                        date_create timestamp without time zone,
                        liffe double precision,
                        diff double precision,
                        cost_price double precision
                    )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('daily_confirmation_id_seq', (select max(id) + 1 from  daily_confirmation));
        ''')   
        
        return
    
    def sys_daily_confirmation_line(self):
        sql ='''
        INSERT INTO 
            daily_confirmation_line
            (
                id,
                create_date,create_uid,
                write_date, write_uid, 
                                    
                daily_id ,
                contract_id ,
                p_contract  ,
                liffe  ,
                diff  ,
                diff_price  ,
                exchange_rate  ,
                qty  
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('%s',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                
                    daily_id ,
                    contract_id ,
                    p_contract  ,
                    liffe  ,
                    diff  ,
                    diff_price  ,
                    exchange_rate  ,
                    qty  
                    
                    
                FROM public.daily_confirmation_line') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        
                        daily_id integer,
                        contract_id integer,
                        p_contract character varying ,
                        liffe double precision,
                        diff double precision,
                        diff_price double precision,
                        exchange_rate double precision,
                        qty double precision
                    )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('daily_confirmation_line_id_seq', (select max(id) + 1 from  daily_confirmation_line));
        ''')   
        
        return
    
    
    
    def sys_certificate_s_contract_ref(self):
        sql ='''
        INSERT INTO 
            certificate_s_contract
            (
                s_contract_id, 
                certificate_id
            )        
        
        SELECT 
            *
            FROM public.dblink
                    ('%s',
                     'SELECT 
                        s_contract_id, 
                        certificate_id
                    FROM public.certificate_s_contract') 
                        AS DATA(s_contract_id integer ,
                                certificate_id integer 
                        )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
    
    def sys_certificate_shipping_instruction_ref(self):
        sql ='''
        INSERT INTO 
            certificate_shipping_instruction
            (
                shipping_instruction_id, 
                certificate_id
            )        
        
        SELECT 
            *
            FROM public.dblink
                    ('%s',
                     'SELECT 
                        shipping_instruction_id, 
                        certificate_id
                    FROM public.certificate_shipping_instruction') 
                        AS DATA(shipping_instruction_id integer ,
                                certificate_id integer 
                        )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
    
    
    def update_traffic(self):
        sql = '''
            UPDATE
                s_contract set traffic_link_id = foo.traffic_link_id
            FROM(
                SELECT 
                        *
                FROM public.dblink
                    ('%s',
                     'SELECT 
                        id ,
                        traffic_link_id
                    FROM public.s_contract') 
                    AS DATA(
                        id integer,
                        traffic_link_id integer
                    )) foo
                where s_contract.id = foo.id
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        
    
    def sys_ned_origin(self):
        sql ='''
        INSERT INTO 
            ned_origin 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name,
                code
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    name,
                    code
                    
                FROM public.ned_origin') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name character varying(256) ,
                        code character varying(128)
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('ned_origin_id_seq', (select max(id) + 1 from  ned_origin));
        ''')   
        return
    
    def sys_x_unallocated_pcontract(self):
        sql ='''
        INSERT INTO 
            x_unallocated_pcontract 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                product_id ,
                partner_id ,
                ship_month_id ,
                name  ,
                quality ,
                origin ,
                entity_date ,
                dd_from ,
                dd_to ,
                description ,
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
                    product_id ,
                    partner_id ,
                    ship_month_id ,
                    name  ,
                    quality ,
                    origin ,
                    entity_date ,
                    dd_from ,
                    dd_to ,
                    description ,
                    quantity 
                    
                FROM public.x_unallocated_pcontract') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        product_id integer,
                        partner_id integer,
                        ship_month_id integer,
                        name character varying(64) ,
                        quality character varying(128) ,
                        origin character varying ,
                        entity_date date,
                        dd_from date,
                        dd_to date,
                        description text,
                        quantity double precision
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('x_unallocated_pcontract_id_seq', (select max(id) + 1 from  x_unallocated_pcontract));
        ''')   
        return
    
    def sys_up_location_for_picking(self):
        sql = '''
            UPDATE
                stock_picking_type set default_location_src_id = foo.default_location_src_id, 
                default_location_dest_id = foo.default_location_dest_id,
                picking_type_npe_id = foo.picking_type_npe_id,
                picking_type_nvp_id = foo.picking_type_nvp_id
            FROM(
                SELECT 
                        *
                FROM public.dblink
                    ('%s',
                     'SELECT 
                        id ,
                        default_location_src_id,
                        default_location_dest_id,
                        picking_type_npe_id,
                        picking_type_nvp_id
                        
                    FROM public.stock_picking_type') 
                    AS DATA(
                        id integer,
                        default_location_src_id integer,
                        default_location_dest_id integer,
                        picking_type_npe_id integer,
                        picking_type_nvp_id integer
                    )) foo
                where stock_picking_type.id = foo.id
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
    
    def sys_x_fob_management_s_contract_rel(self):
        sql ='''
        INSERT INTO 
            x_fob_management_s_contract_rel 
            (
                fob_management_id,
                s_contract_id
            )        
        
        SELECT 
            *
        FROM public.dblink
            ('%s',
             'SELECT 
                fob_management_id,
                s_contract_id
            FROM public.x_fob_management_s_contract_rel') 
            AS DATA(
                fob_management_id integer,
                s_contract_id integer
            )
        '''%(self.server_db_link)
        print(sql)
        self.env.cr.execute(sql)
        
    
    def sys_traffic_contract_pcontract_rel(self):
        sql ='''
        INSERT INTO 
            traffic_contract_pcontract_rel 
            (
                sid,
                pid
            )        
        
        SELECT 
            sid,
            pid
        FROM public.dblink
                ('%s',
                 'SELECT 
                    sid,
                    pid
                FROM public.traffic_contract_pcontract_rel') 
                AS DATA(
                        sid integer,
                        pid integer
                    )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
      
    def sys_traffic_contract(self):
        sql ='''
        INSERT INTO 
            traffic_contract 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                shipby_id ,
                    shipt_month ,
                    partner_id ,
                    standard_id ,
                    certificate_id ,
                    packing_id ,
                    incoterms_id ,
                    pic_id ,
                    port_of_loading ,
                    port_of_discharge ,
                    shipping_line_id ,
                    parent_id ,
                    status  ,
                    origin  ,
                    name  ,
                    client_ref ,
                    pss_type  ,
                    delivery_type  ,
                    x_p_contract_link  ,
                    shipper_id  ,
                    pss_amount_send ,
                    booking_ref_no  ,
                    remarks  ,
                    pss_late_ontime  ,
                    od_doc_rec_awb  ,
                    awb_sent_no  ,
                    x_remark1  ,
                    x_remark2  ,
                    state  ,
                    x_stuff_place  ,
                    allocated_date ,
                    start_of_ship_period ,
                    end_of_ship_period ,
                    end_of_ship_period_actual ,
                    si_sent_date ,
                    si_received_date ,
                    pss_send_schedule ,
                    pss_approved_date ,
                    factory_etd ,
                    nominated_etd ,
                    bill_date ,
                    pss_sent_date ,
                    eta ,
                    late_ship_end ,
                    late_ship_est ,
                    od_doc_rec_date ,
                    od_doc_sent_date ,
                    x_stuff_date ,
                    p_quality  ,
                    cause_by  ,
                    p_qty ,
                    no_of_pack ,
                    precalculated_freight_cost ,
                    freight ,
                    act_freight_cost 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('%s',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    shipby_id ,
                    shipt_month ,
                    partner_id ,
                    standard_id ,
                    certificate_id ,
                    packing_id ,
                    incoterms_id ,
                    pic_id ,
                    port_of_loading ,
                    port_of_discharge ,
                    shipping_line_id ,
                    parent_id ,
                    status  ,
                    origin  ,
                    name  ,
                    client_ref ,
                    pss_type  ,
                    delivery_type  ,
                    x_p_contract_link  ,
                    shipper_id  ,
                    pss_amount_send ,
                    booking_ref_no  ,
                    remarks  ,
                    pss_late_ontime  ,
                    od_doc_rec_awb  ,
                    awb_sent_no  ,
                    x_remark1  ,
                    x_remark2  ,
                    state  ,
                    x_stuff_place  ,
                    allocated_date ,
                    start_of_ship_period ,
                    end_of_ship_period ,
                    end_of_ship_period_actual ,
                    si_sent_date ,
                    si_received_date ,
                    pss_send_schedule ,
                    pss_approved_date ,
                    factory_etd ,
                    nominated_etd ,
                    bill_date ,
                    pss_sent_date ,
                    eta ,
                    late_ship_end ,
                    late_ship_est ,
                    od_doc_rec_date ,
                    od_doc_sent_date ,
                    x_stuff_date ,
                    p_quality  ,
                    cause_by  ,
                    p_qty ,
                    no_of_pack ,
                    precalculated_freight_cost ,
                    freight ,
                    act_freight_cost 
                    
                FROM public.traffic_contract') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer, 
                                               
                    shipby_id integer,
                    shipt_month integer,
                    partner_id integer,
                    standard_id integer,
                    certificate_id integer,
                    packing_id integer,
                    incoterms_id integer,
                    pic_id integer,
                    port_of_loading integer,
                    port_of_discharge integer,
                    shipping_line_id integer,
                    parent_id integer,
                    status character varying ,
                    origin character varying ,
                    name character varying(128) ,
                    client_ref character varying(128) ,
                    pss_type character varying ,
                    delivery_type character varying ,
                    x_p_contract_link character varying(256) ,
                    shipper_id character varying(256) ,
                    pss_amount_send character varying(256) ,
                    booking_ref_no character varying ,
                    remarks character varying ,
                    pss_late_ontime character varying(128) ,
                    od_doc_rec_awb character varying(256) ,
                    awb_sent_no character varying(256) ,
                    x_remark1 character varying(256) ,
                    x_remark2 character varying(256) ,
                    state character varying ,
                    x_stuff_place character varying(256) ,
                    allocated_date date,
                    start_of_ship_period date,
                    end_of_ship_period date,
                    end_of_ship_period_actual date,
                    si_sent_date date,
                    si_received_date date,
                    pss_send_schedule date,
                    pss_approved_date date,
                    factory_etd date,
                    nominated_etd date,
                    bill_date date,
                    pss_sent_date date,
                    eta date,
                    late_ship_end date,
                    late_ship_est date,
                    od_doc_rec_date date,
                    od_doc_sent_date date,
                    x_stuff_date date,
                    p_quality text ,
                    cause_by text ,
                    p_qty double precision,
                    no_of_pack double precision,
                    precalculated_freight_cost double precision,
                    freight double precision,
                    act_freight_cost double precision
                )
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        
        self.env.cr.execute('''
            SELECT setval('traffic_contract_id_seq', (select max(id) + 1 from  traffic_contract));
        ''')   
        
        return
    


        
    