var rt = null
if(typeof browser != "undefined") rt = browser.runtime;
if(typeof chrome != "undefined") rt = chrome.runtime; // also works for Edge

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
	
// always add the import options to the request, regardless of cmd
    chrome.storage.local.get({
        method:'time',
        timeSel:'72',
        recentSel:'3',
        size:true,
        sizeSel:'100kB',
        removeNumbers:true
    }, function(items) {
        console.log("options retrieved:");
        console.log(items);
        request.data.options=items;
        console.log("about to send using port.postMessage:");
        console.log(request.data);
        // need to post the message asynchronously (here in the local.get callback)
        //  to make sure request.data includes options
        port.postMessage(request.data);
   });

	return true;
}

//rt.onMessageExternal.addListener(fn);

rt.onMessage.addListener(fn);

// if update popup is needed (see popup.js), only show it once per browser session
rt.onStartup.addListener(function() {
	chrome.storage.local.set({'updatePopupShown':'false'});
});