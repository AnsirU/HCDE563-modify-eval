/*
   FILE: rebert_audio.js
   REVISION: December, 2024
   CREATION DATE: December, 2024
   Author: David W. McDonald

   A JavaScript library for working with browser audio. This implements an element that allows
   text input with audio combined with a text box. It allows the user to speak answers to
   questions (about movies) and edit their answers before submitting them back to the server.
   An asynchronous fetch() is used to contact the server for the transcription. This asks
   permission to use the microphone, and has a modal alert that will respond to a denial of
   access. This library also 

   Copyright by Author. All rights reserved. Not for reuse without express permissions.
   
*/


/*  ========================================
    VARIABLES 
============================================ */
//
//  These variables support access to the audio components in the browser and maintain access
//  to the raw audio data.
//
var audio_has_permission = false;
var audio_stream = null;
var rebert_recorder = null;
var rebert_writeable = null;        // legacy, for a local write of the audio file
var rebert_audio_chunk_type = "";
var rebert_audio_chunks = null;
var rebert_audio_blob = null;

//
//  The server URL to use to fetch a transcription
//
var rebert_transcribe_URL = "/transcribe";

//
//  Variables related to the timers that run when audio is being recorded
//
var rebert_audio_timeout = 45000;       // this is currently 45 seconds, in miliseconds
//var rebert_audio_timeout = 10000;       // this is 10 seconds, for tesing timeout condition
var rebert_audio_timeout_timer = null;  // variable to hold the timeout timer
var rebert_audio_timed_out = false;     // did it time out - or user click it
var rebert_audio_interval = 200;        // 200ms or 0.2 seconds
var rebert_audio_interval_timer = null; // variable to hold the interval timer
var rebert_audio_progress_sum = 0;

//
//  A few UI components/controls that we use to control audio recording, transcription and
//  playback.
//
var start_button = null;                //  the button that starts a recording
var stop_button = null;                 //  the button that stops recording
var transcribe_button = null;           //  the button that stops AND transcribes
var play_button = null;                 //  a buttion that will play a recording
var submit_button = null;               //  the button that submits the answer
var append_to_area = null;              //  the textarea element where the
                                        //  trancription is added
var modal_no_perm = null;               //  jQuery, a modal dialog for no permissions
var audio_was_transcribed = false;      //  a flag - if the audio has been transcribed
var user_stop_recording = false;        //  did the user 'stop' the recording?

var notice_recording = null;            // jQuery element, notice shown when recording audio
var notice_transcribing = null;         // jQuery element, notice to show when transcribing
var notice_area = null;                 // jQuery element, the <div> element, where to show

//
//  The progress bar components that we need to display recording progress. This uses a
//  a series of green, yellow, and red, stacked bars to display the recording progress.
//
var rebert_progress_good = null;
var rebert_progress_caution = null;
var rebert_progress_danger = null;
var rebert_good_max = 0;
var rebert_caution_max = 0;


