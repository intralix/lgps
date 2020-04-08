# -*- coding: utf-8 -*-
{
    'name': 'lgps_margins',
    'description': 'Intralix module for internal margins on Sales Orders',
    'author': 'Intralix',    
    'website': 'https://www.intralix.com',
    'category': 'Uncategorized',
    'version': '0.0.1',
    'depends': [
        'base',
        'sale_margin',
        'lgps'
    ],
    'data': [
        'security/security.xml',
        'views/custom_margin_permissions.xml',
        'views/user_max_discount.xml'
    ],
}
