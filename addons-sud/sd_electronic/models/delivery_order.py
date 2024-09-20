# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import datetime
import time
import pytz
import requests
import json
import base64
import uuid
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning

class DeliveyOrder(models.Model):
    _inherit = 'delivery.order'
    
    ref_id = fields.Char('RefID', readonly=True, size=128)
    transaction_id = fields.Char('TransactionID', readonly=True, size=128)
    invoice_number = fields.Char('Invoice Number', readonly=True, size=128)
    invoice_issue_date = fields.Date('Invoice Issued Date', readonly=True)
    status = fields.Char(string="Status", readonly=True, required=False, size=128)
    base64_pdf = fields.Char(string="PDF", required=False, size=128)
    
    
    def get_connect(self, info_config=1):
        try:
            result = requests.post('%s/auth/token' % ('https://api.meinvoice.vn/api/v3'), params={}, data=json.dumps({"appid": "FC772F5F-FC65-47F6-8240-4D10518797C6", "taxcode": "6000706357", "username": "0917185518", "password": "P@ssw0rd17588"}), headers={'content-type': 'application/json'})
            if result.status_code == 200 and result.json().get('Data'):
                token = result.json().get('Data')
                return token
            else:
                self.token = False
                raise UserError(_("Connection Error: %s \n %s" % (
                    result.status_code, result.json().get('Data'))))
        except ValueError as e:
            raise ValueError(e)
            
    def print_preview_delivery(self):
        info_config = 1 #self.info_config
        token = False #self.token
        #info_template = self.info_template
        get_data = ''
        null = None
        if not info_config:
            info_config = self.info_config #= self.get_info_config()
        if not token:
            token = str(self.get_connect(info_config))
        headers = {'Content-type': 'application/json; charset=utf-8',
                   'Authorization': 'Bearer %s' % token}
        data_template = {}
        data_invoice_detail = []
        number = 0
        for line in self.delivery_order_ids:
            number = number + 1
            values = {
              "Amount": 0,
              "AmountOC": 0,
              "AmountWithoutVAT": 0,
              "AmountWithoutVATOC": 0,
              "CustomField10Detail": "",
              "CustomField1Detail": "",
              "CustomField2Detail": "",
              "CustomField3Detail": "",
              "CustomField4Detail": "",
              "CustomField5Detail": "",
              "CustomField6Detail": "",
              "CustomField7Detail": "",
              "CustomField8Detail": "",
              "CustomField9Detail": "",
              "DiscountAmount": 0,
              "DiscountAmountOC": 0,
              "DiscountRate": 0,
              "ItemCode": line.product_id.default_code or null,
              "ItemName": line.product_id.name or ' ', #+ " " + (line.product_id.description_delivery_misa or ' '),
              "ItemType": 1,
              "LineNumber": 1,
              "Quantity": line.product_qty or 0,
              "SortOrder": 1,
              "UnitName": line.product_uom.name or null,
              "UnitPrice": 0,
              "VATAmount": 0,
              "VATAmountOC": 0,
              "VATRateName": "KCT"
            }
            data_invoice_detail.append(values)

        data_invoice = {
            "RefID": str(uuid.uuid4()),
            "InvSeries": "1K24TSV",
            "InvoiceName": "Hoa Don Gia Tri Gia Tang",
            "InvDate":  str(self.date or null),
            "CurrencyCode": self.currency_id.name or null,
            "ExchangeRate": self.currency_id and self.currency_id.rate or 1,
            "PaymentMethodName": "TM/CK",
            "BuyerLegalName": self.partner_id.name or null,
            "BuyerTaxCode": self.partner_id.vat or null,
            "BuyerAddress": self.partner_id.street or null,
            "BuyerCode": self.partner_id.ref or '',
            "BuyerPhoneNumber": self.partner_id.phone or null,
            "BuyerEmail": self.partner_id.email or null,
            "BuyerFullName": self.partner_id.name or null,
            "BuyerBankAccount": null,
            "BuyerBankName": null,
            "ReferenceType": null,
            "OrgInvoiceType": null,
            "OrgInvTemplateNo": null,
            "OrgInvSeries": null,
            "OrgInvNo": null,
            "OrgInvDate": str(datetime.date.today()),
            "TotalSaleAmountOC": 0,
            "TotalAmountWithoutVATOC": 0,
            "TotalVATAmountOC": 0,
            "TotalDiscountAmountOC": 0,
            "TotalAmountOC": 0,
            "TotalSaleAmount": 0,
            "TotalAmountWithoutVAT": 0,
            "TotalVATAmount": 0,
            "TotalDiscountAmount": 0,
            "TotalAmount": 0,
            "TotalAmountInWords": null,
            "OriginalInvoiceDetail": data_invoice_detail,
        "TaxRateInfo": [
                          {
                            "VATRateName": 'KCT',
                            "AmountWithoutVATOC": 0,
                            "VATAmountOC": 0,
                          }
                       ],
          "OptionUserDefined": {
                "AmountDecimalDigits": "2",
                "AmountOCDecimalDigits": "2",
                "CoefficientDecimalDigits": "2",
                "ExchangRateDecimalDigits": "2",
                "MainCurrency": self.currency_id.name or null,
                "QuantityDecimalDigits": "3",
                "UnitPriceDecimalDigits": "2",
                "UnitPriceOCDecimalDigits": "2"
          }
        }

        data = json.dumps(data_invoice)
        result = requests.post('https://api.meinvoice.vn/api/v3/code/itg/invoicepublishing/invoicelinkview?type=1', headers=headers, data=data)
        if result.status_code == 200:
            get_data = result.json().get('Data')
            files_name = 'E-Invoicing.pdf'
            # Luu base64 de khong mat du lieu khi truyen qua controllers
            r = requests.get(get_data, stream=True)
            # Goi controllers xu ly preview pdf
            return {
                'type': 'ir.actions.act_url',
                'url': get_data,
                'target': 'new',
            }
        else:
            raise UserError(_("Connection print preview error: %s \n %s \n %s" % (
                result.status_code, str(get_data), str(data))))

    def inventory_delivery(self):
        ref_id = str(uuid.uuid4())

        get_data = ''
        info_config = 1 #self.info_config
        token = False #self.token
        null = None 
        if not token:
            token = str(self.get_connect(info_config))
        headers = {'Content-type': 'application/json; charset=utf-8', 'Authorization': 'Bearer %s' % token}
        data_template = {}
        data_invoice_detail = []
        number = 0

        for line in self.delivery_order_ids:
            number = number + 1
            values = {
                    "VATRateName": "KCT",
                    "ItemName": line.product_id.name or ' ',
                    "AmountWithoutVATOC": 0,
                    "AmountOC": 0,
                    "DiscountAmount": 0,
                    "DiscountAmountOC": 0,
                    "DiscountRate": 0,
                    "VATAmountOC": 0,
                    "VATAmount": 0,
                    "ItemType": 1,
                    "SortOrder": 1,
                    "LineNumber": 1,
                    "CustomField1Detail": "",
                    "CustomField2Detail": "",
                    "CustomField3Detail": "",
                    "CustomField4Detail": "",
                    "CustomField5Detail": "",
                    "CustomField6Detail": "",
                    "CustomField7Detail": "",
                    "CustomField8Detail": "",
                    "CustomField9Detail": "",
                    "CustomField10Detail": "",
                    "AmountWithoutVAT": self.contract_id.amount_total or 0,
                    "Amount": self.contract_id.amount_total or 0,
                    "Quantity": line.product_qty or 0,
                    "UnitName": line.product_uom.name or null,
                    "ItemCode": line.product_id.default_code or null,
                    "UnitPrice": self.contract_id.contract_line[0].price_unit or 0
                    }
            data_invoice_detail.append(values)

        data_invoice = [{
            "RefID": ref_id,
            "OriginalInvoiceData":
            {
                "InvDate": str(self.date) or null,
                "InvoiceName": "Hoa Don Van Chuyen",
                "TotalAmountInWords": " ",
                "TotalDiscountAmount": 0,
                "TotalAmount": self.contract_id.amount_total or 0,
                "TotalDiscountAmountOC": 0,
                "TotalAmountOC": self.contract_id.amount_total or 0,
                "TotalVATAmountOC": 0,
                "TotalVATAmount": 0,
                "TotalSaleAmountOC": self.contract_id.amount_total or 0,
                "TotalAmountWithoutVAT": self.contract_id.amount_total or 0,
                "TotalSaleAmount": self.contract_id.amount_total or 0,
                "TotalAmountWithoutVATOC": self.contract_id.amount_total or 0,
                "PaymentMethodName": "TM/CK",
                "OrgInvDate": null,
                "CurrencyCode": self.currency_id and self.currency_id.name or "VND",
                "ExchangeRate": self.currency_id and self.currency_id.rate or 1,
                "OrgInvTemplateNo": null,
                "OrgInvoiceType": null,
                "OrgInvNo": null,
                "ReferenceType": null,
                "BuyerEmail": "accounting.vietnam@sucden.com",
                "BuyerBankName": " ",
                "OptionUserDefined": {
                    "ExchangRateDecimalDigits": "2",
                    "AmountDecimalDigits": "2",
                    "UnitPriceDecimalDigits": "2",
                    "MainCurrency": "VND",
                    "QuantityDecimalDigits": "3",
                    "AmountOCDecimalDigits": "2",
                    "UnitPriceOCDecimalDigits": "2",
                    "CoefficientDecimalDigits": "2"
                },
                "InvSeries": "6K24NDO",
                "OriginalInvoiceDetail": data_invoice_detail,
                "CurrencyCode": self.currency_id.name or null,
                "ExchangeRate": self.currency_id and self.currency_id.rate or 1,
                "PaymentMethodName": "TM/CK",
                "BuyerLegalName": self.partner_id.name or null,
                "BuyerTaxCode": self.partner_id.vat or null,
                "BuyerAddress": self.partner_id.street or null,
                "BuyerCode": self.partner_id.ref or '',
                "BuyerPhoneNumber": self.partner_id.phone or null,
                "BuyerFullName": self.partner_id.name or null,
                "BuyerBankAccount": " ",
                "TaxRateInfo": [
                    {
                    "VATRateName": "KCT",
                    "VATAmountOC": self.contract_id.amount_total or 0,
                    "AmountWithoutVATOC": self.contract_id.amount_total or 0
                    }
                ],
                "OrgInvSeries": null,
                "RefID": ref_id,
                "InternalCommandNo": self.name or "",
                "InternalCommand": self.name or "",
                "JournalMemo": self.reason or "",
                "StockOutLegalName": self.trucking_no or "",
                "StockOutAddress": u"Lô đất CN2-1. CN2-2, CN2-3 – Cụm công nghiệp Tân An 2 – TP Buôn Ma Thuột – Tỉnh DăkLăk",
                "TransporterName": self.trucking_no or "",
                "StockOutFullName": self.from_warehouse_id.name or "Factory-BMT",
                "StockInAddress": self.partner_id.name or null,
                "Transport": "Xe Container",
                "ContractDate": str(self.date) or str(datetime.date.today())
            },
            "RefID": ref_id,
            "InvSeries": "6K24NDO",
            "InvoiceName": "Hoa Don Van Chuyen",
            "IsSendEmail": True,
            "ReceiverEmail":"logistics.vietnam@sucden.com",
            "ReceiverName":"Phi"
        }]

        data = json.dumps(data_invoice)

        result = requests.post('%s/itg/invoicepublishing/publishhsm' % 'https://api.meinvoice.vn/api/v3', headers=headers, data=data)
        if result.status_code == 200:
            invoice = {}
            get_data = result.json().get('Data')
            
            convert_dict = json.loads(get_data)
            for i in convert_dict:
                if not i['ErrorCode']:
                    values = {
                        'RefID': ref_id,
                        'TransactionID': i['TransactionID'],
                        'InvoiceNumber': i['InvNo'],
                        'InvoiceIssuedDate': i['InvDate']
                    }
                    invoice = values
            
            try:
                self.write({
                'status': 'Success',
                'ref_id': ref_id,
                'transaction_id': invoice['TransactionID'],
                'invoice_number': invoice['InvoiceNumber'],
                'invoice_issue_date': invoice['InvoiceIssuedDate'],
            })
            except:
                raise UserError("Connection Error Issue Delivery: %s \n %s \n json => %s \n %s" % (result.status_code, result.json(), convert_dict, str(data)))
        else:
            raise UserError("Connection Error Issue Delivery: %s \n %s \n json => %s" % (result.status_code, result.json(), convert_dict))
        return 1

    def convert_invoice(self):
        return
