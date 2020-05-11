# -*- coding: utf-8 -*-
{
    'name': 'lgps_margins',
    'description': 'Intralix module for internal margins on Sales Orders',
    'author': 'Intralix',    
    'website': 'https://www.intralix.com',
    'category': 'Uncategorized',
    'version': '0.0.3',
    'depends': [
        'base',
        'sale_margin',
        'lgps'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/user_config_menu.xml',
        #'views/user_margin_config.xml',
        'views/custom_so_margin.xml',
        'views/margin_permissions.xml',
    ],
}
