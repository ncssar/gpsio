var rt = null;
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
			var hasFilter = Number(response.version) >= 1;
			document.getElementById('v0').style.display = hasFilter ? 'none' : 'block';
			document.getElementById('v1').style.display = hasFilter ? 'block' : 'none';
			document.body.style.height="100px";
			window.setTimeout(function() {
				document.body.style.height="";
			}, 50);
		}
	});
}

save_options = function() {
   var method=document.querySelector('input[name="method"]:checked').id
   var timeSel=document.getElementById('timeSel').value;
   var recentSel=document.getElementById('recentSel').value;
   var size=document.getElementById('size').checked;
   var sizeSel=document.getElementById('sizeSel').value;
   chrome.storage.local.set({
       method:method,
       timeSel:timeSel,
       recentSel:recentSel,
       size:size,
       sizeSel:sizeSel
    });
}

load_options = function() {
    chrome.storage.local.get({
        method:'time',
        timeSel:'72',
        recentSel:'3',
        size:true,
        sizeSel:'100kB'
    }, function(items) {
        document.getElementById(items.method).checked=true;
        document.getElementById('timeSel').value=items.timeSel;
        document.getElementById('recentSel').value=items.recentSel;
        document.getElementById('size').checked=items.size;
        document.getElementById('sizeSel').value=items.sizeSel;
    });
}

_reset = function() {
    document.getElementById('time').checked=true;
    document.getElementById('timeSel').value='72';
    document.getElementById('recentSel').value='3';
    document.getElementById('size').checked=true;
    document.getElementById('sizeSel').value='100kB';
    save_options();
}

_close = function() {
    window.close();
}

about = function() {
    window.location="#about";
}

window.addEventListener('load', function() {
	check();
	load_options();
	document.getElementById('tryagain').addEventListener("click", check);
	document.getElementById('reset').addEventListener("click",_reset);
    document.getElementById('close').addEventListener("click",_close);
    document.getElementById('aboutButton').addEventListener("click",about);
   var inputs=document.querySelectorAll("input,select");
   for (i=0;i<inputs.length;i++) {
       inputs[i].onchange=save_options;
   }
});
