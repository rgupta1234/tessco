from database_service import DatabaseService


class Client:
    account_numbers = []

    def __init__(self, client_tpid, database_service):
        self.client_tpid = client_tpid
        self.database_service = database_service
        client_settings = self.load_client_settings(client_tpid)
        if not client_settings:
            raise Exception('Failed to load client settings for client_tpid = {0}'.format(client_tpid))
        self.iqm_company_id = client_settings['iqm_company_id']
        self.uses_manual_order_process = client_settings['uses_manual_order_process']
        self.uses_sku_injection_process = client_settings['uses_sku_injection_process']
        self.account_numbers = self.get_account_numbers(client_tpid)
        self.processed_purchase_orders = self.get_previous_purchase_orders(client_tpid)

    def __del__(self):
        self.client_tpid = None
        self.database_service = None

    def load_client_settings(self, client_tpid):
        load_client_settings_query = 'SELECT vcc.iqm_company_id, vcc.uses_manual_order_process, ' \
                                     'vcc.uses_sku_injection_process FROM {}.vmi_company_config vcc ' \
                                     'WHERE vcc.tp_id = %s'
        load_client_settings_result = self.database_service.select_first_row(load_client_settings_query, [client_tpid])
        return {k: v for (k, v) in
                load_client_settings_result.items()} if load_client_settings_result else None

    def get_previous_purchase_orders(self, client_tpid):
        get_previous_pos_by_tpid_query = 'SELECT vpo.retailiqpo_ordernumber FROM {}.vmi_purchase_orders vpo ' \
                                         'WHERE vpo.tp_id = %s'
        get_previous_pos_by_tpid_results = self.database_service.select_all_rows(get_previous_pos_by_tpid_query,
                                                                                 [client_tpid])
        return {r['retailiqpo_ordernumber'] for r in get_previous_pos_by_tpid_results} \
            if get_previous_pos_by_tpid_results else set()

    def get_account_numbers(self, client_tpid):
        get_account_numbers_query = 'SELECT vcc.primary_account_number, vcc.alt_account_numbers ' \
                                    'FROM {}.vmi_company_config vcc ' \
                                    'WHERE vcc.tp_id = %s'
        get_account_numbers_result = self.database_service.select_first_row(get_account_numbers_query, [client_tpid])
        account_numbers = []
        if get_account_numbers_result:
            account_numbers.append(get_account_numbers_result['primary_account_number'])
            if get_account_numbers_result['alt_account_numbers']:
                account_numbers.extend(get_account_numbers_result['alt_account_numbers'])
        return account_numbers
