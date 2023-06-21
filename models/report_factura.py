#-*- coding: utf-8 -*-

from email.policy import strict
from odoo import models, fields, api,_
from odoo.exceptions import UserError
from num2words import num2words

class ReporteFactura(models.Model):

    _inherit = 'account.move'    
    porcentaje =fields.Float(string='Porcentaje', compute="_format_apartado", digits=(16, 2))
    resta = fields.Float(string='resta', compute="_format_apartado", digits=(16, 2))
    cantidad = fields.Float(string="cantidad", compute="_format_apartado", digits=(16, 2))
    
    porcentaje_letra = fields.Char(string="porcentaje letra", compute="get_text_amount_calculo")
    centavo_porcentaje = fields.Char(string="Centavos Porcentaje",compute="get_text_amount_calculo")
    resta_letra = fields.Char(string="Resta letra ", compute="get_text_amount_calculo")
    centavo_resta = fields.Char(string="Centavo letra", compute="get_text_amount_calculo")
    cantidad_letra = fields.Char(string="Cantidad letra", compute="get_text_amount_calculo")
    centavo_cantidad = fields.Char(string="Cantidad centavo", compute="get_text_amount_calculo")
    total_letra = fields.Char(string="total letra", compute="get_text_amount_calculo")
    centavo_total = fields.Char(string="Centavo Total",compute="get_text_amount_calculo")
    total_a_devolver = fields.Float(string="Total a devolver", compute="_total_devolver", digits=(16, 2))
    total_a_devolver_letra = fields.Char(string="Total Letra", compute="get_text_amount_calculo")
    centavo_devolver = fields.Char(string="Centavo a devolver", compute="get_text_amount_calculo")
    precio_unitario_en_letra = fields.Char(string="Precio Unitario", compute="get_text_amount_calculo")
    precio_unitario_centavo = fields.Char(string="Precio centavo", compute="get_text_amount_calculo")

    

    def _total_devolver(self):
        self.total_a_devolver = self.amount_total-self.amount_residual

    
    @api.depends("invoice_payment_term_id")
    def _format_apartado(self):

        try:
            for line in self:
                line.porcentaje = line.invoice_payment_term_id.ji_advance_payment/100
                line.cantidad = line.invoice_payment_term_id.ji_number_quotation
        except Exception as e:
            raise UserError("Dato no encontrado")
        self.porcentaje = self.porcentaje*self.amount_total
        self.resta = self.amount_total-self.porcentaje
        
        if self.porcentaje == 0:
            self.cantidad = 0
        else:
            self.cantidad = self.porcentaje/self.cantidad


    def get_text_amount_calculo(self):
        self.precio_unitario_en_letra = num2words(self.precio_unitario, lang='es').upper()
        self.precio_unitario_en_letra = self.precio_unitario_en_letra.split(" PUNTO ")[0]
        centavo_porcentaje = str(round(self.precio_unitario, 2)).split(".")[1]
        self.precio_unitario_centavo = centavo_porcentaje if len (centavo_porcentaje) > 1 else centavo_porcentaje+'0'

        self.porcentaje_letra = num2words(self.porcentaje, lang='es').upper()
        self.porcentaje_letra = self.porcentaje_letra.split(" PUNTO ")[0]
        centavo_porcentaje = str(round(self.porcentaje, 2)).split(".")[1]
        self.centavo_porcentaje = centavo_porcentaje if len (centavo_porcentaje) > 1 else centavo_porcentaje+'0'

        self.resta_letra =  num2words(self.resta, lang='es').upper()
        self.resta_letra = self.resta_letra.split(" PUNTO ")[0]
        centavo_resta = str(round(self.resta, 2)).split(".")[1]
        self.centavo_resta = centavo_resta if len (centavo_resta) > 1 else centavo_resta+'0'

        self.cantidad_letra =  num2words(self.cantidad, lang='es').upper()
        self.cantidad_letra = self.cantidad_letra.split(" PUNTO ")[0]
        centavo_cantidad = str(round(self.cantidad, 2)).split(".")[1]
        self.centavo_cantidad = centavo_cantidad if len (centavo_cantidad) > 1 else centavo_cantidad+'0'

        self.total_letra =  num2words(self.amount_total, lang='es').upper()
        self.total_letra = self.total_letra.split(" PUNTO ")[0]
        centavo_total = str(round(self.amount_total, 2)).split(".")[1]
        self.centavo_total = centavo_total if len (centavo_total) > 1 else centavo_total+'0'

        self.total_a_devolver_letra = num2words(self.total_a_devolver, lang='es').upper()
        self.total_a_devolver_letra = self.total_a_devolver_letra.split(" PUNTO ")[0]
        centavo_devol = str(round(self.total_a_devolver, 2)).split(".")[1]
        self.centavo_devolver = centavo_devol if len (centavo_devol) > 1 else centavo_devol+'0'

#self.porcentaje_letra = num2words(round(self.porcentaje,2), lang='es').lower()


