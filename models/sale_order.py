# -*- coding: utf-8 -*-
import datetime
import functools
import copy
import logging

_logger = logging.getLogger(__name__)
import dateutil.relativedelta as relativedelta
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from werkzeug import urls
from num2words import num2words

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


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ji_fecha_apartado = fields.Date(string="Fecha de Apartado")
    x_studio_vendedor = fields.Many2one(comodel_name="hr.employee", string="Vendedor")
    x_studio_manzana = fields.Many2one(string="Manzana", comodel_name="manzana.ji", compute="_compute_ji_product_information_form")
    x_studio_lote = fields.Many2one(string="Lote", comodel_name="lotes.ji", compute="_compute_ji_product_information_form")
    x_studio_calle = fields.Many2one(string="Calle", comodel_name="calle.ji", compute="_compute_ji_product_information_form")
    estado_producto = fields.Many2one('estados.g', string='Estado de Producto', compute="state_product")
    x_studio_contrato = fields.Char(string="Contrato" , compute="state_product")
    percent_mora = fields.Float(related="company_id.ji_percent_moratorium", string="Porcentaje Mora")

    # x_studio_contrato = fields.Char()
    # x_studio_calle = fields.Selection()

    @api.depends("state")
    def state_product(self):
        for line in self:
            cont = ""
            if line.invoice_ids:
                for fact in line.invoice_ids:
                    cont = fact.name
                line.estado_producto = line.order_line.product_id.estado_producto
            elif line.state == "sale" or line.state == "done":
                line.estado_producto = 13
            elif line.state == "cancel":
                line.estado_producto = 21
            else:
                line.estado_producto = 21
            line.x_studio_contrato = cont

    @api.depends("order_line")
    def _compute_ji_product_information_form(self):
        try:
            for line in self:
                line.x_studio_manzana = line.order_line.product_id.x_studio_manzana
                line.x_studio_lote = line.order_line.product_id.x_studio_lote
                line.x_studio_calle = line.order_line.product_id.x_studio_calle
                if line.state == "sale":
                    line.order_line.product_id.estado_producto = line.estado_producto
        except Exception as e:
            raise UserError("No es posible agregar otro producto a la línea de pedido.")

    @api.depends("order_line")
    def _compute_ji_estado(self):
        for order in self:
            order.order_line.product_id.estado_producto = order.estado_producto

    @api.model
    def get_name_month(self, month):
        return month_name(month)

    def ji_get_name_product(self):
        if self.order_line:
            dat = ""
            for line in self:
                dat = "MANZANA " + line.x_studio_manzana.name + " LOTE " + line.x_studio_lote.name
            # _name =
            # self.order_line.update_computes.name or ''
            # return _name.upper()
            return dat
        return ""

    def ji_get_area(self):
        if not self.order_line.ids:
            return ""
        return self.order_line[0].ji_area or ""

    def ji_get_street_address(self):
        if self.order_line:
            ji_street = self.order_line[0].product_id.x_studio_calle.name or ''
            return ji_street.upper()
        return ""

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.company_id.ji_apply_developments:
                order.partner_id._compute_ji_commercial()
                vals_commission = order._prepare_invoice_commission()
                if vals_commission:
                    move_commission = order.env["account.move"].create(vals_commission)
        return res

    def _prepare_invoice_commission(self):
        if self.x_studio_vendedor.id:
            amount_commission = (self.x_studio_vendedor.ji_percent_commission / 100) * self.amount_total
            vals = {
                "partner_id": self.x_studio_vendedor.ji_partner_id.id,
                "invoice_date": self.date_order,
                "company_id": self.company_id.id,
                "invoice_line_ids": [[0, 0, self._prepare_invoice_line_commission(amount_commission)]],
                "type": "in_invoice",
                "ji_order_contract": self.id,
                "ji_partner_contract": self.x_studio_vendedor.ji_partner_id.id
            }
            return vals
        return False

    def _prepare_invoice_line_commission(self, amount_commission):
        vals = {
            "name": 'Comision',
            "quantity": 1,
            "price_unit": amount_commission
        }
        return vals

    @api.model
    def update_computes(self):
        for sale in self.search([('company_id','=',5)]):
            sale.partner_id._compute_ji_commercial()
        pass

    text_amount = fields.Char(string="Total In Words", required=False, compute="amount_to_words")

    @api.depends('amount_total')
    def amount_to_words(self):
        self.text_amount = num2words(self.amount_total, lang='es')

    def get_amount_with_separators(self):
        # import locale
        # locale.setlocale(locale.LC_ALL, self.env.user.lang)
        # amount_string = locale.format_string("%d", self.amount_total, grouping=True)
        amount_string = '{:,.2f}'.format(self.amount_total)
        return amount_string

    def get_amount_total_text(self):
        _amount = num2words(self.amount_total, lang='es').upper()
        _amount_text = "SON: " + (_amount or '') + " DÓLARES 00/100 MONEDA DE LOS ESTADOS UNIDOS DE AMÉRICA"
        return _amount_text

    def get_amount_monthly(self):
        line_ids = self.invoice_ids.mapped('line_ids')
        amount_monthly = 0.00
        for li in line_ids:
            if li.ji_term_line_id.ji_type == 'monthly_payments':
                amount_monthly = li.debit
                break
        return amount_monthly

    def get_amount_monthly_separator(self):
        amount_string = '{:,.2f}'.format(self.get_amount_monthly())
        return amount_string

    def get_text_amount_monthly(self):
        _amount = num2words(self.get_amount_monthly(), lang='es').upper()
        _amount_text = "SON: " + (_amount or '') + " DÓLARES 00/100 MONEDA DE LOS ESTADOS UNIDOS DE AMÉRICA"
        return _amount_text

    def get_amount_advance_payment(self):
        if not self.payment_term_id.ji_advance_payment:
            return ""
        if not self.amount_total:
            return ""
        return '{:,.2f}'.format(self.payment_term_id.ji_advance_payment / 100 * self.amount_total)

    def get_text_amount_advance_payment(self):
        if "" == self.get_amount_advance_payment():
            return ""
        _amount = num2words((self.payment_term_id.ji_advance_payment / 100 * self.amount_total), lang='es').upper()
        _amount_text = "SON: " + (_amount or '') + " DÓLARES 00/100 MONEDA DE LOS ESTADOS UNIDOS DE AMÉRICA"
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

    def ji_day(self):
        _today = fields.Datetime.context_timestamp(self.company_id.partner_id, self.date_order)
        return _today

    def ji_month_name(self):
        _today = fields.Datetime.context_timestamp(self.company_id.partner_id, self.date_order)
        return month_name(_today.month)

    def get_last_payment_move(self):
        if self.invoice_ids.ids:
            line_ids = self.invoice_ids[0].mapped('line_ids').sorted(lambda l: l.ji_sequence_payments, reverse=True)
            if line_ids.ids:
                return line_ids[0]
        return False

    def ji_get_last_date_payment_text(self):
        line_move = self.get_last_payment_move()
        if line_move:
            if line_move.date_maturity:
                _today = line_move.date_maturity
                return "el día " + str(_today.day) + " de " + str(month_name(_today.month)) + " del " + str(_today.year)
        return ""

    def ji_get_street(self):
        if not self.order_line.ids:
            return ""
        ji_street = self.order_line[0].ji_street or ""
        return ji_street.upper()

    def ji_get_number_payments(self):
        return self.payment_term_id.ji_number_quotation or ""

    def ji_get_number_payments_advance_now(self):
        return self.payment_term_id.get_number_payments_advance_now()

    def ji_get_amount_month_payment(self):
        percent = self.payment_term_id.get_percent_month_payments()
        return (percent / 100) * self.amount_total

    def ji_get_text_amount_month_payment(self):
        return num2words(self.ji_get_amount_month_payment(), lang='es')

    def open_payments(self):
        
        payment_ids = []
        # pagosa = self.env["account.payment"].search([('payment_reference', '=', self.name)], order='payment_date desc')
        for order in self:
            transactions = order.sudo().transaction_ids.filtered(lambda a: a.state == "done")
            
            for item in transactions:
                payment_ids.append(item.payment_id.id)

            
        action_ref = "account.action_account_payments"
        
        [action] = self.env.ref(action_ref).read()
        action["context"] = {'default_payment_type': 'inbound', 'default_partner_type': 'customer', 'search_default_inbound_filter': 1, 'res_partner_search_mode': 'customer'}

        if len(payment_ids) > 1:
            action["domain"] = [("id", "in", payment_ids)]
        elif payment_ids:
            action["views"] = [(self.env.ref("account.view_account_payment_form").id, "form")]
            action["res_id"] = payment_ids[0]
        notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('mejoras'),
                    'message': str(action),
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
        # return notification
        return action

    @api.depends("line_ids")
    def get_reporte_amoritizacionv2(self):
        for res in self:
            move = []
            account = []
            today = fields.Date.today()
            anticipo = []
            name = res.name
            payment_ids = []
            transactions = res.sudo().transaction_ids.filtered(lambda a: a.state == "done")
            for item in transactions:
                payment_ids.append(item.payment_id.id)
            pagosa = self.env["account.payment"].search([('id', 'in', payment_ids)], order='payment_date asc')
           
            compaRecords = []
            compani = res.company_id
            tov = res.amount_untaxed
            por = res.amount_untaxed * 0.1
            anticp = por
            sald_ant=0
            cont=0

            anticipo.append({
                "number": "Anticipo 0",
                "date_f": "",
                "mora": 0,
                "impo": 0,
                "total": anticp,
                "real": 0,
            })

            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('mejoras'),
                    'message': "pagos",
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            # return notification
            pagov = 1
            ofpa = ""
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

            
           


            move.append({
                "name": res.name,
                "cliente": res.partner_id.name,
                "date": res.ji_fecha_apartado,
                
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
                'client': res.partner_id.name,
                'contrato':"PRE-"+ res.name,
                'produc': "Manzana " + res.x_studio_manzana.name + ", Lote " + res.x_studio_lote.name + ", Calle " + res.x_studio_calle.name,
                'date': str(today.day) + " de " + str(month_name(today.month)) + " del " + str(today.year),
                'move_id': move,
                'ofpay': ofpa,
                'anti': anticipo,
                'comapany': compaRecords,
            }
            return self.env.ref('jibaritolotes.report_amortizacionv2').report_action(self, data=data)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange("product_id")
    def onchange_ji_product(self):
        if self.order_id.company_id.ji_apply_developments:
            if self.product_id.id:
                self.product_uom_qty = self.product_id.ji_area


    @api.model
    @api.onchange("product_id")
    def _produ_nuevo_renew(self):
        for rec in self:
            res = {}
            if (rec.product_id):
                productos = self.env['product.template'].search(
                    [('estado_producto.name', '=', 'Nuevo')])

                # rec.was_credit = True
                if productos:
                    res['domain'] = {'product_id': [('id', 'in', productos.ids)]}
                # domain = [('id', 'in', pedido.ids)]
                else:
                    #    domain = [('id','=',0)]
                    res['domain'] = {'product_id': [('id', '=', 0)]}

            return res