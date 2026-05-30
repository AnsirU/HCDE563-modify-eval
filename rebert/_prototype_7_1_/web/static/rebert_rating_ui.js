/*
    FILE: rebert_rating_ui.js
    REVISION: February, 2025
    CREATION DATE: February, 2025
    Author: David W. McDonald

    A JavaScript library for working with the UI components of the movie rating interface
    
    Copyright by Author. All rights reserved. Not for reuse without express permissions.
*/


//
//  The server URL to use to fetch a transcription
//
var rebert_movie_info_URL = "/movie_info";



//
//  Set up the UI components on the rating page
//
function setupRatingPageUI() {
    var starting = $("#rate_start");
    // If this is a follow-up question, then we don't need the
    // special question setup, maybe something else?
    if ( !starting.val() ) {
        //console.log("Set-up: follow-up question", starting.val());
        var question = $('#rating_question_input');
        //console.log("Q:", question.val());
        // every now and then, the input field is not updated with
        // the question ... maybe we need to use this to force set
        // the question in the input field?
    } else {
        // If we're just starting to rate set up the inital question controls
        //console.log("Set-up: starting rating, initital question", starting.val());
        var dropdown = $("#rating-question-dropdown");
        var question = $('#rating_question_input');
        // Find all of the list items in the dropdown
        var dropdown_len = dropdown.find('li').length;
        //console.log("dropdown_len:",dropdown_len)
        // Pick a random index in the range 0 .. (dropdown_len-1)
        var random_index = Math.floor(Math.random() * (dropdown_len))
        //console.log("random_index:",random_index)
        //var item = dropdown.children('li').eq(0);
        // Grab that index item
        var item = dropdown.children('li').eq(random_index);
        // Set that item into the text field
        question.val(item.text());
        addRatingQuestionTextListener();
    };
    
    // Now, check to see if this page came with some title candidates
    var candidates = $("#title_candidates");
    //console.log("Candidates:", candidates.val());
    var matched_movie = $("#matched_tmdb_id");
    //console.log("Not matched:", !matched_movie.val());
    // If we have title candidates and do NOT have a matched movie
    if ( candidates.val() && !matched_movie.val() ) { 
        showTitleConfirmation(true);
        addTitleConfirmationDropdownListener();
    };
    
    if ( matched_movie.val() ) { 
        console.log("setup - matched_movie: ", matched_movie.val());
        // Set the initial value of the drop down
        //var match_index = Number($("#matched_index").val());
        var match_index = $("#matched_index").val();
        console.log("setup - matched_index: ", match_index);
        // 
        var dropdown = $("#rating-movie-title-dropdown");
        var list_item = dropdown.children('li').eq((match_index-1));
        //  Fix for special case when user creates their own record
        if ( match_index == 0 ) {
            list_item = dropdown.children('li').eq(0);
        }
        //$('#rating_movie_title_input').val(list_item.text());
        var anchor = list_item.children('a').eq(0)
        //var tmdb_id = anchor.attr("tmdb_id");
        var title = anchor.attr("title");
        $('#rating_movie_title_input').val(title);
        //
        //  Fetch the data that fills in the fields
        fetchMovieInfo(title, matched_movie.val(), match_index);
        //  Try to add this selector last
        addMatchedMovieDropdownListener();
        //  Should only have the score on an 'edit' movie
        var rating = $("#current_score");
        if ( rating ) {
            if ( rating.val() < 0 ) {
                $('#score_movie_input').val("None");
            } else {
                $('#score_movie_input').val(rating.val());
            };
        };
        addMovieScoreDropdownListener();
    };
    
};



//
//  Updates the movie question they are answering
//
function addRatingQuestionTextListener() {
    var rate_item = $("#rating-question-dropdown li");
    if ( rate_item ) {
        rate_item.on("click", function(){
            $('#rating_question_input').val($(this).text());
        });
    };
};



//
//  Given a potential title list, this sets the movie title
//  confirmation UI element (text input).
//
function setupTitleConfirmation(title_list) {
    var matched_movie = $("#matched_movie");
    // If we have a matched title, then we can skip all of this
    //console.log("Matched:", matched_movie.val());
    if ( matched_movie.val() ) { return };
    // Return if title_list is not an array
    if ( !Array.isArray(title_list) ) { return };
    // Return if list is empty, no need to show title confirmation
    if ( title_list.length == 0 )  { return };
    var dropdown = $("#title-confirmation-dropdown");
    var input_text = $('#title_confirmation_text');
    // Add the titles to the dropdown list
    for (var title of title_list) {
        var new_item = '<li><a class="dropdown-item" href="#">'+title+'</a></li>\n';
        dropdown.append(new_item);
    };
    var item = dropdown.children('li').eq(0);
    // Update the value in the text field - only if it is empty
    if ( !input_text.val() ) { 
        input_text.val(item.text());
    };
    // Insert a blank at the start, to make it easy to clear
    //var blank_item = '<li><a class="dropdown-item" href="#">&nbsp;</a></li>\n';
    //dropdown.prepend(blank_item);
    showTitleConfirmation(true);
    addTitleConfirmationDropdownListener();
};

