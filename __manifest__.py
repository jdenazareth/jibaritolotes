# -*- coding: utf-8 -*-
{
    # App information
    "name": "Moratorias Jibarito - MX",
    "category": "Tools",
    "summary": "Desarrollos para la compañia Jibarito.",
    "version": "13.0.2",
    "website": "https://www.pragmatic.com.pe/",
    "contributors": [
        "Catalica",
        "Kelvin Meza <kmeza@pragmatic.com.pe>",
    ],
    "depends": [
        'base',
        "base_setup",
       # "account_followup",
        "sale",
        "hr",
        "stock",
        "account",
        "contacts"
    ],
    "data": [
        "security/security.xml",
        "views/res_config_settings.xml",
        "views/notification_slow_payer.xml",
        "views/estados.xml",

        "security/ir.model.access.csv",

        "data/ir_cron.xml",
        "data/mail_template.xml",
        "data/function.xml",
        "report/sale_order_contract.xml",
        #"views/account_followup_views.xml",
        "views/res_partner.xml",
        "views/res_company.xml",

        "views/sale_order.xml",
        "views/product_product.xml",
        "views/product_template.xml",
        "views/lotes.xml",
        "views/manzana.xml",
        "views/calle.xml",
        "views/account_payment_term.xml",
        # "views/moratorium_interest.xml",
        "views/account_move.xml",
        "views/template_apartado.xml",
        "views/templatesdevo.xml",
        "views/template_carta_cartera.xml",
        "views/template_carta_invacion.xml",
        "views/template_finiquito.xml",
        "views/template_entrega.xml",
        "views/template_cesion_derechos.xml", 
        "views/template_acuse_entrega.xml",
        "views/template_contrato_transaccion.xml",
        "report/account_report.xml",
        "report/account_payment.xml",
        "report/report_amortizacion.xml",
        "views/hr_employee.xml",
        "wizard/asiento_mora.xml",


    ],
    "images": [
    ],

    "author": "Pragmatic S.A.C",
    "website": "pragmatic.com.pe",
    "maintainer": "Pragmatic S.A.C.",
    "installable": True,
    "auto_install": False,
    "application": True,
}
