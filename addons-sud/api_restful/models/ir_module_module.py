# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
import requests
import json


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"