//
//  Shows or not, the title confirmation area
//
function showTitleConfirmation(visible) {
    if (visible) {
        $('#title-confirmation-area').show();
    } else {
        $('#title-confirmation-area').hide();
    };
};

//
//  Updates the movie title confirmation text 
//  While rating a movie - this tries to guess the title but does not
//  necessarily a "match"
//
function addTitleConfirmationDropdownListener() {
    var title_item = $("#title-confirmation-dropdown li");
    if ( title_item ) {
        title_item.on("click", function(){
            var selected_text = $(this).text();
            $('#title_confirmation_text').val(selected_text);
        });
    };
};

//
//  This updates the 'matched' movie selected by the participant
//  The presentation of the title in the list shows the year to help disambiguate
//  movies that have the same title.
//
function addMatchedMovieDropdownListener() {
    var title_item = $("#rating-movie-title-dropdown li");
    if ( title_item ) {
        title_item.on("click", function(){
            var selected_text = $(this).text();
            var anchor = $(this).children('a').eq(0)
            var tmdb_id = anchor.attr("tmdb_id");
            var title = anchor.attr("title");
            //var title = selected_text.slice(0,selected_text.length-6);
            //console.log("tmdb_id: ", tmdb_id);
            //console.log("title: ", title);
            //$('#rating_movie_title_input').val($(this).text());
            $('#rating_movie_title_input').val(title);
            fetchMovieInfo(title, tmdb_id, -1);
        });
    };
};


function addMovieScoreDropdownListener() {
    var score_item = $("#score-movie-dropdown li");
    if ( score_item ) {
        score_item.on("click", function(){
            var selected_text = $(this).text();
            $('#score_movie_input').val(selected_text);
        });
    };
};



//
//  Request movie information for a specific movie
//
async function fetchMovieInfo(title, tmdb_id, match_index) {
    console.log("fetchMovieInfo()");
    console.log("title: ", title);
    console.log("tmdb_id: ", tmdb_id);
    console.log("match_index: ", match_index);
    //
    //  See if we can get a session id from the current page
    var session_field = $('#session_id');
    var session_id = "";
    if ( session_field.val() ) {
        session_id = session_field.val();
        //console.log("session_id: ", session_id);
    }
    var editing_field = $('#edit_rating');
    var editing = "";
    if ( editing_field.val() ) {
        editing = editing_field.val();
        //console.log("editing: ", editing);
    }
    //
    //  Create a form to use to post back the data this should be a 
    //  multi-part MIME form
    var rebert_movie_info_form = new FormData();
    rebert_movie_info_form.append('session_id', session_id)
    rebert_movie_info_form.append('title', title)
    rebert_movie_info_form.append('tmdb_id', tmdb_id)
    rebert_movie_info_form.append('match_index', match_index)
    rebert_movie_info_form.append('edit_rating', editing)
    //
    //  Given all of the ways this can go wrong, the actual request is
    //  placed in a try block
    try {
        //  The fetch function - get the movie info
        var response = await fetch(rebert_movie_info_URL, {
            method: 'POST',
            body: rebert_movie_info_form
        });
        
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        };
        
        var movie_info_json = await response.text();
        var movie_info = JSON.parse(movie_info_json)
        var year_field = $('#matched_year');
        var genre_field = $('#matched_genres');
        var synopsis_field = $('#matched_synopsis');
        var index_field = $('#matched_index');
        
        //if ( movie_info.error ) {
        //    console.log("ERROR");
        //    console.log(movie_info_json);
        //} else {
        //    console.log("Received response: no error");
        //}; 
        
        if ( year_field ) {
            year_field.val(movie_info.year)
            //console.log("Got Year:", movie_info.year);
        } else {
            console.log("field 'matched_year' was not found. Year:", movie_info.year);
        };
        
        if ( genre_field ) {
            genre_field.val(movie_info.genre)
            //console.log("Got Genre:", movie_info.genre);
        } else {
            console.log("field 'matched_genres' was not found. Genre:", movie_info.genre);
        }
        
        if ( synopsis_field ) {
            synopsis_field.val(movie_info.synopsis)
            //console.log("Got Synopsis:", movie_info.synopsis);
        } else {
            console.log("field 'matched_synopsis' was not found. Synopsis:", movie_info.synopsis);
        }
        
        if ( index_field ) {
            index_field.val(movie_info.matched_index)
            //console.log("Got matched_index:", movie_info.matched_index);
        } else {
            console.log("field 'matched_index' was not found. Index:", movie_info.matched_index);
        }
    //
    //  If there is some kind of error/exception catch it and post that to the console
    } catch (error) {
        console.error(error.message);
    };
};




