# -*- coding: utf-8 -*-
{
    'name': 'lgps_notifications',
    'description': 'Intralix module for record offline notifications',
    'author': 'Intralix',    
    'website': 'https://www.intralix.com',
    'category': 'Uncategorized',
    'version': '1.1.4',
    'depends': [
        'base',
        'lgps'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/offline_notification_menu.xml',
        'views/cron_task.xml',
        'views/offline_gpsdevice.xml',
        'views/offline_notification_rules.xml',
        'views/offline_client_configuration.xml',
        'views/offline_notifications.xml',
        'reports/email_preview.xml',
    ],
}
