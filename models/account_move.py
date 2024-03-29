# -*- coding: utf-8 -*-
import datetime
import functools
import copy
import logging
_logger = logging.getLogger(__name__)
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError, except_orm

from collections import defaultdict
MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}
from odoo.tools import safe_eval
import dateutil.relativedelta as relativedelta
from werkzeug import urls
from num2words import num2words
import json
import qrcode
import base64
from io import BytesIO
from odoo.http import request


try:
    # We use a jinja2 sandboxed environment to render mako templates.
    # Note that the rendering does not cover all the mako syntax, in particular
    # arbitrary Python statements are not accepted, and not all expressions are
    # allowed: only "public" attributes (not starting with '_') of objects may
    # be accessed.
    # This is done on purpose: it prevents incidental or malicious execution of
    # Python code that may break the security of the server.
    from jinja2.sandbox import SandboxedEnvironment

    mako_template_env = SandboxedEnvironment(
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="${",
        variable_end_string="}",
        comment_start_string="<%doc>",
        comment_end_string="</%doc>",
        line_statement_prefix="%",
        line_comment_prefix="##",
        trim_blocks=True,  # do not output newline after blocks
        autoescape=True,  # XML/HTML automatic escaping
    )
    mako_template_env.globals.update({
        'str': str,
        'quote': urls.url_quote,
        'urlencode': urls.url_encode,
        'datetime': tools.wrap_module(datetime, []),
        'len': len,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'filter': filter,
        'reduce': functools.reduce,
        'map': map,
        'round': round,

        # dateutil.relativedelta is an old-style class and cannot be directly
        # instanciated wihtin a jinja2 expression, so a lambda "proxy" is
        # is needed, apparently.
        'relativedelta': lambda *a, **kw: relativedelta.relativedelta(*a, **kw),
    })
    mako_safe_template_env = copy.copy(mako_template_env)
    mako_safe_template_env.autoescape = False
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


