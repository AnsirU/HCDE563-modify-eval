/*
    FILE: rebert_mainpage_ui.js
    REVISION: November, 2024
    CREATION DATE: June, 2024
    Author: David W. McDonald
    
    A JavaScript library for working with the rebert web interface.
    
    This version is for prototype 6
    
    Copyright by Author. All rights reserved. Not for reuse without express permissions.
*/

function hideAllSynopsis() {
    $('#synopsis_1').hide();
    $('#synopsis_2').hide();
    $('#synopsis_3').hide();
    $('#synopsis_4').hide();
    $('#synopsis_5').hide();
    $('#synopsis_6').hide();
    $("#synopsis_state").val(0);
};

function setSynopsisToPoster(slot) {
    var poster = "#poster_"+slot
    var toast = "#synopsis_"+slot
    var poff = $(poster).offset();
    var pheight = $(poster).outerHeight();
    var pwidth = $(poster).outerWidth();
    $(toast).css('top',poff.top);
    $(toast).css('left',poff.left);
    $(toast).outerWidth(pwidth);
    $(toast).outerHeight(pheight);
    $(toast).show();
}

function showSynopsis(slot) {
    var old_slot = $("#synopsis_state").val()
    if (old_slot != 0) {
        return
    }
    if (slot == 1) {
        setSynopsisToPoster(slot)
    } else if (slot == 2) {   
        setSynopsisToPoster(slot)
    } else if (slot == 3) {   
        setSynopsisToPoster(slot)
    } else if (slot == 4) {   
        setSynopsisToPoster(slot)
    } else if (slot == 5) {   
        setSynopsisToPoster(slot)
    } else if (slot == 6) {   
        setSynopsisToPoster(slot)
    };
    $("#synopsis_state").val(slot);
};

function setupSynopsis() {
    var slot = $("#synopsis_state").val()
    if (slot == 1) {
        setSynopsisToPoster(slot)
    } else if (slot == 2) {   
        setSynopsisToPoster(slot)
    } else if (slot == 3) {   
        setSynopsisToPoster(slot)
    } else if (slot == 4) {   
        setSynopsisToPoster(slot)
    } else if (slot == 5) {   
        setSynopsisToPoster(slot)
    } else if (slot == 6) {   
        setSynopsisToPoster(slot)
    };
    $("#synopsis_state").val(slot);
};

function hideSynopsisToast(slot) {
    if (slot == 1) {
        $('#synopsis_1').hide();
    } else if (slot == 2) {   
        $('#synopsis_2').hide();
    } else if (slot == 3) {   
        $('#synopsis_3').hide();
    } else if (slot == 4) {   
        $('#synopsis_4').hide();
    } else if (slot == 5) {   
        $('#synopsis_5').hide();
    } else if (slot == 6) {   
        $('#synopsis_6').hide();
    };
    $("#synopsis_state").val(-1);
};

function resetSynopsisState() {
    var old_slot = $("#synopsis_state").val()
    if (old_slot == -1) {
        $("#synopsis_state").val(0);
    };
};

var synopsisDelay = 850;
var synopsisHoverConst;

function setPosterSynopsisHover() {
    $( "#poster_1" ).on("mouseenter",
        function() {
            synopsisHoverConst = setTimeout(function() {
                showSynopsis(1); }, synopsisDelay) }
        ).on("mouseleave",
        function() {
            resetSynopsisState();
            clearTimeout(synopsisHoverConst); });
    $( "#poster_2" ).on("mouseenter",
        function() {
            synopsisHoverConst = setTimeout(function() {
                showSynopsis(2); }, synopsisDelay) }
        ).on("mouseleave",
        function() {
            resetSynopsisState();
            clearTimeout(synopsisHoverConst); });
    $( "#poster_3" ).on("mouseenter",
        function() {
            synopsisHoverConst = setTimeout(function() {
                showSynopsis(3); }, synopsisDelay) }
        ).on("mouseleave",
        function() {
            resetSynopsisState();
            clearTimeout(synopsisHoverConst); });
    $( "#poster_4" ).on("mouseenter",
        function() {
            synopsisHoverConst = setTimeout(function() {
                showSynopsis(4); }, synopsisDelay) }
        ).on("mouseleave",
        function() {
            resetSynopsisState();
            clearTimeout(synopsisHoverConst); });
    $( "#poster_5" ).on("mouseenter",
        function() {
            synopsisHoverConst = setTimeout(function() {
                showSynopsis(5); }, synopsisDelay) }
        ).on("mouseleave",
        function() {
            resetSynopsisState();
            clearTimeout(synopsisHoverConst); });
    $( "#poster_6" ).on("mouseenter",
        function() {
            synopsisHoverConst = setTimeout(function() {
                showSynopsis(6); }, synopsisDelay) }
        ).on("mouseleave",
        function() {
            resetSynopsisState();
            clearTimeout(synopsisHoverConst); });
};


