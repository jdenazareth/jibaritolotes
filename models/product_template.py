# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ji_area = fields.Float(string="Area")
    ji_street = fields.Char(string="Street")
    ji_corner_with = fields.Char(string="Corner With")
