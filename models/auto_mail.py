
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo import api, exceptions ,models, fields, _
from odoo.exceptions import UserError
import numpy
from dateutil import rrule
from odoo import SUPERUSER_ID
from odoo.http import request
import requests
from odoo.tools.safe_eval import safe_eval, test_python_expr
import json
import base64
from io import StringIO
import logging
import pathlib
import os

import openpyxl
from openpyxl.styles import Border, Font, Alignment


class Notimove(models.Model):
    _inherit ="account.move"

    def ks_apply_style(self, ks_cell, kc='', vc='', sz=False, wp=False):
        ks_cell.alignment = Alignment(horizontal="center" if kc else '', vertical="center" if vc else '',
                                      wrap_text=wp)
        if sz: ks_cell.font = Font(b=True, size=sz)

    def Cxp_create_workbook_header(self, report_name, sheet):
        sheet.title = str(report_name)

        sheet['A1'] = "Nombre Proveedor"
        self.ks_apply_style(sheet['A1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

        sheet['B1'] = "Descripcion"
        self.ks_apply_style(sheet['B1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

        sheet['C1'] = "Cuenta"
        self.ks_apply_style(sheet['C1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

        sheet['D1'] = "Fecha"
        self.ks_apply_style(sheet['D1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

        sheet['E1'] = "Monto Residual"
        self.ks_apply_style(sheet['E1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

        sheet['F1'] = "Monto Total"
        self.ks_apply_style(sheet['F1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

    def Cxc_create_workbook_header(self, report_name, sheet):
        sheet.title = str(report_name)

        sheet['A1'] = "Nombre Proveedor"
        self.ks_apply_style(sheet['A1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

        sheet['B1'] = "Manzana"
        self.ks_apply_style(sheet['B1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

        sheet['C1'] = "Lote"
        self.ks_apply_style(sheet['C1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

        sheet['D1'] = "Contrato"
        self.ks_apply_style(sheet['D1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

        sheet['E1'] = "Fecha de Vencimiento"
        self.ks_apply_style(sheet['E1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

        sheet['F1'] = "Meses vencidos"
        self.ks_apply_style(sheet['F1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

        sheet['G1'] = "Audeudo con mora"
        self.ks_apply_style(sheet['G1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

        sheet['H1'] = "Saldo Insoluto"
        self.ks_apply_style(sheet['H1'], True, True, 12, True)
        sheet.merge_cells(start_row=1, end_row=1, start_column=1, end_column=1)

    @api.model
    def generate_mail_cxp(self):
        busqueda = self.env['ji.notification.slow.payer'].search([('ji_models', '=', 'account.move')])
        for noti in busqueda:
            today = fields.Date.context_today(self)
            if noti.active and noti.type == 'cxp':


                for lines in noti.notification_lines:
                    factu = self.env['account.move'].search(
                            [('type', '=', 'in_invoice'), ('state', '=', 'posted'), ('invoice_payment_state','!=', 'paid')])
                    if lines.partner_id:
                        factu = self.env['account.move'].search(
                            [('type', '=', 'in_invoice'), ('state', '=', 'posted'),('partner_id','=',lines.partner_id.id),('invoice_payment_state','!=', 'paid')])


                    template_id = self.env['ir.model.data'].get_object_reference('jibaritolotes','mail_template_slow_payer_cxp')[1]

                    email_object = self.env['mail.template'].browse(template_id)


                    #raise UserError(_(f'DATOS {factu}'))
                    if template_id:
                        data = []
                        mail_from = ""
                        ids= 0
                        report_name = "Cuentas por Pagar"
                        workbook = openpyxl.Workbook()

                        sheet = workbook.active

                        self.Cxp_create_workbook_header(report_name, sheet)
                        i = 1
                        row = 2
                        col = 0
                        for account in factu:

                            mail_from = account.company_id.partner_id.email
                            ids = account.id
                            sheet.cell(row, 1, account.partner_id.name)

                            # linea facturable
                            desc = ""
                            accu = ""
                            for linea in account.invoice_line_ids:
                                desc = linea.name
                                accu = linea.account_id.name

                            sheet.cell(row, 2, desc)
                            sheet.cell(row, 3, accu)
                            sheet.cell(row, 4, account.date)
                            sheet.cell(row, 5, account.amount_residual)
                            sheet.cell(row, 6, account.amount_total)
                            row += 1
                            i += 1
                        output = StringIO()
                        # tupla = numpy.asarray(data)
                        #raise UserError(_(f'DATOS {tupla}'))
                        # numpy.savetxt('/tmp/file.csv', tupla, delimiter=";", newline="\n", fmt="%s")
                        lectura = ""
                        # with open("/tmp/file.csv", "rb") as rfile:
                            #encoded = base64.b64encode(rfile.read())
                            #
                            # lectura= rfile.read()
                        # data_record = base64.encodebytes((lectura).encode())
                        filename = ('/tmp/' + str(report_name) + '.xlsx')
                        workbook.save(filename)
                        fp = open(filename, "rb")
                        file_data = fp.read()
                        data_record = base64.b64encode(file_data)
                        att = {
                                'name': str(report_name) + '.xlsx',
                                'type': 'binary',
                                'datas': data_record,
                                'store_fname': data_record,
                                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            }
                        data_id = self.env['ir.attachment'].create(att)

                        value = email_object.generate_email(ids)

                        value['email_from'] = mail_from
                        # value['email_to'] = partner.email
                        value['email_to'] = str([partner.email for partner in noti.partner_ids]).replace('[', '').replace(']', '').replace("'","")
                        value['subject'] = noti.object
                        # raise UserError(_(value['email_to']))
                        value['attachment_ids'] = [(6,0, [data_id.id])]
                        # value['model_id'] = 'account.move'
                        value['author_id'] = self.env['res.users'].browse(request.env.uid).partner_id.id
                        mail_mail_obj = self.env['mail.mail']
                        # raise UserError(_(str([partner.id for partner in noti.partner_ids]).replace('[', '').replace(']', '')))
                        msg_id = mail_mail_obj.sudo().create(value)

                        mail_mail_obj.send([msg_id])
                        mail_mail_obj.send(msg_id)
    @api.model
    def prueba_whasthapp(self):
        url = "https://api.apichat.io/v1/sendText"
        headers = {
            "Content-Type": "application/json",
            "client-id": "21746",
            "token": "hnw36fDy44HL"
        }
        body = {"number": "5215581692962", "text": "Que onda aprin debes $45000!  🤝"}

        requests.post(url, json=body, headers=headers)
    @api.model
    def generate_mail_cxc(self):

        busqueda = self.env['ji.notification.slow.payer'].search([('ji_models', '=', 'account.move')])
        for noti in busqueda:

            today = fields.Date.context_today(self)
            if noti.active and noti.type == 'cxc':

                for lines in noti.notification_lines:

                    busqueda = [('type', '=', 'out_invoice'), ('state', '=', 'posted'),('invoice_payment_state', '!=', 'paid') ]

                    if lines.partner_id:
                        busqueda.append(('partner_id', '=', lines.partner_id.id))
                    if noti.is_mora:
                        busqueda.append(('ji_is_moratorium', '=', noti.is_mora))
                    factu = self.env['account.move'].search(busqueda)
                    template_id = self.env['ir.model.data'].get_object_reference('jibaritolotes', 'mail_template_cuenta_cobrar')[1]

                    email_object = self.env['mail.template'].browse(template_id)

                    # raise UserError(_(f'DATOS {factu}'))
                    if template_id:
                        data = []
                        mail_from = ""
                        ids = 0
                        report_name = "Cuentas por Cobrar"
                        workbook = openpyxl.Workbook()

                        sheet = workbook.active

                        self.Cxc_create_workbook_header(report_name, sheet)
                        i = 1
                        row = 2
                        col = 0

                        for account in factu:
                            account.action_moratorio_v()
                            mail_from = account.company_id.partner_id.email
                            ids = account.id
                            sheet.cell(row, 1, account.partner_id.name)

                            # linea facturable
                            date_ultpay = fields.Date.from_string(account.proxfecha_venci)
                            total = account.amount_residual + account.total_moratorium

                            sheet.cell(row, 2, account.x_studio_manzana.name)
                            sheet.cell(row, 3, account.x_studio_lote.name)
                            sheet.cell(row, 4, account.name)
                            sheet.cell(row, 5, date_ultpay)
                            sheet.cell(row, 6, account.total_mes)
                            sheet.cell(row, 7, account.saldo_pend)
                            sheet.cell(row, 8,total)
                            row += 1
                            i += 1
                        output = StringIO()
                        # tupla = numpy.asarray(data)
                        # raise UserError(_(f'DATOS {tupla}'))
                        # numpy.savetxt('/tmp/file.csv', tupla, delimiter=";", newline="\n", fmt="%s")
                        lectura = ""
                        # with open("/tmp/file.csv", "rb") as rfile:
                        # encoded = base64.b64encode(rfile.read())
                        #
                        # lectura= rfile.read()
                        # data_record = base64.encodebytes((lectura).encode())
                        filename = ('/tmp/' + str(report_name) + '.xlsx')
                        workbook.save(filename)
                        fp = open(filename, "rb")
                        file_data = fp.read()
                        data_record = base64.b64encode(file_data)
                        att = {
                            'name': str(report_name) + '.xlsx',
                            'type': 'binary',
                            'datas': data_record,
                            'store_fname': data_record,
                            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        }
                        data_id = self.env['ir.attachment'].create(att)

                        value = email_object.generate_email(ids)

                        value['email_from'] = mail_from
                        # value['email_to'] = partner.email
                        value['email_to'] = str([partner.email for partner in noti.partner_ids]).replace('[',
                                                                                                         '').replace(
                            ']', '').replace("'", "")
                        value['subject'] = noti.object
                        # raise UserError(_(value['email_to']))
                        value['attachment_ids'] = [(6, 0, [data_id.id])]
                        # value['model_id'] = 'account.move'
                        value['author_id'] = self.env['res.users'].browse(request.env.uid).partner_id.id
                        mail_mail_obj = self.env['mail.mail']
                        # raise UserError(_(str([partner.id for partner in noti.partner_ids]).replace('[', '').replace(']', '')))
                        msg_id = mail_mail_obj.sudo().create(value)

                        mail_mail_obj.send([msg_id])
                        mail_mail_obj.send(msg_id)

    @api.model
    def generate_mail_move(self):
        #su_id = self.env['account.move'].browse(SUPERUSER_ID)

        busqueda = self.env['ji.notification.slow.payer'].search([('ji_models', '=', 'account.move')])
        for noti in busqueda:
            today = fields.Date.context_today(self)
            if noti.active and noti.type == 'cliente':
            
                for lines in noti.notification_lines:
                    factu = self.env['account.move'].search(
                            [('type', '=', 'out_invoice'), ('state', '=', 'posted'), ])
                    if lines.partner_id:
                        factu = self.env['account.move'].search(
                            [('type', '=', 'out_invoice'), ('state', '=', 'posted'),('partner_id','=',lines.partner_id.id), ])
                    for account in factu:
                        partner = account.partner_id

                        date_ultpay = fields.Date.from_string(account.proxfecha_venci)
                        # date_ultpay -= relativedelta(months=account.total_mes)
                        con = False

                        if noti.recurrencia == 'semana':
                                date_ultpay = date_ultpay
                                con = today.strftime("%w") == lines.name

                        elif noti.recurrencia == 'mes':
                            if lines.is_mora:
                                # date_ultpay -= relativedelta(months=account.total_mes)
                                # date_ultpay += relativedelta(months=lines.name)
                                # date_ultpay = date_ultpay.date()
                                if lines.name == today.day:
                                    con = True
                            else:
                                date_ultpay -= relativedelta(months=lines.name)
                                date_ultpay = date_ultpay
                                if lines.name == today.day and date_ultpay.month == today.month:
                                    con = True


                        elif noti.recurrencia == 'periodo':
                            if lines.is_mora:
                                date_ultpay += relativedelta(day=lines.name)
                                date_ultpay = date_ultpay.date()
                                con = date_ultpay == today
                            else:
                                date_ultpay -= relativedelta(day=lines.name)
                                date_ultpay = date_ultpay.date()
                                con = date_ultpay == today

                        #
                        template_id = self.env['ir.model.data'].get_object_reference('jibaritolotes','paltilla_factura_atraso')[1]
                        #
                        email_object = self.env['mail.template'].browse(template_id)

                        if template_id and con:
                            value = email_object.generate_email(account.id)
                            value['email_from'] = account.company_id.partner_id.email
                            value['email_to'] = partner.email
                            # value['partner_to'] = str([partner.id for partner in noti.partner_ids]).replace('[', '').replace(']', '')
                            value['subject'] = noti.object
                            # value['model_id'] = 'account.move'
                            value['author_id'] = self.env['res.users'].browse(request.env.uid).partner_id.id
                            mail_mail_obj = self.env['mail.mail']
                            # raise UserError(_(str([partner.id for partner in noti.partner_ids]).replace('[', '').replace(']', '')))
                            msg_id = mail_mail_obj.sudo().create(value)
                            if msg_id:
                                mail_mail_obj.sudo().send([msg_id])
                            
    @api.model
    def generate_email_etado_cuenta(self):
        # self.prueba_whasthapp()
        busqueda = self.env['ji.notification.slow.payer'].search([('ji_models', '=', 'account.move')])
        for noti in busqueda:
            today = fields.Date.context_today(self)
            if noti.active and noti.type == 'clien_estado':

                for lines in noti.notification_lines:
                    busqueda = [('type', '=', 'out_invoice'), ('state', '=', 'posted'), ]

                    if lines.partner_id:
                            busqueda.append(('partner_id', '=', lines.partner_id.id))
                    if noti.is_mora:
                        busqueda.append(('ji_is_moratorium', '=', noti.is_mora))
                    factu = self.env['account.move'].search(busqueda)
                    for account in factu:
                        partner = account.partner_id

                        date_ultpay = fields.Date.from_string(account.proxfecha_venci)
                        # date_ultpay -= relativedelta(months=account.total_mes)
                        con = False

                        if noti.recurrencia == 'semana':
                            date_ultpay = date_ultpay
                            if today.strftime("%w") == lines.name:
                                con = True
                        elif noti.recurrencia == 'mes':
                                if lines.name == today.day:
                                    con = True
                        elif noti.recurrencia == 'periodo':

                                date_ultpay -= relativedelta(months=1)
                                date_ultpay += timedelta(days=1)
                                if date_ultpay == today:
                                    con = True

                        #
                        template_id = self.env['ir.model.data'].get_object_reference('jibaritolotes', 'mail_template_estado_cuenta')[1]
                        #
                        email_object = self.env['mail.template'].browse(template_id)
                        # raise UserError(_(str(con)))
                        if template_id and con:

                            document = factu.get_reporte_amoritizacionv2_pdf(account)

                            data_record = base64.b64encode(document[0])
                            ir_values = {
                                'name': "Estado de Cuenta",
                                'type': 'binary',
                                'datas': data_record,
                                'store_fname': data_record,
                                'mimetype': 'application/x-pdf',
                            }
                            data_id = self.env['ir.attachment'].create(ir_values)
                            email_object.partner_to = str([partner.id for partner in noti.partner_ids]).replace('[', '').replace(']', '').replace("'","")
                            value = email_object.generate_email(account.id)
                            value['email_from'] = account.company_id.partner_id.email
                            value['email_to'] = partner.email
                            value['recipient_ids'] = noti.partner_ids
                            value['subject'] = noti.object
                            # value['model_id'] = 'account.move'
                            value['attachment_ids'] = [(6, 0, [data_id.id])]
                            value['author_id'] = self.env['res.users'].browse(request.env.uid).partner_id.id
                            mail_mail_obj = self.env['mail.mail']
                            # raise UserError(_(str([partner.id for partner in noti.partner_ids]).replace('[', '').replace(']', '')))
                            msg_id = mail_mail_obj.sudo().create(value)
                            if msg_id:
                                mail_mail_obj.sudo().send([msg_id])