// 
//  This is the output, copied from each browsers' develper console from
//  early December 2024.
//
//  The transcription tool currently supports the following mimeTypes: 
//  flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, or webm.
//  
//  Google Chrome, Opera output (on MacOS)
//
//  Type 'audio/flac'   is NOT supported
//  Type 'audio/mp3'    is NOT supported
//  Type 'audio/mp4'    is SUPPORTED
//  Type 'video/mp4'    is SUPPORTED
//  Type 'audio/mpeg'   is NOT supported
//  Type 'video/mpeg'   is NOT supported
//  Type 'audio/ogg'    is NOT supported
//  Type 'video/ogg'    is NOT supported
//  Type 'audio/wav'    is NOT supported
//  Type 'audio/m4a'    is NOT supported
//  Type 'video/m4a'    is NOT supported
//  Type 'audio/mpga'   is NOT supported
//  Type 'video/mpga'   is NOT supported
//  Type 'audio/webm'   is SUPPORTED
//  Type 'video/webm'   is SUPPORTED
//  
//
//  Safari output (on MacOS)
//
//  Type 'audio/flac'   is NOT supported
//  Type 'audio/mp3'    is NOT supported
//  Type 'audio/mp4'    is SUPPORTED
//  Type 'video/mp4'    is SUPPORTED
//  Type 'audio/mpeg'   is NOT supported
//  Type 'video/mpeg'   is NOT supported
//  Type 'audio/ogg'    is NOT supported
//  Type 'video/ogg'    is NOT supported
//  Type 'audio/wav'    is NOT supported
//  Type 'audio/m4a'    is NOT supported
//  Type 'video/m4a'    is NOT supported
//  Type 'audio/mpga'   is NOT supported
//  Type 'video/mpga'   is NOT supported
//  Type 'audio/webm'   is NOT supported
//  Type 'video/webm'   is NOT supported
//  
//  
//  Firefox output (on MacOS)
//
//  Type ' audio/flac ' is NOT supported
//  Type ' audio/mp3 '  is NOT supported 
//  Type ' audio/mp4 '  is NOT supported 
//  Type ' video/mp4 '  is NOT supported 
//  Type ' audio/mpeg ' is NOT supported
//  Type ' video/mpeg ' is NOT supported
//  Type ' audio/ogg '  is SUPPORTED
//  Type ' video/ogg '  is NOT supported 
//  Type ' audio/wav '  is NOT supported 
//  Type ' audio/m4a '  is NOT supported 
//  Type ' video/m4a '  is NOT supported 
//  Type ' audio/mpga ' is NOT supported
//  Type ' video/mpga ' is NOT supported
//  Type ' audio/webm ' is SUPPORTED
//  Type ' video/webm ' is SUPPORTED
//


//
//  Two small functions that dump the supported media types. These are only
//  used for testing the supported media types in browser.
//
//function echoMediaTypesSupported(type) {
//    if (MediaRecorder.isTypeSupported(type)) {
//        console.log("Type '",type,"' is SUPPORTED")
//    } else {
//        console.log("Type '",type,"' is NOT supported")
//    };
//};
//
//function testMediaTypes() {
//    echoMediaTypesSupported("audio/flac");
//    echoMediaTypesSupported("audio/mp3");
//    echoMediaTypesSupported("audio/mp4");
//    echoMediaTypesSupported("video/mp4");
//    echoMediaTypesSupported("audio/mpeg");
//    echoMediaTypesSupported("video/mpeg");
//    echoMediaTypesSupported("audio/ogg");
//    echoMediaTypesSupported("video/ogg");
//    echoMediaTypesSupported("audio/wav");
//    echoMediaTypesSupported("audio/m4a");
//    echoMediaTypesSupported("video/m4a");
//    echoMediaTypesSupported("audio/mpga");
//    echoMediaTypesSupported("video/mpga");
//    echoMediaTypesSupported("audio/webm");
//    echoMediaTypesSupported("video/webm");
//};
//



/*  ========================================

    UI CONTROL SETUP AND STYLING

============================================ */

//
//  This initializes the components that make up the UI. Most of these
//  are accessed through DOM IDs, the modal is through the JQuery version
//  of the ID (e.g., "#<name>")
//
function setupAudioUIControls (start, stop, play, transcribe, submit, textarea, no_permission) {
    //  These are regular DOM elements
    //start_button = document.getElementById(start);
    //stop_button = document.getElementById(stop);
    //transcribe_button = document.getElementById(transcribe);
    //play_button = document.getElementById(play);
    //submit_button = document.getElementById(submit);
    //append_to_area = document.getElementById(textarea);
    //
    //  Using jQuery for to set up each of these elements
    start_button = $(start);
    stop_button = $(stop);
    play_button = $(play);
    transcribe_button = $(transcribe);
    submit_button = $(submit);
    append_to_area = $(textarea);
    modal_no_perm = $(no_permission);
    setupAudioActionListeners();
    //  If they're set up, set them to their initial state
    setStartAudioUIControl(true,"primary");
    setStopAudioUIControl(false,"hidden");
    setPlayAudioUIControl(false,"hidden");
    setTranscribeAudioUIControl(false,"secondary");
    setSubmitUIControl(false,"primary");
};

