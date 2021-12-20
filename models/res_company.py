# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.tools.safe_eval import safe_eval, test_python_expr
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    ji_apply_developments = fields.Boolean(string="Apply developments")
    ji_number_slow_payer = fields.Integer(string="Number to Slow Payer")
    ji_partner_ids = fields.Many2many(comodel_name="res.partner", string="Partners To Notification")
    ji_mail_template = fields.Many2one(comodel_name="mail.template", string="Template for Notification")
    ji_contract_template = fields.Html(string="Contract Template")
    ji_annex_a = fields.Html(string="Annex A Template")
    ji_annex_b = fields.Html(string="Annex B Template")
    ji_annex_c = fields.Html(string="Annex C Template")
    ji_annex_d = fields.Html(string="Annex D Template")
    ji_annex_e = fields.Html(string="Annex E Template")
    ji_annex_f = fields.Html(string="Annex F Template")
    ji_annex_g = fields.Html(string="Annex G Template")
    ji_annex_h = fields.Html(string="Annex H Template")
    ji_percent_moratorium = fields.Float(string="Percent Moratorium")
    tz = fields.Selection(related="partner_id.tz", string="TZ", readonly=False)
    ji_code = fields.Text(string="Code", default="result = 1")
    ji_codev = fields.Text(string="Code Fondo", default="result = 1")

    @api.constrains('ji_code')
    def _check_python_ji_code(self):
        for action in self.sudo().filtered('ji_code'):
            msg = test_python_expr(expr=action.ji_code.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    def migrate_commercial(self):
        sales = self.env['sale.order'].search([('user_id', '!=', False)])
        for sale in sales:
            sale.partner_id.write({"user_id": sale.user_id.id})

    def migrate_old_sequences(self, account_moves):
        def list_duplicates(seq):
            seen = set()
            seen_add = seen.add
            seen_twice = set(x for x in seq if x in seen or seen_add(x))
            return list(seen_twice)

        for move in account_moves:
            value_amounts = move.invoice_payment_term_id.line_ids.mapped('value_amount')
            value_amounts = list_duplicates(value_amounts)
            for avalue in value_amounts:
                amount_by_percent = round((avalue / 100) * move.amount_total, 2)
                payment_lines = move.invoice_payment_term_id.line_ids.filtered(lambda pl: pl.value_amount == avalue)
                move_lines = move.line_ids.filtered(
                    lambda ml: ml.debit == amount_by_percent and ml.account_id.code == '121000')
                ob_pay_line = False
                for index in range(0, len(move_lines)):
                    if index <= len(payment_lines) - 1:
                        ob_pay_line = payment_lines[index].id
                    move_lines[index].write({'ji_term_line_id': ob_pay_line})
            move._compute_ji_json_numbers()
            move.line_ids._compute_ji_sequence_payments()
            move.line_ids._compute_ji_number()
