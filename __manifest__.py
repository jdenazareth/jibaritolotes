# -*- coding: utf-8 -*-
{
    # App information
    "name": "Moratorias Jibarito - MX",
    "category": "Tools",
    "summary": "Desarrollos para la compañia Jibarito.",
    "version": "13.0.1",
    "license": "OPL-1",
    "website": "https://www.pragmatic.com.pe/",
    "contributors": [
        "Catalica",
        "Kelvin Meza <kmeza@pragmatic.com.pe>",
    ],
    "depends": [
        "base_setup",
       # "account_followup",
        "sale",
        "hr"
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        #"data/ir_cron.xml",
        #"data/mail_template.xml",
        "data/function.xml",
        "report/sale_order_contract.xml",
        "views/res_config_settings.xml",
        #"views/account_followup_views.xml",
        "views/res_partner.xml",
        "views/res_company.xml",
        #"views/notification_slow_payer.xml",
        "views/sale_order.xml",
        "views/product_product.xml",
        "views/product_template.xml",
        "views/estados.xml",
        "views/account_payment_term.xml",
        "views/moratorium_interest.xml",
        "views/account_move.xml",
        "report/account_payment.xml",
        "views/hr_employee.xml",

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
