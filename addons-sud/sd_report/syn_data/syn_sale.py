from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
# from pip._vendor.pygments.lexer import _inherit
DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    def syz_sale_contract(self):
        self.env.cr.execute('''
            DELETE FROM s_period;
            DELETE FROM s_ship_by;
            DELETE FROM s_pic;
            DELETE FROM account_incoterms;
            DELETE FROM ned_certificate_license;
            DELETE FROM s_contract;
            DELETE FROM s_contract_line;
            
            DELETE FROM shipping_instruction;
            DELETE FROM shipping_instruction_line;
            
            DELETE FROM sale_contract;
            DELETE FROM sale_contract_line;
            
            DELETE FROM sale_contract_certificate_ref;
            
            DELETE FROM delivery_order;
            DELETE FROM delivery_order_line;
            
            DELETE FROM post_shipment_line;
            DELETE FROM post_shipment;
        ''')
        
        self.s_period()
        self.sys_s_ship_by()
        self.sys_s_pic()
        self.sys_account_incoterms()
        self.sys_ned_certificate_license()
        self.sys_s_contract()
        self.sys_s_contract_line()
        self.sys_shipping_instruction()
        self.sys_shipping_instruction_line()
        
        #Cái này chưa hiểu, nên chưa cho run
        # sefl.sys_sale_contract_deatail()
    
    def syz_sale_contract_1(self):
        self.env.cr.execute('''
            
            DELETE FROM sale_contract;
            DELETE FROM sale_contract_line;
            
            DELETE FROM sale_contract_certificate_ref;
            
            DELETE FROM delivery_order;
            DELETE FROM delivery_order_line;
            
            DELETE FROM post_shipment_line;
            DELETE FROM post_shipment;
        ''')
        
        self.sys_sale_contract()
        self.sys_sale_contract_line()
        self.sys_sale_contract_certificate_ref()
        
    
    def update_lot_for_s_contract(self):
        sql ='''
            UPDATE s_contract set wr_line = xoo.lot_id
            from
            (
                SELECT 
                    *
                    FROM public.dblink
                        ('%s',
                            'SELECT s.id contract_id, p.id lot_id   
                            FROM s_contract s 
                                join stock_stack p on s.wr_line = p.id') 
                            AS DATA(
                                    contract_id integer,
                                    lot_id integer 
                                )
                        
                ) xoo
                where s_contract.id = xoo.contract_id
        '''%(self.server_db_link)
        self.env.cr.execute(sql)
        return
    
        
        
    def Update_origin_new_for_scontract(self):
        sql ='''
            UPDATE s_contract set origin_new = foo.country_id
            FROM (
                SELECT s.id,s.origin, s.origin_new, rc.id as country_id
                from s_contract s left join res_country rc on s.origin =  rc.code) foo
            WHERE s_contract.id = foo.id
        '''
        self.env.cr.execute(sql)
    
    def syz_sale_contract_2(self):
        self.Update_origin_new_for_scontract()
        self.sys_delivery_order()
        self.sys_delivery_order_line()
        
        
    
    
    def syz_sale_contract_3(self):
        self.sys_post_shipment()
        self.sys_post_shipment_line()
    
    
    def compute_shipping_instruction(self):
        for i in self.env['shipping.instruction'].search([]):
            i._compute_contracts()
            # i._compute_invoices()
            i._compute_line_qty()
            i._compute_cont_qty()
            i.get_allocated_s()
            i.get_allocated_p()
            
            i.get_quality()
            i._invoiced_qty()
            i._do_qty() # hàm này phải có DO mới chạy được
    # def compute_shipping_instruction_line(self):
    #     for i in self.env['shipping.instruction.line'].search([]):
    
    def compute_do(self):
        for i in self.env['delivery.order'].search([]):
            i._total_qty()
            i._factory_qty()
            
    def compute_sale_contract(self):
        for i in self.env['sale.contract'].search([]):
            # i._compute_pickings()
            i._compute_deliverys()
            i._compute_invoices()
            i.get_pcontract()
            i.get_quantity_contract()
    
    def compute_sale_contract_line(self):
        for i in self.env['sale.contract.line'].search([]):
            i._compute_amount()
            i._compute_premium()
            i._provisional_price()
            i._final_price()
    
    def compute_scontract_line(self):
        for i in self.env['s.contract.line'].search([]):
            i._compute_amount()
            i._compute_state()
            i.compute_remaning_qty()
    
    def compute_scontract(self):
        for i in self.env['s.contract'].search([]):
            i.compute_license_char_number()
            i.compute_p_allocated()
            i.compute_license_char_number()
            i._get_franchise()
            i._total_remaining_qty()
            
    def sys_s_contract(self):
        sql ='''
        INSERT INTO 
            s_contract 
            (
                id, 
                create_date, create_uid, 
                write_date,  write_uid, 
                company_representative ,
                warehouse_id  ,
                partner_id  ,
                customer_representative ,
                partner_invoice_id ,
                partner_shipping_id ,
                currency_id  ,
                payment_term_id ,
                bank_id ,
                user_approve ,
                port_of_loading ,
                port_of_discharge ,
                product_id ,
                shipby_id ,
                crop_id  ,
                incoterms_id ,
                s_contract_link ,
                --traffic_link_id ,
                delivery_place_id ,
                pic_id ,
                shipt_month ,
                shipping_line_id ,
                certificate_id ,
                packing_id ,
                standard_id ,
                name   ,
                picking_policy  ,
                state   ,
                type   ,
                acc_number   ,
                trader   ,
                dispatch_mode   ,
                container_status   ,
                weights   ,
                transportation_charges ,
                qty_condition ,
                char_license ,
                --certificate_supplier ,
                x_coffee_type ,
                status ,
                shipper_id  ,
                buyer_ref ,
                wr_no ,
                bb_info ,
                fm_info ,
                mc_info ,
                abv_scr  ,
                client_ref   ,
                pss_type   ,
                delivery_type ,
                bill_no   ,
                od_doc_rec_awb  ,
                awb_sent_no   ,
                pss_amount_send  ,
                pss_late_ontime   ,
                booking_ref_no   ,
                ico_permit_no   ,
                transaction   ,
                vessel_flight_no   ,
                remarks   ,
                origin   ,
                date ,
                validity_date  ,
                expiration_date ,
                date_approve ,
                date_done ,
                deadline  ,
                shipment_date ,
                fob_delivery ,
                date_pss ,
                date_catalog ,
                wr_date ,
                allocated_date ,
                start_of_ship_period ,
                end_of_ship_period ,
                end_of_ship_period_actual ,
                bill_date ,
                si_received_date ,
                pss_send_schedule ,
                si_sent_date ,
                nominated_etd ,
                od_doc_rec_date ,
                od_doc_sent_date ,
                pss_sent_date ,
                pss_approved_date ,
                factory_etd ,
                booking_date ,
                reach_date ,
                ico_permit_date ,
                eta ,
                late_ship_end ,
                late_ship_est ,
                note  ,
                marking  ,
                p_quality  ,
                cause_by  ,
                amount_untaxed ,
                amount_tax ,
                amount_total ,
                --p_contract_diff ,
                --total_remaining_qty ,
                pss ,
                check_by_cont ,
                pss_sent ,
                pss_approved ,
                x_is_bonded ,
                exchange_rate  ,
                delivery_tolerance  ,
                --p_allocated  ,
                --p_unallocated  ,
                differential  ,
                allowed_franchise  ,
                p_qty  ,
                no_of_pack  ,
                instored_wei  ,
                doc_wei  ,
                real_wei  ,
                loss_wei  ,
                precalculated_freight_cost ,
                act_freight_cost ,
                freight  ,
                license_id ,
                expired_date,
                company_id,
                certificate,
                cert_validity,
                stock_validity,
                status_p, 
                bag_in_stock, 
                bag_out_stock, 
                allocated_not_out, 
                allocated_bag_not_out
            )        
        
        SELECT 
            id, 
                create_date, create_uid, 
                write_date, write_uid, 
                company_representative ,
                warehouse_id  ,
                partner_id  ,
                customer_representative ,
                partner_invoice_id ,
                partner_shipping_id ,
                currency_id  ,
                payment_term_id ,
                bank_id ,
                user_approve ,
                port_of_loading ,
                port_of_discharge ,
                product_id ,
                shipby_id ,
                crop_id  ,
                incoterms_id ,
                s_contract_link ,
                --traffic_link_id ,
                delivery_place_id ,
                pic_id ,
                shipt_month ,
                shipping_line_id ,
                certificate_id ,
                packing_id ,
                standard_id ,
                name   ,
                picking_policy  ,
                state   ,
                type   ,
                acc_number   ,
                trader   ,
                dispatch_mode   ,
                container_status   ,
                weights   ,
                transportation_charges ,
                qty_condition ,
                char_license ,
                --certificate_supplier ,
                x_coffee_type ,
                status ,
                shipper_id  ,
                buyer_ref ,
                wr_no ,
                bb_info ,
                fm_info ,
                mc_info ,
                abv_scr  ,
                client_ref   ,
                pss_type   ,
                delivery_type ,
                bill_no   ,
                od_doc_rec_awb  ,
                awb_sent_no   ,
                pss_amount_send  ,
                pss_late_ontime   ,
                booking_ref_no   ,
                ico_permit_no   ,
                transaction   ,
                vessel_flight_no   ,
                remarks   ,
                origin   ,
                date ,
                validity_date  ,
                expiration_date ,
                date_approve ,
                date_done ,
                deadline  ,
                shipment_date ,
                fob_delivery ,
                date_pss ,
                date_catalog ,
                wr_date ,
                allocated_date ,
                start_of_ship_period ,
                end_of_ship_period ,
                end_of_ship_period_actual ,
                bill_date ,
                si_received_date ,
                pss_send_schedule ,
                si_sent_date ,
                nominated_etd ,
                od_doc_rec_date ,
                od_doc_sent_date ,
                pss_sent_date ,
                pss_approved_date ,
                factory_etd ,
                booking_date ,
                reach_date ,
                ico_permit_date ,
                eta ,
                late_ship_end ,
                late_ship_est ,
                note  ,
                marking  ,
                p_quality  ,
                cause_by  ,
                amount_untaxed ,
                amount_tax ,
                amount_total ,
                --p_contract_diff ,
                --total_remaining_qty ,
                pss ,
                check_by_cont ,
                pss_sent ,
                pss_approved ,
                x_is_bonded ,
                exchange_rate  ,
                delivery_tolerance  ,
                --p_allocated  ,
                --p_unallocated  ,
                differential  ,
                allowed_franchise  ,
                p_qty  ,
                no_of_pack  ,
                instored_wei  ,
                doc_wei  ,
                real_wei  ,
                loss_wei  ,
                precalculated_freight_cost ,
                act_freight_cost ,
                freight  ,
                license_id ,
                expired_date,
                1 as  company_id,
                certificate,
                cert_validity,
                stock_validity,
                status_p, 
                bag_in_stock, 
                bag_out_stock, 
                allocated_not_out, 
                allocated_bag_not_out
                
            FROM public.dblink
            ('sucdendblink',
             'SELECT 
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                company_representative ,
                warehouse_id  ,
                partner_id  ,
                customer_representative ,
                partner_invoice_id ,
                partner_shipping_id ,
                currency_id  ,
                payment_term_id ,
                bank_id ,
                user_approve ,
                port_of_loading ,
                port_of_discharge ,
                product_id ,
                shipby_id ,
                crop_id  ,
                incoterms_id ,
                s_contract_link ,
                --traffic_link_id ,
                delivery_place_id ,
                pic_id ,
                shipt_month ,
                shipping_line_id ,
                certificate_id ,
                packing_id ,
                standard_id ,
                name   ,
                picking_policy  ,
                state   ,
                type   ,
                acc_number   ,
                trader   ,
                dispatch_mode   ,
                container_status   ,
                weights   ,
                transportation_charges ,
                qty_condition ,
                char_license ,
                --certificate_supplier ,
                x_coffee_type ,
                status ,
                shipper_id  ,
                buyer_ref ,
                wr_no ,
                bb_info ,
                fm_info ,
                mc_info ,
                abv_scr  ,
                client_ref   ,
                pss_type   ,
                delivery_type ,
                bill_no   ,
                od_doc_rec_awb  ,
                awb_sent_no   ,
                pss_amount_send  ,
                pss_late_ontime   ,
                booking_ref_no   ,
                ico_permit_no   ,
                transaction   ,
                vessel_flight_no   ,
                remarks   ,
                origin   ,
                date ,
                validity_date  ,
                expiration_date ,
                date_approve ,
                date_done ,
                deadline  ,
                shipment_date ,
                fob_delivery ,
                date_pss ,
                date_catalog ,
                wr_date ,
                allocated_date ,
                start_of_ship_period ,
                end_of_ship_period ,
                end_of_ship_period_actual ,
                bill_date ,
                si_received_date ,
                pss_send_schedule ,
                si_sent_date ,
                nominated_etd ,
                od_doc_rec_date ,
                od_doc_sent_date ,
                pss_sent_date ,
                pss_approved_date ,
                factory_etd ,
                booking_date ,
                reach_date ,
                ico_permit_date ,
                eta ,
                late_ship_end ,
                late_ship_est ,
                note  ,
                marking  ,
                p_quality  ,
                cause_by  ,
                amount_untaxed ,
                amount_tax ,
                amount_total ,
                --p_contract_diff ,
                --total_remaining_qty ,
                pss ,
                check_by_cont ,
                pss_sent ,
                pss_approved ,
                x_is_bonded ,
                exchange_rate  ,
                delivery_tolerance  ,
                --p_allocated  ,
                --p_unallocated  ,
                differential  ,
                allowed_franchise  ,
                p_qty  ,
                no_of_pack  ,
                instored_wei  ,
                doc_wei  ,
                real_wei  ,
                loss_wei  ,
                precalculated_freight_cost ,
                act_freight_cost ,
                freight  ,
                license_id ,
                expired_date,
                certificate,
                cert_validity,
                stock_validity,
                status_p, 
                bag_in_stock, 
                bag_out_stock, 
                allocated_not_out, 
                allocated_bag_not_out
             
            FROM public.s_contract') 
            AS DATA(id INTEGER,
                create_date timestamp without time zone,
                create_uid integer,
                write_date timestamp without time zone,
                write_uid integer, 
                                           
                company_representative integer,
                warehouse_id integer ,
                partner_id integer ,
                customer_representative integer,
                partner_invoice_id integer,
                partner_shipping_id integer,
                currency_id integer ,
                payment_term_id integer,
                bank_id integer,
                user_approve integer,
                port_of_loading integer,
                port_of_discharge integer,
                product_id integer,
                shipby_id integer,
                crop_id integer ,
                incoterms_id integer,
                s_contract_link integer,
                --traffic_link_id integer,
                delivery_place_id integer,
                pic_id integer,
                shipt_month integer,
                shipping_line_id integer,
                certificate_id integer,
                packing_id integer,
                standard_id integer,
                name character varying ,
                picking_policy character varying ,
                state character varying ,
                type character varying ,
                acc_number character varying ,
                trader character varying ,
                dispatch_mode character varying ,
                container_status character varying ,
                weights character varying ,
                transportation_charges character varying ,
                qty_condition character varying ,
                char_license character varying ,
                --certificate_supplier character varying ,
                x_coffee_type character varying(128) ,
                status character varying ,
                shipper_id character varying(256) ,
                buyer_ref character varying ,
                wr_no character varying(256) ,
                bb_info character varying(128) ,
                fm_info character varying(128) ,
                mc_info character varying(128) ,
                abv_scr character varying(128) ,
                client_ref character varying ,
                pss_type character varying ,
                delivery_type character varying ,
                bill_no character varying ,
                od_doc_rec_awb character varying(256) ,
                awb_sent_no character varying(256) ,
                pss_amount_send character varying(256) ,
                pss_late_ontime character varying(128) ,
                booking_ref_no character varying ,
                ico_permit_no character varying ,
                transaction character varying ,
                vessel_flight_no character varying ,
                remarks character varying ,
                origin character varying ,
                date date,
                validity_date date ,
                expiration_date date,
                date_approve date,
                date_done date,
                deadline date ,
                shipment_date date,
                fob_delivery date,
                date_pss date,
                date_catalog date,
                wr_date date,
                allocated_date date,
                start_of_ship_period date,
                end_of_ship_period date,
                end_of_ship_period_actual date,
                bill_date date,
                si_received_date date,
                pss_send_schedule date,
                si_sent_date date,
                nominated_etd date,
                od_doc_rec_date date,
                od_doc_sent_date date,
                pss_sent_date date,
                pss_approved_date date,
                factory_etd date,
                booking_date date,
                reach_date date,
                ico_permit_date date,
                eta date,
                late_ship_end date,
                late_ship_est date,
                note text,
                marking text ,
                p_quality text ,
                cause_by text ,
                amount_untaxed numeric,
                amount_tax numeric,
                amount_total numeric,
               -- p_contract_diff numeric,
                --total_remaining_qty numeric,
                pss boolean,
                check_by_cont boolean,
                pss_sent boolean,
                pss_approved boolean,
                x_is_bonded boolean,
                exchange_rate double precision,
                delivery_tolerance double precision,
                --p_allocated double precision,
                --p_unallocated double precision,
                differential double precision,
                allowed_franchise double precision,
                p_qty double precision,
                no_of_pack double precision,
                instored_wei double precision,
                doc_wei double precision,
                real_wei double precision,
                loss_wei double precision,
                precalculated_freight_cost double precision,
                act_freight_cost double precision,
                freight double precision,
                license_id integer,
                expired_date date,
                
                
                certificate character varying,
                cert_validity date,
                stock_validity date,
                status_p character varying, 
                bag_in_stock double precision, 
                bag_out_stock double precision, 
                allocated_not_out double precision, 
                allocated_bag_not_out double precision
            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('s_contract_id_seq', (select max(id) + 1 from  s_contract));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
         
    def sys_ned_certificate_license(self):
        sql ='''
        INSERT INTO 
            ned_certificate_license 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                certificate_id  ,
                partner_id  ,
                name    ,
                state   ,
                certification_date ,
                expired_date  ,
                quota  ,
                initial_amount ,
                consumed_amount ,
                sales_amount ,
                active ,
                parent_id ,
                type   ,
                remark_cert   ,
                type_license   ,
                purchased_amount ,
                balance ,
                faq_purchase  ,
                g1_s18_purchase  ,
                g1_s16_purchase  ,
                g2_purchase  ,
                faq_allocated  ,
                g1_s18_allocated  ,
                g1_s16_allocated  ,
                g2_allocated  ,
                faq_allocated_not_out  ,
                g1_s18_allocated_not_out  ,
                g1_s16_allocated_not_out  ,
                g2_allocated_not_out  ,
                faq_allocated_out  ,
                g1_s18_allocated_out  ,
                g1_s16_allocated_out  ,
                g2_allocated_out  ,
                faq_unallocated  ,
                g1_s18_unallocated  ,
                g1_s16_unallocated  ,
                g2_unallocated  ,
                faq_balance  ,
                g1_s18_balance  ,
                g1_s16_balance  ,
                g2_balance  ,
                faq_derivable  ,
                g1_s18_derivable  ,
                g1_s16_derivable  ,
                g2_derivable  ,
                final_balance  ,
                faq_tobe_received  ,
                g1_s18_tobe_received  ,
                g1_s16_tobe_received  ,
                g2_tobe_received  ,
                faq_position  ,
                g1_s18_position ,
                g1_s16_position ,
                g2_position  ,
                crop_id 
            )        
        
        SELECT 
           id,
                create_date,create_uid,
                write_date, write_uid,                     
                certificate_id  ,
                partner_id  ,
                name    ,
                state   ,
                certification_date ,
                expired_date  ,
                quota  ,
                initial_amount ,
                consumed_amount ,
                sales_amount ,
                active ,
                parent_id ,
                type   ,
                remark_cert   ,
                type_license   ,
                purchased_amount ,
                balance ,
                faq_purchase  ,
                g1_s18_purchase  ,
                g1_s16_purchase  ,
                g2_purchase  ,
                faq_allocated  ,
                g1_s18_allocated  ,
                g1_s16_allocated  ,
                g2_allocated  ,
                faq_allocated_not_out  ,
                g1_s18_allocated_not_out  ,
                g1_s16_allocated_not_out  ,
                g2_allocated_not_out  ,
                faq_allocated_out  ,
                g1_s18_allocated_out  ,
                g1_s16_allocated_out  ,
                g2_allocated_out  ,
                faq_unallocated  ,
                g1_s18_unallocated  ,
                g1_s16_unallocated  ,
                g2_unallocated  ,
                faq_balance  ,
                g1_s18_balance  ,
                g1_s16_balance  ,
                g2_balance  ,
                faq_derivable  ,
                g1_s18_derivable  ,
                g1_s16_derivable  ,
                g2_derivable  ,
                final_balance  ,
                faq_tobe_received  ,
                g1_s18_tobe_received  ,
                g1_s16_tobe_received  ,
                g2_tobe_received  ,
                faq_position  ,
                g1_s18_position ,
                g1_s16_position ,
                g2_position  ,
                crop_id 
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date,  write_uid, 
                    certificate_id  ,
                    partner_id  ,
                    name    ,
                    state   ,
                    certification_date ,
                    expired_date  ,
                    quota  ,
                    initial_amount ,
                    consumed_amount ,
                    sales_amount ,
                    active ,
                    parent_id ,
                    type   ,
                    remark_cert   ,
                    type_license   ,
                    purchased_amount ,
                    balance ,
                    faq_purchase  ,
                    g1_s18_purchase  ,
                    g1_s16_purchase  ,
                    g2_purchase  ,
                    faq_allocated  ,
                    g1_s18_allocated  ,
                    g1_s16_allocated  ,
                    g2_allocated  ,
                    faq_allocated_not_out  ,
                    g1_s18_allocated_not_out  ,
                    g1_s16_allocated_not_out  ,
                    g2_allocated_not_out  ,
                    faq_allocated_out  ,
                    g1_s18_allocated_out  ,
                    g1_s16_allocated_out  ,
                    g2_allocated_out  ,
                    faq_unallocated  ,
                    g1_s18_unallocated  ,
                    g1_s16_unallocated  ,
                    g2_unallocated  ,
                    faq_balance  ,
                    g1_s18_balance  ,
                    g1_s16_balance  ,
                    g2_balance  ,
                    faq_derivable  ,
                    g1_s18_derivable  ,
                    g1_s16_derivable  ,
                    g2_derivable  ,
                    final_balance  ,
                    faq_tobe_received  ,
                    g1_s18_tobe_received  ,
                    g1_s16_tobe_received  ,
                    g2_tobe_received  ,
                    faq_position  ,
                    g1_s18_position ,
                    g1_s16_position ,
                    g2_position  ,
                    crop_id 
                    
                    
                FROM public.ned_certificate_license') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    
                    certificate_id integer ,
                    partner_id integer ,
                    name character varying  ,
                    state character varying ,
                    certification_date date,
                    expired_date date ,
                    quota numeric ,
                    initial_amount numeric,
                    consumed_amount numeric,
                    sales_amount numeric,
                    active boolean,
                    parent_id integer,
                    type character varying ,
                    remark_cert character varying ,
                    type_license character varying ,
                    purchased_amount numeric,
                    balance numeric,
                    faq_purchase double precision,
                    g1_s18_purchase double precision,
                    g1_s16_purchase double precision,
                    g2_purchase double precision,
                    faq_allocated double precision,
                    g1_s18_allocated double precision,
                    g1_s16_allocated double precision,
                    g2_allocated double precision,
                    faq_allocated_not_out double precision,
                    g1_s18_allocated_not_out double precision,
                    g1_s16_allocated_not_out double precision,
                    g2_allocated_not_out double precision,
                    faq_allocated_out double precision,
                    g1_s18_allocated_out double precision,
                    g1_s16_allocated_out double precision,
                    g2_allocated_out double precision,
                    faq_unallocated double precision,
                    g1_s18_unallocated double precision,
                    g1_s16_unallocated double precision,
                    g2_unallocated double precision,
                    faq_balance double precision,
                    g1_s18_balance double precision,
                    g1_s16_balance double precision,
                    g2_balance double precision,
                    faq_derivable double precision,
                    g1_s18_derivable double precision,
                    g1_s16_derivable double precision,
                    g2_derivable double precision,
                    final_balance double precision,
                    faq_tobe_received double precision,
                    g1_s18_tobe_received double precision,
                    g1_s16_tobe_received double precision,
                    g2_tobe_received double precision,
                    faq_position double precision,
                    g1_s18_position double precision,
                    g1_s16_position double precision,
                    g2_position double precision,
                    crop_id integer
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('ned_certificate_license_id_seq', (select max(id) + 1 from ned_certificate_license));
        ''')  
    
    def sys_s_pic(self):
        sql ='''
        INSERT INTO 
            s_pic 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name,
                code
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date, write_uid, 
            name,
            code
            FROM public.dblink
                        ('sucdendblink',
                         'SELECT 
                            id, 
                            create_date, create_uid, 
                            write_date, write_uid, 
                            name,
                            code
                        FROM public.s_pic') 
                        AS DATA(id INTEGER,
                                create_date timestamp without time zone,
                                create_uid integer,
                                write_date timestamp without time zone,
                                write_uid integer,                            
                                name CHARACTER VARYING,
                                code CHARACTER VARYING
                            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('s_pic_id_seq', (select max(id) + 1 from  s_pic));
        ''')    
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_s_ship_by(self):
        sql ='''
        INSERT INTO 
            s_ship_by 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name,
                code
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date,  write_uid, 
            name,
            code
            FROM public.dblink
                        ('sucdendblink',
                         'SELECT 
                            id, 
                            create_date, create_uid, 
                            write_date, write_uid, 
                            name,
                            code
                        FROM public.s_ship_by') 
                        AS DATA(id INTEGER,
                                create_date timestamp without time zone,
                                create_uid integer,
                                write_date timestamp without time zone,
                                write_uid integer,                            
                                name CHARACTER VARYING,
                                code CHARACTER VARYING
                            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('s_ship_by_id_seq', (select max(id) + 1 from  s_ship_by));
        ''')    
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def s_period(self):
        sql ='''
        INSERT INTO 
            s_period 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name,
                code,
                date_from,
                date_to
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
                    code,
                    date_from,
                    date_to
                    
                FROM public.s_period') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name CHARACTER VARYING ,
                        code CHARACTER VARYING ,
                        date_from date,
                        date_to date
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('s_period_id_seq', (select max(id) + 1 from  s_period));
        ''')    
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_account_incoterms(self):
        sql ='''
        INSERT INTO 
            account_incoterms 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name,
                code, 
                active
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date,  write_uid, 
            jsonb_build_object('en_US', name ) as name,
            code,
            active
            
            FROM public.dblink
                        ('sucdendblink',
                         'SELECT 
                            id, 
                            create_date, create_uid, 
                            write_date, write_uid, 
                            name,
                            code, 
                            active
                        FROM public.stock_incoterms') 
                        AS DATA(id INTEGER,
                                create_date timestamp without time zone,
                                create_uid integer,
                                write_date timestamp without time zone,
                                write_uid integer,                            
                                name CHARACTER VARYING,
                                code CHARACTER VARYING,
                                active boolean
                            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('account_incoterms_id_seq', (select max(id) + 1 from  account_incoterms));
        ''')    
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_s_contract_line(self):
        sql ='''
        INSERT INTO 
            s_contract_line 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                contract_id ,
                sequence ,
                company_id ,
                partner_id ,
                currency_id ,
                product_id  ,
                product_uom  ,
                packing_id ,
                certificate_id ,
                license_id ,
                p_contract_id ,
                state   ,
                type   ,
                name   ,
                price_subtotal ,
                price_tax ,
                price_total ,
                market_price ,
                p_contract_diff ,
                product_qty   ,
                price_unit   ,
                number_of_bags  ,
                original_diff
            )        
        
        SELECT 
            id, 
            create_date, create_uid, 
            write_date, write_uid, 
            contract_id ,
            sequence ,
            company_id ,
            partner_id ,
            currency_id ,
            product_id  ,
            product_uom  ,
            packing_id ,
            certificate_id ,
            license_id ,
            p_contract_id ,
            state   ,
            type   ,
            name   ,
            price_subtotal ,
            price_tax ,
            price_total ,
            market_price ,
            p_contract_diff ,
            product_qty   ,
            price_unit   ,
            number_of_bags  ,
            original_diff
            FROM public.dblink
                        ('sucdendblink',
                         'SELECT 
                            id, 
                            create_date, create_uid, 
                            write_date,  write_uid, 
                            contract_id ,
                            sequence ,
                            company_id ,
                            partner_id ,
                            currency_id ,
                            product_id  ,
                            product_uom  ,
                            packing_id ,
                            certificate_id ,
                            license_id ,
                            p_contract_id ,
                            state   ,
                            type   ,
                            name   ,
                            price_subtotal ,
                            price_tax ,
                            price_total ,
                            market_price ,
                            p_contract_diff ,
                            product_qty   ,
                            price_unit   ,
                            number_of_bags  ,
                            original_diff
                            -- no_of_teus 
                            
                        FROM public.s_contract_line') 
                        AS DATA(id INTEGER,
                                create_date timestamp without time zone,
                                create_uid integer,
                                write_date timestamp without time zone,
                                write_uid integer,                            
                                contract_id integer,
                                sequence integer,
                                company_id integer,
                                partner_id integer,
                                currency_id integer,
                                product_id integer ,
                                product_uom integer ,
                                packing_id integer,
                                certificate_id integer,
                                license_id integer,
                                p_contract_id integer,
                                state character varying ,
                                type character varying ,
                                name text  ,
                                price_subtotal numeric,
                                price_tax numeric,
                                price_total numeric,
                                market_price numeric,
                                p_contract_diff numeric,
                                product_qty double precision ,
                                price_unit double precision ,
                                number_of_bags double precision,
                                original_diff double precision
                                --no_of_teus double precision
                            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('s_contract_line_id_seq', (select max(id) + 1 from  s_contract_line));
        ''')    
        
        return
    
    def sys_shipping_instruction(self):
        sql ='''
        INSERT INTO 
            shipping_instruction 
            (
                id, 
            create_date, create_uid, 
            write_date,   write_uid, 
            contract_id ,
                sequence ,
                company_id  ,
                warehouse_id  ,
                partner_id ,
                user_confirm ,
                user_approve ,
                shipping_line ,
                port_of_loading ,
                port_of_discharge ,
                incoterms_id ,
                product_id ,
                scertificate_id ,
                spacking_id ,
                certificate_id ,
                standard_id ,
                fumigation_id ,
                shipping_line_id ,
                delivery_place_id ,
                shipt_month ,
                pic_id ,
                name    ,
                state   ,
                origin   ,
                forwarding_agent ,
                container_status ,
                booking_ref_no ,
                ico_permit_no ,
                transaction  ,
                vessel_flight_no ,
                production_status ,
                status  ,
                p_allocated_ids  ,
                materialstatus ,
                pss_condition ,
                bill_no ,
                vessel ,
                voyage ,
                remarks ,
                priority_by_month ,
                awb_sent_no ,
                packing_place ,
                specs ,
                delivery_type ,
                date ,
                deadline  ,
                date_confirm ,
                date_approve ,
                factory_etd ,
                push_off_etd ,
                booking_date ,
                reach_date ,
                ico_permit_date ,
                prodcompleted ,
                date_sent ,
                pss_sent_date ,
                pss_approved_date ,
                shipment_date ,
                fumigation_date ,
                bill_date ,
                pss_send_schedule ,
                si_received_date ,
                si_sent_date ,
                nominated_etd ,
                od_doc_rec_date ,
                od_doc_sent_date ,
                start_of_ship_period ,
                end_of_ship_period ,
                allocated_date ,
                eta ,
                late_ship_end ,
                late_ship_est ,
                note  ,
                type_of_stuffing  ,
                marking  ,
                description_of_goods  ,
                other_detail  ,
                cause_by  ,
                ross_weight ,
                pss_sent ,
                pss_approved ,
                shipped ,
                closing_time ,
                no_of_bag ,
                request_qty  ,
                license_list   ,
                --number_of_container ,
                total_line_qty  
                --total_cont_qty  
            )        
        
        SELECT 
            id, 
            create_date, create_uid, 
            write_date,   write_uid, 
            contract_id ,
                sequence ,
                company_id  ,
                warehouse_id  ,
                partner_id ,
                user_confirm ,
                user_approve ,
                shipping_line ,
                port_of_loading ,
                port_of_discharge ,
                incoterms_id ,
                product_id ,
                scertificate_id ,
                spacking_id ,
                certificate_id ,
                standard_id ,
                fumigation_id ,
                shipping_line_id ,
                delivery_place_id ,
                shipt_month ,
                pic_id ,
                name    ,
                state   ,
                origin   ,
                forwarding_agent ,
                container_status ,
                booking_ref_no ,
                ico_permit_no ,
                transaction  ,
                vessel_flight_no ,
                production_status ,
                status  ,
                p_allocated_ids  ,
                materialstatus ,
                pss_condition ,
                bill_no ,
                vessel ,
                voyage ,
                remarks ,
                priority_by_month ,
                awb_sent_no ,
                packing_place ,
                specs ,
                delivery_type ,
                date ,
                deadline  ,
                date_confirm ,
                date_approve ,
                factory_etd ,
                push_off_etd ,
                booking_date ,
                reach_date ,
                ico_permit_date ,
                prodcompleted ,
                date_sent ,
                pss_sent_date ,
                pss_approved_date ,
                shipment_date ,
                fumigation_date ,
                bill_date ,
                pss_send_schedule ,
                si_received_date ,
                si_sent_date ,
                nominated_etd ,
                od_doc_rec_date ,
                od_doc_sent_date ,
                start_of_ship_period ,
                end_of_ship_period ,
                allocated_date ,
                eta ,
                late_ship_end ,
                late_ship_est ,
                note  ,
                type_of_stuffing  ,
                marking  ,
                description_of_goods  ,
                other_detail  ,
                cause_by  ,
                ross_weight ,
                pss_sent ,
                pss_approved ,
                shipped ,
                closing_time ,
                no_of_bag ,
                request_qty  ,
                license_list   ,
                --number_of_container ,
                total_line_qty  
                --total_cont_qty  
            FROM public.dblink
        ('sucdendblink',
         'SELECT 
            id, 
            create_date, create_uid, 
            write_date, write_uid, 
            contract_id ,
                sequence ,
                company_id  ,
                warehouse_id  ,
                partner_id ,
                user_confirm ,
                user_approve ,
                shipping_line ,
                port_of_loading ,
                port_of_discharge ,
                incoterms_id ,
                product_id ,
                scertificate_id ,
                spacking_id ,
                certificate_id ,
                standard_id ,
                fumigation_id ,
                shipping_line_id ,
                delivery_place_id ,
                shipt_month ,
                pic_id ,
                name    ,
                state   ,
                origin   ,
                forwarding_agent ,
                container_status ,
                booking_ref_no ,
                ico_permit_no ,
                transaction  ,
                vessel_flight_no ,
                production_status ,
                status  ,
                p_allocated_ids  ,
                materialstatus ,
                pss_condition ,
                bill_no ,
                vessel ,
                voyage ,
                remarks ,
                priority_by_month ,
                awb_sent_no ,
                packing_place ,
                specs ,
                delivery_type ,
                date ,
                deadline  ,
                date_confirm ,
                date_approve ,
                factory_etd ,
                push_off_etd ,
                booking_date ,
                reach_date ,
                ico_permit_date ,
                prodcompleted ,
                date_sent ,
                pss_sent_date ,
                pss_approved_date ,
                shipment_date ,
                fumigation_date ,
                bill_date ,
                pss_send_schedule ,
                si_received_date ,
                si_sent_date ,
                nominated_etd ,
                od_doc_rec_date ,
                od_doc_sent_date ,
                start_of_ship_period ,
                end_of_ship_period ,
                allocated_date ,
                eta ,
                late_ship_end ,
                late_ship_est ,
                note  ,
                type_of_stuffing  ,
                marking  ,
                description_of_goods  ,
                other_detail  ,
                cause_by  ,
                ross_weight ,
                pss_sent ,
                pss_approved ,
                shipped ,
                closing_time ,
                no_of_bag ,
                request_qty  ,
                license_list   ,
                --number_of_container ,
                total_line_qty  
                --total_cont_qty  

        FROM public.shipping_instruction') 
        AS DATA(id INTEGER,
                create_date timestamp without time zone,
                create_uid integer,
                write_date timestamp without time zone,   
                write_uid integer,                        
                contract_id integer,
                sequence integer,
                company_id integer ,
                warehouse_id integer ,
                partner_id integer,
                user_confirm integer,
                user_approve integer,
                shipping_line integer,
                port_of_loading integer,
                port_of_discharge integer,
                incoterms_id integer,
                product_id integer,
                scertificate_id integer,
                spacking_id integer,
                certificate_id integer,
                standard_id integer,
                fumigation_id integer,
                shipping_line_id integer,
                delivery_place_id integer,
                shipt_month integer,
                pic_id integer,
                name character varying  ,
                state character varying ,
                origin character varying ,
                forwarding_agent character varying(128) ,
                container_status character varying ,
                booking_ref_no character varying ,
                ico_permit_no character varying ,
                transaction character varying ,
                vessel_flight_no character varying ,
                production_status character varying ,
                status character varying ,
                p_allocated_ids character varying(256) ,
                materialstatus character varying(256) ,
                pss_condition character varying ,
                bill_no character varying ,
                vessel character varying ,
                voyage character varying ,
                remarks character varying ,
                priority_by_month character varying ,
                awb_sent_no character varying(256) ,
                packing_place character varying ,
                specs character varying(256) ,
                delivery_type character varying ,
                date date,
                deadline date ,
                date_confirm date,
                date_approve date,
                factory_etd date,
                push_off_etd date,
                booking_date date,
                reach_date date,
                ico_permit_date date,
                prodcompleted date,
                date_sent date,
                pss_sent_date date,
                pss_approved_date date,
                shipment_date date,
                fumigation_date date,
                bill_date date,
                pss_send_schedule date,
                si_received_date date,
                si_sent_date date,
                nominated_etd date,
                od_doc_rec_date date,
                od_doc_sent_date date,
                start_of_ship_period date,
                end_of_ship_period date,
                allocated_date date,
                eta date,
                late_ship_end date,
                late_ship_est date,
                note text ,
                type_of_stuffing text ,
                marking text ,
                description_of_goods text ,
                other_detail text ,
                cause_by text ,
                ross_weight numeric,
                pss_sent boolean,
                pss_approved boolean,
                shipped boolean,
                closing_time timestamp without time zone,
                no_of_bag double precision,
                request_qty double precision,
                license_list character varying ,
                --number_of_container integer,
                total_line_qty double precision
                --total_cont_qty double precision
            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('shipping_instruction_id_seq', (select max(id) + 1 from  shipping_instruction));
        ''')    
        return
    
    def sys_shipping_instruction_line(self):
        sql ='''
        INSERT INTO 
            shipping_instruction_line 
            (
                id, 
                create_date, create_uid, 
                write_date,   write_uid, 
                shipping_id ,
                sequence ,
                company_id ,
                partner_id ,
                product_id  ,
                product_uom  ,
                packing_id ,
                certificate_id ,
                state   ,
                name   ,
                product_qty   ,
                price_unit   ,
                bags  ,
                tare_weight  ,
                gross_weight  ,
                diff_net  
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    shipping_id ,
                    sequence ,
                    company_id ,
                    partner_id ,
                    product_id  ,
                    product_uom  ,
                    packing_id ,
                    certificate_id ,
                    state   ,
                    name   ,
                    product_qty   ,
                    price_unit   ,
                    bags  ,
                    tare_weight  ,
                    gross_weight  ,
                    diff_net  
                    
                FROM public.shipping_instruction_line') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    shipping_id integer,
                    sequence integer,
                    company_id integer,
                    partner_id integer,
                    product_id integer ,
                    product_uom integer ,
                    packing_id integer,
                    certificate_id integer,
                    state character varying ,
                    name text  ,
                    product_qty double precision ,
                    price_unit double precision ,
                    bags double precision,
                    tare_weight double precision,
                    gross_weight double precision,
                    diff_net double precision
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('shipping_instruction_line_id_seq', (select max(id) + 1 from  shipping_instruction_line));
        ''')    
        
        return
    
    def sys_sale_contract(self):
        sql ='''
        INSERT INTO 
            sale_contract 
            (
                id, 
                create_date, create_uid, 
                write_date,  write_uid, 
                company_id  ,
                company_representative ,
                warehouse_id ,
                partner_id ,
                customer_representative ,
                partner_invoice_id ,
                partner_shipping_id ,
                currency_id ,
                payment_term_id ,
                bank_id ,
                user_approve ,
                port_of_loading ,
                port_of_discharge ,
                shipping_id ,
                scontract_id ,
                contract_p_id ,
                delivery_id ,
                crop_id  ,
                product_id ,
                entries_id ,
                --certificate_id ,
                --picking_id ,
                --scertificate_id ,
                product_id1 ,
                product_id2 ,
                name   ,
                picking_policy   ,
                state  ,
                type   ,
                acc_number  ,
                origin  ,
                dispatch_mode  ,
                container_status  ,
                weights  ,
                transportation_charges  ,
                --x_p_allocate  ,
                p_contract  ,
                lot_no  ,
                date ,
                validity_date  ,
                expiration_date ,
                date_approve ,
                date_done ,
                deadline ,
                date_invoice ,
                note  ,
                amount_untaxed ,
                amount_tax ,
                amount_total ,
                do_qty ,
                remain_qty ,
                loss_qty ,
                invoiced_qty ,
                invoiced_amount_total ,
                total_qty ,
                x_is_bonded ,
                confirm_qc ,
                confirm_date ,
                exchange_rate ,
                delivery_tolerance ,
                p_qty_contract ,
                p_bag_contract ,
                si_qty_contract ,
                si_bag_contract ,
                s_allocated_qty ,
                s_unallocate_qty ,
                s_allocated_bag ,
                s_unallocate_bag ,
                p_allocated_qty ,
                p_unallocate_qty ,
                p_allocated_bag ,
                p_unallocate_bag ,
                request_qty ,
                request_bag ,
                si ,
                sd
            )        
        
        SELECT 
            id, 
            create_date, create_uid, 
            write_date, write_uid, 
            company_id  ,
            company_representative ,
            warehouse_id ,
            partner_id ,
            customer_representative ,
            partner_invoice_id ,
            partner_shipping_id ,
            currency_id ,
            payment_term_id ,
            bank_id ,
            user_approve ,
            port_of_loading ,
            port_of_discharge ,
            shipping_id ,
            scontract_id ,
            contract_p_id ,
            delivery_id ,
            crop_id  ,
            product_id ,
            entries_id ,
            --certificate_id ,
            --picking_id ,
            --scertificate_id ,
            product_id1 ,
            product_id2 ,
            name   ,
            picking_policy   ,
            state  ,
            type   ,
            acc_number  ,
            origin  ,
            dispatch_mode  ,
            container_status  ,
            weights  ,
            transportation_charges  ,
            --x_p_allocate  ,
            p_contract  ,
            lot_no  ,
            date ,
            validity_date  ,
            expiration_date ,
            date_approve ,
            date_done ,
            deadline ,
            date_invoice ,
            note  ,
            amount_untaxed ,
            amount_tax ,
            amount_total ,
            do_qty ,
            remain_qty ,
            loss_qty ,
            invoiced_qty ,
            invoiced_amount_total ,
            total_qty ,
            x_is_bonded ,
            confirm_qc ,
            confirm_date ,
            exchange_rate ,
            delivery_tolerance ,
            p_qty_contract ,
            p_bag_contract ,
            si_qty_contract ,
            si_bag_contract ,
            s_allocated_qty ,
            s_unallocate_qty ,
            s_allocated_bag ,
            s_unallocate_bag ,
            p_allocated_qty ,
            p_unallocate_qty ,
            p_allocated_bag ,
            p_unallocate_bag ,
            request_qty ,
            request_bag ,
            si ,
            sd
                            
        FROM public.dblink
        ('sucdendblink',
            'SELECT 
            id, 
            create_date, create_uid, 
            write_date, write_uid, 
            company_id  ,
            company_representative ,
            warehouse_id ,
            partner_id ,
            customer_representative ,
            partner_invoice_id ,
            partner_shipping_id ,
            currency_id ,
            payment_term_id ,
            bank_id ,
            user_approve ,
            port_of_loading ,
            port_of_discharge ,
            shipping_id ,
            scontract_id ,
            contract_p_id ,
            delivery_id ,
            crop_id  ,
            product_id ,
            entries_id ,
            --certificate_id ,
            picking_id ,
            --scertificate_id ,
            product_id1 ,
            product_id2 ,
            name   ,
            picking_policy   ,
            state  ,
            type   ,
            acc_number  ,
            origin  ,
            dispatch_mode  ,
            container_status  ,
            weights  ,
            transportation_charges  ,
            --x_p_allocate  ,
            p_contract  ,
            lot_no  ,
            date ,
            validity_date  ,
            expiration_date ,
            date_approve ,
            date_done ,
            deadline ,
            date_invoice ,
            note  ,
            amount_untaxed ,
            amount_tax ,
            amount_total ,
            do_qty ,
            remain_qty ,
            loss_qty ,
            invoiced_qty ,
            invoiced_amount_total ,
            total_qty ,
            x_is_bonded ,
            confirm_qc ,
            confirm_date ,
            exchange_rate ,
            delivery_tolerance ,
            p_qty_contract ,
            p_bag_contract ,
            si_qty_contract ,
            si_bag_contract ,
            s_allocated_qty ,
            s_unallocate_qty ,
            s_allocated_bag ,
            s_unallocate_bag ,
            p_allocated_qty ,
            p_unallocate_qty ,
            p_allocated_bag ,
            p_unallocate_bag ,
            request_qty ,
            request_bag ,
            si ,
            sd
            
            
        FROM public.sale_contract') 
        AS DATA(id INTEGER,
                create_date timestamp without time zone,
                create_uid integer,
                write_date timestamp without time zone,
                write_uid integer,                            
                company_id integer ,
                company_representative integer,
                warehouse_id integer,
                partner_id integer,
                customer_representative integer,
                partner_invoice_id integer,
                partner_shipping_id integer,
                currency_id integer,
                payment_term_id integer,
                bank_id integer,
                user_approve integer,
                port_of_loading integer,
                port_of_discharge integer,
                shipping_id integer,
                scontract_id integer,
                contract_p_id integer,
                delivery_id integer,
                crop_id integer ,
                product_id integer,
                entries_id integer,
                --certificate_id integer,
                picking_id integer,
                --scertificate_id integer,
                product_id1 integer,
                product_id2 integer,
                name character varying  ,
                picking_policy character varying  ,
                state character varying ,
                type character varying  ,
                acc_number character varying ,
                origin character varying ,
                dispatch_mode character varying ,
                container_status character varying ,
                weights character varying ,
                transportation_charges character varying ,
                --x_p_allocate character varying ,
                p_contract character varying ,
                lot_no character varying ,
                date date,
                validity_date date ,
                expiration_date date,
                date_approve date,
                date_done date,
                deadline date,
                date_invoice date,
                note text ,
                amount_untaxed numeric,
                amount_tax numeric,
                amount_total numeric,
                do_qty numeric,
                remain_qty numeric,
                loss_qty numeric,
                invoiced_qty numeric,
                invoiced_amount_total numeric,
                total_qty numeric,
                x_is_bonded boolean,
                confirm_qc boolean,
                confirm_date timestamp without time zone,
                exchange_rate double precision,
                delivery_tolerance double precision,
                p_qty_contract double precision,
                p_bag_contract double precision,
                si_qty_contract double precision,
                si_bag_contract double precision,
                s_allocated_qty double precision,
                s_unallocate_qty double precision,
                s_allocated_bag double precision,
                s_unallocate_bag double precision,
                p_allocated_qty double precision,
                p_unallocate_qty double precision,
                p_allocated_bag double precision,
                p_unallocate_bag double precision,
                request_qty double precision,
                request_bag double precision,
                si double precision,
                sd double precision
            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('sale_contract_id_seq', (select max(id) + 1 from  sale_contract));
        ''')    
        
        return
    
    def sys_sale_contract_line(self):
        sql ='''
        INSERT INTO 
            sale_contract_line
            (
                id,
                create_date,create_uid,
                write_date, write_uid,  
                contract_id,                   
                sequence ,
                company_id ,
                partner_id ,
                currency_id ,
                product_id  ,
                product_uom  ,
                certificate_id ,
                packing_id ,
                state  ,
                name   ,
                price_unit ,
                price_subtotal ,
                price_tax ,
                price_total ,
                conversion ,
                provisional_g2_price ,
                provisional_g2_diff ,
                provisional_price ,
                final_g2_price ,
                final_g2_diff ,
                product_qty  ,
                premium ,
                premium_adjustment  
            )        
        
       SELECT 
            id,
            create_date, create_uid, 
            write_date, write_uid, 
            contract_id,
            sequence ,
            company_id ,
            partner_id ,
            currency_id ,
            product_id  ,
            product_uom  ,
            certificate_id ,
            packing_id ,
            state  ,
            name   ,
            price_unit ,
            price_subtotal ,
            price_tax ,
            price_total ,
            conversion ,
            provisional_g2_price ,
            provisional_g2_diff ,
            provisional_price ,
            final_g2_price ,
            final_g2_diff ,
            product_qty  ,
            premium ,
            premium_adjustment  
             
            FROM public.dblink
            ('sucdendblink',
             'SELECT 
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                contract_id ,
                sequence ,
                company_id ,
                partner_id ,
                currency_id ,
                product_id  ,
                product_uom  ,
                certificate_id ,
                packing_id ,
                state  ,
                name   ,
                price_unit ,
                price_subtotal ,
                price_tax ,
                price_total ,
                conversion ,
                provisional_g2_price ,
                provisional_g2_diff ,
                provisional_price ,
                final_g2_price ,
                final_g2_diff ,
                product_qty  ,
                premium ,
                premium_adjustment   
                
            FROM public.sale_contract_line') 
            AS DATA(id INTEGER,
                create_date timestamp without time zone,
                create_uid integer,
                write_date timestamp without time zone,
                write_uid integer,                            
                contract_id integer,
                sequence integer,
                company_id integer,
                partner_id integer,
                currency_id integer,
                product_id integer ,
                product_uom integer ,
                certificate_id integer,
                packing_id integer,
                state character varying ,
                name text  ,
                price_unit numeric,
                price_subtotal numeric,
                price_tax numeric,
                price_total numeric,
                conversion numeric,
                provisional_g2_price numeric,
                provisional_g2_diff numeric,
                provisional_price numeric,
                final_g2_price numeric,
                final_g2_diff numeric,
                product_qty double precision ,
                premium double precision,
                premium_adjustment double precision
            )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('sale_contract_line_id_seq', (select max(id) + 1 from  sale_contract_line));
        ''')    
        
        return
    def sys_sale_contract_certificate_ref(self):
        sql ='''
        INSERT INTO 
            sale_contract_certificate_ref
            (
                sale_contract_id, 
                cert_id
            )        
        
        SELECT 
            sale_contract_id, 
            cert_id
            FROM public.dblink
                    ('sucdendblink',
                     'SELECT 
                        sale_contract_id, 
                        cert_id
                    FROM public.sale_contract_certificate_ref') 
                        AS DATA(sale_contract_id integer ,
                                cert_id integer 
                        )
        '''
        self.env.cr.execute(sql)
        return
    
    def sys_sale_contract_deatail(self):
        sql ='''
        INSERT INTO 
            sale_contract_deatail
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                p_contract_id ,
                product_id ,
                shipper_id ,
                scertificate_id ,
                stack_id ,
                warehouse_id ,
                sp_id ,
                name ,
                state ,
                stack_on_hand ,
                confirm_date ,
                x_bag_qty  ,
                x_gd_qty  ,
                allocated_qty  ,
                tobe_qty  ,
                tobe_bag  ,
                balance_qty  ,
                p_on_hand   
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date, write_uid, 
            p_contract_id ,
            product_id ,
            shipper_id ,
            scertificate_id ,
            stack_id ,
            warehouse_id ,
            sp_id ,
            name ,
            state ,
            stack_on_hand ,
            confirm_date ,
            x_bag_qty  ,
            x_gd_qty  ,
            allocated_qty  ,
            tobe_qty  ,
            tobe_bag  ,
            balance_qty  ,
            p_on_hand   
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    p_contract_id ,
                    product_id ,
                    shipper_id ,
                    scertificate_id ,
                    stack_id ,
                    warehouse_id ,
                    sp_id ,
                    name ,
                    state ,
                    stack_on_hand ,
                    confirm_date ,
                    x_bag_qty  ,
                    x_gd_qty  ,
                    allocated_qty  ,
                    tobe_qty  ,
                    tobe_bag  ,
                    balance_qty  ,
                    p_on_hand    
                    
                FROM public.sale_contract_deatail') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        p_contract_id integer,
                        product_id integer,
                        shipper_id integer,
                        scertificate_id integer,
                        stack_id integer,
                        warehouse_id integer,
                        sp_id integer,
                        name character varying(256) ,
                        state character varying ,
                        stack_on_hand character varying ,
                        confirm_date timestamp without time zone,
                        x_bag_qty double precision,
                        x_gd_qty double precision,
                        allocated_qty double precision,
                        tobe_qty double precision,
                        tobe_bag double precision,
                        balance_qty double precision,
                        p_on_hand double precision  
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('sale_contract_deatail_id_seq', (select max(id) + 1 from  sale_contract_deatail));
        ''')    
        
        return
    
    def sys_delivery_order(self):
        sql ='''
        INSERT INTO 
            delivery_order
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                trucking_id ,
                currency_id ,
                user_approve ,
                warehouse_id ,
                picking_type_id ,
                partner_id ,
                contract_id ,
                --picking_id ,
                shipping_id ,
                packing_id ,
                certificate_id ,
                product_id ,
                move_id ,
                packing_qty ,
                from_warehouse_id  ,
                name  ,
                state  ,
                vehicle_manufacture  ,
                trucking_no  ,
                driver_name  ,
                registration_certificate  ,
                company_ref_guide  ,
                transporter_ref_guide  ,
                is_bonded  ,
                type  ,
                packing_place  ,
                date ,
                date_approve ,
                date_out ,
                received_date ,
                date_invoice ,
                markings  ,
                reason  ,
                total_qty ,
                bagsfactory ,
                weightfactory ,
                storing_loss ,
                transportation_loss ,
                bags ,
                shipped_weight ,
                transrate ,
                real_qty  
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date, write_uid, 
            trucking_id ,
            currency_id ,
            user_approve ,
            warehouse_id ,
            picking_type_id ,
            partner_id ,
            contract_id ,
            --picking_id ,
            shipping_id ,
            packing_id ,
            certificate_id ,
            product_id ,
            move_id ,
            packing_qty ,
            from_warehouse_id  ,
            name  ,
            state  ,
            vehicle_manufacture  ,
            trucking_no  ,
            driver_name  ,
            registration_certificate  ,
            company_ref_guide  ,
            transporter_ref_guide  ,
            is_bonded  ,
            type  ,
            packing_place  ,
            date ,
            date_approve ,
            date_out ,
            received_date ,
            date_invoice ,
            markings  ,
            reason  ,
            total_qty ,
            bagsfactory ,
            weightfactory ,
            storing_loss ,
            transportation_loss ,
            bags ,
            shipped_weight ,
            transrate ,
            real_qty  
            FROM public.dblink
            ('sucdendblink',
             'SELECT 
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                trucking_id ,
                currency_id ,
                user_approve ,
                warehouse_id ,
                picking_type_id ,
                partner_id ,
                contract_id ,
                picking_id ,
                shipping_id ,
                packing_id ,
                certificate_id ,
                product_id ,
                move_id ,
                packing_qty ,
                from_warehouse_id  ,
                name  ,
                state  ,
                vehicle_manufacture  ,
                trucking_no  ,
                driver_name  ,
                registration_certificate  ,
                company_ref_guide  ,
                transporter_ref_guide  ,
                is_bonded  ,
                type  ,
                packing_place  ,
                date date,
                date_approve ,
                date_out ,
                received_date ,
                date_invoice ,
                markings  ,
                reason  ,
                total_qty ,
                bagsfactory ,
                weightfactory ,
                storing_loss ,
                transportation_loss ,
                bags ,
                shipped_weight ,
                transrate ,
                real_qty  
            FROM public.delivery_order') 
            AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    trucking_id integer,
                    currency_id integer,
                    user_approve integer,
                    warehouse_id integer,
                    picking_type_id integer,
                    partner_id integer,
                    contract_id integer,
                    picking_id integer,
                    shipping_id integer,
                    packing_id integer,
                    certificate_id integer,
                    product_id integer,
                    move_id integer,
                    packing_qty integer,
                    from_warehouse_id integer ,
                    name character varying ,
                    state character varying ,
                    vehicle_manufacture character varying ,
                    trucking_no character varying ,
                    driver_name character varying ,
                    registration_certificate character varying ,
                    company_ref_guide character varying ,
                    transporter_ref_guide character varying ,
                    is_bonded character varying ,
                    type character varying ,
                    packing_place character varying ,
                    date date,
                    date_approve date,
                    date_out date,
                    received_date date,
                    date_invoice date,
                    markings text ,
                    reason text ,
                    total_qty numeric,
                    bagsfactory numeric,
                    weightfactory numeric,
                    storing_loss numeric,
                    transportation_loss numeric,
                    bags numeric,
                    shipped_weight numeric,
                    transrate double precision,
                    real_qty double precision
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('delivery_order_id_seq', (select max(id) + 1 from  delivery_order));
        ''')    
        
        return
    
    def sys_delivery_order_line(self):
        sql ='''
        INSERT INTO 
            delivery_order_line 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                delivery_id ,
                sequence ,
                product_id  ,
                product_uom  ,
                packing_id ,
                certificate_id ,
                state   ,
                name  ,
                product_qty ,
                price_unit 
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date, write_uid, 
            delivery_id ,
            sequence ,
            product_id  ,
            product_uom  ,
            packing_id ,
            certificate_id ,
            state   ,
            name  ,
            product_qty ,
            price_unit 
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    delivery_id ,
                    sequence ,
                    product_id  ,
                    product_uom  ,
                    packing_id ,
                    certificate_id ,
                    state   ,
                    name  ,
                    product_qty ,
                    price_unit 
                 
                FROM public.delivery_order_line') 
                AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    delivery_id integer,
                    sequence integer,
                    product_id integer ,
                    product_uom integer ,
                    packing_id integer,
                    certificate_id integer,
                    state character varying ,
                    name text ,
                    product_qty double precision ,
                    price_unit double precision
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('delivery_order_line_id_seq', (select max(id) + 1 from  delivery_order_line));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_post_shipment(self):
        sql ='''
        INSERT INTO 
            post_shipment 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                do_id ,
                nvs_nls_id ,
                delivery_place_id ,
                packing_id ,
                name  ,
                truck_plate ,
                notes 
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date, write_uid, 
            do_id ,
            nvs_nls_id ,
            delivery_place_id ,
            packing_id ,
            name  ,
            truck_plate ,
            notes 
            --cont_no ,
            --bl_no 
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                        do_id ,
                        nvs_nls_id ,
                        delivery_place_id ,
                        packing_id ,
                        name  ,
                        truck_plate ,
                        notes  
                        --cont_no ,
                       -- bl_no 
                 
                FROM public.post_shipment') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        do_id integer,
                        nvs_nls_id integer,
                        delivery_place_id integer,
                        packing_id integer,
                        name character varying  ,
                        truck_plate character varying(128) ,
                        notes text 
                       -- cont_no character varying(128) ,
                        --bl_no character varying(128) 
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('post_shipment_id_seq', (select max(id) + 1 from  post_shipment));
        ''')   
        
        return
    
    def sys_post_shipment_line(self):
        sql ='''
        INSERT INTO 
            post_shipment_line
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                post_id ,
                nvs_nls_id ,
                do_id ,
                cont_no  ,
                bl_no  ,
                supervisor_id ,
                loading_date ,
                bl_date ,
                bags ,
                shipped_weight ,
                --lot_id ,
                lot_ned 
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date, write_uid, 
            post_id ,
            nvs_nls_id ,
            do_id ,
            cont_no  ,
            bl_no  ,
            supervisor_id ,
            loading_date ,
            bl_date ,
            bags ,
            shipped_weight ,
            --lot_id ,
            lot_ned 
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                        post_id ,
                        nvs_nls_id ,
                        do_id ,
                        cont_no  ,
                        bl_no  ,
                        supervisor_id ,
                        loading_date ,
                        bl_date ,
                        bags ,
                        shipped_weight ,
                        lot_id ,
                        lot_ned 
                 
                FROM public.post_shipment_line') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        post_id integer,
                        nvs_nls_id integer,
                        do_id integer,
                        cont_no character varying(128)  ,
                        bl_no character varying(128) ,
                        supervisor_id character varying(128) ,
                        loading_date date,
                        bl_date date,
                        bags numeric,
                        shipped_weight numeric,
                        lot_id integer,
                        lot_ned character varying 
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('post_shipment_line_id_seq', (select max(id) + 1 from  post_shipment_line));
        ''')   
        
        return
    
    


        
    