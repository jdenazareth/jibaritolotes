# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ji_area = fields.Float(string="Area")
    ji_street = fields.Char(string="Street")
    ji_corner_with = fields.Char(string="Corner With")
    estado_producto = fields.Many2one('estados.g', string='Estado')


class Estadosg(models.Model):
    _name = "estados.g"
    _inherit = ['mail.thread']

    name = fields.Char(String="Estado", track_visibility='onchange')