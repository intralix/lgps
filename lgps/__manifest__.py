# -*- coding: utf-8 -*-
{
    'name': 'lgps',
    'author': 'Intralix',
    'website': 'https://www.intralix.com',
    'category': 'Uncategorized',
    'version': '0.0.2',
    'depends': [
        'base',
        'stock',
        'contacts',
        'account',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'reports/devices.xml',
        'views/lgps_main_menu.xml',
        'views/gpsdevice.xml',
        'views/cellchip.xml',
        'views/partner.xml',
        'views/accessory.xml',
    ],
}
