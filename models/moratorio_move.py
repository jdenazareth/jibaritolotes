# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil import relativedelta
from odoo import api, models, fields, _
from odoo.exceptions import UserError
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

    @api.depends("line_ids")
    def get_plazo_actual(self):
        for res in self:
            move = []
            account = []
            today = fields.Date.today()
            anticipo = []
            name = res.name
            pagosto = 0
            if self.type == "out_invoice":
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
                for lin in lines:

                    mora = 0
                    mora_prox = 0.0
                    prox_sal = 0.0
                    if sald_ant > 0:
                        impo = 0 + sald_ant
                        sald_ant2 = 0

                    else:
                        impo = 0
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
                                    fechan = pay.payment_date.strftime('%d-%m-%y')

                                    impo = impo + pay.amount
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
                                    fechan = pay.payment_date.strftime('%d-%m-%y')
                                    impo = impo + pay.amount
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
                                prox_sal = lin.debit - sald_ant + mora
                            else:
                                prox_sal = lin.debit + mora
                        else:
                            prox_sal = 0

                        prox_pay = json.loads(res.moratex)
                        mora_prox = 0.0
                        for px_py in prox_pay:
                            if px_py["fecha"] == str(lin.date_maturity):
                                unit_p = float(px_py["unimora"])
                                mes_p = float(px_py["mes"])
                                mora_prox = unit_p * mes_p

                                # return notification
                        prox_sal = prox_sal + round(mora_prox, 2)
                        if impo > lin.debit:
                            sald_ant = impo - lin.debit + sald_ant2
                            impo = lin.debit
                        elif impo < lin.debit:
                            sald_ant = impo - lin.debit + sald_ant2

                        else:
                            sald_ant = 0
                            impo = lin.debit
                        tov = tov - (pimp - mora) + round(mora_prox, 2)
                        if (impo == 0):
                            fecpag = ""
                            sald_ant = 0
                        # mora + round(mora_prox, 2)
                        if mora <= 0:
                            mora = mora_prox

                        account.append({
                            "number": pagov,
                            "date_f": lin.date_maturity.strftime('%d-%m-%y'),
                            "date_p": fechan,
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

                pagosto = co
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

    @api.depends("company_id","partner_id", "total_moratorium")
    def action_regenerate_unreconciled_aml_dues(self):
        # self.validate_regenerate_aml()
        for record in self:
            if record.total_moratorium > 0:
                companies = self.env["res.company"].search([('ji_apply_developments', '=', True)])

                if len(companies.ids) == 0:
                    raise UserError(_('No Apply for this companies'))
                partners = []
                for company in companies:
                    partners_slow_payer = record.partner_id.get_number_slow_payer_cronv(company,record)

                    for p in partners_slow_payer:
                        number_slow_payer, amls = p.get_number_slow_payer_cron(company)
                        partners.append({"partner": p, "amls": amls})
                        # raise UserError(_(amls))
                    if len(partners) > 0:
                        # record.moratorio_line.unlink()
                        for partner in partners:
                            notification_lines = []
                            # raise UserError(_(partner["amls"]))
                            
                            for aml in partner["amls"]:
                                if aml.move_id.id == record.id:
                                    if aml.id not in record.get_exist_payments():
                                        notification_lines.append([0, 0, {
                                            "name": len(partner["amls"]),
                                            # "moratorium_id": aml.move_id.id,
                                            "unreconciled_aml": aml.id

                                        }])

                    # raise UserError(_(notification_lines))
                    self.write({"moratorio_line": notification_lines})

    # ji_accoun_line = fields.One2many('account.move.line', 'move_id', string="Moratorium S")
    total_moratorium = fields.Monetary(string="Total Moratorios", compute="action_moratorio_dues")
    total_mes = fields.Integer(string="Meses a Pagar")
    moratex = fields.Text(string="Mora Json")
   
    @api.depends("company_id", "partner_id", "percent_moratorium", "at_date")
    def action_moratorio_dues(self):
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
                    partners_slow_payer = record.partner_id.get_partners_slow_payer_moratorium(company)
                    # raise UserError(_(partners_slow_payer))
                    for p in partners_slow_payer:
                        number_slow_payer, amls = p.get_number_slow_payer_cronv(company,record)
                        partners.append({"partner": p, "amls": amls})

                        # raise UserError(_(amls))
                    if len(partners) > 0:
                        # record.moratorio_line.unlink()
                        for partner in partners:
                            # notification_lines = []
                            # raise UserError(_(partner["amls"]))
                            paml =partner["amls"]


                            
                            tpay = 0.0
                            for aml in paml:
                                pagos = self.env["account.payment"].search([('payment_reference', '=', aml.move_id.invoice_payment_ref)])
                                if aml.move_id.id == record.id:
                                    # if aml.id not in record.get_exist_payments():
                                    # record.ji_accoun_line.append(aml)
                                    pay = 0.0
                                    pay2 = 0.0
                                    for lp in pagos:
                                       if aml.date_maturity == lp["ji_moratorio_date"]:
                                           pay = pay + lp["ji_moratorio"]
                                    # mesp = mesp + 1
                                    todate = fields.Date.today()
                                    r = relativedelta.relativedelta(record.at_date, aml.date_maturity)
                                    month_number = r.months + 2
                                    if month_number > mesp:
                                        mesp = month_number
                                    amount = aml.amount_residual_currency if aml.currency_id else aml.amount_residual
                                    unit_moratorium = ((record.percent_moratorium / 100) * amount)
                                    amount_total_moratorium = round(float(month_number) * float(unit_moratorium),2)
                                    if tpay != 0:
                                        pay = tpay
                                    if pay > amount_total_moratorium:
                                        tpay = pay - amount_total_moratorium
                                        pay = (pay - tpay)
                                    mora = mora + amount_total_moratorium - pay
                                    mest = mest +1
                                    pmora.append({
                                        
                                        "fecha": str(aml.date_maturity),
                                        "mora": amount_total_moratorium - pay,
                                        "pay": pay,
                                        "unimora": unit_moratorium,
                                        "mes":month_number,
                                        "tmes": r.months,
                                       
                                    })
                                    

                                    # objects = {'o': record, 'amount_residual': amount, 'month_number': month_number}
                                    # python_code = record.company_id.ji_codev
                                    #
                                    # if python_code:
                                    #     safe_eval(record.company_id.ji_codev, objects, mode="exec", nocopy=True)
                                    #     real_amount_moratorium = objects['result']
                                    # else:
                                    #     real_amount_moratorium = 0.00

            record.moratex = json.dumps(pmora)
            record.total_mes = mesp
            record.total_moratorium = mora
        if self.total_moratorium > 0:
            self.ji_is_moratorium = True
        else:
            self.ji_is_moratorium = False

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
    amount_total_moratorium = fields.Monetary(string="Amount Total Moratorium",
                                              compute="_compute_amount_total_moratorium")
    amount_pay = fields.Monetary(string="Pagos",
                                              compute="_compute_amount_total_moratorium")
    real_amount_moratorium = fields.Monetary(string="Total Moratorium", store=True,
                                             compute="_compute_real_amount_moratorium")

    moratorium_accumulated = fields.Monetary(string="Accumulated Moratorium", store=True,
                                             compute="_compute_moratorium_accumulated")

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



    @api.depends("month_number", "moratorium_id", "amount_residual")
    def _compute_moratorium_accumulated(self):
        for mora in self:
            amount = mora.amount_residual
            mora_accumulated = 0.0
            for index in range(0, mora.month_number):
                mora_accumulated += amount * (mora.moratorium_id.percent_moratorium / 100)
                amount = amount + (amount * (mora.moratorium_id.percent_moratorium / 100))
            mora.moratorium_accumulated = mora_accumulated

    @api.depends("moratorium_id", "month_number", "amount_residual")
    def _compute_real_amount_moratorium(self):
        for mora in self:
            # raise UserError(_(self.moratorium_id.company_id.name))
            mora.real_amount_moratorium = (mora.exec_formula_python()) - mora.amount_pay

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

    @api.depends("month_number", "amount_unit_moratorium")
    def _compute_amount_total_moratorium(self):
        for line in self:
            pagos = self.env["account.payment"].search([('payment_reference', '=', line.moratorium_id.invoice_payment_ref)])
            pay = 0.0
            pay2 = 0.0
            for lp in pagos:
                if line.date_maturity == lp["ji_moratorio_date"]:
                    pay = pay + lp["ji_moratorio"]
            line.amount_pay = pay
            line.amount_total_moratorium = (line.month_number * line.amount_unit_moratorium) - pay

    @api.depends("date_maturity", "at_date")
    def _compute_month_number(self):
        for line in self:
            r = relativedelta.relativedelta(line.at_date, line.date_maturity)
            line.month_number = r.months + 1

    @api.depends("amount_residual", "moratorium_id")
    def _compute_amount_unit_moratorium(self):
        for line in self:
            line.amount_unit_moratorium = ((line.moratorium_id.percent_moratorium / 100) * line.amount_residual)

    @api.depends("unreconciled_aml", "moratorium_id")
    def _compute_unreconciled_values(self):
        for line in self:
            currency = line.currency_id or line.moratorium_id.company_id.currency_id
            amount = line.unreconciled_aml.amount_residual_currency if line.unreconciled_aml.currency_id else line.unreconciled_aml.amount_residual
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