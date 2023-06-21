from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, timedelta

class MoratorioAsiento(models.Model):
    _name = 'ji.mora.asiento'
    _description = 'Generar Reporte de Gastos'

    name = fields.Char(string="Name")
    date_i = fields.Date(string="Fecha Inicial")
    date_f = fields.Date(string="Fecha Final")

    Categorias = fields.Many2one(comodel_name="product.category", string="Categoria de Producto")

    def searchdat(self, purch):
        dev = 0.0
        for de in purch:
            dev += de.amount
        return dev

    def run(self):
        for res in self:
            Categorias = res.Categorias
            datef = res.date_f
            datei = res.date_i
            pay = self.env['account.payment']
            account = self.env['account.move.line']
            # account.categoria_venta()
            searmen = [
               ('categoria_producto','=',Categorias.id),
               ('state','=','posted'),
               ('payment_date', '>=', datei),
               ('payment_date', '<=', datef),
               ('payment_type', '=', 'inbound'),
               ('journal_id', '=', 8),


            ]
            searmenwf = [
               ('categoria_producto','=',Categorias.id),
               ('state','=','posted'),
               ('payment_date', '>=', datei),
               ('payment_date', '<=', datef),
               ('payment_type', '=', 'inbound'),
               ('journal_id', '=', 11),


            ]
            searant = [
                ('categoria_producto', '=', Categorias.id),
                ('state', '=', 'posted'),
                ('payment_date', '>=', datei),
                ('payment_date', '<=', datef),
                ('payment_type', '=', 'inbound'),
                ('journal_id', '=', 9),


            ]
            searantwf = [
                ('categoria_producto', '=', Categorias.id),
                ('state', '=', 'posted'),
                ('payment_date', '>=', datei),
                ('payment_date', '<=', datef),
                ('payment_type', '=', 'inbound'),
                ('journal_id', '=', 10),


            ]

            devent = [
               ('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),
                ('codigo_prod.code', '=', '101.01.001.3'),


            ]

            mensualidades = pay.search(searmen)
            mensualidadeswf = pay.search(searmenwf)
            anticipo = pay.search(searant)
            anticipowf = pay.search(searantwf)
            devent = pay.search(devent)

            mejor= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '501.01.01.01'),])
            seguridad= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '501.01.01.02'),])
            levantamientos= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '501.01.01.03'),])
            laboratorio= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '501.01.01.04'),])
            jardineria= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '501.01.01.05'),])
            topografia= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '501.01.01.06'),])
            otros_gastos= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '601.84.01.01'),])
            plan_maestro= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '601.84.01.02'),])
            obra= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '601.84.01.03'),])
            gastos_venta= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.01.01'),])
            promocion_publicidad= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.01.02'),])
            comisiones= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.01.03'),])
            predial= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.01.04'),])
            nomina= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.02.01'),])
            viaticos= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.02.02'),])
            dividendos= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.02.03'),])
            transporte= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.02.04'),])
            mensajeria= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.02.05'),])
            rentas= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.02.06'),])
            papeleria= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.02.07'),])
            servicios_oficina= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.02.08'),])
            telefonia_internet= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.02.09'),])
            gastos_varios= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.02.10'),])
            mantenimiento= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.02.11'),])
            honorarios= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.03.01'),])
            juzgado= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.03.02'),])
            apoyos= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.03.03'),])
            gastos_legales= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.03.04'),])
            gastos_legaleswf= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.03.05'),])
            indivi= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '602.02.03.06'),])
            otros_productos= pay.search([('state','=','posted'),('payment_date', '>=', datei),('payment_date', '<=', datef),('codigo_prod.code', '=', '601.84.01.04'),])

            mensu = 0
            mora = 0
            mensuwf = 0
            morawf = 0
            antic = 0
            anticwf = 0
            dev = 0
            ''' Mensualidades y moratorios
                incluyen wf
            '''

            for men in mensualidades:
                if men.codigo_prod:
                    if men.codigo_prod.code == '601.84.01.04':
                        mensu -= men.amount
                mensu += men.amount
                # an = self.env['account.payment'].search([('name', '=',men.name)])
                mora += float(men.ji_moratorio)


            for men in mensualidadeswf:
                if men.codigo_prod:
                    if men.codigo_prod.code == '601.84.01.04':
                        mensuwf -= men.amount
                mensuwf += men.amount
                # an = self.env['account.payment'].search([('name', '=', men.name)])
                morawf += float(men.ji_moratorio)

            ''' Anticipos
             incluyen wf
            '''
            ant_mora = 0
            for ant in anticipo:
                if ant.codigo_prod:
                    if ant.codigo_prod.code == '601.84.01.04':
                        antic -= ant.amount
                antic += ant.amount
                ant_mora += float(ant.ji_moratorio)

            ant_mora_wf = 0
            for ant in anticipowf:
                if ant.codigo_prod:
                    if ant.codigo_prod.code == '601.84.01.04':
                        anticwf -= ant.amount
                anticwf += ant.amount
                ant_mora_wf += float(ant.ji_moratorio)

            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': ('mejoras'),
                    'message': str(mensu) + " " + str(mensuwf) + " | "+str(antic) + " " + str(anticwf),
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            # return notification


            for de in devent:
                dev += de.amount
            mej = res.searchdat(mejor)
            seg = res.searchdat(seguridad)
            lev = res.searchdat(levantamientos)
            lab = res.searchdat(laboratorio)
            jar = res.searchdat(jardineria)
            topo = res.searchdat(topografia)
            otr_gast = res.searchdat(otros_gastos)
            plan_maes = res.searchdat(plan_maestro)
            obra = res.searchdat(obra)
            Gast_vent = res.searchdat(gastos_venta)
            prom_pub = res.searchdat(promocion_publicidad)
            comis = res.searchdat(comisiones)
            predi = res.searchdat(predial)
            nomina = res.searchdat(nomina)
            viati = res.searchdat(viaticos)
            divid = res.searchdat(dividendos)
            trans = res.searchdat(transporte)
            mensj = res.searchdat(mensajeria)
            rentas = res.searchdat(rentas)
            papel = res.searchdat(papeleria)
            serv_ofic = res.searchdat(servicios_oficina)
            tel_inter = res.searchdat(telefonia_internet)
            gast_var = res.searchdat(gastos_varios)
            mant = res.searchdat(mantenimiento)

            honor = res.searchdat(honorarios)
            juzg = res.searchdat(juzgado)
            apoyos = res.searchdat(apoyos)
            gast_leg = res.searchdat(gastos_legales)
            gast_legwf = res.searchdat(gastos_legaleswf)
            indivi = res.searchdat(indivi)
            otr_prod = res.searchdat(otros_productos)


            vent_net = mensu + mensuwf + mora + morawf + antic + anticwf + ant_mora + ant_mora_wf - dev
            cost_vent = mej + seg + lev + lab + jar + topo
            util_perd_bru = vent_net - cost_vent
            Gast_ventg = Gast_vent + prom_pub + comis + predi
            gast_admin = nomina + trans + mensj + rentas +  papel + serv_ofic +  tel_inter + gast_var + mant
            gas_cons = viati + divid
            gas_leg = honor + juzg +apoyos + gast_leg + gast_legwf + indivi
            util_perd_oper= util_perd_bru - Gast_ventg - gast_admin - gas_cons - gas_leg
            otrs_gast = otr_gast + plan_maes + obra
            otrs_prod = otr_prod
            util_perd_ejer = util_perd_oper - otrs_gast + otrs_prod

            egre= cost_vent + Gast_ventg + gast_admin + gas_cons + gas_leg + otrs_gast
            por=0
            data = {
               'categoria': Categorias.name,
               'por': por,
               'datei': datei.strftime('%d-%m-%y'),
               'datef': datef.strftime('%d-%m-%y'),
               'mens': "$ {0:,.2f}".format(mensu),
               'menswf': "$ {0:,.2f}".format(mensuwf),
               'mora': "$ {0:,.2f}".format(mora),
               'morawf': "$ {0:,.2f}".format(morawf),
               'anticipo': "$ {0:,.2f}".format(antic),
               'anticipowf': "$ {0:,.2f}".format(anticwf),
               'ant_mora': "$ {0:,.2f}".format(ant_mora),
               'ant_mora_wf': "$ {0:,.2f}".format(ant_mora_wf),
               'dev': "$ {0:,.2f}".format(dev),
               'ven_net': "$ {0:,.2f}".format(vent_net),
               'ven_net_o': "$ {0:,.2f}".format(vent_net + otr_prod),
               'mejoras': "$ {0:,.2f}".format(mej),
               'seguridad': "$ {0:,.2f}".format(seg),
               'levant': "$ {0:,.2f}".format(lev),
               'labora': "$ {0:,.2f}".format(lab),
               'jardin': "$ {0:,.2f}".format(jar),
               'topog': "$ {0:,.2f}".format(topo),
               'cost_vent': "$ {0:,.2f}".format(cost_vent),
               'util_perd_bru': "$ {0:,.2f}".format(util_perd_bru),
               'Gast_vent': "$ {0:,.2f}".format(Gast_vent),
               'prom_pub': "$ {0:,.2f}".format(prom_pub),
               'comis': "$ {0:,.2f}".format(comis),
               'predi': "$ {0:,.2f}".format(predi),
               'Gast_ventg': "$ {0:,.2f}".format(Gast_ventg),
               'gast_admin': "$ {0:,.2f}".format(gast_admin),
               'nomina': "$ {0:,.2f}".format(nomina),
               'trans': "$ {0:,.2f}".format(trans),
               'mensj': "$ {0:,.2f}".format(mensj),
               'rentas': "$ {0:,.2f}".format(rentas),
               'papel': "$ {0:,.2f}".format(papel),
               'serv_ofic': "$ {0:,.2f}".format(serv_ofic),
               'tel_inter': "$ {0:,.2f}".format(tel_inter),
               'gast_var': "$ {0:,.2f}".format(gast_var),
               'mant': "$ {0:,.2f}".format(mant),
               'gas_cons': "$ {0:,.2f}".format(gas_cons),
               'viati': "$ {0:,.2f}".format(viati),
               'divid': "$ {0:,.2f}".format(divid),
               'gas_leg': "$ {0:,.2f}".format(gas_leg),
               'honor': "$ {0:,.2f}".format(honor),
               'juzg': "$ {0:,.2f}".format(juzg),
               'apoyos': "$ {0:,.2f}".format(apoyos),
               'gast_leg': "$ {0:,.2f}".format(gast_leg),
               'gast_legwf': "$ {0:,.2f}".format(gast_legwf),
               'indivi': "$ {0:,.2f}".format(indivi),
               'util_perd_oper': "$ {0:,.2f}".format(util_perd_oper),
               'otrs_gast': "$ {0:,.2f}".format(otrs_gast),
               'otr_gast': "$ {0:,.2f}".format(otr_gast),
               'plan_maes': "$ {0:,.2f}".format(plan_maes),
               'obra': "$ {0:,.2f}".format(obra),
               'otrs_prod': "$ {0:,.2f}".format(otrs_prod),
               'otr_prod': "$ {0:,.2f}".format(otr_prod),
               'util_perd_ejer': "$ {0:,.2f}".format(util_perd_ejer),
               'egre': "$ {0:,.2f}".format(egre),
               'resul': "$ {0:,.2f}".format(vent_net + otrs_prod - egre),
               'dif': "$ {0:,.2f}".format(vent_net - egre - util_perd_ejer + otrs_prod),

            }
            return self.env.ref('jibaritolotes.report_gastos').report_action(self, data=data)

