import xml.etree.ElementTree as ET
import arrow


class XMLFormat(object):
    def __init__(self):
        self.tXML = ET.Element('tXML')
        # Sub Element for tXML
        self.request = ET.SubElement(self.tXML, 'Request')
        # Sub Element for Request
        self.orderRequest = ET.SubElement(self.request, 'OrderRequest')
        # Sub Element for Order Request
        self.orderRequestHeader = ET.SubElement(self.orderRequest, 'OrderRequestHeader')
        self.orderRequestHeader.set('orderType', 'SA')
        # Sub Elements for Order Request Header
        self.total = ET.SubElement(self.orderRequestHeader, 'Total')
        self.customer = ET.SubElement(self.orderRequestHeader, 'Customer')
        self.orderSource = ET.SubElement(self.orderRequestHeader, 'OrderSource')
        # Sub Element for Total
        self.money1 = ET.SubElement(self.total, 'Money')
        self.money1.set('currency', 'USD')
        # Sub Element for Order Source
        self.orderEntryMethod = ET.SubElement(self.orderSource, 'OrderEntryMethod')
        self.orderEntryMethod.text = 'WIQM'


    def setOrderRequestHeader(self, orderID, purchaseOrder):
        self.orderRequestHeader.set('orderID', str(orderID))
        self.orderRequestHeader.set('purchaseOrder', str(purchaseOrder))
        self.orderRequestHeader.set('orderDate', arrow.now().format('YYYY-MM-DD'))

    def setAccountLocation(self, accountNumber):
        account_number = str(accountNumber).strip()
        value7 = ET.SubElement(self.customer, 'Account')
        value7.text = account_number[:7]
        value4 = ET.SubElement(self.customer, 'Location')
        value4.text = account_number[-4:]

    def setCustomValues(self, invoiceNumber, orderID, storeID):
        customInvoice = ET.SubElement(self.customer, 'CustomValue')
        customInvoice.set('name', 'RLSE')
        customInvoice.text = str(invoiceNumber)
        customOrder = ET.SubElement(self.customer, 'CustomValue')
        order_number = str(orderID).strip()
        store_number = str(storeID).strip()
        order_number_and_store_number = str('{0}:{1}'.format(order_number, store_number))
        customOrder.set('name', 'IQID')
        customOrder.text = order_number_and_store_number

    def printXML(self):
        ET.dump(self.tXML)

    def setItem(self, count, quantity, vendorSku, productSku, productItemID, productCost):
        item_new = ET.SubElement(self.orderRequest, 'Item')
        item_new.set('quantity', str(quantity))
        item_new.set('customerLineNumber', str(count))
        # Sub Elements for Item
        itemID = ET.SubElement(item_new, 'ItemID')
        itemDetail = ET.SubElement(item_new, 'ItemDetail')
        # Sub Elements for ItemID
        partID = ET.SubElement(itemID, 'PartID')
        partID.set('code', 'VN')
        partID.text = str(vendorSku)
        customerPartIDBP = ET.SubElement(itemID, 'CustomerPartID')
        customerPartIDBP.set('code', 'BP')
        customerPartIDBP.text = str(productSku)
        customerPartIDPQ = ET.SubElement(itemID, 'CustomerPartID')
        customerPartIDPQ.set('code', 'PQ')
        customerPartIDPQ.text = str(productItemID)
        # Sub Elements for Item Detail
        customerPrice = ET.SubElement(itemDetail, 'CustomerPrice')
        # Sub Elements for Customer Price
        money = ET.SubElement(customerPrice, 'Money')
        money.set('currency', '')
        money.text = str(productCost)

    def getXML(self):
        return self.tXML
