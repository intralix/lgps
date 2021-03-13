# -*- coding: utf-8 -*-
{
    'name': 'lgps_vehicle',
    'description': 'Intralix module for manage vehicles',
    'author': 'Intralix',    
    'website': 'https://www.intralix.com',
    'category': 'Uncategorized',
    'version': '0.0.1',
    'depends': [
        'base',        
        'lgps',
        'fleet'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/vehicle_device.xml',
        'views/vehicle.xml',
        'views/vehicle_type.xml',
        'views/vehicle_custom_tree.xml',
    ],
}