//
//  This function adds listeners to the button items for start, stop and play.
//  This could also be done by using the onclick=function() approach in the
//  HTML document. The action listeners follow from the use of the UI Control
//  set up function - and the enable/disable approach
//
function setupAudioActionListeners () {
//    if ( start_button ) {
//        start_button.addEventListener("click", audioStartRecording);
//    };
//    
//    if ( stop_button ) {
//        stop_button.addEventListener("click", audioTranscribeRecording);
//    };
//    
//    if ( transcribe_button ) {
//        stop_button.addEventListener("click", audioTranscribeRecording);
//    };
//    
//    if ( play_button ) {
//        play_button.addEventListener("click", audioPlayRecording);
//    };
//    
//    if ( append_to_area ) {
//        append_to_area.addEventListener("input", activateSubmitUIControl);
//    };

    if ( start_button ) {
        start_button.on("click", audioStartRecording);
    };
    
    if ( stop_button ) {
        stop_button.on("click", audioStopRecording);
    };
    
    if ( transcribe_button ) {
        transcribe_button.on("click", audioTranscribeRecording);
    };
    
    if ( play_button ) {
        play_button.on("click", audioPlayRecording);
    };
    
    if ( append_to_area ) {
        append_to_area.on("input", activateSubmitUIControl);
    };
};

//
//  A function that can be used to style or hide buttons. This is used to change
//  the state of the record, stop, and play buttons to indicate what is likely the
//  'next' step as a function of whether there is audio available
//
function styleAudioUIControl (button, enabled, style) {
//    if ( button ) {
//        if ( enabled ) {
//            button.disabled = false;
//        } else {
//            button.disabled = true;
//        };
//        if (style == "hidden") {
//            button.hidden = true;
//        } else if (style == "o-primary") {
//            button.setAttribute("class","btn btn-outline-primary");
//            button.hidden = false;
//        } else if (style == "o-secondary") {
//            button.setAttribute("class","btn btn-outline-secondary");
//            button.hidden = false;
//        } else if (style == "primary") {
//            button.setAttribute("class","btn btn-primary");
//            button.hidden = false;
//        } else if (style == "secondary") {
//            button.setAttribute("class","btn btn-secondary");
//            button.hidden = false;
//        };
    if ( button ) {
        if ( enabled ) {
            button.prop("disabled", false);
        } else {
            button.prop("disabled", true);
        };
        if (style == "hidden") {
            button.hide();
        } else if (style == "o-primary") {
            button.attr("class","btn btn-outline-primary");
            button.show()
        } else if (style == "o-secondary") {
            button.attr("class","btn btn-outline-secondary");
            button.show()
        } else if (style == "primary") {
            button.attr("class","btn btn-primary");
            button.show()
        } else if (style == "secondary") {
            button.attr("class","btn btn-secondary");
            button.show()
        };
    };
};

//
//  Style the 'start' recording button
//
function setStartAudioUIControl ( enabled, style ) {
    if ( start_button ) {
        styleAudioUIControl(start_button, enabled, style);
    };
};

//
//  Style the 'stop' recording button 
//
function setStopAudioUIControl ( enabled, style ) {
    if ( stop_button ) {
        styleAudioUIControl(stop_button, enabled, style);
    };
};

//
//  Style the 'transcribe' recording button
//
function setTranscribeAudioUIControl ( enabled, style ) {
    if ( transcribe_button ) {
        styleAudioUIControl(transcribe_button, enabled, style);
    };
};

//
//  Style the 'play' button - only active when there is audio in the
//  buffer that could be played
//
function setPlayAudioUIControl ( enabled, style ) {
    if ( play_button ) {
        styleAudioUIControl(play_button, enabled, style);
    };
};

//
//  Style the 'submit' button - should only be active when there is
//  text in the text area and NOT recording
//
function setSubmitUIControl ( enabled, style ) {
    if ( submit_button ) {
        styleAudioUIControl(submit_button, enabled, style);
    };
};


//
//  Activate the 'submit' button on a condition where there
//  is some text in the text area
//
function activateSubmitUIControl( ) {
    if ( append_to_area ) {
        var content = append_to_area.val()
        if ( content ) {
            setSubmitUIControl(true,"primary");
        } else {
            setSubmitUIControl(false,"primary");
        };
    };
};