class tranfermoratorio(models.Model):
    _name = 'ji.mora.tranfer'
    _description = 'Tranferir Moratorio'

    name = fields.Float(string="Monto a transferir", compute="buscar")
    mora = fields.Float(string="Monto Mora a transferir", compute="buscar")
    date_i = fields.Date(string="Fecha Inicial")
    date_f = fields.Date(string="Fecha Final")
    diario = fields.Many2one(comodel_name="account.journal", string="Diario Origen")
    diario_des = fields.Many2one(comodel_name="account.journal", string="Diario Destino")

    @api.depends("date_i", "date_f", "diario")
    @api.onchange("date_i", "date_f", "diario")
    def buscar(self):
        for res in self:
            date_i = res.date_i
            date_f = res.date_f
            diario = res.diario

            payment = self.env['account.payment'].sudo().search([
                ('payment_date', '>=', date_i),
                ('payment_date', '<=', date_f),
                ('trasnfer', '=', False),
                ('state', '=', 'posted'),
                ('journal_id', '=', diario.id)])
            mora=0
            importe = 0

            for pay in payment:
                mora += pay.ji_moratorio
                importe += pay.amount

            res.name = importe
            res.mora = mora

    def create_data(self):
        for res in self:
            date_i = res.date_i
            date_f = res.date_f
            diario = res.diario
            diariod = res.diario_des

            mora = {
                'partner_id': 1,
                'company_id': 1,
                "amount": res.mora,
                "communication": "Tranfer Interna",
                "payment_type": "inbound",
                "partner_type": "supplier",
                "journal_id": diariod.id,
                "payment_method_id":1,
                "trasnfer": True,
            }

            mensual = {
                "amount": res.name,
                "communication": "Tranfer Interna",
                "payment_type": "transfer",
                "partner_type": "supplier",
                "journal_id": diario.id,
                "destination_journal_id": diariod.id,
                "payment_method_id": 1,
                "trasnfer": True,
            }


            # raise UserError(_(mora))



            pagos= self.env['account.payment']

            moratorio=pagos.create(mora)
            moratorio.post()
            trasfin = pagos.create(mensual)
            trasfin.post()

            payment = self.env['account.payment'].sudo().search([
                ('payment_date', '>=', date_i),
                ('payment_date', '<=', date_f),
                ('trasnfer', '=', False),
                ('state', '=', 'posted'),
                ('journal_id', '=', diario.id)])

            for pay in payment:
                pay.trasnfer = True
