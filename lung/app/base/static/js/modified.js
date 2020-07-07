
// disable flash message after 4s
jQuery(function($){
  setTimeout(function(){
      $('.flash-message').hide();
  }, 4000)
});


/* dropzone */

$('form#ct-scan-upload input').on('change', function() {
    var rawInput = $('input#raw-file');
    var mhdInput = $('input#mhd-file');

    var rawFullName = rawInput.val().split('\\').pop();
    var rawFullNameSplit = rawFullName.split('.');
    var rawExtension = rawFullNameSplit.pop().toLowerCase();
    var rawName = rawFullNameSplit.join('');

    var mhdFullName = mhdInput.val().split('\\').pop();
    var mhdFullNameSplit = mhdFullName.split('.');
    var mhdExtension = mhdFullNameSplit.pop().toLowerCase();
    var mhdName = mhdFullNameSplit.join('');

    // check extension of raw file
    if (rawInput.val()) {
        if (rawExtension === 'raw'){
            $(this).closest('#dropzone').find('.file-name').html(rawFullName);
            $('#raw-file-error').hide();
        } else {
            $(this).val('');
            $(this).closest('#dropzone').find('.file-name').html('');
            $('#raw-file-error').show();
            $('#error-raw-mhd').hide();
        }
    }

    // check extension of mhd file
    if (mhdInput.val()) {
        if (mhdExtension === 'mhd') {
            $(this).closest('#dropzone1').find('.file-name').html(mhdFullName);
            $('#mhd-file-error').hide();
        } else {
            $(this).val('');
            $(this).closest('#dropzone1').find('.file-name').html('');
            $('#mhd-file-error').show();
            $('#error-raw-mhd').hide();
        }
    }

    // check if raw file and mhd file match
    if ( rawInput.val() && mhdInput.val() ) {
        if (rawName !== mhdName) {
            $('#raw-file').val('');
            $('#raw-file').closest('#dropzone').find('.file-name').html('');

            $('#mhd-file').val('');
            $('#mhd-file').closest('#dropzone1').find('.file-name').html('');

            $('#error-raw-mhd').show();

        } else {
            $('#error-raw-mhd').hide();
        }
    }
})


// loading progress bar

$('form#ct-scan-upload').on('submit', function(e) {
    current_progress = 0.1;
    step = 0.01; // the smaller this is the slower the progress bar

    interval = setInterval(function() {
        current_progress += step;
        progress = Math.round(Math.atan(current_progress) / (Math.PI / 2) * 100 * 1000 / 1000);

        $('#loader').show();
        $(".progress-bar")
            .css("width", progress + "%")
            .attr("aria-valuenow", progress);

        $('#process-percent').text(progress + "%");

        if (progress >= 100){
            clearInterval(interval);
        } else if(progress >= 70) {
            step = 0.1
        }
     }, 100);


    $('#stop').on('click', function(){
        $(".progress-bar").css("width","100%").attr("aria-valuenow", 100);
        $('#process-percent').text("100% Complete");
        clearInterval(interval); // Important to stop the progress bar from increasing
    })
    /* Stop button */

    $('#reset').on('click', function() {
        $(".progress-bar").css("width","0%").attr("aria-valuenow", 0);
        $('#process-percent').hide();
        clearInterval(interval);
    });

});


// profile picture upload

$(".picture-file").change(function() {
  if($(this).val()) {
    var picture_name = $(this).val().split('\\').pop();
    var picture_extension = picture_name.split('.').pop().toLowerCase();

    if (picture_extension === 'png' || picture_extension === 'jpg'){
        var reader = new FileReader();

        reader.onload = function(e) {
          $('.picture-now')
          .attr('src', e.target.result);


        }
        reader.readAsDataURL(this.files[0]); // convert to base64 string
        $('.picture-error').hide();

    } else {
        $(this).val('');
        $('.picture-error').show();
    }
  }
});

// patient-form input type number
$('form#patient-form input[type="number"]').each(function(i, input){
     if (input.value === ''){
        input.value = 0;
     };
})


