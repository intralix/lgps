# -*- coding: utf-8 -*-
{
    'name': 'lgps_failures',
    'description': 'Intralix module for record faluires',
    'author': 'Intralix',    
    'website': 'https://www.intralix.com',
    'category': 'Uncategorized',
    'version': '0.0.1',
    'depends': [
        'base',
        'lgps'        
    ],    
    'data': [        
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/failures_menu.xml',
        'views/failures.xml',
        'views/failure_functionalities_list.xml',
        'views/failure_components_list.xml',
        'views/failure_root_problem_list.xml',
        'views/failures_odt.xml',
        'views/failure_symptoms_list.xml'
    ],
}
