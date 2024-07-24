# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class NameCapacity(models.Model):
    _name = "name.capacity"
    
    name = fields.Char(string="Name")
    tph = fields.Integer(string="TPH")
    month_capacity = fields.Integer(string="Month Capacity")
    annual_capacity = fields.Integer(string="Annual Capacity")


class AvailableOpeartionTime(models.Model):
    _name = "available.operation.time"
    
    name = fields.Char(string="Name")
    hours = fields.Integer(string="Hours")
    non_indus_downtime = fields.Integer(string="Non Industrial Downtime")

class PlanedOperationTime(models.Model):
    _name = "planed.operation.time"
    
    name = fields.Char(string="Name")
    operation_hours = fields.Integer(string="Operation Hours/Year")
    scheduled_downtime_hours = fields.Integer(string="Scheduled Downtime Hours/Year")
    non_scheduled_downtime_hours = fields.Integer(string="Non Scheduled Downtime Hours/Year")