from burp import IBurpExtender, IHttpListener
from subprocess import Popen, PIPE

class BurpExtender(IBurpExtender):
    def registerExtenderCallbacks(self, callbacks):
	self._callbacks = callbacks
	self._helpers = callbacks.getHelpers()
	callbacks.setExtensionName("Inflight JS-Beautifier")
	callbacks.registerHttpListener(InflightJsBeautifier(self))

class InflightJsBeautifier(IHttpListener):
    def __init__(self, extender):
	self._callbacks = extender._callbacks
	self._helpers = extender._helpers

    def processHttpMessage(self, toolFlag, messageIsRequest, messageInfo):
        # only process responses
        if messageIsRequest:
            return
        response = messageInfo.getResponse()
        info = self._helpers.analyzeResponse(response)
        # Only process javascript responses
	headers = info.getHeaders()
        if any("Content-Type: text/javascript" in h for h in headers):
            # extract the body
            body = response[info.getBodyOffset():]
            # pipe it through js-beautify. Jython seems to not use the context manager
            proc = Popen("js-beautify", stdin=PIPE, stdout=PIPE)
            proc.stdin.write(body)
            proc.stdin.close()
            body = proc.stdout.read()
            proc.stdout.close()
            proc.terminate()
            # overwrite the output
	    response_bytes = self._helpers.buildHttpMessage(headers, body)
	    messageInfo.setResponse(response_bytes)


