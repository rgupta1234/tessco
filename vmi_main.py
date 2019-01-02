import argparse
import config
import xmlbuilder
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import logging
import csv_builder
import arrow
from client import Client
import traceback

database_service = None
slack = None
log_service = None
client = None
COMMITTED_ORDER_TYPE = 'COMMITTED'
MANUAL_ORDER_TYPE = 'MANUAL'


def process_stores():
    store_list = config.iqmetrix_client.service.GetStoreList(
        Vendor={'VendorID': config.vendor_id, 'Username': config.user_name, 'Password': config.password,
                'Client': {'ClientID': client.iqm_company_id, 'Name': None, 'StoreID': 0,
                           'VendorAccountNumber': None}})
    if not store_list:
        return

    for store in store_list:
        log_service.info("Accessing store: " + store.Name)
        log_service.info('Vendor Account # is ' + store.VendorAccountNumber[:7])
        if store.VendorAccountNumber[:7] in client.account_numbers:
            log_service.info("Store account number is valid, Getting Purchase Orders...")
            process_purchase_orders_based_on_type(client.iqm_company_id, store, COMMITTED_ORDER_TYPE)
            if client.uses_manual_order_process:
                log_service.info("Looking for Manually Purchased Orders...")
                process_purchase_orders_based_on_type(client.iqm_company_id, store, MANUAL_ORDER_TYPE)
            log_service.info('Flag for Manually Purchased Orders is: '
                             + str(client.uses_manual_order_process))
        else:
            log_service.warning(store.Name + " is not valid, skipping store.")


# This method looks for orders based on Committed or Manual type.
# There are two different API calls to iQmetrix for Committed and Manual.
def process_purchase_orders_based_on_type(iqm_company_id, store, order_type):
    store_id = store.StoreID
    store_van = store.VendorAccountNumber
    store_name = store.Name

    logging.info(
        'Looking for POs in ClientID: {0}, StoreID: {1}, Name: {2}'.format(iqm_company_id, store_id, store_name))
    if order_type == COMMITTED_ORDER_TYPE:
        api_call_start_time = datetime.now()

        purchase_order_list = config.iqmetrix_client.service.GetCommittedPurchaseOrderList(
            vendor={'VendorID': config.vendor_id, 'Username': config.user_name, 'Password': config.password,
                    'Client': {'ClientID': iqm_company_id, 'StoreID': store_id}})

        api_call_end_time = datetime.now()

        log_service.info("Committed Order Pull call was completed in: " + str(api_call_end_time - api_call_start_time))
    elif order_type == MANUAL_ORDER_TYPE:
        api_call_start_time = datetime.now()

        purchase_order_list = config.iqmetrix_client.service.GetClientPurchaseOrdersByStatus(
            vendor={'VendorID': config.vendor_id, 'Username': config.user_name, 'Password': config.password,
                    'Client': {'ClientID': iqm_company_id, 'StoreID': store_id}
                    },
            startDate=arrow.now().shift(days=-1).format('YYYY-MM-DD'),
            endDate=arrow.now().shift(days=+1).format('YYYY-MM-DD'),
            isCompleted=False,
            isCommitted=True)

        api_call_end_time = datetime.now()

        log_service.info("Manual Order Pull call was completed in: " + str(api_call_end_time - api_call_start_time))
    else:
        raise Exception('Invalid Order Type: ' + order_type + '!')

    process_purchase_orders(purchase_order_list, order_type, iqm_company_id, store_id, store_van, store_name)


def process_purchase_orders(purchase_order_list, order_type, iqm_company_id, store_id, store_van, store_name):
    if not purchase_order_list:
        log_service.warning('No POs for ClientID: {0}, StoreID: {1}'.format(iqm_company_id, store_id))
        return

    log_service.info('Found {0} POs for ClientID: {1}, StoreID: {2}'
                     .format(len(purchase_order_list), iqm_company_id, store_id))
    for po in purchase_order_list:
        if str(po.PurchaseOrderData.RetailiQPurchaseOrderNumber) in client.processed_purchase_orders:
            log_service.warning('Duplicate Purchase Order')
        else:
            count = 1

            # Initialize XML Format
            xml = xmlbuilder.XMLFormat()
            xml.setAccountLocation(store_van)

            csv = csv_builder.CSVBuilder()
            csv.set_account_and_ordernumber(store_van[:7], po.PurchaseOrderData.RetailiQPurchaseOrderNumber)

            # Set Order Request Header
            xml.setOrderRequestHeader(po.PurchaseOrderData.RetailiQPurchaseOrderID,
                                      po.PurchaseOrderData.RetailiQPurchaseOrderNumber)

            xml.setCustomValues(po.PurchaseOrderData.VendorInvoiceNumber, po.PurchaseOrderData.PurchaseOrderID,
                                str(store_id))

            log_service.info('po_id: {0} and po_orderid: {1} po_ordernumber: {2}'.format(
                po.PurchaseOrderID, po.PurchaseOrderData.RetailiQPurchaseOrderID,
                po.PurchaseOrderData.RetailiQPurchaseOrderNumber))

            product_information_list = po.ProductsOrdered.ProductInformation

            for product in product_information_list:
                xml.setItem(count, product.QuantityOrdered, product.VendorSKU, product.ProductSKU,
                            product.ProductItemID, product.ProductCost)
                csv.add_item(product.VendorSKU, product.QuantityOrdered, str(count))

                count = count + 1

            if client.uses_sku_injection_process:
                get_active_skus(str(store_id), count, xml, csv, str(po.PurchaseOrderID))

            summarized_content_string = csv.get_string()

            logging.info(summarized_content_string)

            xml_string = minidom.parseString(ET.tostring(xml.getXML(),
                                                         encoding='utf8',
                                                         method='xml')).toprettyxml(indent="\t")
            put_purchase_order_into_database(str(po.PurchaseOrderData.RetailiQPurchaseOrderID),
                                                              str(po.PurchaseOrderData.RetailiQPurchaseOrderNumber),
                                                              xml_string, str(summarized_content_string),
                                                              str(store_id), str(store_name), client.client_tpid,
                                                              str(client.account_numbers[0]), str(order_type))

            client.processed_purchase_orders.add(str(po.PurchaseOrderData.RetailiQPurchaseOrderNumber))


