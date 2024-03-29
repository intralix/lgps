# -*- coding: utf-8 -*-
{
    'name': 'lgps',
    'description': 'Intralix module for internal processes',
    'author': 'Intralix',
    'application': True,
    'website': 'https://www.intralix.com',
    'category': 'Uncategorized',
    'version': '0.5.6',
    'depends': [
        'base',
        'stock',
        'contacts',
        'account',
        'repair',
        'crm',
        'sale_subscription',
        'helpdesk',
        'mail',
        'project',
        'sale'
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
        'views/odt_custom_list_view.xml',
        'views/tracking.xml',
        'views/tracking_logs.xml',
        'views/odt.xml',
        'views/lead.xml',
        'views/tickets.xml',
        'views/res_config_settings_views.xml',
        'views/sales_order_custom_list_view.xml',
        'views/sales_order_custom_form_view.xml',
        'views/sales_order_custom_crm_list_view.xml',
        'views/helpdesk_custom_tree_view.xml',
        'views/helpdesk_custom_form_view.xml',
        'views/task_custom_form_view.xml',
        'views/wizard_common_operations.xml',
        'views/device_history.xml',
        'views/wizard_accessory_operations.xml',
        'views/accessory_history.xml',
        'views/authorization_request_odt_wizard.xml',
        'views/authorization_odt_wizard.xml',
        'views/custom_account_invoice_cancel.xml',
        'views/custom_payment_invoice_cancel.xml',
        'views/dolar_history.xml',
        'views/wizard_mass_comment.xml'
    ],
}
