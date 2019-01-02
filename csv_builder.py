
class CSVBuilder:
    def __init__(self):
        self.list_of_items = []
        self.account_number = ''
        self.order_number = ''

    def set_account_and_ordernumber(self, iQAccount_number, iQOrder_number, ):
        self.account_number = str(iQAccount_number)
        self.order_number = str(iQOrder_number)

    def add_item(self, vendorsku, quantity, count):
        item = self.item_translation(vendorsku, quantity, count)
        self.list_of_items.append(item)

    def item_translation(self, vendorsku, quantity, count):
        return 'SKU: ' + str(vendorsku) + ' ' + 'Quantity: ' + str(quantity) + ' ' + 'LineNumber: ' + count

    def get_items(self):
        return str(self.list_of_items)

    def get_string(self):
        return 'Account Number: ' + self.account_number + '\n' + 'Order Number: ' + self.order_number + '\n' + '\n' + \
               '\n' + '\n'.join(self.list_of_items)