def get_active_skus(store_id, count, xml, csv, purchase_order_id):
    get_active_skus_query = 'SELECT DISTINCT sku, pricing, quantity ' \
                            'FROM {}.vmi_sku_list ' \
                            'WHERE client_account = %s ' \
                            'AND (%s = ANY(store_ids) ' \
                            'OR %s = ANY(store_ids)) ' \
                            'AND end_date > to_date(%s, %s) ' \
                            'AND start_date <= to_date(%s, %s)'
    get_active_skus_args = [client.account_numbers[0],
                            '-9999',
                            str(store_id),
                            str(arrow.now().format('YYYY-MM-DD')), 'yyyy-mm-dd',
                            str(arrow.now().format('YYYY-MM-DD')), 'yyyy-mm-dd']

    get_active_skus_results = database_service.select_all_rows(get_active_skus_query, get_active_skus_args)

    # Add Sku Data to dictionary; SKU # is the key.
    active_skus_dict = {active_sku['sku']: active_sku for active_sku in get_active_skus_results}
    for key, value in active_skus_dict.items():
        product_sku = value['sku']
        product_price = value['pricing']
        product_quantity = value['quantity']
        log_service.info("Inserting SKU #: " + product_sku + " into Purchase Order #: " + purchase_order_id)
        xml.setItem(count, product_quantity, product_sku, product_sku, product_sku, product_price)
        csv.add_item(product_sku, 1, str(count))
        count = count + 1


def put_purchase_order_into_database(retailiqpo_id, retailiqpo_ordernumber, xml_content, summarized_content,
                                         store_id, store_name, tp_id, vendor_account_number, order_type):
    insert_po_query = 'INSERT INTO {}.vmi_purchase_orders (retailiqpo_id, retailiqpo_ordernumber, ' \
                      'xml_content, summarized_content, store_id, store_name, tp_id, ' \
                      'vendor_account_number, order_type) ' \
                      'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ' \
                      'ON CONFLICT (tp_id, retailiqpo_ordernumber) ' \
                      'DO NOTHING'
    insert_po_args = [retailiqpo_id, retailiqpo_ordernumber, xml_content, summarized_content, store_id, store_name,
                      tp_id, vendor_account_number, order_type]
    database_service.execute_cmd(insert_po_query, insert_po_args)


def update_last_ran(client_tpid):
    update_last_ran_query = 'UPDATE {}.vmi_company_config SET last_modified_date = NOW(), last_ran = NOW() ' \
                            'WHERE tp_id = %s'
    update_last_ran_args = [client_tpid]
    config.database_service.execute_cmd(update_last_ran_query, update_last_ran_args)


if __name__ == '__main__':
    start_time = datetime.now()
    # Grab the command line arguments
    parser = argparse.ArgumentParser(description='process VMI feed')
    parser.add_argument('client_tpid', metavar='Client TPID', help='TPID for Client you want to pull')
    parser.add_argument('environment_path', metavar='Environment Path',
                        help='File path for the env.json you want to use. '
                             'Example: vmi_qa.json, vmi_stg.json, vmi_prod.json')
    args = parser.parse_args()

    # Set Client TPID and Initialize Configurations
    client_tpid = str(args.client_tpid)
    environment_path = str(args.environment_path)
    try:
        config.initialize(environment_path, client_tpid)
        config_start_time = datetime.now()
        # Open Database Service
        database_service = config.database_service

        # Open Slack Utility
        slack = config.slack

        # Get log_service
        log_service = config.log_service

        # Start application
        client = Client(client_tpid, database_service)
        log_service.info('Configuration Time: ' + str(datetime.now() - config_start_time))
        if client.iqm_company_id:
            process_stores()
        else:
            log_service.error(client_tpid + ' could not load IQM Company Code!')

        update_last_ran(client_tpid)
        log_service.info("It took the entire application this amount of time to finish")
        log_service.info(datetime.now() - start_time)
    except Exception as e:
        if config.log_service:
            config.log_service.error('Unexpected Error: {0}\n{1}'.format(str(e), str(traceback.print_exc())))
        if slack:
            slack.send_message_to_slack('*VMI Upload Processor (Python)* :fireball: \n' +
                                    '*Issue:* ' + 'We Ran into an unaccounted for issue processing client: ' +
                                    client_tpid + '\n' +
                                    '*From Python:* ' + str(e) + '\n' +
                                    '*Stack Trace:* ' + str(traceback.print_exc()) + '\n' +
                                    '*Date:* ' + str(arrow.now().format('MM/DD/YYYY')))
        raise e