//
//  Set up the progress bar. This calculates how many miliseconds to stay in each
//  state of 'good', or 'caution' with the 'danger' being the remains
//
function setupAudioUIProgress (good, good_pct, caution, caution_pct, danger, danger_pct) {
    rebert_progress_good = document.getElementById(good);
    rebert_progress_caution = document.getElementById(caution);
    rebert_progress_danger = document.getElementById(danger);
    
    rebert_good_max = rebert_audio_timeout * (good_pct/100.0);
    rebert_caution_max = rebert_good_max + (rebert_audio_timeout * (caution_pct/100.0));
    //console.log("good_max: ",rebert_good_max," caution_max: ",rebert_caution_max)
    resetAudioProgress();
};

//
//  Reset the audio progress bar to it's initial state, 0% for each stacked bar.
//
function resetAudioProgress () {
    if (rebert_progress_good) {
        rebert_progress_good.style.width = "0%"
    };
    if (rebert_progress_caution) {
        rebert_progress_caution.style.width = "0%"
    };
    if (rebert_progress_danger) {
        rebert_progress_danger.style.width = "0%"
    };
};

//
//  This function is called by a timer to update the audio recording progress bar.
//  Each time the function is called, it calculates the percentage filled for 
//  the stacked progress indicators 'good', 'caution', and 'danger'. Those values
//  are then set on the UI components.
//
function updateAudioProgress() {
    //  Add the update interval, but trap the value to the maximum allowed
    rebert_audio_progress_sum = rebert_audio_progress_sum + rebert_audio_interval;
    if (rebert_audio_progress_sum > rebert_audio_timeout) {
        rebert_audio_progress_sum = rebert_audio_timeout
    }
    
    //  Variables used to set the style of the progress bar
    var style = ""
    var width = "width: "
    var percentage = 0.0
    
    //  If we're exclusively in the 'good' range
    if (rebert_audio_progress_sum <= rebert_good_max) {
        percentage = (rebert_audio_progress_sum / rebert_good_max) * 100;
        width = width + percentage.toString();
        style = width.split('.')[0] + "%";
        width = style.split(' ')[1];
        if (rebert_progress_good) {
            rebert_progress_good.style.width = width;
            console.log("progress_good: ",width);
        };
        return
    };
    
    //  If we're past the 'good' range, and still in the 'caution' range 
    if (rebert_audio_progress_sum <= rebert_caution_max) {
        var caution_amount = rebert_audio_progress_sum - rebert_good_max;
        percentage = (caution_amount / (rebert_caution_max - rebert_good_max)) * 100;
        width = width + percentage.toString();
        style = width.split('.')[0] + "%";
        width = style.split(' ')[1];
        if (rebert_progress_good) {
            rebert_progress_good.style.width = "100%";
        };
        if (rebert_progress_caution) {
            rebert_progress_caution.style.width = width;
            console.log("progress_caution: ",width);
        };
        return
    };
    
    //  We're in the 'danger' range
    var danger_amount = rebert_audio_progress_sum - rebert_caution_max;
    percentage = (danger_amount/(rebert_audio_timeout-rebert_caution_max)) * 100;
    width = width + percentage.toString();
    style = width.split('.')[0] + "%";
    width = style.split(' ')[1];
    if (rebert_progress_good) {
        rebert_progress_good.style.width = "100%";
    };
    if (rebert_progress_caution) {
        rebert_progress_caution.style.width = "100%";
    };
    if (rebert_progress_danger) {
        rebert_progress_danger.style.width = width;
    };
};


/*  ========================================

    NOTICES

============================================ */

//
//  This is setup for jQuery access to these UI components. The assumption is that
//  there will be three things: a <div> or element that is used for a "recording in
//  progress" (notice_recording), a <div> or element that is used for a "transcribing
//  in progress" (notice_transcribing), and an area <div> or other element that these
//  notices will overlay when they are being displayed.
//
function setupAudioWaitAlerts (elt_record, elt_transcribe, area) {
    if ( elt_record ) {
        notice_recording = $(elt_record);
        notice_recording.hide();
    };
    if ( elt_transcribe ) {
        notice_transcribing = $(elt_transcribe);
        notice_transcribing.hide();
    };
    if ( area ) {
        notice_area = $(area);
    };
    // These update the positions of these to cover the notice area 
    // and then makes sure they are hidden
    showNoticeRecording(false);
    showNoticeTranscribing(false);
};

