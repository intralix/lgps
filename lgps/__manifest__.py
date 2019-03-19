# -*- coding: utf-8 -*-
{
    'name': 'lgps',
    'author': 'Intralix',
    'website': 'https://www.intralix.com',
    'category': 'Uncategorized',
    'version': '0.0.6',
    'depends': [
        'base',
        'stock',
        'contacts',
        'account',
        'repair',
        'crm',
        'sale_subscription',
        'helpdesk',
        'mail'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'reports/devices.xml',
        'reports/suscriptions_detail.xml',
        'views/lgps_main_menu.xml',
        'views/gpsdevice.xml',
        'views/cellchip.xml',
        'views/partner.xml',
        'views/accessory.xml',
        'views/wizard.xml',
        'views/suscription.xml',
        'views/tracking.xml',
        'views/odt.xml',
        'views/lead.xml',
        'views/tickets.xml',
        'views/drop_device_wizard.xml',
        'views/res_config_settings_views.xml'
    ],
}