def month_name(number):
    if number == 0:
        return _('No Date Selected')
    if number == 1:
        return _('January')
    elif number == 2:
        return _('February')
    elif number == 3:
        return _('March')
    elif number == 4:
        return _('April')
    elif number == 5:
        return _('May')
    elif number == 6:
        return _('June')
    elif number == 7:
        return _('July')
    elif number == 8:
        return _('August')
    elif number == 9:
        return _('September')
    elif number == 10:
        return _('October')
    elif number == 11:
        return _('November')
    elif number == 12:
        return _('December')

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
class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',
                                              domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                              readonly=True, states={'draft': [('readonly', False)]}, track_visibility='onchange')
    fecha_fact = fields.Date(string="Fecha de Factura")
    ji_partner_contract = fields.Many2one(comodel_name="res.partner", string="Commission Agent")
    ji_order_contract = fields.Many2one(comodel_name="sale.order", string="Order Contract")
    ji_is_moratorium = fields.Boolean(string="Moratorium", default=False)
    ji_json_numbers = fields.Text(string="Json Number", store=True, compute="_compute_ji_json_numbers")
    ji_json_sequences = fields.Text(string="Json Sequences", store=True, compute="_compute_ji_json_numbers")
    x_studio_contrato = fields.Char(string="Contrato", compute="contrato")
    x_studio_vendedor = fields.Many2one(comodel_name="hr.employee",store=True, related="partner_id.sale_order_ids.x_studio_vendedor", string="Vendedor")
    cliente_anterior = fields.Many2one(comodel_name="res.partner", string="Cliente anterior")
    fecha_entrega = fields.Datetime(string="Fecha de entrega")
    mes_entrega = fields.Char(string="Mes")
    last_payment_date = fields.Date(string="Ultima fecha de pago", compute="_compute_paymentlast")
    last_payment_anticipo = fields.Date(string="Ultima fecha de pago Anticipo", compute="state_product")
    last_payment_name = fields.Char(string="Recivo", compute="_compute_paymentlast")
    last_payment = fields.Float(string="Ultimo Pago", compute="_compute_paymentlast")
    motarorio_pay = fields.Monetary(string="Moratorio Pagados", compute="_compute_paymentlast")
    estado_producto = fields.Many2one('estados.g', string='Estado de Producto', compute="state_product")
    ji_documents = fields.Boolean(string="Revision de documentacion", compute="get_documents")
    ji_textalert = fields.Char(string="mjs")
    x_studio_manzana = fields.Many2one(string="Manzana", comodel_name="manzana.ji", store=True, related="invoice_line_ids.product_id.x_studio_manzana")
    x_studio_lote = fields.Many2one(string="Lote", comodel_name="lotes.ji", store=True, related="invoice_line_ids.product_id.x_studio_lote")
    x_studio_calle = fields.Many2one(string="Calle", comodel_name="calle.ji", store=True, related="invoice_line_ids.product_id.x_studio_calle")
    categoria_producto = fields.Many2one(string="Categoria de producto", comodel_name="product.category")
    codigo_prod = fields.Many2one(string="Codigo de producto", comodel_name="account.account")
    dia_dato_pago = fields.Integer(string="Pago dia de cada mes", compute="get_origin")
    dia_letra_pago = fields.Char(string="Pago dia Letra", compute="get_origin")
    mensaualidad_pago = fields.Float(string="pago mensual", compute="get_page_mensual")
    precio_unitario = fields.Float(string="Precio unitario",related="invoice_line_ids.product_id.list_price")
    anticipo_total = fields.Float(string="Totla anticipo", compute="get_anticipo")
    total_menos_anticipo = fields.Float(string="Total sin anticipo", compute="get_anticipo")
    mensualidades_atra = fields.Float(string="mensaulidades vencidad", compute="get_anticipo")
    

    qr_finiquito = fields.Binary("QR Code", compute='_generate_qr_code')

    def _generate_qr_code(self):
        service = "Fecha de expedición: " + str( fields.Date.context_today(self).strftime('%d-%m-%Y'))
        # Check if BIC exists: version 001 = BIC, 002 = no BIC
        version = 'Convenio INDIVI : 102799 - 102800'
        code = self.partner_id.name
        function = "Manzana " + self.x_studio_manzana.name + ", Lote " + self.x_studio_lote.name + ", Colonia " + self.categoria_producto.name + ", C.P. 22010, Tijuana, B.C."
        bic = str(self.ji_get_area()) + " M2"

        reference = "Contrato : " + self.name
        lf = '\n'
        ibanqr = lf.join([service, version, code, function, bic, reference])
        if len(ibanqr) > 331:
            raise except_orm(_('Error'),
                                        _('IBAN QR code "%s" length %s exceeds 331 bytes') % (ibanqr, len(ibanqr)))
        self.qr_finiquito = generate_qr_code(ibanqr)

    @api.depends("type","line_ids","name")
    def get_anticipo(self):
        sin_anticipo = 0
        mensua_ven = 0
        for res in self:
            if res.type == "out_invoice":
                venta=self.env['sale.order'].search([('name','=',self.invoice_origin)])
                res.anticipo_total = 0
                mensua_ven = res.saldo_pend - res.total_moratorium
                res.mensualidades_atra = mensua_ven
                res.total_menos_anticipo = venta.total_adeudo

                if res.invoice_line_ids:
                    for il in res.invoice_line_ids:
                        if il.product_id:
                            res.categoria_producto= il.product_id.categ_id
                        if il.account_id:
                            res.codigo_prod = il.account_id
            else:
                res.mensualidades_atra = 0
                res.anticipo_total = 0
                res.total_menos_anticipo = 0
                res.invoice_payment_ref = res.name

                if res.invoice_line_ids:
                    for il in res.invoice_line_ids:
                        if il.product_id:
                            res.categoria_producto= il.product_id.categ_id
                        if il.account_id:
                            res.codigo_prod = il.account_id

    @api.depends("line_ids")
    def get_page_mensual(self):
        for res in self:
            mensual = 0.0
            for lin in res.line_ids:
                if lin.ji_number.find('A') != 0 and lin.debit >= 1:
                    mensual = lin.debit
                    break

            res.mensaualidad_pago = mensual
    

    def action_conf(self):
        for res in self:
            res.button_draft()
            # res.invoice_payment_term_id = 385
            # res.action_post()
            res.button_cancel()
    def action_confirm(self):
        for res in self:
            res.action_post()
    def onchange_invoice_date(self):
        self._recompute_dynamic_lines(recompute_tax_base_amount=True)
    def action_invoice_register_payment(self):
        for res in self:
            flag = self.env['res.users'].has_group('deltatech_sale_payment.group_caja_pagos')
            if not flag:
                raise UserError(_("No tienes Permiso Para realizar el pago"))
            if not res.ji_documents and self.type == "out_invoice":
                raise UserError(_("Completar la Documentacion Faltante"))
            return self.env['account.payment'] \
                .with_context(active_ids=self.ids, active_model='account.move', active_id=self.id) \
                .action_register_payment()
    def get_origin(self):
        for res in self:
            # datos=self.env['account.move'].search([('invoice_payment_ref','=',res.payment_reference)]) #consulta
            dia = 0

            for lin in res.line_ids:
                if lin.ji_number.find('A') != 0 and lin.debit >= 1:
                    dia = lin.date_maturity.day
                    mensual = lin.debit
                    break
            res.dia_dato_pago = dia
            res.dia_letra_pago = num2words(dia, lang='es').upper()

    def noti_docs(self,mesaje,title):
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': (title),
                'message': mesaje,
                'type': 'warning',  # types: success,warning,danger,info
                'sticky': True,  # True/False will display for few seconds if false
            },
        }
        return notification
    def get_documents(self):
        for mov in self:
            cli = mov.partner_id
            ndoc= cli.count_doct
            aprov = False
            if ndoc >= 3:

                for doc in cli.attachment_ids:
                    if doc.aprobado:
                        aprov = doc.aprobado
                    else:
                        aprov = doc.aprobado
                        break

                if not aprov:
                    mov.ji_textalert = "Los ducumentos No se encuentran Aprobados, Verificar información"
                mov.ji_documents = aprov
            else:
                mov.ji_textalert = "Sin Documentación, Favor de Subir la documentacion requerida"
                mov.ji_documents = aprov
                # mov.noti_docs("", "")

    def change_payments(self):
        for res in self:
            pagos = self.env["account.payment"].search(
                [('communication', '=', res.invoice_payment_ref), ('x_studio_tipo_de_pago', '!=', 'Anticipo'),
                 ('state', '=', 'posted')], order='payment_date,id asc')
            for pa in pagos:
                pa.action_draft()
                pa.partner_id = res.partner_id
                pa.post()
            pagosa = self.env["account.payment"].search(
                [('communication', '=', res.invoice_payment_ref), ('x_studio_tipo_de_pago', '=', 'Anticipo'),
                 ('state', '=', 'posted')], order='id asc')
            if (len(pagosa) == 0):
                sale = self.env["sale.order"].search([('name', '=', res.invoice_payment_ref)])
                payment_ids = []
                for order in sale:
                    transactions = order.sudo().transaction_ids.filtered(lambda a: a.state == "done")
                    for item in transactions:
                        payment_ids.append(item.payment_id.id)
                pagosa = self.env["account.payment"].search([('id', 'in', payment_ids), ('state', '=', 'posted')],
                                                            order='payment_date asc')
            for pa in pagosa:
                pa.action_draft()
                pa.partner_id = res.partner_id
                pa.post()

    def printcontratoaction(self):
        for res in self:
            if not res.ji_documents and self.type == "out_invoice":
                raise UserError(_("Completar la Documentacion Faltante"))
            if not res.partner_id.street or not res.partner_id.city or not res.partner_id.street or not res.partner_id.state_id or not res.partner_id.zip or not res.partner_id.country_id:
                raise UserError(_("El cliente no cuenta con su dirección completa, favor de completar su dirección!"))
            return self.env.ref('jibaritolotes.action_report_sale_order_contract').report_action(self)
    def get_amount_advance_payment(self):
        if not self.invoice_payment_term_id.ji_advance_payment:
            return ""
        if not self.amount_total:
            return ""
        return '{:,.2f}'.format(self.invoice_payment_term_id.ji_advance_payment / 100 * self.amount_total)

    def get_text_amount_advance_payment(self):
        if "" == self.get_amount_advance_payment():
            return ""
        _amount = num2words((self.invoice_payment_term_id.ji_advance_payment / 100 * self.amount_total), lang='es').upper()
        _amount = _amount.split(" PUNTO ")[0]
        _centa_total = str(round((self.invoice_payment_term_id.ji_advance_payment / 100 * self.amount_total), 2)).split(".")[1]
        centavo = _centa_total  if len ( _centa_total) > 1 else  _centa_total +'0'
        _amount_text = "SON: " + (_amount or '') + " DÓLARES " + (centavo or '') + "/100 MONEDA DE LOS ESTADOS UNIDOS DE AMÉRICA"
        return _amount_text

    def get_amount_monthly(self):
        amount_monthly = 0.00
        for li in self:
            for line in li.line_ids:
                if line.ji_term_line_id.ji_type == 'monthly_payments':
                    amount_monthly = line.debit
                    break
        return amount_monthly

    def get_amount_monthly_separator(self):
        amount_string = '{:,.2f}'.format(self.get_amount_monthly())
        return amount_string
    def get_text_amount_monthly(self):
        _amount = num2words(self.get_amount_monthly(), lang='es').upper()
        _amount = _amount.split(" PUNTO ")[0]
        _centa_total = str(round(self.get_amount_monthly(), 2)).split(".")[1]
        centavo = _centa_total  if len ( _centa_total) > 1 else  _centa_total +'0'
        _amount_text = "SON: " + (_amount or '') + " DÓLARES " + (centavo or '') + "/100 MONEDA DE LOS ESTADOS UNIDOS DE AMÉRICA"
        return _amount_text


    def ji_render_template(self, template_txt):
        self.ensure_one()
        mako_env = mako_safe_template_env if self.env.context.get('safe') else mako_template_env
        template = mako_env.from_string(tools.ustr(template_txt))
        variables = {
            "object": self
        }
        render_result = template.render(variables)
        return render_result
    def get_amount_with_separators(self):
        # import locale
        # locale.setlocale(locale.LC_ALL, self.env.user.lang)
        # amount_string = locale.format_string("%d", self.amount_total, grouping=True)
        amount_string = '{:,.2f}'.format(self.total_menos_anticipo)
        return amount_string
        
    def get_amount_with_separators_total(self):
        # import locale
        # locale.setlocale(locale.LC_ALL, self.env.user.lang)
        # amount_string = locale.format_string("%d", self.amount_total, grouping=True)
        amount_string_total = '{:,.2f}'.format(self.amount_total)
        return amount_string_total

    def get_amount_total_text_total(self):    
        _amount = num2words(self.amount_total, lang='es').upper()
        _amount = _amount.split(" PUNTO ")[0]
        _centa_total = str(round(self.amount_total, 2)).split(".")[1]
        centavo = _centa_total  if len ( _centa_total) > 1 else  _centa_total +'0'
        _amount_text_total = "SON: " + (_amount or '') + " DÓLARES " + (centavo or '') + "/100 MONEDA DE LOS ESTADOS UNIDOS DE AMÉRICA"
        return _amount_text_total


    def get_amount_total_text(self):    
        _amount = num2words(self.total_menos_anticipo, lang='es').upper()
        _amount = _amount.split(" PUNTO ")[0]
        _centa_total = str(round(self.total_menos_anticipo, 2)).split(".")[1]
        centavo = _centa_total  if len ( _centa_total) > 1 else  _centa_total +'0'
        _amount_text = "SON: " + (_amount or '') + " DÓLARES " + (centavo or '') + "/100 MONEDA DE LOS ESTADOS UNIDOS DE AMÉRICA"
        return _amount_text

    def ji_day(self):
        _today = self.invoice_date
        return _today

    def ji_month_name(self):
        _today = self.invoice_date
        return month_name(_today.month)

    def get_last_payment_move(self):
        if self.last_payment_date:
            line_ids = self.invoice_ids[0].mapped('line_ids').sorted(lambda l: l.ji_sequence_payments, reverse=True)
            if line_ids.ids:
                return line_ids[0]
        return False

    def ji_get_last_date_payment_text(self):
        for move in self:
            if move.last_payment_date:
                _today = move.last_payment_date
                return "el día " + str(_today.day) + " de " + str(month_name(_today.month)) + " del " + str(_today.year)
        return ""
    def ji_get_last_date_text(self):
        for move in self:
            _today = fields.Date.context_today(self)
            for lin in move.line_ids:
                if( str(lin.date_maturity) > str(_today) and lin.debit > 0):
                    _today = lin.date_maturity

        return "el día " + str(_today.day) + " de " + str(month_name(_today.month)) + " del " + str(_today.year)

    def ji_get_name_product(self):
            dat = ""
            for line in self:
                dat = "MANZANA " + line.x_studio_manzana.name + " LOTE " + line.x_studio_lote.name
            # _name =
            # self.order_line.update_computes.name or ''
            # return _name.upper()
            return dat

    def ji_get_area(self):
        if not self.invoice_line_ids.ids:
            return ""
        dat = ""
        for line in self:
            dat = " METROS CUADRADOS, DE LA CALLE, " + line.x_studio_calle.name
        return f' {self.invoice_line_ids[0].quantity:.3f}'

    def ji_get_street(self):
        for line in self:
            ji_street = ""
            for stre in line.x_studio_calle:
                ji_street = line.x_studio_calle.name
            return ji_street.upper()

    def ji_get_number_payments(self):
        return self.payment_term_id.ji_number_quotation or ""

    def ji_get_number_payments_advance_now(self):
        return self.payment_term_id.get_number_payments_advance_now()

    def ji_get_amount_month_payment(self):
        percent = self.payment_term_id.get_percent_month_payments()
        return (percent / 100) * self.amount_total

    def ji_get_text_amount_month_payment(self):
        return num2words(round(self.ji_get_amount_month_payment()), lang='es')

    @api.depends("state")
    def state_product(self):
        for line in self:
            pagos = self.env["account.payment"].search([('payment_reference', '=', line.invoice_payment_ref),('x_studio_tipo_de_pago','=','Anticipo')], order='payment_date desc')
            last_pay = fields.Date.today()
            apar = line.amount_total - round(line.amount_total * 0.10,2)
            # raise UserError(_( str(line.amount_residual)+ " " +str(apar)))
            # 10000 <= 12056,18
            if line.state == "posted":
                # raise UserError(_(pagos))
                line.estado_producto = 12
                for pay in pagos:
                    last_pay = pay.payment_date
                    break
            elif line.state == "cancel":
                line.estado_producto = 22
            else:
                line.estado_producto = line.invoice_line_ids.product_id.estado_producto
            line.last_payment_anticipo = last_pay
            line._compute_ji_product_information_form()

    @api.depends("invoice_line_ids")
    def _compute_ji_product_information_form(self):
        for line in self:
            if line.state == "posted" and line.invoice_line_ids.product_id:
                if line.estado_producto:
                    line.invoice_line_ids.product_id.estado_producto = line.estado_producto





    def open_payments(self):
        flag = self.env['res.users'].has_group('jibaritolotes.group_ji_pagos')
        if not flag:
            raise UserError(_("No tienes Permiso Para ver el pagos"))
        self.ensure_one()
        invoice_payments_widget = json.loads(self.invoice_payments_widget)
        payment_ids = []
        for item in invoice_payments_widget["content"]:
            payment_ids.append(item["account_payment_id"])

        if self.type == "out_invoice":
             action_ref = "account.action_account_payments"
        else:
            action_ref = "account.action_account_payments_payable"
        [action] = self.env.ref(action_ref).read()
        action["context"] = dict(safe_eval(action.get("context")))
        notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('mejoras'),
                    'message':str(action["context"]),
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
        # return notification
        if len(payment_ids) > 1:
            action["domain"] = [("id", "in", payment_ids)]
        elif payment_ids:
            action["views"] = [(self.env.ref("account.view_account_payment_form").id, "form")]
            action["res_id"] = payment_ids[0]
        
        return action

    def _compute_paymentlast(self):
        for res in self:
            #pagos = self.env["account.payment"].search([('payment_reference', '=', res.invoice_payment_ref)])
            pagos = self.env["account.payment"].search([('communication', '=', res.invoice_payment_ref),('state', '=', 'posted')])
            date = fields.Date.today()
            name = ""
            pay = 0.0
            morap = 0.0
            i=0
            for lp in pagos:
                if i == 0:
                    date = lp["payment_date"]
                    name = lp["name"]
                    pay = lp["amount"]

                    i = i + 1
                morap = morap + lp["ji_moratorio"]
            res.last_payment_date = date
            res.last_payment_name = name
            res.last_payment = pay
            res.motarorio_pay = morap

    @api.depends("partner_id")
    def _compute_ji_contrato(self):
      for res in self:
        res.x_studio_contrato = res.partner_id.sale_order_ids.x_studio_contrato

    def regenerate_correlative(self):
        self.company_id.migrate_old_sequences(self)

    def get_contract_number(self):
        sale = False
        for move in self:
            sale = self.env["sale.order"].search([('name', '=', move.invoice_origin)])
        if sale:
            return sale.x_studio_contrato
        return False

    @api.depends("line_ids")
    def get_reporte_amoritizacion(self):
        for res in self:
            if not res.ji_documents and self.type == "out_invoice":
                raise UserError(_("Completar la Documentacion Faltante"))
            move = []
            account = []
            today = fields.Date.today()
            compaRecords=[]
            compani = res.company_id
            tov = res.amount_untaxed
            pagov = 1
            ofpa = 0
            lines = self.env["account.move.line"].search([('move_id.id', '=', res.id)], order='date_maturity asc')

            for lin in lines:
                if lin.debit > 0:
                    tov = tov - lin.debit
                    if lin.ji_number.find('A') != 0 and lin.debit >=1:
                        account.append({
                            "number": lin.ji_number.replace('/', ' de '),
                            "date_f": lin.date_maturity.strftime('%d-%m-%y'),
                            "debit": lin.debit,
                            "credit": lin.credit,
                            "total" : tov
                        })
                        pagov = pagov + 1
                        ofpa = pagov

            move.append({
                "name": res.name,
                "cliente": res.partner_id.name,
                "date": res.invoice_date,
                "company": res.invoice_date
            })

            compaRecords.append({
                'name': compani.name,
                'zip': compani.zip,
                'street': compani.street,
                'street2': compani.street2,
                'city': compani.city,
                'state_id': compani.state_id.name,
                'country_id': compani.country_id.name,
                'phone': compani.phone,
                'id': compani.id,
                'website': compani.website,
            })

            data = {
                'client':res.partner_id.name,
                'contrato': res.name,
                'produc':"Manzana " + res.x_studio_manzana.name + ", Lote " + res.x_studio_lote.name + ", Calle" + res.x_studio_calle.name,
                'date': str(today.day) + " de " + str(month_name(today.month)) + " del " + str(today.year),
                'move_id': move,
                'ofpay': ofpa,
                'acco': account,
                'comapany': compaRecords,
            }
            return self.env.ref('jibaritolotes.report_amortizacion').report_action(self, data=data)
            # raise UserError(_(data))


    def get_reporte_amoritizacionv2(self):
        for res in self:
            move = []
            account = []
            today = fields.Date.today()
            anticipo = []
            name = res.name

            pagos = self.env["account.payment"].search(
                [('communication', '=', res.invoice_payment_ref), ('x_studio_tipo_de_pago', '!=', 'Anticipo'),
                 ('state', '=', 'posted')], order='payment_date,id asc')
            lines = self.env["account.move.line"].search([('move_id.id', '=', res.id)], order='date_maturity asc')
            pagosa = self.env["account.payment"].search(
                [('communication', '=', res.invoice_payment_ref), ('x_studio_tipo_de_pago', '=', 'Anticipo'),
                 ('state', '=', 'posted')], order='id asc')
            if (len(pagosa) == 0):
                sale = self.env["sale.order"].search([('name', '=', res.invoice_payment_ref)])
                payment_ids = []
                for order in sale:
                    transactions = order.sudo().transaction_ids.filtered(lambda a: a.state == "done")
                    for item in transactions:
                        payment_ids.append(item.payment_id.id)
                pagosa = self.env["account.payment"].search([('id', 'in', payment_ids), ('state', '=', 'posted')],
                                                            order='payment_date asc')
            tipo = res.invoice_payment_term_id
            anticipov = 0
            porc = 0
            for ant in tipo.line_ids:
                if ant.value == "fixed" and ant.ji_type == "money_advance":
                    anticipov += ant.value_amount
                if ant.value == "percent" and ant.ji_type == "money_advance":
                    porc += ant.value_amount

            compaRecords = []
            compani = res.company_id
            tov = res.amount_untaxed
            por = 0
            if anticipov > 0:
                por = anticipov
            else:
                por = res.amount_untaxed * (porc/100)
            anticp = por


            anticipo.append({
                "number": "Anticipo 0",
                "date_f": "",
                "mora": 0,
                "impo": 0,
                "total": anticp,
                "real": 0,
            })

            conan = 1
            co_pay = 1

            for pay in pagosa:
                mora = pay.ji_moratorio
                impo = pay.amount
                fecpag = pay.payment_date.strftime('%d-%m-%y')
                pimp = pay.ji_moratorio + pay.amount
                anticp = anticp - impo
                tov = tov - impo

                anticipo.append({
                    "number": "Anticipo " + str(conan),
                    "date_f": fecpag,
                    "mora": mora,
                    "impo": impo,
                    "total": anticp,
                    "real": pimp,
                })
                conan = conan + 1
                co_pay = co_pay + 1
            pagov = 1
            ofpa = ""
            account.append({
                "number": 0,
                "date_f": "",
                "date_p": "",
                "mora": 0,
                "sald": 0,
                "impo": 0,
                "debit": 0,
                "credit": 0,
                "total": tov,
                "real": 0,
                "prox_sal": 0,
            })

            co_pay = len(pagos)
            sal_acom = 0.0
            co = 0
            cont = 0
            cont2 = 0
            sald_ant2 = 0
            fecpag = ""
            sald_ant = 0
            solo_pagos = 0
            for lin in lines:

                mora = 0
                mora_prox = 0.0
                prox_sal = 0.0
                if sald_ant > 0:
                    impo = 0 + sald_ant
                    sald_ant2 = 0

                else:
                    impo = 0
                    solo_pagos = 0
                    sald_ant2 = sald_ant
                pimp = 0.0
                if lin.ji_number.find('A') != 0 and lin.debit >= 1:
                    co2 = 0
                    fechan=""
                    if sald_ant < lin.debit:
                        co3 = 0
                        for pay in pagos:#103
                            if co_pay > 0 and impo < lin.debit and cont2 == cont and co == co2:
                                fecpag = pay.payment_date.strftime('%d-%m-%y')

                                impo = impo + pay.amount
                                solo_pagos = solo_pagos + pay.amount
                                mora = mora + pay.ji_moratorio
                                pimp = impo + mora - sald_ant + sald_ant2
                                co_pay = co_pay - 1
                                co3 = co3 + 1
                                if impo >= lin.debit:
                                    co = co + co3
                                    cont2 = cont2 + 1
                                    co3 = 0
                            elif co_pay > 0 and impo >= lin.debit and co == cont and co == co2:
                                fecpag = pay.payment_date.strftime('%d-%m-%y')
                                impo = impo + pay.amount
                                solo_pagos = solo_pagos + pay.amount
                                mora = mora + pay.ji_moratorio
                                pimp = impo + mora - sald_ant + sald_ant2
                                co_pay = co_pay - 1
                                if impo >= lin.debit:
                                    co = co + 1
                                    cont2 = cont2 + 1
                                    co3 = 0
                            if co > co2:
                                co2 = co2 + 1
                        cont = cont + 1
                        if sald_ant > 0:
                            prox_sal = lin.debit - mora
                        else:
                            prox_sal = lin.debit - mora - sald_ant2

                    else:
                        prox_sal = 0

                    prox_pay = json.loads(res.moratex)
                    # raise UserError(_(prox_pay))
                    mora_prox = 0.0
                    for px_py in prox_pay:
                        if px_py["fecha"] == str(lin.date_maturity):
                            unit_p = float(px_py["unimora"])
                            mes_p = float(px_py["mes"])
                            mora_prox = unit_p * mes_p

                            # return notification
                    isigual = ""

                    if impo == lin.debit:
                        isigual = "Si"
                        sald_ant = 0
                        impo = lin.debit
                        sald_ant2 = 0
                        prox_sal = 0
                        mora_prox = 0
                    elif impo < lin.debit:
                        sald_ant = 0
                        isigual = "sald_ant = " + str(sald_ant)
                        prox_sal = prox_sal - impo


                    else:
                        sald_ant = round(impo - lin.debit ,2)
                        impo = lin.debit
                        prox_sal = 0
                        mora_prox = 0
                        isigual = ">sald_ant = " + str(sald_ant)
                    prox_sal = prox_sal + round(mora_prox, 2)
                    tov = tov - (pimp - mora) + round(mora_prox, 2)
                    if (impo == 0):
                        fecpag = ""
                        sald_ant = 0
                    # mora + round(mora_prox, 2)
                    if mora_prox > 0:
                        mora = mora_prox - mora
                    elif mora <= 0:
                        mora = mora_prox



                    account.append({
                        "number": pagov,
                        "date_f": lin.date_maturity.strftime('%d-%m-%y'),
                        "date_p": fecpag,
                        "mora": mora,
                        "sald": sald_ant,
                        "impo": impo,
                        "debit": lin.debit,
                        "credit": lin.credit,
                        "total": tov,
                        "real": pimp,
                        "prox_sal": prox_sal,
                    })

                    ofpa = " de " + str(pagov)
                    pagov = pagov + 1
            prod = "Manzana " + res.x_studio_manzana.name + ", Lote " + res.x_studio_lote.name
            if res.x_studio_calle:
                prod += ", Calle " + res.x_studio_calle.name
            else:
                raise UserError(_("Error no se encontro la calle"))

            data = {
                'client': res.partner_id.name,
                'contrato': res.name,
                'produc': prod,
                'date': str(today.day) + " de " + str(month_name(today.month)) + " del " + str(today.year),

                'move_id': move,
                'ofpay': ofpa,
                'acco': account,
                'anti': anticipo,
                'comapany': compaRecords,
            }
            return self.env.ref('jibaritolotes.report_amortizacionv2').report_action(self, data=data)

    def get_reporte_amoritizacionv2_pdf(self,acount):
        for res in acount:
            move = []
            account = []
            today = fields.Date.today()
            anticipo = []
            name = res.name

            pagos = self.env["account.payment"].search(
                [('communication', '=', res.invoice_payment_ref), ('x_studio_tipo_de_pago', '!=', 'Anticipo'),
                 ('state', '=', 'posted')], order='payment_date,id asc')
            lines = self.env["account.move.line"].search([('move_id.id', '=', res.id)], order='date_maturity asc')
            pagosa = self.env["account.payment"].search(
                [('communication', '=', res.invoice_payment_ref), ('x_studio_tipo_de_pago', '=', 'Anticipo'),
                 ('state', '=', 'posted')], order='id asc')
            if (len(pagosa) == 0):
                sale = self.env["sale.order"].search([('name', '=', res.invoice_payment_ref)])
                payment_ids = []
                for order in sale:
                    transactions = order.sudo().transaction_ids.filtered(lambda a: a.state == "done")
                    for item in transactions:
                        payment_ids.append(item.payment_id.id)
                pagosa = self.env["account.payment"].search([('id', 'in', payment_ids), ('state', '=', 'posted')],
                                                            order='payment_date asc')
            tipo = res.invoice_payment_term_id
            anticipov = 0
            porc = 0
            for ant in tipo.line_ids:
                if ant.value == "fixed" and ant.ji_type == "money_advance":
                    anticipov += ant.value_amount
                if ant.value == "percent" and ant.ji_type == "money_advance":
                    porc += ant.value_amount

            compaRecords = []
            compani = res.company_id
            tov = res.amount_untaxed
            por = 0
            if anticipov > 0:
                por = anticipov
            else:
                por = res.amount_untaxed * (porc / 100)
            anticp = por

            anticipo.append({
                "number": "Anticipo 0",
                "date_f": "",
                "mora": 0,
                "impo": 0,
                "total": anticp,
                "real": 0,
            })

            conan = 1
            co_pay = 1

            for pay in pagosa:
                mora = pay.ji_moratorio
                impo = pay.amount
                fecpag = pay.payment_date.strftime('%d-%m-%y')
                pimp = pay.ji_moratorio + pay.amount
                anticp = anticp - impo
                tov = tov - impo

                anticipo.append({
                    "number": "Anticipo " + str(conan),
                    "date_f": fecpag,
                    "mora": mora,
                    "impo": impo,
                    "total": anticp,
                    "real": pimp,
                })
                conan = conan + 1
                co_pay = co_pay + 1
            pagov = 1
            ofpa = ""
            account.append({
                "number": 0,
                "date_f": "",
                "date_p": "",
                "mora": 0,
                "sald": 0,
                "impo": 0,
                "debit": 0,
                "credit": 0,
                "total": tov,
                "real": 0,
                "prox_sal": 0,
            })

            co_pay = len(pagos)
            sal_acom = 0.0
            co = 0
            cont = 0
            cont2 = 0
            sald_ant2 = 0
            fecpag = ""
            sald_ant = 0
            solo_pagos = 0
            for lin in lines:

                mora = 0
                mora_prox = 0.0
                prox_sal = 0.0
                if sald_ant > 0:
                    impo = 0 + sald_ant
                    sald_ant2 = 0

                else:
                    impo = 0
                    solo_pagos = 0
                    sald_ant2 = sald_ant
                pimp = 0.0
                if lin.ji_number.find('A') != 0 and lin.debit >= 1:
                    co2 = 0
                    fechan = ""
                    if sald_ant < lin.debit:
                        co3 = 0
                        for pay in pagos:  # 103
                            if co_pay > 0 and impo < lin.debit and cont2 == cont and co == co2:
                                fecpag = pay.payment_date.strftime('%d-%m-%y')

                                impo = impo + pay.amount
                                solo_pagos = solo_pagos + pay.amount
                                mora = mora + pay.ji_moratorio
                                pimp = impo + mora - sald_ant + sald_ant2
                                co_pay = co_pay - 1
                                co3 = co3 + 1
                                if impo >= lin.debit:
                                    co = co + co3
                                    cont2 = cont2 + 1
                                    co3 = 0
                            elif co_pay > 0 and impo >= lin.debit and co == cont and co == co2:
                                fecpag = pay.payment_date.strftime('%d-%m-%y')
                                impo = impo + pay.amount
                                solo_pagos = solo_pagos + pay.amount
                                mora = mora + pay.ji_moratorio
                                pimp = impo + mora - sald_ant + sald_ant2
                                co_pay = co_pay - 1
                                if impo >= lin.debit:
                                    co = co + 1
                                    cont2 = cont2 + 1
                                    co3 = 0
                            if co > co2:
                                co2 = co2 + 1
                        cont = cont + 1
                        if sald_ant > 0:
                            prox_sal = lin.debit - mora
                        else:
                            prox_sal = lin.debit - mora - sald_ant2

                    else:
                        prox_sal = 0

                    prox_pay = json.loads(res.action_moratorio_json())
                    # raise UserError(_(prox_pay))
                    mora_prox = 0.0
                    for px_py in prox_pay:
                        if px_py["fecha"] == str(lin.date_maturity):
                            unit_p = float(px_py["unimora"])
                            mes_p = float(px_py["mes"])
                            mora_prox = unit_p * mes_p

                            # return notification
                    isigual = ""

                    if impo == lin.debit:
                        isigual = "Si"
                        sald_ant = 0
                        impo = lin.debit
                        sald_ant2 = 0
                        prox_sal = 0
                        mora_prox = 0
                    elif impo < lin.debit:
                        sald_ant = 0
                        isigual = "sald_ant = " + str(sald_ant)
                        prox_sal = prox_sal - impo


                    else:
                        sald_ant = round(impo - lin.debit, 2)
                        impo = lin.debit
                        prox_sal = 0
                        mora_prox = 0
                        isigual = ">sald_ant = " + str(sald_ant)
                    prox_sal = prox_sal + round(mora_prox, 2)
                    tov = tov - (pimp - mora) + round(mora_prox, 2)
                    if (impo == 0):
                        fecpag = ""
                        sald_ant = 0
                    # mora + round(mora_prox, 2)
                    if mora < 0:
                        mora = mora_prox * -1

                    account.append({
                        "number": pagov,
                        "date_f": lin.date_maturity.strftime('%d-%m-%y'),
                        "date_p": fecpag,
                        "mora": mora,
                        "sald": sald_ant,
                        "impo": impo,
                        "debit": lin.debit,
                        "credit": lin.credit,
                        "total": tov,
                        "real": pimp,
                        "prox_sal": prox_sal,
                    })

                    ofpa = " de " + str(pagov)
                    pagov = pagov + 1

            data = {
                'client': res.partner_id.name,
                'contrato': res.name,
                'produc': "Manzana " + res.x_studio_manzana.name + ", Lote " + res.x_studio_lote.name + ", Calle " + res.x_studio_calle.name,
                'date': str(today.day) + " de " + str(month_name(today.month)) + " del " + str(today.year),

                'move_id': move,
                'ofpay': ofpa,
                'acco': account,
                'anti': anticipo,
                'comapany': compaRecords,
            }
            return self.env.ref('jibaritolotes.report_amortizacionv2_pdf').render_qweb_pdf(self, data=data)

    @api.model
    def update_computes(self):
        for move in self.search([('id', '=', 19154)]):
            pass
            # move._compute_ji_json_numbers()
            # move.line_ids._compute_ji_sequence_payments()
            # move.line_ids._compute_ji_number()
            # move.line_ids._compute_ji_name()
        pass


    @api.depends("line_ids", "invoice_payment_term_id")
    def _compute_ji_json_numbers(self):
        for move in self:
            jsonobs = {}
            json_numbers = {}
            count_monthly = 1
            count_advance = 1
            count_payment = 3
            for line in move.line_ids:
                sequence = ""
                if line.ji_term_line_id.ji_type == 'money_advance':
                    sequence = "A" + str(count_advance)
                    count_advance += 1
                if line.ji_term_line_id.ji_type == 'monthly_payments':
                    sequence = str(count_monthly) + "/" + str(line.ji_term_line_id.payment_id.ji_numbers_monthly)
                    count_monthly += 1
                jsonobs[str(line.id)] = sequence
                # SET Correlative
                if not line.ji_term_line_id.id:
                    json_numbers[str(line.id)] = -1
                if line.ji_term_line_id.ji_type == 'money_advance':
                    json_numbers[str(line.id)] = 2
                if line.ji_term_line_id.ji_type == 'monthly_payments':
                    json_numbers[str(line.id)] = count_payment
                    count_payment += 1;
            move.ji_json_sequences = json.dumps(json_numbers)
            move.ji_json_numbers = json.dumps(jsonobs)

    def _recompute_payment_terms_lines(self):
        ''' Compute the dynamic payment term lines of the journal entry.'''
        if not self.company_id.ji_apply_developments:
            return super(AccountMove, self)._recompute_payment_terms_lines()
        self.ensure_one()
        in_draft_mode = self != self._origin
        today = fields.Date.context_today(self)
        self = self.with_context(force_company=self.journal_id.company_id.id)

        def _get_payment_terms_computation_date(self):
            ''' Get the date from invoice that will be used to compute the payment terms.
            :param self:    The current account.move record.
            :return:        A datetime.date object.
            '''
            if self.invoice_payment_term_id:
                return self.invoice_date or today
            else:
                return self.invoice_date_due or self.invoice_date or today

        def _get_payment_terms_account(self, payment_terms_lines):
            ''' Get the account from invoice that will be set as receivable / payable account.
            :param self:                    The current account.move record.
            :param payment_terms_lines:     The current payment terms lines.
            :return:                        An account.account record.
            '''
            if payment_terms_lines:
                # Retrieve account from previous payment terms lines in order to allow the user to set a custom one.
                return payment_terms_lines[0].account_id
            elif self.partner_id:
                # Retrieve account from partner.
                if self.is_sale_document(include_receipts=True):
                    return self.partner_id.property_account_receivable_id
                else:
                    return self.partner_id.property_account_payable_id
            else:
                # Search new account.
                domain = [
                    ('company_id', '=', self.company_id.id),
                    ('internal_type', '=',
                     'receivable' if self.type in ('out_invoice', 'out_refund', 'out_receipt') else 'payable'),
                ]
                return self.env['account.account'].search(domain, limit=1)

        def _compute_payment_terms(self, date, total_balance, total_amount_currency):
            ''' Compute the payment terms.
            :param self:                    The current account.move record.
            :param date:                    The date computed by '_get_payment_terms_computation_date'.
            :param total_balance:           The invoice's total in company's currency.
            :param total_amount_currency:   The invoice's total in invoice's currency.
            :return:                        A list <to_pay_company_currency, to_pay_invoice_currency, due_date>.
            '''
            if self.invoice_payment_term_id:
                to_compute = self.invoice_payment_term_id.compute(total_balance, date_ref=date,
                                                                  currency=self.company_id.currency_id)
                if self.currency_id != self.company_id.currency_id:
                    # Multi-currencies.
                    to_compute_currency = self.invoice_payment_term_id.compute(total_amount_currency, date_ref=date,
                                                                               currency=self.currency_id)
                    return [(b[0], b[1], ac[1], b[2]) for b, ac in zip(to_compute, to_compute_currency)]
                else:
                    # Single-currency.
                    return [(b[0], b[1], 0.0, b[2]) for b in to_compute]
            else:
                return [(fields.Date.to_string(date), total_balance, total_amount_currency, False)]

        def _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute):
            ''' Process the result of the '_compute_payment_terms' method and creates/updates corresponding invoice lines.
            :param self:                    The current account.move record.
            :param existing_terms_lines:    The current payment terms lines.
            :param account:                 The account.account record returned by '_get_payment_terms_account'.
            :param to_compute:              The list returned by '_compute_payment_terms'.
            '''
            # As we try to update existing lines, sort them by due date.
            existing_terms_lines = existing_terms_lines.sorted(lambda line: line.date_maturity or today)
            existing_terms_lines_index = 0

            # Recompute amls: update existing line or create new one for each payment term.
            new_terms_lines = self.env['account.move.line']
            for date_maturity, balance, amount_currency, term_line_id in to_compute:
                currency = self.journal_id.company_id.currency_id
                if currency and currency.is_zero(balance) and len(to_compute) > 1:
                    continue

                if existing_terms_lines_index < len(existing_terms_lines):
                    # Update existing line.
                    candidate = existing_terms_lines[existing_terms_lines_index]
                    existing_terms_lines_index += 1
                    candidate.update({
                        'date_maturity': date_maturity,
                        'amount_currency': -amount_currency,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'ji_term_line_id': term_line_id,
                    })
                else:
                    # Create new line.
                    create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
                        'account.move.line'].create
                    candidate = create_method({
                        'name': self.invoice_payment_ref or '',
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'quantity': 1.0,
                        'amount_currency': -amount_currency,
                        'date_maturity': date_maturity,
                        'move_id': self.id,
                        'currency_id': self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
                        'account_id': account.id,
                        'partner_id': self.commercial_partner_id.id,
                        'exclude_from_invoice_tab': True,
                        'ji_term_line_id': term_line_id,
                    })
                new_terms_lines += candidate
                # if in_draft_mode:
                candidate._onchange_amount_currency()
                candidate._onchange_balance()
            return new_terms_lines

        existing_terms_lines = self.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        others_lines = self.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
        company_currency_id = (self.company_id or self.env.company).currency_id
        total_balance = sum(others_lines.mapped(lambda l: company_currency_id.round(l.balance)))
        total_amount_currency = sum(others_lines.mapped('amount_currency'))

        if not others_lines:
            self.line_ids -= existing_terms_lines
            return

        computation_date = _get_payment_terms_computation_date(self)
        account = _get_payment_terms_account(self, existing_terms_lines)
        to_compute = _compute_payment_terms(self, computation_date, total_balance, total_amount_currency)
        new_terms_lines = _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute)

        # Remove old terms lines that are no longer needed.
        self.line_ids -= existing_terms_lines - new_terms_lines

        if new_terms_lines:
            self.invoice_payment_ref = new_terms_lines[-1].name or ''
            self.invoice_date_due = new_terms_lines[-1].date_maturity

    def recompute_payment_terms_line(self):
        ''' Compute the dynamic payment term lines of the journal entry.'''
        if not self.company_id.ji_apply_developments:
            return super(AccountMove, self)._recompute_payment_terms_lines()
        self.ensure_one()
        in_draft_mode = self != self._origin
        today = fields.Date.context_today(self)
        self = self.with_context(force_company=self.journal_id.company_id.id)

        def _get_payment_terms_computation_date(self):
            ''' Get the date from invoice that will be used to compute the payment terms.
            :param self:    The current account.move record.
            :return:        A datetime.date object.
            '''
            if self.invoice_payment_term_id:
                return self.invoice_date or today
            else:
                return self.invoice_date_due or self.invoice_date or today

        def _get_payment_terms_account(self, payment_terms_lines):
            ''' Get the account from invoice that will be set as receivable / payable account.
            :param self:                    The current account.move record.
            :param payment_terms_lines:     The current payment terms lines.
            :return:                        An account.account record.
            '''
            if payment_terms_lines:
                # Retrieve account from previous payment terms lines in order to allow the user to set a custom one.
                return payment_terms_lines[0].account_id
            elif self.partner_id:
                # Retrieve account from partner.
                if self.is_sale_document(include_receipts=True):
                    return self.partner_id.property_account_receivable_id
                else:
                    return self.partner_id.property_account_payable_id
            else:
                # Search new account.
                domain = [
                    ('company_id', '=', self.company_id.id),
                    ('internal_type', '=',
                     'receivable' if self.type in ('out_invoice', 'out_refund', 'out_receipt') else 'payable'),
                ]
                return self.env['account.account'].search(domain, limit=1)

        def _compute_payment_terms(self, date, total_balance, total_amount_currency):
            ''' Compute the payment terms.
            :param self:                    The current account.move record.
            :param date:                    The date computed by '_get_payment_terms_computation_date'.
            :param total_balance:           The invoice's total in company's currency.
            :param total_amount_currency:   The invoice's total in invoice's currency.
            :return:                        A list <to_pay_company_currency, to_pay_invoice_currency, due_date>.
            '''
            if self.invoice_payment_term_id:
                to_compute = self.invoice_payment_term_id.compute(total_balance, date_ref=date,
                                                                  currency=self.company_id.currency_id)
                if self.currency_id != self.company_id.currency_id:
                    # Multi-currencies.
                    to_compute_currency = self.invoice_payment_term_id.compute(total_amount_currency, date_ref=date,
                                                                               currency=self.currency_id)
                    return [(b[0], b[1], ac[1], b[2]) for b, ac in zip(to_compute, to_compute_currency)]
                else:
                    # Single-currency.
                    return [(b[0], b[1], 0.0, b[2]) for b in to_compute]
            else:
                return [(fields.Date.to_string(date), total_balance, total_amount_currency, False)]

        def _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute):
            ''' Process the result of the '_compute_payment_terms' method and creates/updates corresponding invoice lines.
            :param self:                    The current account.move record.
            :param existing_terms_lines:    The current payment terms lines.
            :param account:                 The account.account record returned by '_get_payment_terms_account'.
            :param to_compute:              The list returned by '_compute_payment_terms'.
            '''
            # As we try to update existing lines, sort them by due date.
            existing_terms_lines = existing_terms_lines.sorted(lambda line: line.date_maturity or today)
            existing_terms_lines_index = 0

            # Recompute amls: update existing line or create new one for each payment term.
            new_terms_lines = self.env['account.move.line']
            for date_maturity, balance, amount_currency, term_line_id in to_compute:
                currency = self.journal_id.company_id.currency_id
                if currency and currency.is_zero(balance) and len(to_compute) > 1:
                    continue

                if existing_terms_lines_index < len(existing_terms_lines):
                    # Update existing line.
                    candidate = existing_terms_lines[existing_terms_lines_index]
                    existing_terms_lines_index += 1
                    candidate.update({
                        'date_maturity': date_maturity,
                        'amount_currency': -amount_currency,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'ji_term_line_id': term_line_id,
                    })
                else:
                    # Create new line.
                    create_method = in_draft_mode and self.env['account.move.line'].new or self.env[
                        'account.move.line'].create
                    candidate = create_method({
                        'name': self.invoice_payment_ref or '',
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'quantity': 1.0,
                        'amount_currency': -amount_currency,
                        'date_maturity': date_maturity,
                        'move_id': self.id,
                        'currency_id': self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
                        'account_id': account.id,
                        'partner_id': self.commercial_partner_id.id,
                        'exclude_from_invoice_tab': True,
                        'ji_term_line_id': term_line_id,
                    })
                new_terms_lines += candidate
                if in_draft_mode:
                    candidate._onchange_amount_currency()
                    candidate._onchange_balance()
            return new_terms_lines

        existing_terms_lines = self.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        others_lines = self.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
        company_currency_id = (self.company_id or self.env.company).currency_id
        total_balance = sum(others_lines.mapped(lambda l: company_currency_id.round(l.balance)))
        total_amount_currency = sum(others_lines.mapped('amount_currency'))

        if not others_lines:
            self.line_ids -= existing_terms_lines
            return

        computation_date = _get_payment_terms_computation_date(self)
        account = _get_payment_terms_account(self, existing_terms_lines)
        to_compute = _compute_payment_terms(self, computation_date, total_balance, total_amount_currency)
        new_terms_lines = _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute)

        # Remove old terms lines that are no longer needed.
        self.line_ids -= existing_terms_lines - new_terms_lines

        if new_terms_lines:
            self.invoice_payment_ref = new_terms_lines[-1].name or ''
            self.invoice_date_due = new_terms_lines[-1].date_maturity



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    ji_number = fields.Char(string="Correlative", store=True, compute="_compute_ji_number")

    ji_name = fields.Char(string="Name", store=True, compute="_compute_ji_name")

    jicategoria = fields.Char(string="Categoria de Producto", compute="categoria_venta")
    ji_categoria = fields.Char(string="Categoria de Producto")

    ji_term_line_id = fields.Many2one(comodel_name="account.payment.term.line", string="Payment Term Line Id")

    ji_sequence_payments = fields.Integer(string="Order Payments", store=True, compute="_compute_ji_sequence_payments")

    @api.depends("move_id", "ji_term_line_id")
    def _compute_ji_sequence_payments(self):
        for line in self:
            json_numbers = json.loads(line.move_id.ji_json_sequences)
            line.ji_sequence_payments = json_numbers.get(str(line.id), 0)

    @api.depends("ji_number", "move_id")
    def _compute_ji_name(self):
        for line in self:
            line.ji_name = "{name}-{correlative}".format(name=line.move_id.name, correlative=line.ji_number)

    @api.depends("move_id", "ji_term_line_id")
    def _compute_ji_number(self):
        for line in self:
            json_numbers = json.loads(line.move_id.ji_json_numbers)
            line.ji_number = json_numbers.get(str(line.id), "")

    @api.model
    @api.depends("ref","move_id")
    def categoria_venta(self):
        for line in self:
            catego = ""

            if line.move_id:
                for fac in line.move_id:
                    for lin in fac.invoice_line_ids:
                        if lin.product_id:
                            for cat in lin.product_id.categ_id:
                                catego = cat.name


            if line.ref and catego == "":
                ref = line.ref.split("-")
                datos = self.env['account.move'].search([('invoice_payment_ref', '=', ref[0])])
                for fac in datos:
                    for lin in fac.invoice_line_ids:
                        if lin.product_id:
                            for cat in lin.product_id.categ_id:
                                catego = cat.name

                if catego == "":
                    datos = self.env['sale.order'].search([('reference', '=', ref[0])])
                    for fac in datos:
                        for lin in fac.order_line:
                            if lin.product_id:
                                for cat in lin.product_id.categ_id:
                                    catego = cat.name
            line.ji_categoria = catego
            line.jicategoria = catego

   



