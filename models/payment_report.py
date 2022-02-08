#-*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError
from num2words import num2words
from werkzeug import secure_filename

class ReportePayment(models.Model):

    _inherit = 'account.payment'  
    cantidad_letra = fields.Char(string="Cantidad letra", compute="get_text_amount_total")
    dia_dato_pago = fields.Integer(string="Pago dia de cada mes", compute="get_origin")
    pagos_mensualidad = fields.Monetary(string="Pagos de: ", compute="get_origin")
    total_contrato = fields.Monetary(string="Total contrato", compute="get_origin")
    pago_mensualidad_letra = fields.Char(string="pagos en letra", compute="get_text_amount_mensaulidad")
    residual = fields.Monetary(string="Residual ", compute="get_origin")
    residual_letra = fields.Char(strin="Residual letra", compute="get_text_amount_mensaulidad")
    total_factura = fields.Float(string="Total Facturas", compute="get_origin")
    total_amount = fields.Monetary(string="Total", compute="get_text_amount_total")
    centa_totla = fields.Char(string="Centavos pago")
    total_contrato_letra = fields.Char(string="Total contrato letra", compute="get_origin")
    cent_contrato = fields.Char(string="Centavos contrato", comput="get_origin")
    cent_residual = fields.Char(string="Centavos residual", comput="get_origin")
    cent_pago_mesual = fields.Char(string="Centavos pagos mensua", comput="get_origin")

    

    def get_text_amount_total(self):
        totall = 0
        for rec in self:
            
            totall = rec.ji_moratorio + rec.amount
            rec.total_amount = totall
            rec.cantidad_letra = num2words(totall, lang='es').upper()
            rec.cantidad_letra = rec.cantidad_letra.split(" PUNTO ")[0]
            centavo_total = str(round(totall, 2)).split(".")[1]
            rec.centa_totla= centavo_total  if len (centavo_total) > 1 else centavo_total+'0'
            rec.second_cantidad_lera = rec.cantidad_letra.split(" PUNTO ")[0]


            
    def action_conf(self):
        for res in self:
            com = res.communication.split("-")
            res.payment_reference = com[0]
    def get_origin(self):
        for res in self:
            # datos=self.env['account.move'].search([('invoice_payment_ref','=',res.payment_reference)]) #consulta
            dia = 0
            mensual = 0
            total = 0
            rtotal = 0.0
            contrato = 0
            for fact in res.invoice_ids:
                total = fact.amount_total
                anticipo = round(total * fact.invoice_payment_term_id.ji_advance_payment / 100, 2)
                contrato = total - anticipo
                rtotal = round(fact.amount_residual, 2)
                for lin in fact.line_ids:
                    if lin.ji_number.find('A') != 0 and lin.debit >= 1:
                        dia = lin.date_maturity.day
                        mensual = lin.debit
                        break
            res.dia_dato_pago = dia
            res.total_factura = total
            res.residual = round(rtotal, 3)
            centavo_redisual = str(round(res.residual, 2)).split(".")[1]
            res.cent_residual = centavo_redisual if len(centavo_redisual) > 1 else centavo_redisual+'0'
                
            res.total_contrato =  contrato
            res.pagos_mensualidad = round(mensual, 2)
            centavo_pago_mensual = str(round(mensual, 2)).split(".")[1]
            res.cent_pago_mesual = centavo_pago_mensual if len(centavo_pago_mensual) > 1 else centavo_pago_mensual+'0'
            res.total_contrato_letra = num2words(contrato, lang='es').upper()
            res.total_contrato_letra = res.total_contrato_letra.split(" PUNTO ")[0]
            centavo_contrato = str(round(contrato, 2)).split(".")[1]
            res.cent_contrato = centavo_contrato if len (centavo_contrato) > 1 else centavo_contrato+'0'


    
    def get_text_amount_mensaulidad(self):
        menusalidad = num2words(self.pagos_mensualidad, lang='es').upper()
        self.pago_mensualidad_letra = menusalidad.split( "PUNTO" )[0]
        residual = num2words(self.residual, lang='es').upper()
        self.residual_letra = residual.split(" PUNTO ")[0]

    payment_refer = fields.Char(strin="Referencia", compute="get_referencia")
    @api.model
    @api.depends("communication","state")
    def get_referencia(self):
        for rec in self:
            com = rec.communication.split("-")
            rec.payment_reference = com[0]
            if rec.journal_id.name == "Anticipo":
                rec.x_studio_tipo_de_pago = "Anticipo"
            rec.payment_refer = com[0]


class ReportePaymentTerm(models.Model):
    _inherit = 'account.payment.term'
    dia_dato = fields.Integer(string="Mensualidad los dias: ", compute="_format_dia_de_mes")


    
    @api.depends("line_ids")
    def _format_dia_de_mes(self):
            for line in self:
                dia = 0
                for li in line.line_ids:
                    if li.ji_type == 'monthly_payments':
                        dia = li.day_of_the_month
                        break
                line.dia_dato = dia

    

