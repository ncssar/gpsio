
window.addEventListener("message", function(event) {
    if(event.data.source == "page" && event.data.type === "gpsio") {
    	if(event.data.cmd == "ping-extension") {
        	window.postMessage({source: "content_script", type: 'gpsio', id: event.data.id, response: {cmd: "ping-extension", status: "ok"}}, "*");    		
        	return;
    	}
        try {
			chrome.runtime.sendMessage({data: event.data}, function(response) {
        		window.postMessage({source: "content_script", type: 'gpsio', id: event.data.id, response: response}, "*");
        	});
		}
		catch(err) { // see https://stackoverflow.com/questions/53939205
			alert('GPSIO internal communication failed:\n'+err+'\nIf you recently installed or updated the extension, a page reload may resolve the problem.  Reload the page and try again.  If this message still appears, contact the administrator.');
		}
    }
}, false);
