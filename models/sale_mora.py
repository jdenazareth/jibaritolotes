from datetime import datetime
from dateutil import relativedelta
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval, test_python_expr
import json

class moratorio_move(models.Model):
    _inherit = "sale.order"



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
                                    month_number = r.months + 1
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
                                        "tmes": mest,
                                       
                                    })
                                    

                                    # objects = {'o': record, 'amount_residual': amount, 'month_number': month_number}
                                    # python_code = record.company_id.ji_codev
                                    #
                                    # if python_code:
                                    #     safe_eval(record.company_id.ji_codev, objects, mode="exec", nocopy=True)
                                    #     real_amount_moratorium = objects['result']
                                    # else:
                                    #     real_amount_moratorium = 0.00
            record.moratex=json.dumps(pmora)
            record.total_mes = mesp
            record.total_moratorium = mora