//
//  We will update the placement right before the show()
//  This does not update the positioning dynamically - say like on a window resize
//
function showNoticeRecording (visible) {
    if ( notice_recording ) {
        if ( notice_area ) {
            var ta_off = notice_area.offset();
            var ta_height = notice_area.outerHeight();
            var ta_width = notice_area.outerWidth();
            //console.log("recording notice coordinates: ",ta_off.top,ta_off.left,ta_height,ta_width);
            notice_recording.css('top',ta_off.top);
            notice_recording.css('left',ta_off.left);
            notice_recording.outerWidth(ta_width);
            notice_recording.outerHeight(ta_height);
            if ( visible ) {
                notice_recording.show();
            } else {
                notice_recording.hide();
            };
        };
    };
};

//
//  We will update the placement right before the show()
//  This does not update the positioning dynamically - say like on a window resize
//
function showNoticeTranscribing (visible) {
    if ( notice_transcribing ) {
        if ( notice_area ) {
            var ta_off = notice_area.offset();
            var ta_height = notice_area.outerHeight();
            var ta_width = notice_area.outerWidth();
            //console.log("transcribing notice coordinates: ",ta_off.top,ta_off.left,ta_height,ta_width);
            notice_transcribing.css('top',ta_off.top);
            notice_transcribing.css('left',ta_off.left);
            notice_transcribing.outerWidth(ta_width);
            notice_transcribing.outerHeight(ta_height);
            if ( visible ) {
                notice_transcribing.show();
            } else {
                notice_transcribing.hide();
            };
        };
    };
};


/*  ========================================

    FUNCTIONS/ACTIONS 

============================================ */


//
//  We need to ask permission from the user to access their microphone
//
async function audioRequestPermission () {
    //
    try {
        //  Get permission initialize the audio stream
        audio_stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        rebert_recorder = null;
        audio_has_permission = true;
    } catch (err) {
        audio_stream = null;
        rebert_recorder = null;
        audio_has_permission = false;
        if ( modal_no_perm ) {
            modal_no_perm.modal('show')
        };
    };
    return audio_has_permission;
};


//
//  When the MediaRecorder has completed a chunk, this function is
//  called to add a chunk to the growing audio buffer. That buffer is
//  eventually sent to the server to be transcribed.
//
function appendAudioChunk ( data ) {
    if ( !data ) return;
    if ( !rebert_audio_chunks ) {
        rebert_audio_chunks = new Array();
    };
    rebert_audio_chunk_type = data.type;
    rebert_audio_chunks.push(data)
};