//  ===============
//
//  EPHEMERAL RECOMMENDATION PROMPTS 
//  This is the code that is used to manage the 'ephemeral-questions'
//
//  ===============

function setupEphemeralQuestions() {
    var q_showing = $("#ephem_q_state").val()
    var s_showing = $("#ephem_s_state").val()
    hideAllSynopsis();
    if (q_showing > 0) {
        $('#ephemeral-questions').show();
    } else {
        $('#ephemeral-questions').hide();
    };
    if (s_showing > 0) {
        $('#ephemeral-solicitation').show();
    } else {
        $('#ephemeral-solicitation').hide();
    };
};


function showEphemeralQuestions() {
    var q_showing = $("#ephem_q_state").val()
    hideAllSynopsis();
    if (q_showing > 0) {
        $("#ephem_q_state").val(0);
        $("#ephem_s_state").val(1);
    } else {
        $("#ephem_q_state").val(1);
        $("#ephem_s_state").val(0);
    };
    setupEphemeralQuestions();
};




//  ===============
//
//  DISCUSS/CHAT AREA
//  This is the code that is used to manage the "Ask Rebert" discussion text area
//
//  ===============


//
//  Function hides all of the poster associated discussion flags
//
function hideAllDiscussFlags() {
    $('#discuss_slot_1').hide();
    $('#discuss_slot_2').hide();
    $('#discuss_slot_3').hide();
    $('#discuss_slot_4').hide();
    $('#discuss_slot_5').hide();
    $('#discuss_slot_6').hide();
};
//
//  Function hides any showing discssion flags and then shows the new flag based
//  on the specific slot number passed into the function
//
function showDiscussFlag(slot) {
    hideAllDiscussFlags();
    var old_slot = $("#discuss_state").val()
    if (slot == old_slot) {
        $('#converse').hide();
        $("#discuss_state").val(0);
        return
    };
    $('#converse').show();
    if (slot == 1) {
        $('#discuss_slot_1').show();
        $("#discuss_state").val(slot);
        $("#ask_output").val($("#discuss_1").val());
    } else if (slot == 2) {   
        $('#discuss_slot_2').show();
        $("#discuss_state").val(slot);
        $("#ask_output").val($("#discuss_2").val());
    } else if (slot == 3) {   
        $('#discuss_slot_3').show();
        $("#discuss_state").val(slot);
        $("#ask_output").val($("#discuss_3").val());
    } else if (slot == 4) {   
        $('#discuss_slot_4').show();
        $("#discuss_state").val(slot);
        $("#ask_output").val($("#discuss_4").val());
    } else if (slot == 5) {   
        $('#discuss_slot_5').show();
        $("#discuss_state").val(slot);
        $("#ask_output").val($("#discuss_5").val());
    } else if (slot == 6) {   
        $('#discuss_slot_6').show();
        $("#discuss_state").val(slot);
        $("#ask_output").val($("#discuss_6").val());
    };
};
//
//  Function this uses the existing state - supplied by the server to setup
//  the visual state of the discussion area
//
function setupDiscussFlag() {
    hideAllDiscussFlags();
    var slot = $("#discuss_state").val()
    if (slot == 0) {
        $('#converse').hide();
    } else {
        $('#converse').show();
    };
    if (slot == 1) {
        $('#discuss_slot_1').show();
        $("#discuss_state").val(slot);
        $("#ask_output").val($("#discuss_1").val());
    } else if (slot == 2) {   
        $('#discuss_slot_2').show();
        $("#discuss_state").val(slot);
        $("#ask_output").val($("#discuss_2").val());
    } else if (slot == 3) {   
        $('#discuss_slot_3').show();
        $("#discuss_state").val(slot);
        $("#ask_output").val($("#discuss_3").val());
    } else if (slot == 4) {   
        $('#discuss_slot_4').show();
        $("#discuss_state").val(slot);
        $("#ask_output").val($("#discuss_4").val());
    } else if (slot == 5) {   
        $('#discuss_slot_5').show();
        $("#discuss_state").val(slot);
        $("#ask_output").val($("#discuss_5").val());
    } else if (slot == 6) {   
        $('#discuss_slot_6').show();
        $("#discuss_state").val(slot);
        $("#ask_output").val($("#discuss_6").val());
    };
};

