# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from dateutil import rrule
from odoo.tools.safe_eval import safe_eval, test_python_expr
import json

class moratorio_move(models.Model):
    _inherit = "account.move"

    # def copy(self, default=None):
    #     self.ensure_one()
    #     raise UserError(_("You cannot duplicate this record, please create a new one."))
    #     return super(moratorio_move, self).copy(default=default)

    # def unlink(self):
    #     if self.state == "invoiced":
    #         raise UserError(_("You cannot delete a record in invoiced."))
    #     return super(moratorio_move, self).unlink()

    at_date = fields.Date(string="At Date", default=fields.Date.context_today)
    #interest_line = fields.One2many(comodel_name="ji.moratorium.interest.line", string="Interest line",
    #                                inverse_name="moratorium_id")
    moratorio_line = fields.One2many(comodel_name="ji.moratorium.account.line", string="Interest line",
                                    inverse_name="moratorium_id")
    percent_moratorium = fields.Float(related="company_id.ji_percent_moratorium", string="Percent Moratorium")
    ji_condition = fields.Selection(related="partner_id.ji_condition", string="Condicion")
    ji_number_slow_payer = fields.Integer(related="partner_id.ji_number_slow_payer", string="Number Slow Payer")
    amount_total_moratorium = fields.Monetary(string="Amount Total Moratorium")
    ji_plazo_actual = fields.Integer(string="Meses pagados en totalidad", compute="get_plazo_actual")

    restante = fields.Float(string="Saldo restante mes")
    saldo_pend = fields.Float(string="Saldo pendiente")
    total_adeudo = fields.Float(string="Adeudo Total")
    proxfecha_venci = fields.Date(string="Fecha a vencer")


    def get_plazo_actual(self):
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
            compaRecords = []
            compani = res.company_id
            tov = res.amount_untaxed
            por = res.amount_untaxed * 0.1
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
            co5 = 0
            sald_pen =0
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
            sal_pendt = 0
            date_end  = fields.Date.from_string(res.invoice_date)
            today = fields.Date.context_today(self)

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
                if lin.ji_number.find('A') != 0 and lin.debit >= 1 :
                    co2 = 0
                    fechan = ""
                    if sald_ant < lin.debit :
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
                    if mora <= 0:
                        mora = mora_prox

                    if prox_sal == 0:
                        co5 = co5 + 1
                    if prox_sal < lin.debit:
                        sald_pen = prox_sal
                    sal_pendt = sal_pendt + prox_sal
                    if str(today) > str(lin.date_maturity):
                        date_end = fields.Date.from_string(lin.date_maturity)

                    if prox_sal == lin.debit:
                        break
            date_end += relativedelta(months=1)
            res.proxfecha_venci = date_end
            pagosto = co5
            res.saldo_pend = sal_pendt

            res.restante = sald_pen
            res.ji_plazo_actual = pagosto




    def _prapare_invoice(self):
        line_vals = []
        for line in self.moratorio_line:
            line_vals.append([0, 0, line._prepare_invoice_line()])
        vals = {
            "partner_id": self.partner_id.id,
            "invoice_date": self.at_date,
            "company_id": self.company_id.id,
            "invoice_line_ids": line_vals,
            "type": "out_invoice",
            "ji_is_moratorium": True
        }
        return vals

    def validate_create_invoice(self):
        if len(self.moratorio_line.ids) == 0:
            raise UserError(_("It does not contain overdue payments."))

    def create_invoice(self):
        self.ensure_one()
        self.validate_create_invoice()
        if not self.invoice_id.id:
            vals = self._prapare_invoice()
            invoice = self.env["account.move"].create(vals)
            self.write({"invoice_id": invoice.id})

        self.write({"state": "invoiced"})

    def action_view_invoice(self):
        self.ensure_one()
        # self.invoice_id.write({"ji_is_moratorium": True})
        return {
            'name': _('Customer Invoice Moratorium'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_id.id,
        }

    @api.depends("moratorio_line")
    def _compute_amount_total_moratorium(self):
        # self.action_regenerate_unreconciled_aml_dues()
         for moratorium in self:
             moratorium.amount_total_moratorium = sum(line.amount_total_moratorium for line in self.moratorio_line)

    def validate_regenerate_aml(self):
        if not self.partner_id.id:
            raise UserError(_("Client not selected"))

    def get_exist_payments(self):
        moratoriums = self.env['account.move'].search(
            [('partner_id', '=', self.partner_id.id), ('state', 'not in', ['draft', 'cancel'])])
        return moratoriums.moratorio_line.mapped('unreconciled_aml').ids


    def action_regenerate_unreconciled_aml_dues(self):
        # self.validate_regenerate_aml()
        for record in self:
                companies = self.env["res.company"].search([('ji_apply_developments', '=', True)])

                if len(companies.ids) == 0:
                    raise UserError(_('No Apply for this companies'))
                partners = []

                for company in companies:
                    today=fields.Date.context_today(self)
                    number_slow_payer = 0
                    amls = []
                    notification_lines = []
                    for aml in record.line_ids:
                        if aml.date_maturity:
                            # raise UserError(_(str(aml.date_maturity) + " - date"))
                            if str(today) > str(aml.date_maturity) and not aml.reconciled:
                                # raise UserError(_("entr"))
                                number_slow_payer += 1
                                amls.append(aml)
                    partners.append({"partner": record.partner_id, "amls": amls})
                    # raise UserError(_(str(amls) + " - aml"))
                        # raise UserError(_(amls))
                    if len(partners) > 0:
                        # record.moratorio_line.unlink()
                        for partner in partners:

                            # raise UserError(_(partner["amls"]))
                            
                            for aml in partner["amls"]:

                                if aml.id not in record.get_exist_payments():
                                    notification_lines.append([0, 0, {
                                        "name": len(partner["amls"]),
                                        # "moratorium_id": aml.move_id.id,
                                        "unreconciled_aml": aml.id

                                    }])
                                    # raise UserError(_(notification_lines))

                    # raise UserError(_(notification_lines))

                    self.write({"moratorio_line": notification_lines})

    # ji_accoun_line = fields.One2many('account.move.line', 'move_id', string="Moratorium S")
    total_moratorium = fields.Monetary(string="Total Moratorios", compute="action_moratorio_dues")
    total_mes = fields.Integer(string="Meses a Pagar")
    moratex = fields.Text(string="Mora Json", compute="action_moratorio_dues")

    def action_moratorio_v(self):
        for record in self:
            # record.validate_regenerate_aml()
            mora = 0.0
            mest = 0
            mesp = 0
            pmora = []
            id_term = 0
            today = fields.Date.context_today(self)
            for term in record.invoice_payment_term_id:
                id_term = term.id
            if record.partner_id and id_term> 1:
                companies = self.env["res.company"].search([('ji_apply_developments', '=', True)])
                if len(companies.ids) == 0:
                    mora = 0.0
                partners = []

                for company in companies:

                    number_slow_payer = 0
                    amls = []
                    for aml in record.line_ids:
                        # raise UserError(_(str(today) + " >= " + str(aml.date_maturity)))
                        if aml.date_maturity:
                            if today > aml.date_maturity and not aml.reconciled:
                                number_slow_payer += 1
                                amls.append(aml)
                    partners.append({"partner": record.partner_id, "amls": amls})
                    # raise UserError(_(amls))
                    if len(partners) > 0:
                        # record.moratorio_line.unlink()
                        for partner in partners:
                            # notification_lines = []
                            # raise UserError(_(partner["amls"]))
                            paml = partner["amls"]
                            tpay = 0.0
                            for aml in paml:
                                # pagos = self.env["account.payment"].search([('payment_reference', '=', aml.move_id.invoice_payment_ref)])
                                pagos = self.env["account.payment"].search(
                                    [('communication', '=', record.invoice_payment_ref),
                                     ('x_studio_tipo_de_pago', '!=', 'Anticipo'),
                                     ('state', '=', 'posted')], order='payment_date,id asc')
                                # if aml.id not in record.get_exist_payments():
                                # record.ji_accoun_line.append(aml)
                                pay = 0.0
                                pay2 = 0.0
                                for lp in pagos:
                                    if aml.date_maturity == lp["ji_moratorio_date"]:
                                        pay = pay + lp["ji_moratorio"]
                                # mesp = mesp + 1
                                todate = fields.Date.context_today(self)
                                date_ultpay = fields.Date.from_string(todate)
                                date_ultpay -= timedelta(days=1)
                                r = rrule.rrule(rrule.MONTHLY, dtstart=aml.date_maturity, until=date_ultpay)
                                month_number = int(r.count())

                                month_number = month_number
                                if month_number > mesp:
                                    mesp = month_number

                                amount = aml.debit
                                unit_moratorium = round((record.percent_moratorium / 100) * round(amount, 2), 2)
                                amount_total_moratorium = round(float(month_number) * float(unit_moratorium), 2)
                                if tpay != 0:
                                    pay = tpay
                                if pay > amount_total_moratorium:
                                    tpay = pay - amount_total_moratorium
                                    pay = (pay - tpay)
                                mora = mora + amount_total_moratorium - pay
                                mest = mest + 1
                                pmora.append({

                                    "fecha": str(aml.date_maturity),
                                    "mora": amount_total_moratorium - pay,
                                    "pay": pay,
                                    "unimora": unit_moratorium,
                                    "mes": month_number,


                                })
            if str(today) == str(record.proxfecha_venci):
                mest += 1
            record.total_mes = mest

            return mora

    def action_moratorio_dues(self):
        for record in self:
            moratex = record.action_moratorio_json()
            record.moratex = moratex

            total_moratorium = record.action_moratorio_v()
            if total_moratorium > 0:
                record.ji_is_moratorium = True
            else:
                record.ji_is_moratorium = False
            record.total_adeudo = record.amount_residual + total_moratorium
            record.total_moratorium = total_moratorium

    def action_moratorio_json(self):
        for record in self:
            # record.validate_regenerate_aml()
            mora = 0.0
            mest = 0
            mesp = 0
            pmora = []
            if record.partner_id:
                companies = self.env["res.company"].search([('ji_apply_developments', '=', True)])
                if len(companies.ids) == 0:
                    mora = 0.0
                partners = []

                for company in companies:
                    today = fields.Date.context_today(self)
                    number_slow_payer = 0
                    amls = []
                    for aml in record.line_ids:
                        # raise UserError(_(str(today) + " >= " + str(aml.date_maturity)))
                        if aml.date_maturity:
                            if str(today) > str(aml.date_maturity) and not aml.reconciled:
                                number_slow_payer += 1
                                amls.append(aml)
                    partners.append({"partner": record.partner_id, "amls": amls})
                    # raise UserError(_(amls))
                    if len(partners) > 0:
                        # record.moratorio_line.unlink()
                        for partner in partners:
                            # notification_lines = []
                            # raise UserError(_(partner["amls"]))
                            paml = partner["amls"]

                            tpay = 0.0
                            for aml in paml:
                                # pagos = self.env["account.payment"].search([('payment_reference', '=', aml.move_id.invoice_payment_ref)])
                                pagos = self.env["account.payment"].search(
                                    [('communication', '=', record.invoice_payment_ref),
                                     ('x_studio_tipo_de_pago', '!=', 'Anticipo'),
                                     ('state', '=', 'posted')], order='payment_date,id asc')
                                # if aml.id not in record.get_exist_payments():
                                # record.ji_accoun_line.append(aml)
                                pay = 0.0
                                pay2 = 0.0
                                for lp in pagos:
                                    if aml.date_maturity == lp["ji_moratorio_date"]:
                                        pay = pay + lp["ji_moratorio"]
                                # mesp = mesp + 1
                                todate = fields.Date.context_today(self)
                                date_ultpay = fields.Date.from_string(todate)

                                date_ultpay -= timedelta(days=1)
                                # raise UserError(_(str(date_ultpay)))
                                r = rrule.rrule(rrule.MONTHLY, dtstart=aml.date_maturity, until=date_ultpay)
                                month_number = int(r.count())
                                # sum = 1
                                # if str(today) > str(aml.date_maturity):
                                #     sum = 0
                                # month_number = month_number - sum
                                if month_number > mesp:
                                    mesp = month_number
                                amount = aml.debit
                                unit_moratorium = round((record.percent_moratorium / 100) * amount, 2)
                                amount_total_moratorium = round(float(month_number) * float(unit_moratorium), 2)
                                if tpay != 0:
                                    pay = tpay
                                if pay > amount_total_moratorium:
                                    tpay = pay - amount_total_moratorium
                                    pay = (pay - tpay)
                                mora =  amount_total_moratorium - pay
                                mest = mest + 1
                                pmora.append({

                                    "fechato": str(date_ultpay),
                                    "fecha": str(aml.date_maturity),
                                    "mora": mora ,
                                    "pay": pay,
                                    "unimora": unit_moratorium,
                                    "mes": month_number,


                                })
            return json.dumps(pmora)

                # raise UserError(_(notification_lines))
                # self.write({"moratorio_line": notification_lines})

    def action_generate_asiento_mora(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generar Asiento a moratorio'),
            'res_model': 'ji.mora.asiento',
            'view_mode': 'form',
            'domain': [('factura_id.id', '=', self.ids[0])],
            'target': 'new',
            'context': {
                'default_type': 'factura',
                'default_factura_id': self.id,
                'default_total_moratorium':self.total_moratorium,

            },
        }


    def exec_formula_python(self,a,m):
        objects = {'o': self,'amount_residual':a,'month_number':m}

        python_code = self.get_formula_python()

        if python_code:
            safe_eval(self.get_formula_python(), objects, mode="exec", nocopy=True)
            return objects['result']
        else:
            return 0.00

    def get_formula_python(self):
        return self.company_id.ji_codev

class JiMoratoriumaccountLine(models.Model):
    _name = "ji.moratorium.account.line"
    _description = "Details Interest for moratorium"

    moratorium_id = fields.Many2one(comodel_name="account.move", string="Moratorium", ondelete="cascade",
                                    index=True)
    unreconciled_aml = fields.Many2one(comodel_name="account.move.line", string="Unreconciled Due")

    name = fields.Char(string="Name", store=True, compute="_compute_name")
    date = fields.Date(string="Date", compute="_compute_unreconciled_values", store=True)
    date_maturity = fields.Date(string="Due Date", compute="_compute_unreconciled_values", store=True)
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", store=True,
                                  compute="_compute_unreconciled_values")
    amount_residual = fields.Monetary(string="Amount", store=True, compute="_compute_unreconciled_values")
    at_date = fields.Date(string="At Date", related="moratorium_id.at_date")
    month_number = fields.Integer(string="Number Month", compute="_compute_month_number")
    amount_unit_moratorium = fields.Monetary(string="Amount Unit Moratorium", compute="_compute_amount_unit_moratorium")
    amount_total_moratorium = fields.Monetary(string="Moratorio Restante",
                                              compute="_compute_amount_total_moratorium")
    amount_pay = fields.Monetary(string="Pagos",
                                              compute="_compute_amount_total_moratorium")
    real_amount_moratorium = fields.Monetary(string="Total Moratorium", store=True,
                                             compute="_compute_real_amount_moratorium")

    moratorium_accumulated = fields.Monetary(string="Accumulated Moratorium", store=True,
                                             compute="_compute_moratorium_accumulated")

    mount_mora = fields.Monetary(string="A Pagar", store=True, compute="_compute_amount_moratorium")

    def _prepare_invoice_line(self):
        vals = {
            "name": self.name,
            "quantity": 1,
            "price_unit": self.real_amount_moratorium
        }
        return vals

    @api.depends("unreconciled_aml")
    def _compute_name(self):
        for line in self:
            # raise UserError(_(line.unreconciled_aml.ji_name))
            line.name ="Mora - " + line.unreconciled_aml.ji_name
    @api.depends("amount_pay","moratorium_id","unreconciled_aml", "amount_residual")
    def _compute_amount_moratorium(self):
        for mora in self:
            mora.mount_mora = mora.amount_residual + mora.amount_total_moratorium - mora.amount_pay

    @api.depends("month_number","moratorium_id","unreconciled_aml", "amount_residual")
    def _compute_moratorium_accumulated(self):
        for mora in self:
            amount = mora.amount_residual
            mora_accumulated = 0.0
            for index in range(0, mora.month_number):
                mora_accumulated += amount * (mora.moratorium_id.percent_moratorium / 100)
                amount = amount + (amount * (mora.moratorium_id.percent_moratorium / 100))
            mora.moratorium_accumulated = mora_accumulated

    @api.depends("moratorium_id", "month_number", "amount_residual","amount_pay")
    def _compute_real_amount_moratorium(self):
        for mora in self:
            # raise UserError(_(self.moratorium_id.company_id.name))

            # mora.real_amount_moratorium = (mora.exec_formula_python()) - mora.amount_pay

            mora.real_amount_moratorium = mora.amount_total_moratorium


    def exec_formula_python(self):
        objects = {'o': self}
        python_code = self.get_formula_python()

        if python_code:
            safe_eval(self.get_formula_python(), objects, mode="exec", nocopy=True)
            return objects['result']
        else:
            return 0.00

    def get_formula_python(self):
        return self.moratorium_id.company_id.ji_code

    @api.depends("month_number", "amount_unit_moratorium","moratorium_id","unreconciled_aml")
    def _compute_amount_total_moratorium(self):
        for line in self:
            # pagos = self.env["account.payment"].search([('payment_reference', '=', line.moratorium_id.invoice_payment_ref)])
            pagos = self.env["account.payment"].search(
                [('communication', '=', line.moratorium_id.invoice_payment_ref), ('x_studio_tipo_de_pago', '!=', 'Anticipo'),
                 ('state', '=', 'posted')], order='payment_date,id asc')
            pay = 0.0
            pay2 = 0.0
            for lp in pagos:

                if line.date_maturity == lp["ji_moratorio_date"]:
                    pay = pay + lp["ji_moratorio"]
                    pay2 = pay2 + lp["amount"]

            line.amount_pay = pay
            total_m = round((line.month_number * line.amount_unit_moratorium ) - pay,2)
            line.mount_mora = line.amount_residual + total_m - pay2

            line.amount_total_moratorium = total_m

    @api.depends("date_maturity", "at_date")
    def _compute_month_number(self):
        for line in self:
            todate = fields.Date.context_today(self)
            date_ultpay = fields.Date.from_string(todate)
            date_ultpay -= timedelta(days=1)
            r = rrule.rrule(rrule.MONTHLY, dtstart=line.date_maturity, until=date_ultpay)

            line.month_number = int(r.count())
            # raise UserError(_(r.count()))
            # r = relativedelta.relativedelta(line.at_date, line.date_maturity)


    @api.depends("amount_residual","moratorium_id","unreconciled_aml")
    def _compute_amount_unit_moratorium(self):
        for line in self:
            line.amount_unit_moratorium = round(((line.moratorium_id.percent_moratorium / 100) * line.amount_residual),2)

    @api.depends("unreconciled_aml", "moratorium_id")
    def _compute_unreconciled_values(self):
        for line in self:
            currency = line.currency_id or line.moratorium_id.company_id.currency_id
            amount = line.unreconciled_aml.debit
            # amount = line.unreconciled_aml.amount_residual_currency if line.unreconciled_aml.currency_id else line.unreconciled_aml.amount_residual
            line.amount_residual = amount
            line.date = line.unreconciled_aml.date
            line.date_maturity = line.unreconciled_aml.date_maturity
            line.currency_id = currency.id
            line.name = line.unreconciled_aml.ji_name

# class JiMoratoriumaccountLine(models.Model):
#     _name = "ji.moratorium.pay"
#     _description = "Pagos a moratorios"
#
#     name = fields.Char(string="Name")
#     account_id = fields.Many2one(comodel_name="account.move", string="Moratorium")
#     amount_residual = fields.Monetary(string="Pago" )
#     mes_apagar = fields.Integer(string="Meses")