var rt = null
if(typeof browser != "undefined") rt = browser.runtime;
if(typeof chrome != "undefined") rt = chrome.runtime;

var fn = function(request, sender, sendResponse) {
	var port = rt.connectNative("com.caltopo.gpsio");
	var debug="True";
	if (debug=="True") {
		console.log("request="+JSON.stringify(request,null,4));
		console.log("sender="+JSON.stringify(sender,null,4));
		console.log("cmd="+request.data.cmd);
	}

	var buffer="";
	port.onMessage.addListener(function(msg) {
		if (debug=="True") {
			console.log("received " + msg);
		}
		buffer+=msg;
	});
	port.onDisconnect.addListener(function(msg) {
		if (debug=="True") {
			console.log("disconnected with msg="+JSON.stringify(msg));
		}
		if (buffer!="") {
// must send JSON.parse(buffer) to avoid 'Content not allowed in prolog'
			if (debug=="True") {
				console.log("sending buffer to browser:"+JSON.parse(buffer))
			}
			sendResponse(JSON.parse(buffer));
			buffer="";
		} else {
// even in the failure case, the response object must have status and message elements
			sendResponse({status: 'error', message: 'Unexpected disconnect'});
		}
	});
	port.postMessage(request.data);
	return true;
}

//rt.onMessageExternal.addListener(fn);

rt.onMessage.addListener(fn);

