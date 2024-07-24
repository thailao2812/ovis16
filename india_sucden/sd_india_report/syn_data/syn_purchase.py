from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    
    def comupte_total_payment_received(self):
        count = 0
        name = ''
        for i in self.env['purchase.contract'].search([('compute','=',False)], order= 'id desc'):
            if count < 50:
                i.compute = True
                name = i.id , i.name, count
                count +=1
                # print(name)
                i._compute_amount()
                
            else:
                break
        
        return name
        
    
    def sys_purchase_run1(self):
        self.env.cr.execute('''
            delete from purchase_contract_according;
            delete from npe_nvp_relation;
            delete from interest_rate;
            delete from request_payment;
            delete from purchase_contract_line;
            delete from purchase_contract;
            delete from ptbf_rolling_month;
            delete from appendix_ptbf;
        ''')
        
        self.sys_purchase_contract_according()
        self.sys_purchase_contract()
        self.sys_purchase_contract_line()
        self.sys_npe_nvp_relation()
        self.sys_appendix_ptbf()
        self.sys_ptbf_rolling_month()
    
    def sys_purchase_run2(self):
        self.env.cr.execute('''
            delete from interest_rate;
            delete from request_payment;
        ''')
        
        self.sys_request_payment()
        self.sys_interest_rate()
        
    
    def sys_purchase_run3(self):
        self.env.cr.execute('''
            delete from payment_allocation_line;
            delete from payment_allocation;
            delete from history_rate;
        ''')
        
        self.sys_payment_allocation()
        self.sys_payment_allocation_line()
        self.sys_ptbf_fixprice()
        self.sys_stock_allocation()
        self.sys_history_rate()
        # self.compute_purchase()
        
    
    def compute_purchase(self):
        self.env.cr.execute('''
            delete from account_account_account_tag;
            ALTER TABLE purchase_contract drop column amount_deposit;
        ''')
        
        
        # k = 0
        # obj = self.env['purchase.contract'].search([('type','=','ptbf')])
        # obj = obj.filtered(lambda d: len(d.ptbf_ids) >0 and len(d.ptbf_ids.history_rate_ids)>0)
        # for i in obj:
        #     k += 1
        #     print(k)
        #     i._amount_all()
    
    def sys_purchase_run4(self):
        self.env.cr.execute('''
            delete from history_rate;
        ''')
        self.sys_history_rate()
    
    
    def sys_history_rate(self):
        sql ='''
        INSERT INTO 
            history_rate 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                product_id ,
                history_id ,
                ptbf_id ,
                move_id ,
                grn_id ,
                date_receive ,
                qty_price ,
                qty_receive ,
                rate ,
                final_price_en ,
                final_price_vn ,
                total_amount_en ,
                total_amount_vn 
            )        
        
        SELECT 
            id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    product_id ,
                    history_id ,
                    ptbf_id ,
                    move_id ,
                    grn_id ,
                    date_receive ,
                    qty_price ,
                    qty_receive ,
                    rate ,
                    final_price_en ,
                    final_price_vn ,
                    total_amount_en ,
                    total_amount_vn 
                    
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    product_id ,
                    history_id ,
                    ptbf_id ,
                    move_id ,
                    grn_id ,
                    date_receive ,
                    qty_price ,
                    qty_receive ,
                    rate ,
                    final_price_en ,
                    final_price_vn ,
                    total_amount_en ,
                    total_amount_vn 
                FROM public.history_rate') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        product_id integer,
                        history_id integer,
                        ptbf_id integer,
                        move_id integer,
                        grn_id integer,
                        date_receive date,
                        qty_price double precision,
                        qty_receive double precision,
                        rate double precision,
                        final_price_en double precision,
                        final_price_vn double precision,
                        total_amount_en double precision,
                        total_amount_vn double precision
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('history_rate_id_seq', (select max(id) + 1 from  history_rate));
        ''')   
        
        return
        
    def sys_ptbf_rolling_month(self):
        sql ='''
        INSERT INTO 
            ptbf_rolling_month 
            (
                id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    contract_id ,
                    no   ,
                    date_rolling  ,
                    date_fixed  ,
                    date  ,
                    diff_price ,
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
                    no   ,
                    date_rolling  ,
                    date_fixed  ,
                    date  ,
                    diff_price ,
                    quantity  
                    
                FROM public.ptbf_rolling_month') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        contract_id integer,
                        no character varying ,
                        date_rolling date ,
                        date_fixed date ,
                        date date ,
                        diff_price double precision,
                        quantity double precision
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('ptbf_rolling_month_id_seq', (select max(id) + 1 from  ptbf_rolling_month));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_appendix_ptbf(self):
        sql ='''
        INSERT INTO 
            appendix_ptbf 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                ptbf_id ,
                name ,
                date_order ,
                quantity ,
                liffe_price ,
                differencial ,
                exchange_rate 
            )        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date,  write_uid, 
                    ptbf_id ,
                    name ,
                    date_order ,
                    quantity ,
                    liffe_price ,
                    differencial ,
                    exchange_rate 
                    
                FROM public.appendix_ptbf') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        ptbf_id integer,
                        name character varying ,
                        date_order date,
                        quantity double precision,
                        liffe_price double precision,
                        differencial double precision,
                        exchange_rate double precision  
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('appendix_ptbf_id_seq', (select max(id) + 1 from  appendix_ptbf));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_ptbf_fixprice(self):
        sql ='''
        INSERT INTO 
            ptbf_fixprice 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                contract_id ,
                product_id ,
                no ,
                name  ,
                date_fix ,
                input_centlb ,
                quantity ,
                price_fix ,
                final_price ,
                total_amount
                --diff 
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
                    no ,
                    name  ,
                    date_fix ,
                    input_centlb ,
                    quantity ,
                    price_fix ,
                    final_price ,
                    total_amount 
                   -- diff 
                FROM public.ptbf_fixprice') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        contract_id integer,
                        product_id integer,
                        no character varying ,
                        name character varying ,
                        date_fix date,
                        input_centlb numeric,
                        quantity double precision,
                        price_fix double precision,
                        final_price double precision,
                        total_amount double precision
                       -- diff double precision
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('uom_category_id_seq', (select max(id) + 1 from  uom_category));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return  
        
    def sys_payment_allocation_line(self):
        sql ='''
        
        INSERT INTO 
            payment_allocation_line 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                pay_allocation_id ,
                total_date ,
                month ,
                from_date ,
                to_date ,
                amount_interest_rate ,
                interest_pay ,
                actual_interest_pay ,
                rate 
            )        
        
        SELECT 
           *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date,  write_uid,
                    pay_allocation_id ,
                    total_date ,
                    month ,
                    from_date ,
                    to_date ,
                    amount_interest_rate ,
                    interest_pay ,
                    actual_interest_pay ,
                    rate 
                    
                FROM public.payment_allocation_line') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,
                        pay_allocation_id integer,
                        total_date integer,
                        month character varying ,
                        from_date date,
                        to_date date,
                        amount_interest_rate numeric,
                        interest_pay numeric,
                        actual_interest_pay numeric,
                        rate numeric
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('payment_allocation_line_id_seq', (select max(id) + 1 from  payment_allocation_line));
        ''')   
    
    def sys_payment_allocation(self):
        sql ='''
        INSERT INTO 
            payment_allocation 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                pay_id ,
                partner_id ,
                contract_id ,
                move_id ,
                day_tz ,
                date_tz ,
                allocation_amount 
            )        
        
        SELECT 
            id, 
                create_date, create_uid, 
                write_date, write_uid, 
                pay_id ,
                partner_id ,
                contract_id ,
                move_id ,
                day_tz ,
                date_tz ,
                allocation_amount 
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    pay_id ,
                    partner_id ,
                    contract_id ,
                    move_id ,
                    day_tz ,
                    date_tz ,
                    allocation_amount 
                FROM public.payment_allocation where pay_id !=40395') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        pay_id integer,
                        partner_id integer,
                        contract_id integer,
                        move_id integer,
                        day_tz character varying ,
                        date_tz date,
                        allocation_amount numeric
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('payment_allocation_id_seq', (select max(id) + 1 from  payment_allocation));
        ''')   
    
    def sys_stock_allocation(self):
        sql ='''
        INSERT INTO 
            stock_allocation 
            (
                id, 
                    create_date, 
                    create_uid, 
                    write_date,  
                    write_uid, 
                    
                    contract_id ,
                    product_id ,
                    picking_id ,
                    partner_id ,
                    allocation_picking_id ,
                    warehouse_id ,
                    license_id ,
                    type_contract  ,
                    state  ,
                    date_allocation ,
                    qty_contract ,
                    qty_allocation ,
                    qty_received ,
                    qty_unreceived ,
                    compare_qty ,
                    date_picking ,
                    price_contract
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, 
                    create_uid, 
                    write_date,  
                    write_uid, 
                    
                    contract_id ,
                    product_id ,
                    picking_id ,
                    partner_id ,
                    allocation_picking_id ,
                    warehouse_id ,
                    license_id ,
                    type_contract  ,
                    state  ,
                    date_allocation ,
                    qty_contract ,
                    qty_allocation ,
                    qty_received ,
                    qty_unreceived ,
                    compare_qty ,
                    date_picking ,
                    price_contract
                        
                FROM public.stock_allocation') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        contract_id integer,
                        product_id integer,
                        picking_id integer,
                        partner_id integer,
                        allocation_picking_id integer,
                        warehouse_id integer,
                        license_id integer,
                        type_contract character varying ,
                        state character varying ,
                        date_allocation date,
                        qty_contract numeric,
                        qty_allocation numeric,
                        qty_received numeric,
                        qty_unreceived numeric,
                        compare_qty boolean,
                        date_picking timestamp without time zone,
                        price_contract double precision 
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('stock_allocation_id_seq', (select max(id) + 1 from  stock_allocation));
        ''')   
        
        return
    
    def sys_interest_rate(self):
        sql ='''
        INSERT INTO 
            interest_rate 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                request_id ,
                contract_id ,
                month ,
                date ,
                date_end ,
                rate 
            )        
        
        SELECT 
            id,
            create_date, create_uid, 
            write_date, write_uid, 
            request_id ,
            contract_id ,
            month ,
            date ,
            date_end ,
            rate 
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    request_id ,
                    contract_id ,
                    month ,
                    date ,
                    date_end ,
                    rate 
                    
                FROM public.interest_rate') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        request_id integer,
                        contract_id integer,
                        month character varying,
                        date date,
                        date_end date,
                        rate numeric
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('interest_rate_id_seq', (select max(id) + 1 from  interest_rate));
        ''')   
        return
    
    def sys_purchase_contract_according(self):
        sql ='''
        INSERT INTO 
            purchase_contract_according 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                name ,
                name_vn  ,
                eposition ,
                vnposition ,
                "number" ,
                appr_date 
            )        
        
        SELECT 
           *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    name ,
                    name_vn  ,
                    eposition ,
                    vnposition ,
                    "number" ,
                    appr_date 
                 
                FROM public.purchase_contract_according') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        name character varying(256) ,
                        name_vn character varying(256) ,
                        eposition character varying(256) ,
                        vnposition character varying(256) ,
                        "number" character varying(256) ,
                        appr_date date
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('purchase_contract_according_id_seq', (select max(id) + 1 from  purchase_contract_according));
        ''')   
        
        return
    
    def sys_purchase_contract(self):
        sql ='''
        INSERT INTO 
            purchase_contract 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                company_id  ,
                company_representative ,
                partner_invoice_id  ,
                partner_shipping_id  ,
                partner_id  ,
                supplier_representative ,
                currency_id  ,
                bank_id ,
                payment_term_id ,
                warehouse_id  ,
                user_approve ,
                npe_contract_id ,
                product_id ,
                license_id ,
                crop_id  ,
                "number" ,
                state_id ,
                songay ,
                delivery_place_id ,
                interest_move_id ,
                interest_move_entries_id ,
                certificate_id ,
                premium ,
                g2diff ,
                packing_terms_id ,
                trader_id ,
                according_id ,
                contract_p_id ,
                name   ,
                state  ,
                acc_number  ,
                transportation_charges  ,
                type   ,
                origin  ,
                interest  ,
                cert_type  ,
                contract_type  ,
                --month_code  ,
                validity_date  ,
                expiration_date ,
                date_order ,
                deadline_date ,
                price_estimation_date ,
                delivery_from ,
                delivery_to ,
                date_approve ,
                date_done ,
                fixation_deadline ,
                from_date_rate ,
                to_date_rate ,
                date_payment_final ,
                date_fix ,
                payment_description  ,
                note  ,
                payment_term_item  ,
                amount_untaxed ,
                amount_tax ,
                amount_total ,
                total_qty ,
                total_interest_pay ,
                amount_sub_total ,
                amount_sub_rel_total ,
                amount_deposit ,
                qty_received ,
                qty_unreceived ,
                total_advance ,
                total_payment_received ,
                total_payment_remain ,
                total_qty_fixed ,
                qty_unfixed ,
                --total_payment ,
                check_qty ,
                check_price_unit ,
                no_copute ,
                is_temp_quota ,
                is_according ,
                exchange_rate  ,
                --relation_price_unit ,
                --relation_premium ,
                advance_amount ,
                lifffe_line ,
                --lifffe_line_ptbf ,
                difams ,
                ex ,
                diff_price ,
                --fixed_vnd ,
                --qty_allocate ,
                sd_price ,
                si_price ,
                cert_cost ,
                grade_id 
                --print_count ,
                --pending_allocation_qty 
        )
        SELECT 
            id,
            create_date,create_uid,
            write_date, write_uid,                     
            company_id  ,
            company_representative ,
            partner_invoice_id  ,
            partner_shipping_id  ,
            partner_id  ,
            supplier_representative ,
            currency_id  ,
            bank_id ,
            payment_term_id ,
            warehouse_id  ,
            user_approve ,
            npe_contract_id ,
            product_id ,
            license_id ,
            crop_id  ,
            "number" ,
            state_id ,
            songay ,
            delivery_place_id ,
            null as interest_move_id ,
            null as interest_move_entries_id ,
            certificate_id ,
            premium ,
            g2diff ,
            packing_terms_id ,
            trader_id ,
            according_id ,
            contract_p_id ,
            name   ,
            state  ,
            acc_number  ,
            transportation_charges  ,
            type   ,
            origin  ,
            interest  ,
            cert_type  ,
            contract_type  ,
            --month_code  ,
            validity_date  ,
            expiration_date ,
            date_order ,
            deadline_date ,
            price_estimation_date ,
            delivery_from ,
            delivery_to ,
            date_approve ,
            date_done ,
            fixation_deadline ,
            from_date_rate ,
            to_date_rate ,
            date_payment_final ,
            date_fix ,
            payment_description  ,
            note  ,
            payment_term_item  ,
            amount_untaxed ,
            amount_tax ,
            amount_total ,
            total_qty ,
            total_interest_pay ,
            amount_sub_total ,
            amount_sub_rel_total ,
            amount_deposit ,
            qty_received ,
            qty_unreceived ,
            total_advance ,
            total_payment_received ,
            total_payment_remain ,
            total_qty_fixed ,
            qty_unfixed ,
            --total_payment ,
            check_qty ,
            check_price_unit ,
            no_copute ,
            is_temp_quota ,
            is_according ,
            exchange_rate  ,
            --relation_price_unit ,
            --relation_premium ,
            advance_amount ,
            lifffe_line ,
            --lifffe_line_ptbf ,
            difams ,
            ex ,
            diff_price ,
            --fixed_vnd ,
            --qty_allocate ,
            sd_price ,
            si_price ,
            cert_cost ,
            grade_id 
            --print_count ,
            --pending_allocation_qty 
            
        FROM public.dblink
            ('sucdendblink',
             'SELECT 
                id, 
                create_date, create_uid, 
                write_date, write_uid, 
                company_id  ,
                    company_representative ,
                    partner_invoice_id  ,
                    partner_shipping_id  ,
                    partner_id  ,
                    supplier_representative ,
                    currency_id  ,
                    bank_id ,
                    payment_term_id ,
                    warehouse_id  ,
                    user_approve ,
                    npe_contract_id ,
                    product_id ,
                    license_id ,
                    crop_id  ,
                    "number" ,
                    state_id ,
                    songay ,
                    delivery_place_id ,
                    interest_move_id ,
                    interest_move_entries_id ,
                    certificate_id ,
                    premium ,
                    g2diff ,
                    packing_terms_id ,
                    trader_id ,
                    according_id ,
                    contract_p_id ,
                    name   ,
                    state  ,
                    acc_number  ,
                    transportation_charges  ,
                    type   ,
                    origin  ,
                    interest  ,
                    cert_type  ,
                    contract_type  ,
                    --month_code  ,
                    validity_date  ,
                    expiration_date ,
                    date_order ,
                    deadline_date ,
                    price_estimation_date ,
                    delivery_from ,
                    delivery_to ,
                    date_approve ,
                    date_done ,
                    fixation_deadline ,
                    from_date_rate ,
                    to_date_rate ,
                    date_payment_final ,
                    date_fix ,
                    payment_description  ,
                    note  ,
                    payment_term_item  ,
                    amount_untaxed ,
                    amount_tax ,
                    amount_total ,
                    total_qty ,
                    total_interest_pay ,
                    amount_sub_total ,
                    amount_sub_rel_total ,
                    amount_deposit ,
                    qty_received ,
                    qty_unreceived ,
                    total_advance ,
                    total_payment_received ,
                    total_payment_remain ,
                    total_qty_fixed ,
                    qty_unfixed ,
                    --total_payment ,
                    check_qty ,
                    check_price_unit ,
                    no_copute ,
                    is_temp_quota ,
                    is_according ,
                    exchange_rate  ,
                    --relation_price_unit ,
                    --relation_premium ,
                    advance_amount ,
                    lifffe_line ,
                    --lifffe_line_ptbf ,
                    difams ,
                    ex ,
                    diff_price ,
                    --fixed_vnd ,
                    --qty_allocate ,
                    sd_price ,
                    si_price ,
                    cert_cost ,
                    grade_id 
                    --print_count ,
                    --pending_allocation_qty 
             
            FROM public.purchase_contract') 
            AS DATA(id INTEGER,
                    create_date timestamp without time zone,
                    create_uid integer,
                    write_date timestamp without time zone,
                    write_uid integer,                            
                    company_id integer ,
                    company_representative integer,
                    partner_invoice_id integer ,
                    partner_shipping_id integer ,
                    partner_id integer ,
                    supplier_representative integer,
                    currency_id integer ,
                    bank_id integer,
                    payment_term_id integer,
                    warehouse_id integer ,
                    user_approve integer,
                    npe_contract_id integer,
                    product_id integer,
                    license_id integer,
                    crop_id integer ,
                    "number" integer,
                    state_id integer,
                    songay integer,
                    delivery_place_id integer,
                    interest_move_id integer,
                    interest_move_entries_id integer,
                    certificate_id integer,
                    premium integer,
                    g2diff integer,
                    packing_terms_id integer,
                    trader_id integer,
                    according_id integer,
                    contract_p_id integer,
                    name character varying  ,
                    state character varying ,
                    acc_number character varying ,
                    transportation_charges character varying ,
                    type character varying  ,
                    origin character varying ,
                    interest character varying(256) ,
                    cert_type character varying ,
                    contract_type character varying ,
                    --month_code character varying ,
                    validity_date date ,
                    expiration_date date,
                    date_order date,
                    deadline_date date,
                    price_estimation_date date,
                    delivery_from date,
                    delivery_to date,
                    date_approve date,
                    date_done date,
                    fixation_deadline date,
                    from_date_rate date,
                    to_date_rate date,
                    date_payment_final date,
                    date_fix date,
                    payment_description text ,
                    note text ,
                    payment_term_item text ,
                    amount_untaxed numeric,
                    amount_tax numeric,
                    amount_total numeric,
                    total_qty numeric,
                    total_interest_pay numeric,
                    amount_sub_total numeric,
                    amount_sub_rel_total numeric,
                    amount_deposit numeric,
                    qty_received numeric,
                    qty_unreceived numeric,
                    total_advance numeric,
                    total_payment_received numeric,
                    total_payment_remain numeric,
                    total_qty_fixed numeric,
                    qty_unfixed numeric,
                    --total_payment numeric,
                    check_qty boolean,
                    check_price_unit boolean,
                    no_copute boolean,
                    is_temp_quota boolean,
                    is_according boolean,
                    exchange_rate double precision ,
                    --relation_price_unit double precision,
                    --relation_premium double precision,
                    advance_amount double precision,
                    lifffe_line double precision,
                    --lifffe_line_ptbf double precision,
                    difams double precision,
                    ex double precision,
                    diff_price double precision,
                    --fixed_vnd double precision,
                    --qty_allocate double precision,
                    sd_price double precision,
                    si_price double precision,
                    cert_cost double precision,
                    grade_id integer
                    --print_count integer,
                    --pending_allocation_qty numeric
                )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('purchase_contract_id_seq', (select max(id) + 1 from  purchase_contract));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_purchase_contract_line(self):
        sql ='''
        INSERT INTO 
            purchase_contract_line 
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
                    contract_p_id ,
                    delivery_place_id ,
                    certificate_id ,
                    trader_id ,
                    crop_id ,
                    state  ,
                    type_price_weight  ,
                    type  ,
                    cert_type  ,
                    certification_type  ,
                    trade_month  ,
                    fix_status  ,
                    delivery_status  ,
                    count_down  ,
                    in_exposure  ,
                    grade_2  ,
                    group_location  ,
                    date_fix ,
                    deadline_date ,
                    date_order ,
                    delivery_from ,
                    delivery_to ,
                    fixation_date ,
                    name   ,
                    product_qty ,
                    price_subtotal ,
                    price_tax ,
                    price_total ,
                    qty_received ,
                    qty_unreceived ,
                    price_unit  ,
                    delivery_tolerance ,
                    premium ,
                    diff_price ,
                    qty_mt ,
                    ex ,
                    total_lot ,
                    fix_lot ,
                    unfix_lot ,
                    transport_to_factory ,
                    cost_to_fob_hcm ,
                    pre_dis_vs_g2 ,
                    cert_pre ,
                    g2_fob_equiv ,
                    product_fob ,
                    provisional_amount ,
                    stoploss_level ,
                    hedged_fixed_level ,
                    hedged_fixed_level_report ,
                    ctr_fob_price ,
                    mtm_fob_price ,
                    price_diff_usd_mt ,
                    flat_exposure ,
                    diff_exposure ,
                    ptbf_unpaid_amount ,
                    deposit ,
                    sum_exposure ,
                    difams 
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
                    sequence ,
                    company_id ,
                    partner_id ,
                    currency_id ,
                    product_id  ,
                    product_uom  ,
                    packing_id ,
                    contract_p_id ,
                    delivery_place_id ,
                    certificate_id ,
                    trader_id ,
                    crop_id ,
                    state  ,
                    type_price_weight  ,
                    type  ,
                    cert_type  ,
                    certification_type  ,
                    trade_month  ,
                    fix_status  ,
                    delivery_status  ,
                    count_down  ,
                    in_exposure  ,
                    grade_2  ,
                    group_location  ,
                    date_fix ,
                    deadline_date ,
                    date_order ,
                    delivery_from ,
                    delivery_to ,
                    fixation_date ,
                    name   ,
                    product_qty ,
                    price_subtotal ,
                    price_tax ,
                    price_total ,
                    qty_received ,
                    qty_unreceived ,
                    price_unit  ,
                    delivery_tolerance ,
                    premium ,
                    diff_price ,
                    qty_mt ,
                    ex ,
                    total_lot ,
                    fix_lot ,
                    unfix_lot ,
                    transport_to_factory ,
                    cost_to_fob_hcm ,
                    pre_dis_vs_g2 ,
                    cert_pre ,
                    g2_fob_equiv ,
                    product_fob ,
                    provisional_amount ,
                    stoploss_level ,
                    hedged_fixed_level ,
                    hedged_fixed_level_report ,
                    ctr_fob_price ,
                    mtm_fob_price ,
                    price_diff_usd_mt ,
                    flat_exposure ,
                    diff_exposure ,
                    ptbf_unpaid_amount ,
                    deposit ,
                    sum_exposure ,
                    difams 
                 
                FROM public.purchase_contract_line') 
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
                        contract_p_id integer,
                        delivery_place_id integer,
                        certificate_id integer,
                        trader_id integer,
                        crop_id integer,
                        state character varying ,
                        type_price_weight character varying ,
                        type character varying ,
                        cert_type character varying ,
                        certification_type character varying ,
                        trade_month character varying ,
                        fix_status character varying ,
                        delivery_status character varying ,
                        count_down character varying ,
                        in_exposure character varying ,
                        grade_2 character varying ,
                        group_location character varying ,
                        date_fix date,
                        deadline_date date,
                        date_order date,
                        delivery_from date,
                        delivery_to date,
                        fixation_date date,
                        name text  ,
                        product_qty numeric ,
                        price_subtotal numeric,
                        price_tax numeric,
                        price_total numeric,
                        qty_received numeric,
                        qty_unreceived numeric,
                        price_unit double precision ,
                        delivery_tolerance double precision,
                        premium double precision,
                        diff_price double precision,
                        qty_mt double precision,
                        ex double precision,
                        total_lot double precision,
                        fix_lot double precision,
                        unfix_lot double precision,
                        transport_to_factory double precision,
                        cost_to_fob_hcm double precision,
                        pre_dis_vs_g2 double precision,
                        cert_pre double precision,
                        g2_fob_equiv double precision,
                        product_fob double precision,
                        provisional_amount double precision,
                        stoploss_level double precision,
                        hedged_fixed_level double precision,
                        hedged_fixed_level_report double precision,
                        ctr_fob_price double precision,
                        mtm_fob_price double precision,
                        price_diff_usd_mt double precision,
                        flat_exposure double precision,
                        diff_exposure double precision,
                        ptbf_unpaid_amount double precision,
                        deposit double precision,
                        sum_exposure double precision,
                        difams double precision
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('purchase_contract_line_id_seq', (select max(id) + 1 from  purchase_contract_line));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return
    
    def sys_npe_nvp_relation(self):
        sql ='''
        INSERT INTO 
            npe_nvp_relation 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                npe_contract_id ,
                contract_id ,
                ptbf_id ,
                partner_id ,
                product_id ,
                type  ,
                date_fixed ,
                product_qty ,
                total_qty_fixed ,
                --qty_unfixed ,
                --original_npe_qty ,
                --qty_unreceived ,
                rate  
                --relation_price_unit 
            )        
        
        SELECT 
            *
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date,create_uid, 
                    write_date, write_uid, 
                    npe_contract_id ,
                    contract_id ,
                    ptbf_id ,
                    partner_id ,
                    product_id ,
                    type  ,
                    date_fixed ,
                    product_qty ,
                    total_qty_fixed ,
                    --qty_unfixed ,
                    --original_npe_qty ,
                    --qty_unreceived ,
                    rate  
                    --relation_price_unit 
                 
                FROM public.npe_nvp_relation') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        npe_contract_id integer,
                        contract_id integer,
                        ptbf_id integer,
                        partner_id integer,
                        product_id integer,
                        type character varying ,
                        date_fixed date,
                        product_qty numeric,
                        total_qty_fixed numeric,
                        --qty_unfixed numeric,
                        --original_npe_qty numeric,
                        --qty_unreceived numeric,
                        rate double precision
                        --relation_price_unit double precision
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('npe_nvp_relation_id_seq', (select max(id) + 1 from  npe_nvp_relation));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return  
    
    def sys_request_payment(self):
        sql ='''
        INSERT INTO 
            request_payment 
            (
                id,
                create_date,create_uid,
                write_date, write_uid,                     
                partner_id ,
                songay ,
                company_id ,
                purchase_contract_id ,
                users_request_id ,
                partner_bank_id ,
                ptbt_fix_price ,
                name  ,
                chinhanh ,
                account_no ,
                state  ,
                type  ,
                type_payment  ,
                date ,
                request_amount ,
                advance_payment_quantity ,
                total_payment ,
                total_remain ,
                amount_approved ,
                full_fixation ,
                payment_quantity ,
                fx_price ,
                market_price ,
                provisional_price ,
                fixation_amount ,
                fix_price ,
                diff_price ,
                ref_price ,
                rate ,
                request_amount_temp ,
                request_fun_amount 
            )        
        
        SELECT 
            id, 
            create_date, create_uid, 
            write_date, write_uid, 
            partner_id ,
            songay ,
            company_id ,
            purchase_contract_id ,
            users_request_id ,
            partner_bank_id ,
            ptbt_fix_price ,
            name  ,
            chinhanh ,
            COALESCE(account_no,' ') ,
            state  ,
            type  ,
            type_payment  ,
            date ,
            request_amount ,
            advance_payment_quantity ,
            total_payment ,
            total_remain ,
            amount_approved ,
            full_fixation ,
            payment_quantity ,
            fx_price ,
            market_price ,
            provisional_price ,
            fixation_amount ,
            fix_price ,
            diff_price ,
            ref_price ,
            rate ,
            request_amount_temp ,
            request_fun_amount
            
            FROM public.dblink
                ('sucdendblink',
                 'SELECT 
                    id, 
                    create_date, create_uid, 
                    write_date, write_uid, 
                    partner_id ,
                    songay ,
                    company_id ,
                    purchase_contract_id ,
                    users_request_id ,
                    partner_bank_id ,
                    ptbt_fix_price ,
                    name  ,
                    chinhanh ,
                    account_no ,
                    state  ,
                    type  ,
                    type_payment  ,
                    date ,
                    request_amount ,
                    advance_payment_quantity ,
                    total_payment ,
                    total_remain ,
                    amount_approved ,
                    full_fixation ,
                    payment_quantity ,
                    fx_price ,
                    market_price ,
                    provisional_price ,
                    fixation_amount ,
                    fix_price ,
                    diff_price ,
                    ref_price ,
                    rate ,
                    request_amount_temp ,
                    request_fun_amount 
                 
                FROM public.request_payment') 
                AS DATA(id INTEGER,
                        create_date timestamp without time zone,
                        create_uid integer,
                        write_date timestamp without time zone,
                        write_uid integer,                            
                        partner_id integer,
                        songay integer,
                        company_id integer,
                        purchase_contract_id integer,
                        users_request_id integer,
                        partner_bank_id integer,
                        ptbt_fix_price integer,
                        name character varying ,
                        chinhanh character varying,
                        account_no character varying,
                        state character varying ,
                        type character varying ,
                        type_payment character varying ,
                        date date,
                        request_amount numeric,
                        advance_payment_quantity numeric,
                        total_payment numeric,
                        total_remain numeric,
                        amount_approved numeric,
                        full_fixation boolean,
                        payment_quantity double precision,
                        fx_price double precision,
                        market_price double precision,
                        provisional_price double precision,
                        fixation_amount double precision,
                        fix_price double precision,
                        diff_price double precision,
                        ref_price double precision,
                        rate double precision,
                        request_amount_temp double precision,
                        request_fun_amount double precision
                    )
        '''
        self.env.cr.execute(sql)
        self.env.cr.execute('''
            SELECT setval('request_payment_id_seq', (select max(id) + 1 from  request_payment));
        ''')   
        
        # for catg in self.env['product.category'].search([]):
        #     catg._compute_complete_name()
        return