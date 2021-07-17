// odoo.define('job_drawing_construction_contractingwebsite_portal', function(require) 

//it is usefull for hide footer but not working condition in 13. #odoo13 =---THIS JS IS NOT USED ANY MORE......
odoo.define('job_drawing_construction_contracting.website_portal', function(require) 
{
    'use strict';
var website = require('website.website');
    $(document).ready(function(e){
        if ($("#portal_drawing_document").html() == "True"){
            $("#footer").hide()
            $("div.navbar-static-top").hide()
            var textarea_length = $("textarea").length
            for (var i=0; i<textarea_length; i++){
                $("textarea")[i]['style']['borderColor'] = "#27BB64"
            }
            $("textarea").focus(function(){
                $(this)[0]['style']['borderColor'] = ""
            });
            $("textarea").focusout(function(){
                $(this)[0]['style']['borderColor'] = "#27BB64"
            });

            var select_length = $("select").length
            for (var i=0; i<select_length; i++){
                $("select")[i]['style']['borderColor'] = "#27BB64"
            }
            $("select").focus(function(){
                $(this)[0]['style']['borderColor'] = ""
            });
            $("select").focusout(function(){
                $(this)[0]['style']['borderColor'] = "#27BB64"
            });
            var input_length = $("input").length
            for (var i=0; i<input_length; i++){
                $("input")[i]['style']['borderColor'] = "#27BB64"
            }
            $("input").focus(function(){
                $(this)[0]['style']['borderColor'] = ""
            });
            $("input").focusout(function(){
                $(this)[0]['style']['borderColor'] = "#27BB64"
            });
            $("div.navbar-static-top")[0]['style']['color'] = "red"
        }
    });
});
