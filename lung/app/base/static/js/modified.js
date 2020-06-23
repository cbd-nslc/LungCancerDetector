
// disable flash message after 4s
jQuery(function($){
  setTimeout(function(){
      $('.flash-message').hide();
  }, 4000)
});


/* dropzone */
// zraw file
jQuery(function($) {
  $('input#raw-file').change(function() {
    if ($(this).val()) {
      var filename = $(this).val().split('\\').pop();
      var file_extension = filename.split('.').pop().toLowerCase();

      if (file_extension === 'raw'){
          $(this).closest('#dropzone').find('.file-name').html(filename);
          $('#raw-file-error').hide();

      } else {
          $(this).val('');
          $(this).closest('#dropzone').find('.file-name').html('');
          $('#raw-file-error').show();
      }
    }
  });
});

// mhd file
jQuery(function($) {
  $('input#mhd-file').change(function() {
    if ($(this).val()) {

      var filename = $(this).val().split('\\').pop();
      var file_extension = filename.split('.').pop().toLowerCase();

      if (file_extension === 'mhd') {
          $(this).closest('#dropzone1').find('.file-name').html(filename);
          $('#mhd-file-error').hide();
      } else {
          $(this).val('');
          $(this).closest('#dropzone1').find('.file-name').html('');
          $('#mhd-file-error').show();
      }
    }
  });
});

// loading progress bar
jQuery(function($) {
	$('form#ct-scan-upload').on('submit', function(e) {
	    current_progress = 0.1,
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
        })
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


