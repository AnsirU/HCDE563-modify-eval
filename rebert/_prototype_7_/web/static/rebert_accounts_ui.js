/*
    FILE: rebert_accounts_ui.js
    REVISION: January, 2025
    CREATION DATE: January, 2025
    Author: David W. McDonald

    A JavaScript library for working with the UI components of user account creation and
    user login
    
    Copyright by Author. All rights reserved. Not for reuse without express permissions.
*/

//
//  Toggle the password entry field type to either hide or show the
//  password text when the user wants to see or hide. This relies on
//  the bootstrap icons. Icons need to be loaded before this will work.
function togglePasswordFieldType() {
    var pass1_elt = $("#password_text1_input");
    var togg1_icn = $("#pass1_vis_icn");
    var pass1_type = pass1_elt.attr("type");
    //console.log("pass1_elt_type: ",pass1_type)
    if ( pass1_type == "password" ) {
        // jQuery remove/add attributes - just set the whole thing
        pass1_elt.attr('type','text');
        togg1_icn.attr('class', 'bi bi-eye');
    } else {
        // jQuery remove/add attributes - just set the whole thing
        pass1_elt.attr('type','password');
        togg1_icn.attr('class', 'bi bi-eye-slash');
    };

    //  Check wether or not we have a second password field for matching on
    //  account creation   
    var pass2_elt = $("#password_text2_input");
    var pass2_type = pass2_elt.attr("type");
    //console.log("pass2_elt_type: ",pass2_type)
    if ( pass2_type == "password" ) {
        pass2_elt.attr('type','text');
    } else {
        pass2_elt.attr('type','password');
    };
};

//
//  Adds a listener to the button that is used to toggle the visiblity of
//  passwords in the UI. When the user clicks the button, then it calls
//  the toggle function to change the input type to either hide the password
//  text or show the password text.
function addPasswordToggleListener() {
    var togg_elt = $("#pass1_toggle");
    if ( togg_elt ) {
        //togg_elt.addEventListener("click", togglePasswordFieldType);
        togg_elt.on("click", togglePasswordFieldType);
    };
};

//
//  This validates that two passwords are the same. This does not prevent
//  a user from submitting different passwords, so that needs to be validated
//  in the server before creation of an account. It is just to give the user
//  a visual indicator that they are (or are not) the same.
function comparePasswordChars() {
    var pass1_elt = $("#password_text1_input");
    var pass2_elt = $("#password_text2_input");
    //  Check whether the values are the same in the two fields
    var pass1_chars = pass1_elt.val();
    var pass2_chars = pass2_elt.val();
    if ( pass2_chars ) {
        if ( pass1_chars == pass2_chars ) {
            //  If the characters are the same make it look regular
            pass2_elt.attr('class','form-control');
        } else {
            //  If the characters are different - show the field light red
            pass2_elt.attr('class','form-control text-bg-danger bg-opacity-10 text-body');
        };
    } else {
        //  No caracters in the field - make it regular
        pass2_elt.attr('class','form-control');
    };
};

//
//  Adds a listener to the input field of the second password entry field. 
//  On a 'keyup' it will compare the two password strings.
function addPasswordComparisonListener() {
    var pass2_elt = $("#password_text2_input");
    if ( pass2_elt ) {
        pass2_elt.on("keyup", comparePasswordChars);
    };
};


