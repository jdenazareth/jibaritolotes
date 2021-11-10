# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ji_area = fields.Float(string="Area")
    ji_street = fields.Char(string="Street")
    ji_corner_with = fields.Char(string="Corner With")
    ji_manzana = fields.Char(string="Manzana")
    ji_lote = fields.Char(string="Lote")
    x_studio_no_es_jibarito = fields.Boolean(string="No es Jibarito")
    x_studio_metros_cuadrados = fields.Integer(string="Metros cuadrados")
