
window.addEventListener("message", function(event) {
    if(event.data.source == "page" && event.data.type === "gpsio") {
    	if(event.data.cmd == "ping-extension") {
        	window.postMessage({source: "content_script", type: 'gpsio', id: event.data.id, response: {cmd: "ping-extension", status: "ok"}}, "*");    		
        	return;
    	}
        chrome.runtime.sendMessage({data: event.data}, function(response) {
        	window.postMessage({source: "content_script", type: 'gpsio', id: event.data.id, response: response}, "*");
        });
    }
}, false);
