from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, timedelta

class MoratorioAsiento(models.Model):
    _name = 'ji.mora.asiento'
    _description = 'Generar Reporte de Gastos'

    name = fields.Char(string="Name")
    date_i = fields.Date(string="Fecha Inicial")
    date_f = fields.Date(string="Fecha Final")

    def searchdat(self, purch):
        dev = 0.0
        for de in purch:
            dev += de.debit
        return dev

    def run(self):
        for res in self:
            datef = res.date_f
            datei = res.date_i
            account = self.env['account.move.line']
            searmen = [
               ('date', '>=', datei),
               ('date', '<=', datef),
               ('account_id.code', '=', '101.01.001.1'),

            ]
            searmenwf = [
               ('date', '>=', datei),
               ('date', '<=', datef),
               ('account_id.code', '=', '101.01.001.4'),

            ]
            searant = [
               ('date', '>=', datei),
               ('date', '<=', datef),
               ('account_id.code', '=', '101.01.001.2'),

            ]
            searantwf = [
               ('date', '>=', datei),
               ('date', '<=', datef),
               ('account_id.code', '=', '101.01.001.5'),

            ]

            devent = [
               ('date', '>=', datei),
               ('date', '<=', datef),
               ('account_id.code', '=', '101.01.001.3'),

            ]

            mensualidades = account.search(searmen)
            mensualidadeswf = account.search(searmenwf)
            anticipo = account.search(searant)
            anticipowf = account.search(searantwf)
            devent = account.search(devent)

            mejor= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '501.01.01.01'),])
            seguridad= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '501.01.01.02'),])
            levantamientos= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '501.01.01.03'),])
            laboratorio= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '501.01.01.04'),])
            jardineria= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '501.01.01.05'),])
            topografia= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '501.01.01.06'),])
            otros_gastos= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '601.84.01.01'),])
            plan_maestro= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '601.84.01.02'),])
            obra= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '601.84.01.03'),])
            gastos_venta= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.01.01'),])
            promocion_publicidad= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.01.02'),])
            comisiones= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.01.03'),])
            predial= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.01.04'),])
            nomina= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.02.01'),])
            viaticos= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.02.02'),])
            dividendos= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.02.03'),])
            transporte= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.02.04'),])
            mensajeria= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.02.05'),])
            rentas= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.02.06'),])
            papeleria= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.02.07'),])
            servicios_oficina= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.02.08'),])
            telefonia_internet= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.02.09'),])
            gastos_varios= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.02.10'),])
            mantenimiento= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.02.11'),])
            honorarios= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.03.01'),])
            juzgado= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.03.02'),])
            apoyos= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.03.03'),])
            gastos_legales= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.03'),])
            gastos_legaleswf= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.03.05'),])
            indivi= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '602.02.03.06'),])
            otros_productos= account.search([('date', '>=', datei), ('date', '<=', datef), ('account_id.code', '=', '601.84.01.04'),])

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
               mensu += men.debit
               an = self.env['account.payment'].search([('name', '=',men.name)])
               mora += float(an[0].ji_moratorio)


            for men in mensualidadeswf:
               mensuwf += men.debit
               an = self.env['account.payment'].search([('name', '=', men.name)])
               morawf += float(an[0].ji_moratorio)

            ''' Anticipos
             incluyen wf
            '''

            for ant in anticipo:
               antic += ant.debit


            for ant in anticipowf:
               anticwf += ant.debit


            for de in devent:
                dev += de.debit
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

            notification = {
               'type': 'ir.actions.client',
               'tag': 'display_notification',
               'params': {
                   'title': ('mejoras'),
                   'message': str(mej),
                   'type': 'success',  # types: success,warning,danger,info
                   'sticky': True,  # True/False will display for few seconds if false
               },
            }
            # return notification
            vent_net = mensu + mensuwf + mora + morawf + antic + anticwf - dev
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
               'por': por,
               'datei': datei.strftime('%d-%m-%y'),
               'datef': datef.strftime('%d-%m-%y'),
               'mens': "$ {0:,.2f}".format(mensu),
               'menswf': "$ {0:,.2f}".format(mensuwf),
               'mora': "$ {0:,.2f}".format(mora),
               'morawf': "$ {0:,.2f}".format(morawf),
               'anticipo': "$ {0:,.2f}".format(antic),
               'anticipowf': "$ {0:,.2f}".format(anticwf),
               'dev': "$ {0:,.2f}".format(dev),
               'ven_net': "$ {0:,.2f}".format(vent_net),
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
               'resul': "$ {0:,.2f}".format(vent_net - egre),
               'dif': "$ {0:,.2f}".format(vent_net - egre - util_perd_ejer),

            }
            return self.env.ref('jibaritolotes.report_gastos').report_action(self, data=data)