
class SlackUtility(object):
    def __init__(self, logging, webhook):
        self.webhook = webhook
        self.logging = logging

    def send_message_to_slack(self, text):
        from urllib import request
        import json

        post = {"text": "{0}".format(text)}

        try:
            json_data = json.dumps(post)
            req = request.Request(self.webhook,
                                  data=json_data.encode('ascii'),
                                  headers={'Content-Type': 'application/json'})
            resp = request.urlopen(req)
        except Exception as em:
            self.logging.error("Exception: " + str(em))
