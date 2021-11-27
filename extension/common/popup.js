// MAKE SURE TO UPDATE THE VERSION# IN manifest.json!
// show details here that the user should see when the extension version is
//  equal to the key name but the host version is something older
const updateDetails={
    "1.1.0":`\nCritical?  NO:  you can continue to use GPSIO now.
What changed?  Until the host is updated, the 'Remove numbers from assigment names' checkbox setting in the GPSIO filter settings popup window will be ignored, and numbers will always be removed from exported assignment names (when preceded by a space).  The checkbox value will be respected after the update.`,
    "1.0":"These are the 1.0 details."
}

var rt = null;
if(typeof browser != "undefined") rt = browser.runtime;
if(typeof chrome != "undefined") rt = chrome.runtime;

var id = Math.round(Math.random()*1000000);

check = function() {
	document.getElementById('condition_good').style.display = "none";
	document.getElementById('condition_bad').style.display = "block";
    document.getElementById('condition_host_update_available').style.display = "none";
	rt.sendMessage({data: {cmd: 'ping-host', type: 'gpsio', id: id}}, function(response) {
		if(response.status == "ok") {
            document.getElementById('condition_good').style.display = "block";
            document.getElementById('condition_bad').style.display = "none";
            document.getElementById('condition_host_update_available').style.display = "none";
            // version comparison: see https://stackoverflow.com/a/40201629/3577105
            var hostVersion=response.version;
            if (hostVersion==1) { // first host version returns the number 1
                hostVersion='1.0';
            }
            var extensionVersion=rt.getManifest().version;
            var versionArray=[extensionVersion,hostVersion]
                    .map( a => a.replace('/\d+/g', n => +n+100000 ) ).sort()
                    .map( a => a.replace('/\d+/g', n => +n-100000 ) );
            if ((versionArray[0]!=versionArray[1]) && (versionArray[1]===extensionVersion)) {
                document.getElementById('condition_good').style.display = "none";
                document.getElementById('condition_bad').style.display = "none";
                document.getElementById('condition_host_update_available').style.display = "block";
                // show the update notification just once per browser session;
                //  storage value is reset by runtime.onStartup listener in background.js
                chrome.storage.local.get('updatePopupShown', function(data) {
                    if (data.updatePopupShown!='true') {
                        var details=updateDetails[extensionVersion] || '';
                        alert('A new version of the GPSIO host is available.  Please tell the administrator.\n'+details+'\nCurrent host version: '+hostVersion+' --> Newest host version: '+extensionVersion);
                        chrome.storage.local.set({'updatePopupShown':'true'});
                    }
                });
            }
            // if host version is newer than extension, don't bother showing a message;
            //  this should be OK, and it's not something the user should be bothered
            //  with or should take action on anyway
            document.getElementById('v1').style.display='block';
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
   var removeNumbers=document.getElementById('removeNumbers').checked;
   chrome.storage.local.set({
       method:method,
       timeSel:timeSel,
       recentSel:recentSel,
       size:size,
       sizeSel:sizeSel,
       removeNumbers:removeNumbers
    });
}

load_options = function() {
    chrome.storage.local.get({
        method:'time',
        timeSel:'72',
        recentSel:'3',
        size:true,
        sizeSel:'100kB',
        removeNumbers:true
    }, function(items) {
        document.getElementById(items.method).checked=true;
        document.getElementById('timeSel').value=items.timeSel;
        document.getElementById('recentSel').value=items.recentSel;
        document.getElementById('size').checked=items.size;
        document.getElementById('sizeSel').value=items.sizeSel;
        document.getElementById('removeNumbers').checked=items.removeNumbers;
    });
}

_reset = function() {
    document.getElementById('time').checked=true;
    document.getElementById('timeSel').value='72';
    document.getElementById('recentSel').value='3';
    document.getElementById('size').checked=true;
    document.getElementById('sizeSel').value='100kB';
    document.getElementById('removeNumbers').checked=true;
    save_options();
}

_close = function() {
    window.close();
}

aboutImport = function() {
    window.location="#aboutImport";
}

aboutExport = function() {
    window.location="#aboutExport";
}

window.addEventListener('load', function() {
	check();
	load_options();
	document.getElementById('tryagain').addEventListener("click", check);
	document.getElementById('reset').addEventListener("click",_reset);
    document.getElementById('close').addEventListener("click",_close);
    document.getElementById('aboutImportButton').addEventListener("click",aboutImport);
    document.getElementById('aboutExportButton').addEventListener("click",aboutExport);
    var inputs=document.querySelectorAll("input,select");
   for (i=0;i<inputs.length;i++) {
       inputs[i].onchange=save_options;
   }
});
