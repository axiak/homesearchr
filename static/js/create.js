
function validate_form() {
    var errors = new Array();
    if (!$("#id_email")[0].value)
        errors.push("Please enter a valid email address.");

    if (!$("#id_expires")[0].value)
        errors.push("Please enter a valid expiration date.");

    var size_selected = false;
    var options = $("#id_size")[0].options;
    for (var i=0; i < options.length; i++) {
        if (options[i].selected) {
            size_selected = true;
            break;
        }
    }
    if (!size_selected)
        errors.push("Please select a size.");

    if (!$("#location-data")[0].value)
        errors.push("Please draw at least one circle");

    return errors;
}

function get_count() {
    var errors = validate_form();
    if (errors.length) {
        /* handle errors */
        return;
    }
    var data = {};
    $("input, select").each(function (index, element) {
            data[element.name] = element.value;
        });

    var size_options = $("#id_size")[0].options;
    var sizes = new Array();
    for (var i = 0; i < size_options.length; i++) {
        if (size_options[i].selected)
            sizes.push(size_options[i].value);
    }
    data["size_data"] = sizes.join(",");
    $("#loading-image")[0].style.visibility = "visible";
    $.post("/filters/estimate-traffic/", 
           data,
           function (data, status) {
               $("#loading-image")[0].style.visibility = "hidden";
               if (data) {
                   var result = "Estimated matches: ";
                   if (data["scanned"] >= 750) {
                       $("#estimated-amount")[0].innerHTML = result + "N/A";
                   }
                   else {
                       var c = data["count"];
                       var s = "";
                       if (c < 2) {
                           s = "less than 1 per day";
                       }
                       else {
                           s = "approx " + Math.floor(c / 2) + " per day";
                       }
                       $("#estimated-amount")[0].innerHTML = result + s;
                   }
               }
           },
           "json");
}


function update_form() {
    var output_id = "estimated-amount";
    //Estimated matches: N/A

    if (!window["times"]) {
        window.times = 1;
    }
    else {
        window.times ++;
    }
    get_count();
    //$("#estimated-amount")[0].innerHTML = "Estimated matches: " + window.times;
}

$(document).ready(function () {
        $("input, select").change(function () {
                update_form();
            });
    });