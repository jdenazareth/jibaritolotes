#-*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError
from num2words import num2words

class ReporteFactura(models.Model):

    _inherit = 'account.move'    
    porcentaje =fields.Float(string='Porcentaje', compute="_format_apartado", digits=(16, 2))
    resta = fields.Float(string='resta', compute="_format_apartado", digits=(16, 2))
    cantidad = fields.Float(string="cantidad", compute="_format_apartado", digits=(16, 2))
    
    porcentaje_letra = fields.Char(string="porcentaje letra", compute="get_text_amount_calculo")
    resta_letra = fields.Char(string="Resta letra ", compute="get_text_amount_calculo")
    cantidad_letra = fields.Char(string="Cantidad letra", compute="get_text_amount_calculo")
    total_letra = fields.Char(string="total letra", compute="get_text_amount_calculo")
    total_a_devolver = fields.Float(string="Total a devolver", compute="_total_devolver", digits=(16, 2))
    total_a_devolver_letra = fields.Char(string="Total Letra", compute="get_text_amount_calculo")
    

    

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
        self.porcentaje_letra = num2words(self.porcentaje, lang='es').upper()
        self.resta_letra =  num2words(self.resta, lang='es').upper()
        self.cantidad_letra =  num2words(self.cantidad, lang='es').upper()
        self.total_letra =  num2words(self.amount_total, lang='es').upper()
        self.total_a_devolver_letra = num2words(self.total_a_devolver, lang='es').upper()

#self.porcentaje_letra = num2words(round(self.porcentaje,2), lang='es').lower()


