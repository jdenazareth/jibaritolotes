from datetime import datetime, timedelta
from dateutil import relativedelta
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval, test_python_expr
import json


class moratorio_sale(models.Model):
    _inherit = "sale.order"

    total_mes = fields.Integer(string="dias a Pagar")
    prorroga = fields.Integer(string="Prorroga Dias")
    moratex = fields.Text(string="Mora Json")
    at_date = fields.Date(string="At Date", default=fields.Date.context_today)
    total_moratorium = fields.Monetary(string="Total Moratorios", compute="action_moratorio_dues")
    saldsex = fields.Float(string="Saldo al terminar", compute="action_sal")
    exsalds = fields.Float(string="Saldo al terminar")
    ismora = fields.Boolean('Is Mora')

    def action_sal(self):
        for record in self:
            diap = record.ji_fecha_apartado
            today = record.at_date
            pay_tipo = record.payment_term_id
            dif = 0


            for line in pay_tipo.line_ids:
                if line.ji_type == "money_advance":
                    dif = line.days

            # nday = diap + relativedelta(days=line.days)
            # if today == nday
            dias = (today - diap) / timedelta(days=1)
            record.total_mes = dias
            pror = dif + 15
            if dias > pror and not record.ismora:
                record.ismora = True
                record.exsalds = record.pay_anticipo

            record.saldsex = record.exsalds

    def action_moratorio_dues(self):
        for record in self:
            mora = 0
            mest = 0
            mesp = 0
            pmora = []
            transactions = []
            transactions = record.sudo().transaction_ids.filtered(lambda a: a.state == "done")
            if record.state != "draft" and record.state != "cancel" and record.pay_anticipo > 0:
                if record.payment_term_id and record.payment_term_id.ji_number_quotation:

                    diap = record.ji_fecha_apartado
                    today = record.at_date
                    pay_tipo = record.payment_term_id
                    amount = record.amount_total

                    dif = 0
                    val = 0
                    tipe = ""
                    for line in pay_tipo.line_ids:
                        if line.ji_type == "money_advance":
                            dif = line.days

                    dias = (today - diap) / timedelta(days=1)
                    pror = dif + 15
                    if dias > pror:
                        pay = 0
                        payex = 0
                        mpay = 0
                        sald = 0
                        expay = record.exsalds
                        newpay = record.pay_anticipo
                        unit_moratorium = round((record.percent_mora / 100) * expay, 2)
                        if expay > newpay:
                            for tran in transactions:
                                mpay = mpay + tran.mora
                                pay = pay + tran.amount
                                if pay >= (expay - newpay):
                                    payex = payex + tran.amount

                            diasp = round(mpay / unit_moratorium)
                            dif = (unit_moratorium * diasp) - mpay
                            didif= dias - pror
                            if dif <= 0:
                                unit_moratorium = round((record.percent_mora / 100) * newpay, 2)
                                mora = unit_moratorium * (didif - diasp)
                            else:
                                mora = unit_moratorium * ( didif - diasp) + dif
                            # notification = {
                            #     'type': 'ir.actions.client',
                            #     'tag': 'display_notification',
                            #     'params': {
                            #         'title': ('mejoras'),
                            #         'message': str(mora)+ " "+ str(diasp) + " " + str(didif),
                            #         'type': 'success',  # types: success,warning,danger,info
                            #         'sticky': True,  # True/False will display for few seconds if false
                            #     },
                            # }
                            # return notification
                        else:
                            mora = unit_moratorium * (dias - pror)





            record.moratex = json.dumps(pmora)
            record.total_moratorium = mora
