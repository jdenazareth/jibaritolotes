#-*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError, except_orm
from num2words import num2words
from werkzeug import secure_filename
import json
import qrcode
import base64
from io import BytesIO
from odoo.http import request

def generate_qr_code(value):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=20,
        border=4,
    )
    qr.add_data(value)
    qr.make(fit=True)
    img = qr.make_image()
    temp = BytesIO()
    img.save(temp, format="PNG")
    qr_img = base64.b64encode(temp.getvalue())
    return qr_img
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
    ji_mesto =  fields.Integer(string="Mes Pagado Total", compute="get_origin")
    ji_mes_nuevo = fields.Float(string="Mes nuevo")
    ji_mesnuevo_let = fields.Char(string="Mes abarcado", compute="get_origin")
    numero_engache = fields.Char(string="Numero de enganche", compute="get_text_amount_total")
    qr_pagos = fields.Binary("QR Code", compute='_generate_qr_code')
    ji_amount_fact = fields.Monetary(string="Total Factura T")
    categoria_producto = fields.Many2one(string="Categoria de producto", comodel_name="product.category",store=True, compute="get_categoria")
    codigo_prod = fields.Many2one(string="Codigo de producto", comodel_name="account.account",store=True,compute="get_categoria")

    trasnfer = fields.Boolean(string="Transferido")

    @api.depends("journal_id","communication","payment_transaction_id")
    def get_categoria(self):
        for res in self:

            if res.payment_type == "inbound":
                if res.journal_id.id == 9 or res.journal_id.id == 10:
                    res.x_studio_tipo_de_pago = "Anticipo"
                    res.categoria_producto = res.payment_transaction_id.sale_id.categoria_producto
                else:
                    datos = self.env['account.move'].search([('invoice_payment_ref', '=', res.communication)])
                    res.codigo_prod = datos.codigo_prod
                    res.categoria_producto = datos.categoria_producto
            else:
                datos = self.env['account.move'].search([('name', '=', res.communication)])
                # raise UserError(_("Factura" + str(datos.codigo_prod)))
                if datos:
                    res.codigo_prod = datos.codigo_prod
                    res.categoria_producto = datos.categoria_producto
                else:
                    for fa in res.invoice_ids:
                        res.codigo_prod = fa.codigo_prod
                        res.categoria_producto = fa.categoria_producto


    def get_categorias_prod(self):
        for res in self:
                # raise UserError(_("anticipo" + str(res.payment_transaction_id.sale_id.categoria_producto)))

            if res.payment_type == "inbound":
                if res.journal_id.id == 9 or res.journal_id.id == 10:
                    res.x_studio_tipo_de_pago = "Anticipo"
                    res.categoria_producto = res.payment_transaction_id.sale_id.categoria_producto
                else:
                    datos = self.env['account.move'].search([('invoice_payment_ref', '=', res.communication)])
                    res.codigo_prod = datos.codigo_prod
                    res.categoria_producto = datos.categoria_producto
            else:
                datos = self.env['account.move'].search([('name', '=', res.communication)])
            # raise UserError(_("Factura" + str(datos.codigo_prod)))
                if datos:
                    res.codigo_prod = datos.codigo_prod
                    res.categoria_producto = datos.categoria_producto
                else:
                    for fa in res.invoice_ids:
                        res.codigo_prod = fa.codigo_prod
                        res.categoria_producto = fa.categoria_producto



    def _generate_qr_code(self):
        for res in self:

            if "Tranfer Interna" == self.communication or self.payment_refer == "Tranfer Interna" or self.payment_refer=="" :
                self.qr_pagos = None
            else:
                service = "Fecha : " + str(self.payment_date.strftime('%d-%m-%Y'))
                # Check if BIC exists: version 001 = BIC, 002 = no BIC
                version = 'Convenio INDIVI Folio: 102799 - 102800'
                code = self.partner_id.name
                datos = self.env['account.move'].search([('invoice_payment_ref', '=', self.communication)])  # consulta
                datos2 = self.env['sale.order'].search([('reference', '=', self.payment_refer)])  # consulta
                monto = "Subtotal: USD $ "+ str('{:,.2f}'.format(self.amount)) + ", Moratorio: USD $ " + str('{:,.2f}'.format(self.ji_moratorio)) + ", Total: USD $ " + str('{:,.2f}'.format(self.total_amount))
                function = ""
                reference = ""
                bic=""
                if datos:
                    if datos.x_studio_manzana.name and datos.x_studio_lote.name and  datos.categoria_producto.name:
                        function = "Manzana " + datos.x_studio_manzana.name + ", Lote " + datos.x_studio_lote.name + ", Colonia " + datos.categoria_producto.name + ", C.P. 22010, Tijuana, B.C."
                        bic = str(datos.ji_get_area()) + " M2"

                    reference = "Contrato: " + datos.name
                elif datos2:
                    if datos.x_studio_manzana.name and datos.x_studio_lote.name and  datos.categoria_producto.name:
                        function = "Manzana " + datos2.x_studio_manzana.name + ", Lote " + datos2.x_studio_lote.name + ", Colonia " + datos2.ji_get_categoria() + ", C.P. 22010, Tijuana, B.C."
                        bic = str(datos2.ji_get_area()) + " M2"
                        reference ="Pre Contrato:" + datos2.name
                lf = '\n'
                ibanqr = lf.join([service, version, code, function, bic, monto, reference])
                if len(ibanqr) > 331:
                    raise except_orm(_('Error'),
                                     _('IBAN QR code "%s" length %s exceeds 331 bytes') % (ibanqr, len(ibanqr)))
                self.qr_pagos = generate_qr_code(ibanqr)

    def get_text_amount_total(self):
        

        totall = 0
        for rec in self:
            list_comn = {}
            if rec.communication:
                if "-" in rec.communication:
                    list_comn = rec.communication.split('-')


                if len(list_comn) >= 2:
                    rec.numero_engache = str(rec.communication).split('-')[1]
                    # rec.numero_engache = rec.communication.split('-')
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
            datos=self.env['account.move'].search([('invoice_payment_ref','=',res.communication)]) #consulta
            dia = 0
            mensual = 0.0
            total = 0.0
            rtotal = 0.0
            contrato = 0.0
            messtr = 0.0
            mesesp = res.ji_mensuaidad

            res.ji_amount_fact = res.ji_total_factura - res.amount

            if res.categoria_producto:
                l = 'ok'
            else:
                res.categoria_producto = res.payment_transaction_id.sale_id.categoria_producto

            for fact in datos:
                total = fact.amount_total
                tipo = fact.invoice_payment_term_id
                anticipov = 0
                porc = 0

                for ant in tipo.line_ids:
                    if ant.value == "fixed" and ant.ji_type == "money_advance":
                        anticipov += ant.value_amount
                    if ant.value == "percent" and ant.ji_type == "money_advance":
                        porc += ant.value_amount


                por = 0
                if anticipov > 0:
                    por = anticipov
                elif porc > 0 :
                    por = total * (porc / 100)
                else:
                    por = 0
                anticipo = por

                # anticipo = round(total * fact.invoice_payment_term_id.ji_advance_payment / 100, 2)
                contrato = total - anticipo
                rtotal = round(fact.amount_residual, 2)

                for lin in fact.line_ids:
                    if lin.ji_number.find('A') != 0 and lin.debit >= 1 and lin.date_maturity:
                        dia = lin.date_maturity.day
                        mensual = lin.debit
                        break
            restante = res.ji_restante
            letra_m = ""
            ultimo_mes = 0.0
            total = 0
            if mensual > 0 and res.amount > 0:

                if restante > 0 and restante <= res.amount:

                    mes_abado = (res.amount - restante)/ mensual
                    ultimo_mes = res.amount - restante

                # elif restante == 0 and restante <= res.amount:
                #     restante = res.pagos_mensualidad
                #     res.ji_restante = restante
                #     mes_abado = (res.amount - mesesp) / mensual
                #     res.ji_mes_nuevo = res.amount - mesesp
                else:
                    restante = mensual
                    # res.ji_restante = restante
                    mes_abado = res.amount / mensual
                    ultimo_mes= res.amount - restante

                res.ji_mes_nuevo = ultimo_mes
                # messtr=str(round(mes_abado, 2)).split(".")[0]

                if int(str(round(mes_abado, 2)).split(".")[0]) > 0:
                    mesesp = mesesp + 1


            total = ultimo_mes

            ji_mesto = mesesp
            meses_t =0
            if ultimo_mes >= mensual:
                for l in range(res.ji_mensuaidad, ji_mesto):
                    meses_t += 1
                    total = total - mensual


            res.ji_mesto = ji_mesto + meses_t
            letra_m1 = ""

            if total > 0 and res.ji_mesto > res.ji_mensuaidad:
                letra_m = " y en Parcialidad el mes " + str(res.ji_mesto) +" con $ " + str(round(total,2))
            if res.ji_mesto > res.ji_mensuaidad:
                if res.ji_mesto -1 > res.ji_mensuaidad:
                    letra_m1 = "Meses pagados en su totalidad del " + str(res.ji_mensuaidad) + " al " + str(res.ji_mesto - 1)
                else:
                    letra_m1 = "Mes Pagado en su totalidad " + str(res.ji_mensuaidad)


            res.ji_mesnuevo_let = letra_m1 + letra_m
            res.dia_dato_pago = dia
            res.total_factura = total
            if res.ji_amount_fact >= 0:
                res.residual = round(res.ji_amount_fact, 3)
            else:
                res.residual = round(rtotal, 3)
            centavo_redisual = str(round(res.residual, 2)).split(".")[1]
            res.cent_residual = centavo_redisual if len(centavo_redisual) > 1 else centavo_redisual+'0'
                
            res.total_contrato = contrato
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
            mora = 0
            for trns in rec.payment_transaction_id:
                mora = trns.mora
            if mora > 0:
                rec.ji_moratorio = mora

            if rec.journal_id.name == "Anticipo":
                rec.x_studio_tipo_de_pago = "Anticipo"
            if rec.communication:
                com = rec.communication.split("-")
                rec.payment_reference = com[0]
                rec.payment_refer = com[0]
            else:
                rec.payment_refer = "Tranfer Interna"
                rec.communication = "Tranfer Interna"



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

    

