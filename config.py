import json
from zeep import Client
from zeep import Transport
import slack_utility
from log_service import LogService
from database_service import DatabaseService

# database_configuration = None
database_service = None
iqmetrix_client = None
log_service = None
password = ''
service_provider_configuration = None
slack = None
user_name = ''
vendor_id = ''


def initialize(config_file_path, client_tpid):
    try:
        stream = open(config_file_path, 'r')
        config_data = json.load(stream)
    except Exception:
        raise Exception('Unable to process specified config file: {0}.'.format(config_file_path))

    # Initialize Log Service
    log_configuration = config_data['log_configuration'] if 'log_configuration' in config_data else None
    if log_configuration and all(k in log_configuration for k in ('log_path', 'log_level')):
        global log_service
        log_service = LogService(log_path=log_configuration['log_path'], log_level=log_configuration['log_level'],
                                 client_tpid=client_tpid).logger
    else:
        raise Exception('Log configuration is missing or incomplete.')

    # Retrieve Tessco Credentials
    global service_provider_configuration
    service_provider_configuration = config_data[
        'service_provider_configuration'] if 'service_provider_configuration' in config_data else None
    if not service_provider_configuration or not all(k in service_provider_configuration for k in (
            'wsdl_path', 'vendor_id', 'user_name', 'password', 'timeout', 'slack_webhook')):
        raise Exception('Service Provider configuration is missing or incomplete')

    global vendor_id
    vendor_id = service_provider_configuration['vendor_id']
    global user_name
    user_name = str(service_provider_configuration['user_name'])
    global password
    password = str(service_provider_configuration['password'])

    if not vendor_id or not user_name or not password:
        raise Exception('IQMetrix credentials is missing or incomplete.')

    # Retrieve webhook from config.
    global slack
    slack = slack_utility.SlackUtility(log_service, str(service_provider_configuration['slack_webhook']))

    # Initialize Database Service
    database_configuration = config_data['database_configuration'] if 'database_configuration' in config_data else None
    if not database_configuration or not all(
            k in database_configuration for k in ('host', 'username', 'password', 'db_name', 'schema', 'port')):
        raise Exception('Database configuration is missing or incomplete')

    global database_service
    database_service = DatabaseService(database_configuration['host'], database_configuration['username'],
                                       database_configuration['password'], database_configuration['db_name'],
                                       database_configuration['schema'], database_configuration['port'])

    # Initialize iQmetrix client - pull in WSDL file
    global iqmetrix_client
    iqmetrix_client = Client(service_provider_configuration['wsdl_path'],
                             transport=Transport(timeout=service_provider_configuration['timeout']))
