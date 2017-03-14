var rt = null
if(typeof browser != "undefined") rt = browser.runtime;
if(typeof chrome != "undefined") rt = chrome.runtime;

var id = Math.round(Math.random()*1000000);

check = function() {
	document.getElementById('condition_good').style.display = "none";
	document.getElementById('condition_bad').style.display = "block";
	rt.sendMessage({data: {cmd: 'ping-host', type: 'gpsio', id: id}}, function(response) {
		if(response.status == "ok") {
			document.getElementById('condition_good').style.display = "block";
			document.getElementById('condition_bad').style.display = "none";
		}
	});
}

window.addEventListener('load', function() {
	check();
	document.getElementById('tryagain').addEventListener("click", check, false);
});