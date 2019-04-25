# -*- coding: utf-8 -*-
{
    'name': 'lgps',
    'description': 'Intralix module for internal processes',
    'author': 'Intralix',
    'application': True,
    'website': 'https://www.intralix.com',
    'category': 'Uncategorized',
    'version': '0.0.7',
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
        'reports/suscription_detail_condensed.xml',
        'views/lgps_main_menu.xml',
        'views/gpsdevice.xml',
        'views/cellchip.xml',
        'views/partner.xml',
        'views/accessory.xml',
        'views/assign_accesories_wizard.xml',
        'views/suscription.xml',
        'views/suscription_tree_view.xml',
        'views/suscription_custom_list_view.xml',
        'views/tracking.xml',
        'views/odt.xml',
        'views/lead.xml',
        'views/tickets.xml',
        'views/drop_device_wizard.xml',
        'views/res_config_settings_views.xml',
    ],
}
