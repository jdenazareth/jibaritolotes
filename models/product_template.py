# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from num2words import num2words

class ProductTemplate(models.Model):
    _inherit = "product.template"

    ji_area = fields.Float(string="Area")
    ji_street = fields.Char(string="Street")
    ji_corner_with = fields.Char(string="Corner With")

    x_studio_manzana = fields.Many2one('manzana.ji', string="Manzana")
    x_studio_lote = fields.Many2one('lotes.ji', string="Lote")
    x_studio_calle = fields.Many2one('calle.ji', string="Calle")
    estado_producto = fields.Many2one('estados.g', string='Estado')
    precio_unitario_en_letra = fields.Char(string="Precio Unitario", compute="get_text_amount_calculo_product")
    precio_unitario_centavo = fields.Char(string="Precio centavo", compute="get_text_amount_calculo_product")


    def get_text_amount_calculo_product(self):
        self.precio_unitario_en_letra = num2words(self.list_price, lang='es').upper()
        self.precio_unitario_en_letra = self.precio_unitario_en_letra.split(" PUNTO ")[0]
        centavo_porcentaje = str(round(self.list_price, 2)).split(".")[1]
        self.precio_unitario_centavo = centavo_porcentaje if len (centavo_porcentaje) > 1 else centavo_porcentaje+'0'

class situacionAccionesTexto(models.Model):
    _inherit = "product.template"

    situacion_texto = fields.Text(String="Situación")
    acciones_texto = fields.Text(string="Acciones")



