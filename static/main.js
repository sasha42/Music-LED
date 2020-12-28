"use strict"

// update asyncrynously the status in the background
setInterval(function(){ checkParams(); }, 1000);

// Set global is changed variable
var isChanged = false

function handleChanges() {
    console.log("input event fired");
	window.isChanged = true;

    // Get element from page
    var paramsElement = document.getElementById('params');
	var parsedElement = JSON.parse(paramsElement.innerHTML);

	console.log(parsedElement);
}

document.getElementById("params").addEventListener("click", function() {
	handleChanges();
}, false);

document.getElementById("params").addEventListener("input", function() {
	handleChanges();
}, false);

function setLocalParams(params) {
    console.log(params);
    // Get element from page
    var paramsElement = document.getElementById('params');

    // Set up focused and changed parameters
    var isFocused = (document.activeElement === paramsElement);

    paramsElement.textContent = JSON.stringify(params, undefined, 2);

    // Update local params only if not focused on params element,
    // if there were no changes, and it's not loading
    //if ((isFocused === false) || (isChanged == false)) {
    //	if (paramsElement.innerHTML == 'loading params...') {
//			// Populare initial params on load
//			console.log('asdf')
//			//paramsElement.innerHTML = JSON.stringify(params);
//		        paramsElement.textContent = JSON.stringify(params, undefined, 2);
//
//			console.dir(object, {depth: null, colors: true})
//		} else {
//			if (paramsElement.innerHTML == JSON.stringify(params)) {
//					console.log('asdf')
//					paramsElement.textContent = JSON.stringify(params, undefined, 2);
//					//paramsElement.innerHTML = JSON.stringify(params);
//				} else {
//					//isChanged = true;
//					//paramsElement.classList.add("changed");
//					console.log('Changed');
//				}
//		}
//	}
}

function checkParams() {
    // checks the status from adafruit
    var url = location.protocol+'//'+location.hostname+(location.port ? ':'+location.port: '');
    fetch(url + '/params')
    //fetch("https://noise.fixme.ch/params")
    .then(function(response) {
        return response.json();
    }).then(function(data) {
        //console.log(data);
        setLocalParams(data)
    }).catch(function(error) {
        console.log(error);
        //setLocalStatus('error');
    });
}
