from odoo import api, fields, models, _
from odoo.exceptions import UserError

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
        raise UserError(_("En construccion"))