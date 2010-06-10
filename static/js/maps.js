
var map;
var container;
var circle;
var centerMarker;
var circleUnits;
var circleRadius;
var OverLays = new Array();
var radii = new Array(0.1, 2);
var mapData = new Array();
var colors = ["orange", "green", "blue", "purple"]
var pinicons = {}

$(document).ready(function (e) {
        if (GBrowserIsCompatible()) {
            container = document.getElementById("mapDiv");
            map = new GMap2(container, {draggableCursor:"crosshair"});
            map.setCenter(centerPoint, zoom);

            map.addControl(new GScaleControl());
            map.addControl(new GLargeMapControl());
            map.addControl(new GMapTypeControl());
 
            //map.enableContinuousZoom();
            map.enableScrollWheelZoom();		
 
            var pos = new GControlPosition(G_ANCHOR_TOP_LEFT, new GSize(0, 620));
            /*map.addControl(new MStatusControl({position:pos}));*/
            GEvent.addListener(map, "click", function (ol, pt) {
                    drawCircle(pt);
                    update_form();
                });
	    
	    //make colorful pins
	    for(var i in colors){		
		var icon = new GIcon(G_DEFAULT_ICON)
		icon.image = ["/static/img/pins/",colors[i],".png"].join("")
		pinicons[colors[i]] = icon
	    }
	    //place colorful pins
	    $.getJSON(listingURL, place_colorful_pins)
       }
    });

function price_icon(price){
    if(price < 1000)
	return pinicons.orange;
    if(price < 1500)
	return pinicons.green;
    if(price < 2000)
	return pinicons.blue;
    return pinicons.purple;
}

function place_colorful_pins(results, status) {
    // lol what does status even do?
    var apts = results.results;
    for(var i=0; i<200; i++){
	var apt = apts[i];
	var ll = new GLatLng(apt.location[0],apt.location[1]);
	var marker = new GMarker(ll, {icon:price_icon(apt.price)});
	map.addOverlay(marker);
    }

}

function drawCircle(center) {
    var radius1 = radii[0];
    var radius2 = radii[1];


    centerMarker = new GMarker(center,{draggable:true});
    GEvent.addListener(centerMarker,'dragend',drawCircle);
    map.addOverlay(centerMarker);
    OverLays.push(centerMarker);
 
    var bounds = [new GLatLngBounds(), new GLatLngBounds()];
    var circlePoints = [[], []];
    var d = [radius1 / 3963.189, radius2 / 3963.189];

    with (Math) {
        var lat1 = (PI/180)* center.lat();
        var lng1 = (PI/180)* center.lng();

        for (var a = 0 ; a < 361 ; a+=8) {
            var tc = (PI/180)*a;
            var y, x, dlng;

            for (var i = 0; i < 2; i++) {
                y = asin(sin(lat1)*cos(d[i])+cos(lat1)*sin(d[i])*cos(tc));
                dlng = atan2(sin(tc)*sin(d[i])*cos(lat1),cos(d[i])-sin(lat1)*sin(y));
                x = ((lng1-dlng+PI) % (2*PI)) - PI;
                var point = new GLatLng(parseFloat(y*(180/PI)),parseFloat(x*(180/PI)));
                circlePoints[i].push(point);
                bounds[i].extend(point);
            }
        }
 
        if (d[1] < 1.5678565720686044) {
            circle = new GPolygon(circlePoints[1], '#000000', 2, 1, '#000000', 0.25);	
        }
        else {
            circle = new GPolygon(circlePoints[1], '#000000', 2, 1);	
        }
        map.addOverlay(circle); 
        var circle2 = new GPolygon(circlePoints[0], '#FFFFFF', 2, 1, '#FFFFFF', 0.25);
        map.addOverlay(circle2);
        OverLays.push(circle);
        OverLays.push(circle2);
    }
    mapData.push([center.lat(), center.lng(), radius1, radius2]);
    computeMapData(mapData);
}

function deleteOneCircle() {
    if (OverLays.length >= 3) {
        for (var i = 0; i < 3; i++) {
            var overlay = OverLays.pop();
            map.removeOverlay(overlay);
        }
        mapData.pop();
        computeMapData(mapData);
    }
}

function deleteAllCircles() {
    while (OverLays.length) {
        var overlay = OverLays.pop();
        map.removeOverlay(overlay);
        mapData.pop();
    }
    computeMapData(mapData);
}

function computeMapData(mapData) {
    var result = new Array();
    for (var i = 0; i < mapData.length; i++) {
        for (j = 0; j < mapData[i].length; j++) {
            result.push(mapData[i][j]);
        }
    }
    $("#location-data").val(result.join(","));
}

window.unload = GUnload;


$(document).ready(function (e) {
        $("#mile-range").slider({
                range: true,
                    min: 0,
                    max: 4,
                    step: 0.02,
                    values: [0.2, 2],
                    slide: function (event, ui) {
                    $("#mile-output").html(ui.values[0] + "mi to " + ui.values[1] + "mi");
                    radii[0] = ui.values[0];
                    radii[1] = ui.values[1];
                }
            });
        $('#mile-output').html("0.2mi to 2mi");

        $("#price-range").slider({
                range: true,
                    min: 500,
                    max: 4000,
                    step: 5,
                    values: [800, 2000],
                    slide: function (event, ui) {
                    $("#price-output").val('$' + ui.values[0] + " to $" + ui.values[1]);
                    update_form();
                }
            });
        $('#price-output').val("$800 to $2000");

        $("#id_expires").datepicker({minDate: '+7D', maxDate: '+6M'});

    });