class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.payment"
    x_studio_contrato = fields.Char(string="Contrato", compute="compute_ji_contrato")
    x_studio_tipo_de_pago = fields.Selection(string="Tipo de Pago", default = "Intererses Moratorios + Mensualidades",
        selection=[("Anticipo", "Anticipo"), ("Cobranza Mensualidades", "Cobranza Mensualidades"),
                   ("Intererses Moratorios + Mensualidades","Intererses Moratorios + Mensualidades")])
    ji_moratorio = fields.Monetary(string="Total Moratorios")
    ji_restante = fields.Float(string="Saldo restante de mes")
    ji_mensuaidad = fields.Integer(string="Mes Pagado")
    ji_moratorio_total = fields.Float(string="Total Moratorios in invoice")
    ji_total_factura = fields.Float(string="Total Factura")
    ji_moratorio_date = fields.Date(string="Fecha Moratorio Vencido")


    @api.depends("partner_id", "journal_id", "state")
    def compute_ji_contrato(self):
        for res in self:
            contrato = res.communication
            if res.journal_id.name == "Anticipo":
                res.x_studio_tipo_de_pago = "Anticipo"
            else:
                datos = self.env['account.move'].search([('invoice_payment_ref', '=', res.communication)])
                for fact in datos:
                    contrato = fact.name
            res.x_studio_contrato = contrato

    @api.model
    def default_get(self, default_fields):
        rec = super(AccountFollowupReport, self).default_get(default_fields)
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec

        invoices = self.env['account.move'].browse(active_ids).filtered(
            lambda move: move.is_invoice(include_receipts=True))

        # Check all invoices are open
        if not invoices or any(invoice.state != 'posted' for invoice in invoices):
            raise UserError(_("You can only register payments for open invoices"))
        # Check if, in batch payments, there are not negative invoices and positive invoices
        dtype = invoices[0].type
        for inv in invoices[1:]:
            if inv.type != dtype:
                if ((dtype == 'in_refund' and inv.type == 'in_invoice') or
                        (dtype == 'in_invoice' and inv.type == 'in_refund')):
                    raise UserError(
                        _("You cannot register payments for vendor bills and supplier refunds at the same time."))
                if ((dtype == 'out_refund' and inv.type == 'out_invoice') or
                        (dtype == 'out_invoice' and inv.type == 'out_refund')):
                    raise UserError(
                        _("You cannot register payments for customer invoices and credit notes at the same time."))

        amount = self._compute_payment_amount(invoices, invoices[0].currency_id, invoices[0].journal_id,
                                              rec.get('payment_date') or fields.Date.today())
        rec.update({
            'currency_id': invoices[0].currency_id.id,
            'journal_id': 8,
            'ji_restante': invoices[0].restante,
            'ji_mensuaidad': invoices[0].ji_plazo_actual + 1,
            'ji_moratorio_total': invoices[0].total_moratorium,
            'amount': amount,
            'ji_total_factura': amount,
            'payment_type': 'inbound' if amount > 0 else 'outbound',
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'communication': invoices[0].invoice_payment_ref or invoices[0].ref or invoices[0].name,
            'invoice_ids': [(6, 0, invoices.ids)],
        })
        return rec

    def action_draft(self):
        flag = self.env['res.users'].has_group('jibaritolotes.group_ji_factura')
        if not flag:
            raise UserError(_("No tienes Permiso para esta acción"))
        moves = self.mapped('move_line_ids.move_id')
        moves.filtered(lambda move: move.state == 'posted').button_draft()
        moves.with_context(force_delete=True).unlink()
        self.write({'state': 'draft', 'invoice_ids': False})

    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:
            # if rec.ji_moratorio_total > 0 and rec.ji_moratorio == 0:
            #     raise UserError(_("El contrato contiene moratorio, pagar moratorios."))
            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'posted' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            moves = AccountMove.create(rec._prepare_payment_moves())
            moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

            # Update the state / move before performing any reconciliation.
            move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
            rec.write({'state': 'posted', 'move_name': move_name})

            if rec.payment_type in ('inbound', 'outbound'):
                # ==== 'inbound' / 'outbound' ====
                if rec.invoice_ids:
                    (moves[0] + rec.invoice_ids).line_ids \
                        .filtered(
                        lambda line: not line.reconciled and line.account_id == rec.destination_account_id and not (
                                    line.account_id == line.payment_id.writeoff_account_id and line.name == line.payment_id.writeoff_label)) \
                        .reconcile()
            elif rec.payment_type == 'transfer':
                # ==== 'transfer' ====
                moves.mapped('line_ids') \
                    .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id) \
                    .reconcile()

        return True