//
//  This action starts the recording process
//
async function audioStartRecording () {
    //
    //  First make sure we have permission to record
    if (!audio_has_permission) {
        audio_has_permission = await audioRequestPermission();
        if (!audio_has_permission) return;
    };
    //
    //  Empty all of the old buffers, and make sure the progress bar
    //  is in the inital state
    rebert_audio_chunks = null;
    rebert_audio_blob = null;
    rebert_audio_chunk_type = "";
    audio_was_transcribed = false;
    user_stop_recording = false;
    resetAudioProgress()
    //
    //  Based on the media types supported code, there are only a few supported
    //  types on each browser.
    //
    //  Supported on Chrome & Opera under MacOS
    //rebert_recorder = new MediaRecorder(audio_stream, { mimeType: "audio/mp4" } );
    //rebert_recorder = new MediaRecorder(audio_stream, { mimeType: "audio/webm" } );
    //
    //  Supported on Safari under MacOS
    //rebert_recorder = new MediaRecorder(audio_stream, { mimeType: "audio/mp4" } );
    //
    //  Supported on Firefox under MacOS
    //rebert_recorder = new MediaRecorder(audio_stream, { mimeType: "audio/ogg" } );
    //rebert_recorder = new MediaRecorder(audio_stream, { mimeType: "audio/webm" } );
    //
    //  Under all of those browsers the default will work with the transcriber
    //  API that we are planning to use. So, set this up using the default and
    //  assume it will work across *most* browsers.
    rebert_recorder = new MediaRecorder(audio_stream);
    //
    //  Update the button status - to indicate we're recording that that the
    //  'stop' (or transcribe) button is the thing you should proably click next.
    setStartAudioUIControl(false,"hidden");
    setStopAudioUIControl(true,"primary");
    setTranscribeAudioUIControl(true,"primary");
    setPlayAudioUIControl(false,"hidden");
    //  Disable the submit control while we are recording
    setSubmitUIControl(false,"primary");
    
    //  Start the recording - if it's a lot of data then add the chunks to
    //  the chunk buffer as they are produced.
    rebert_recorder.start();
    rebert_recorder.addEventListener("dataavailable", async (event) => {
        appendAudioChunk(event.data);
    });
    
    //  Start two timers. The first is an interval timer that updates the audio
    //  recording progress bar. The second is a timout timer that stops the
    //  recording when it expires.
    rebert_audio_interval_timer = setInterval(updateAudioProgress, rebert_audio_interval);
    rebert_audio_timeout_timer = setTimeout(audioTimeoutStop, rebert_audio_timeout);
    //  
    //  Show the notice that recording is in progress
    showNoticeRecording(true);
};

//
//  This will stop the audio recording because the timer expired.
//
function audioTimeoutStop () {
    //
    //  stop recording and note that this was a timeout
    rebert_recorder.stop();
    rebert_audio_timed_out = true;

    //  Clear the interval timer - the one for the progress bar
    if ( rebert_audio_interval_timer ) {
        clearInterval(rebert_audio_interval_timer);
        rebert_audio_progress_sum = 0;
        rebert_audio_interval_timer = null;
    };
    //
    //  Clear the timeout timer - the one that stops the recording
    if ( rebert_audio_timeout_timer ) {
        clearTimeout(rebert_audio_timeout_timer);
        rebert_audio_timeout_timer = null;
    };
    //
    //  There should have been a 'recording in progress' notice showing
    //  If we have a reference to that, hide it
    if ( notice_recording ) {
        notice_recording.hide();
    };
    
    //
    //  Reset the audio controls
    setStartAudioUIControl(true,"o-primary");
    setStopAudioUIControl(false,"hidden");
    setTranscribeAudioUIControl(true,"primary");
    setPlayAudioUIControl(true,"o-primary");
    //  Enable the submit once done recording
    activateSubmitUIControl();
    //setSubmitUIControl(true,"primary");
    //
    //  Reset the progress bar
    resetAudioProgress();

};

//
//  STOP the audio recording. This function stops the recording but
//  it does NOT request transcription. This function could be used
//  to separate the STOP from the transcription.
//
function audioStopRecording () {
    //
    //  stop the recording
    rebert_recorder.stop();
    rebert_audio_timed_out = false;

    //  Clear the interval timer - the one for the progress bar
    if ( rebert_audio_interval_timer ) {
        clearInterval(rebert_audio_interval_timer);
        rebert_audio_progress_sum = 0;
        rebert_audio_interval_timer = null;
    };
    //
    //  Clear the timeout timer - the one that stops the recording
    if ( rebert_audio_timeout_timer ) {
        clearTimeout(rebert_audio_timeout_timer);
        rebert_audio_timeout_timer = null;
    };
    //
    //  There should have been a 'recording in progress' notice showing
    //  If we have a reference to that, hide it
    if ( notice_recording ) {
        notice_recording.hide();
    };
    //
    //  Note that the user manually stopped the recording
    user_stop_recording = true;
    //
    //  Reset the audio controls
    setStartAudioUIControl(true,"o-primary");
    setStopAudioUIControl(false,"hidden");
    setTranscribeAudioUIControl(true,"primary");
    setPlayAudioUIControl(true,"o-primary");
    //
    //  Enable the submit once done recording
    activateSubmitUIControl();
    //
    //  Reset the progress bar
    resetAudioProgress();
};

