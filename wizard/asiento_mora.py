from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, timedelta

class MoratorioAsiento(models.Model):
    _name = 'ji.mora.asiento'
    _description = 'Generar Asiento Contable De Moratorio'

    name = fields.Char(string="Name", compute="get_namepago")
    factura_id = fields.Many2one('account.move', string="Factura")
    total_moratorium = fields.Float(string="Total Moratorios")
    mes_apagar = fields.Integer(string="Meses a pagar")

    @api.depends("factura_id")
    def get_namepago(self):
        for res in self:
            res.mes_apagar = res.factura_id.total_mes
            res.name = "Moratorio de " + res.factura_id.name

    def run(self):
        try:
            for res in self:
                a=""
                b=""
                i=0;
                apunte_credit = []
                apunte_debit = []
                for fac in res.factura_id:
                    fac.action_regenerate_unreconciled_aml_dues()
                    mr = 1
                    mto = 0
                    dat = fields.Date.today()
                    for mora in fac.moratorio_line:
                        td = timedelta(1)
                        if res.mes_apagar <= mr:
                            mto = mto + mora.real_amount_moratorium
                        if mora.real_amount_moratorium > 0 and res.mes_apagar <= mr:
                            dat = mora.date_maturity - td
                    for lin in fac.line_ids:
                        if i < 2:
                            if lin.credit > 0:
                                apunte_credit.append(
                                    {
                                        "name": res.name,
                                        "move_id": res.factura_id.id,
                                        # "account_id": lin.account_id.id,
                                        "partner_id": fac.partner_id.id,
                                        "credit": res.total_moratorium,
                                        # "date": lin.date,
                                        "date_maturity": dat,
                                        "debit": 0,
                                    }
                                )
                                a= "Entro " + str(lin.credit)
                                i = i + 1
                            if lin.debit > 0:
                                apunte_credit.append(
                                                      {
                                                          "name": res.name,
                                                          "move_id": res.factura_id.id,
                                                          "account_id": lin.account_id.id,
                                                          "partner_id": fac.partner_id.id,
                                                          "credit": 0,
                                                          "date_maturity": dat,
                                                          "date": lin.date,
                                                          "debit": res.total_moratorium,
                                                      }
                                                      )
                                b = "Entro" + str(lin.debit)
                                i = i + 1

                # raise UserError(_(apunte_credit ))
                # res.factura_id.line_ids.create(apunte_credit)
                res.factura_id.create({"line_ids": [(0, 0, vals) for vals in apunte_credit]})
                # res.factura_id.create({"line_ids": apunte_credit})
                # self.env["account.move.line"].create(apunte_debit)
        except Exception as e:
            raise UserError(_(e))
            # move.post()
            # move1.post()