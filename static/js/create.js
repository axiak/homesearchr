
function validate_form() {
    var errors = new Array();
    if (!$("#id_email")[0].value)
        errors.push("Please enter a valid email address.");

    if (!$("#id_expires")[0].value)
        errors.push("Please enter a valid expiration date.");

    return validate_apt_form(errors);
}

function validate_apt_form(errors) {
    if (typeof(errors) != "object") {
        errors = new Array();
    }
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
    var errors = validate_apt_form();
    if (errors.length) {
        /* handle errors */
        $("#estimated-amount")[0].innerHTML = "Estimated matches: <small><em>please complete the form</em></small>";
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

$(document).ready(function (e) {
        $("input, select").change(function () {
                update_form();
            });

        $("p.required input, p.required select").each(function (v, elem) {
                if (elem.className) {
                    elem.className += " required";
                }
                else {
                    elem.className = "required";
                }
            });

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

        $("#mainform").validate({
                debug: true
                    });

    });