//
//  Request that the server transcribe and return the text of the audio
//
async function fetchAudioTranscription() {
    console.log("fetchAudioTranscription()")
    //  Prevent two attempts at transcribing by disabling the button
    setStopAudioUIControl(false,"hidden");
    setStartAudioUIControl(true,"o-primary");
    setTranscribeAudioUIControl(false,"secondary");
    //
    //  Show the notice that we are now transcribing
    showNoticeTranscribing(true);
    //
    //  Then we create a blob that can be used for playback or send to
    //  server for transcription
    if (!rebert_audio_blob) {
        //console.log("looks like audio chunks are: ", rebert_audio_chunk_type);
        rebert_audio_blob = new Blob(rebert_audio_chunks,{ type: rebert_audio_chunk_type });
        rebert_audio_chunks = null;
        rebert_audio_chunk_type = "";
    };
    console.log("looks like resulting blob is: ", rebert_audio_blob.type);
    //  Create a sample file name that can be used when posting the data 
    //  back to the server
    media_type = rebert_audio_blob.type.split(';')[0]
    suffix = media_type.replace("/",".")
    fname = "user_audio_"+suffix
    //console.log("using filename: ", fname);
    //
    //  See if we can get a session id from the current page
    var session_field = $('#session_id');
    var session_id = "";
    if ( session_field ) {
        session_id = session_field.val()
        //console.log("got session_id: ", session_id);
    }
    //
    //  Create a form to use to post back the data this should be a 
    //  multi-part MIME form
    var rebert_audio_form = new FormData();
    //
    //  Set the session id - either the id or an empty string
    rebert_audio_form.append('session_id', session_id)
    //  Fill the form data - key, file data, and file name
    rebert_audio_form.append('file', rebert_audio_blob, fname)
    //
    //  Given all of the ways this can go wrong, the actual request is
    //  placed in a try block
    try {
        //  The fetch function - specified by the rebert_transcribe_URL
        var response = await fetch(rebert_transcribe_URL, {
            method: 'POST',
            body: rebert_audio_form
        });
        
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        };
        
        audio_was_transcribed = true;
        var text = "";
        var transcript_json = await response.text();
        var transcript = JSON.parse(transcript_json)
        //  Append the transcript to the specified textarea, if one
        //  was specified - or skip it.
        if ( append_to_area ) {
            //text = append_to_area.value;
            text = append_to_area.val();
            if (text) {
                //text = text+"\n"+transcript_json
                text = text+"\n"+transcript.text
            } else {
                //text = transcript_json
                text = transcript.text
            };
            //append_to_area.value = text;
            append_to_area.val(text);
            //console.log("Got transcript:", transcript_json);
            console.log("Got transcript:", transcript.text);
            //
            //  Only when this async function is done will this
            //  be activated - assuming there is some text
            activateSubmitUIControl();
        };
        //
        // NOTE: This is dependent upon code from rebert_rating_ui.js
        //
        if ( transcript.titles ) {
            // from rebert_rating_ui.js file
            setupTitleConfirmation(transcript.titles);
        };
    //
    //  If there is some kind of error/exception catch it and post that
    //  to the console - also try to enable transcription
    } catch (error) {
        //  Re-enable the transcription button - maybe we can try again?
        setStartAudioUIControl(true,"o-primary");
        setStopAudioUIControl(false,"hidden");
        setTranscribeAudioUIControl(true,"primary");
        console.error(error.message);
    };
    //
    //  Once we finish the transcription, hide the notice
    if ( notice_transcribing ) {
        notice_transcribing.hide();
    };
    //  Enable the submit once done fetching transcription
    //activateSubmitUIControl();
};


