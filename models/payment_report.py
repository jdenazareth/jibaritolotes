#-*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError
from num2words import num2words
from werkzeug import secure_filename

class ReportePayment(models.Model):

    _inherit = 'account.payment'  
    cantidad_letra = fields.Char(string="Cantidad letra", compute="get_text_amount_total")
    dia_dato_pago = fields.Integer(string="Pago dia de cada mes", compute="get_origin")
    pagos_mensualidad = fields.Float(string="Pagos de: ", compute="get_origin")
    pago_mensualidad_letra = fields.Char(string="pagos en letra", compute="get_text_amount_mensaulidad")
    residual = fields.Float(string="Residual ", compute="get_origin")
    residual_letra =  fields.Char(strin="Residual letra", compute="get_text_amount_mensaulidad")
    total_factura = fields.Float(string="Total Facturas", compute="get_origin")
    def get_text_amount_total(self):
        self.cantidad_letra = num2words(self.amount, lang='es').upper()

    def get_origin(self):
        datos=self.env['account.move'].search([('name','=',self.communication)]) #consulta
        self.dia_dato_pago = datos.invoice_payment_term_id.dia_dato
        self.total_factura = datos.amount_total
        self.residual = datos.amount_residual
        self.pagos_mensualidad = datos.amount_total - datos.porcentaje
        self.pagos_mensualidad =  self.pagos_mensualidad / datos.invoice_payment_term_id.ji_numbers_monthly
    
    def get_text_amount_mensaulidad(self):
        self.pago_mensualidad_letra = num2words(self.pagos_mensualidad, lang='es').upper()
        self.residual_letra = num2words(self.residual, lang='es').upper()




class ReportePaymentTerm(models.Model):
    _inherit = 'account.payment.term'
    dia_dato = fields.Integer(string="Mensualidad los dias: ", compute="_format_dia_de_mes")


    
    @api.depends("line_ids")
    def _format_dia_de_mes(self):
            for line in self:
                for li in line.line_ids:
                    if li.ji_type == 'monthly_payments':
                        line.dia_dato = li.day_of_the_month
                break
    

