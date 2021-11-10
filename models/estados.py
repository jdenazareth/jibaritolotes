# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class ProductoG(models.Model):
    _inherit = "product.template"

    estado_producto = fields.Many2one('estados.g', string='Estado')


class Estadosg(models.Model):
    _name = "estados.g"
    _inherit = ['mail.thread']

    name = fields.Char(String="Estado", track_visibility='onchange')