//
//  STOP the recording and TRANSCRIBE the audio file with a request
//  to the server
//
async function audioTranscribeRecording () {
    //
    //  Disable the submit button if we are transcribing
    setSubmitUIControl(false,"primary");
    //  Disable the other buttons while transcription is happening
    setStartAudioUIControl(false,"o-primary");
    setStopAudioUIControl(false,"hidden");
    setPlayAudioUIControl(false,"o-primary");
    setTranscribeAudioUIControl(false,"secondary");
    //
    //  Clear the interval timer - the one for the progress bar
    if ( rebert_audio_interval_timer ) {
        clearInterval(rebert_audio_interval_timer);
        rebert_audio_progress_sum = 0;
        rebert_audio_interval_timer = null;
    };
    //
    //  Clear the timeout timer - the one that stops the recording
    if ( rebert_audio_timeout_timer ) {
        clearTimeout(rebert_audio_timeout_timer);
        rebert_audio_timeout_timer = null;
    };
    //
    //  There should have been a 'recording in progress' notice showing
    //  If we have a reference to that, hide it
    if ( notice_recording ) {
        notice_recording.hide();
    };
    //
    //  We add the event listener, to make sure the recorder has finished
    //  and that the data is in the rebert_audio_chunks buffer array
    if ( rebert_audio_timed_out || user_stop_recording ) {
        //  When the timeout happens, then there is "lots" of time for
        //  the buffer action listener to get the data. In this case
        //  we just try to fetch the transcription
        await fetchAudioTranscription();
    } else {
        //  When it is NOT a timout, then we need to artifically wait for
        //  the audio to signal that it has stopped. This allows time for
        //  the data to be transferred into the rebert_audio_chunks buffer
        rebert_recorder.stop();
        rebert_recorder.addEventListener("stop", async (event) => {
            await fetchAudioTranscription();
        });
    };
    //
    //  Reset the timeout flag - we should not allow another call to 
    //  the transcribing action.
    rebert_audio_timed_out = false;
    //
    //  Reset the audio controls
    setStartAudioUIControl(true,"primary");
    setStopAudioUIControl(false,"hidden");
    setPlayAudioUIControl(true,"o-primary");
    setTranscribeAudioUIControl(false,"secondary");
    //
    //  Enable the submit once done with the transcription
    activateSubmitUIControl();
    //
    //  Reset the progress bar
    resetAudioProgress();
};

//
//  PLAY the audio recording that is available in the buffer.
//
async function audioPlayRecording () {
    //
    //  First set the button states.
    //  Prevent two 'play' clicks - don't want it to play twice
    setPlayAudioUIControl(false,"o-primary");
    setStopAudioUIControl(false,"hidden");
    if ( audio_was_transcribed ) {
        setTranscribeAudioUIControl(false,"secondary");
        setStartAudioUIControl(false,"primary");
    } else {
        setTranscribeAudioUIControl(false,"primary");
        setStartAudioUIControl(false,"o-primary");
    };
    //
    //  Reset the progress bar to zero
    resetAudioProgress()
    
    //
    //  If the blob - the contatenated audio chunks - has not been
    //  created then try to creat that blob
    if (!rebert_audio_blob) {
        //console.log("creating blob of type: ", rebert_audio_chunk_type);
        rebert_audio_blob = new Blob(rebert_audio_chunks,{ type: rebert_audio_chunk_type });
        rebert_audio_chunks = null;
        rebert_audio_chunk_type = "";
    };
    //
    //  Using the blob create a local audio URL
    const audio_URL = URL.createObjectURL(rebert_audio_blob);
    const audio = new Audio(audio_URL);
    //console.log("looks like resulting blob is: ", rebert_audio_blob.type);
    
    //
    //  Make sure that the full audio is loaded and ready, when it is
    //  then play that audio  
    audio.addEventListener("canplaythrough", (event) => {
        audio.play();
    });
    
    //
    //  Once the audio has stopped playing then reset the play control
    //  so that it is possible to play it again
    audio.addEventListener("ended", function() {
        setPlayAudioUIControl(true,"o-primary");
        setStopAudioUIControl(false,"hidden");
        if ( audio_was_transcribed ) {
            setTranscribeAudioUIControl(false,"secondary");
            setStartAudioUIControl(true,"primary");
        } else {
            setTranscribeAudioUIControl(true,"primary");
            setStartAudioUIControl(true,"o-primary");
        };
    });
};


/*  ========================================

    END of rebert_audio.js 

============================================ */
