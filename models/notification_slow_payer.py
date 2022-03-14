# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime


class NotificationSlowPayer(models.Model):
    _name = "ji.notification.slow.payer"
    _description = "Notification Slow Payer"

    name = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    company_id = fields.Many2one(comodel_name="res.company", string="Company", default=lambda self: self.env.company)
    notification_lines = fields.One2many(comodel_name="ji.notification.slow.payer.line", string="Notification Lines",
                                         inverse_name="notification_id")
    partner_ids = fields.Many2many(comodel_name="res.partner", string="Partners To Notification",
                                   default=lambda self: self.env.company.ji_partner_ids, required=True)
    active = fields.Boolean(string="Active", default=True)
    object = fields.Char(string="Asunto Correo", required=True)
    is_mora = fields.Boolean(string="Es Vencido?")
    is_estado = fields.Boolean(string="Son Estado(Fiscal, Legal, Cuenta)")


    recurrencia = fields.Selection([

        ('semana', 'Dia de la semana'),
        ('mes', 'Un dia de Mes'),
        ('periodo', 'Periodico en dias'),

    ], string='Recurrencia', required=True,
        help="Seleciona la recurrencia deceada.")

    type = fields.Selection([
        ('cliente', 'A Clientes'),
        ('cxc', 'Cuentas Por Cobrar'),
        ('cxp', 'Cuentas Por Pagar'),
        ('ventas', 'Ventas'),
        ('clien_estado', 'Cliente: Estado de Cuneta'),
        ('legal', 'Estdo Legal'),
        ('financiero', 'Estdo finacieros'),
    ], string='Tipo de correo', required=True
        )

    ji_models = fields.Selection([
        ('sale.order', 'Ventas'),
        ('account.move', 'Facturas'),
        # ('account.payment', 'Pagos'),

    ], string='Modelos', required=True,
        help="Seleciona modelo correspondiente.")


    def get_partner_ids(self):
        return str([partner.id for partner in self.partner_ids]).replace('[', '').replace(']', '')

    def send_notification(self):
        if not self.company_id.ji_mail_template.id:
            raise UserError(_('No Template configurated'))
        template = self.company_id.ji_mail_template
        if template:
            template.send_mail(self.id, force_send=True)

    @api.model
    def get_today_slow_payers(self):
        companies = self.env["res.company"].search([('ji_apply_developments', '=', True)])
        if len(companies.ids) == 0:
            raise UserError(_('No Apply for this companies'))
        partners = []
        for company in companies:
            partners_slow_payer = self.env['res.partner'].search(
                [('company_id', '=', company.id)]).get_partners_slow_payer_cron(company)
            for p in partners_slow_payer:
                number_slow_payer, amls = p.get_number_slow_payer_cron(company)
                if number_slow_payer >= company.ji_number_slow_payer:
                    partners.append({"partner": p, "amls": amls})
            if len(partners) > 0:
                notification_lines = []
                for partner in partners:
                    notification_lines.append([0, 0, {
                        "name": len(partner["amls"]),
                        "partner_id": partner["partner"].id,
                        'unreconciled_aml_dues': [(6, 0, [m.id for m in partner["amls"]])],
                    }])
                vals = {
                    "name": datetime.now(),
                    "company_id": company.id,
                    "notification_lines": notification_lines,
                    "partner_ids": company.ji_partner_ids
                }
                notification = self.create(vals)
                notification.send_notification()

    class NotificationSlowPayerLine(models.Model):
        _name = "ji.notification.slow.payer.line"
        _description = "Lines for Notification Slow Payer"

        name = fields.Integer(string="Numero en recurrencia")
        notification_id = fields.Many2one(comodel_name="ji.notification.slow.payer", string="Notification",
                                          ondelete="cascade")
        partner_id = fields.Many2one(comodel_name="res.partner", string="Customer")
        is_mora = fields.Boolean(string="Fecha Posterior?")
        unreconciled_aml_dues = fields.Many2many(comodel_name="account.move.line", string="Unreconciled Dues")
        text_unreconciled_aml_dues = fields.Text(string="Names Unreconciled Dues")

        def _compute_text_unreconciled_aml_dues(self):
            for line in self:
                line.text_unreconciled_aml_dues = str(
                    ["" + str(aml.name) + "-" + str(aml.ji_number) for aml in line.unreconciled_aml_dues]).replace('[',
                                                                                                            '').replace(
                    ']', '')

        def get_link_detail(self):
            action = self.env.ref('account_followup.action_view_list_customer_statements', False)
            menu = self.env.ref('account_followup.customer_statements_menu', False)

            link = "/web?#id={partner_id}&action={action_id}&model=res.partner&view_type=form&cids={company_id}" \
                   "&menu_id={menu_id}".format(partner_id=self.partner_id.id, action_id=action.id,
                                               company_id=self.notification_id.company_id.id, menu_id=menu.id)
            return self.env['ir.config_parameter'].sudo().get_param('web.base.url') + link
