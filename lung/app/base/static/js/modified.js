


// disable flash message after 4s
jQuery(function($){
  setTimeout(function(){
      $('.flash-message').hide();
  }, 4000)
});

// patient profile upload ct scan
$(function(){
    var hash = location.hash;
    if (hash !='') {
        // show the tab
        $('#myTab a[href="' + hash + '"]').tab('show');
    }
    console.log(hash)
});

/* upload page */

$('#table-patients tbody .row-patients').click(function(){
    window.location = $(this).attr('href');
    return false;
});


// dropzone
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

const fileTypes = ['image/nii', 'image/jpg', 'image/gif', 'image/png', 'image/svg', 'image/jpeg', 'image/raw', ];

function validFileType(file) {
    return fileTypes.includes(file.type.toLowerCase());}
function returnFileSize(number) {
    if(number < 1024) {
        return number + ' bytes';
    } else if(number >= 1024 && number < 1048576) {
        return (number/1024).toFixed(1) + ' KB';
    } else if(number >= 1048576) {
        return (number/1048576).toFixed(1) + ' MB';
    }
}

function returnFileMBSize(number){
    return (number/1048576);
}

$('form#ct-scan-uploadUI input').on('change', function() {
    let input = $('input#fileUI');
    let preview = document.querySelector('.preview');

    let fullName = input.val().split('\\').pop();
    let fullNameSplit = fullName.split('.');
    let extension = fullNameSplit.pop().toLowerCase();
    let name = fullNameSplit.join('');

    while(preview.firstChild) {
        preview.removeChild(preview.firstChild);}

//    $(this).closest('#dropzoneUI').find('.file-name').html(fullName);
//    $('#upload-file-errorUI').hide();

    let file_list = input.prop('files')

    if(file_list.length === 0) {
        const para = document.createElement('p');
        para.textContent = 'No files currently selected for upload';
        preview.appendChild(para);
    } else {
        // check size
        var totalSize = 0;
        var isSame = true
        for (let i=0; i<file_list.length; i++){
//            if (i < file_list.length-1 && file_list[i].type != file_list[i+1].type){
//                var isSame = false;
//                break;}
            totalSize = totalSize + returnFileMBSize(file_list[i].size);}

        if (totalSize > 200) {
            $('#upload-file-errorUI').text('Your files exceed 200 MB, please reupload.').show();
        } else if (isSame === false){
            $('#upload-file-errorUI').text('All files must have the same extension, please reupload.').show();
        } else {
        //  add file list
            const list = document.createElement('ol');
            preview.appendChild(list);

            for(const file of file_list) {
                const listItem = document.createElement('li');
                const para = document.createElement('p');
                para.textContent = `${file.name} - ${returnFileSize(file.size)}`;
                listItem.appendChild(para);

            list.appendChild(listItem);}
        }
    }


    for (let i=0; i<file_list.length; i++){
        console.log(returnFileMBSize(file_list[i].size))
    }
})

// dropzoneUI
//function validate_extension(extensionUI){
//    let input = $('input#fileUI');
//
//    let fullName = input.val().split('\\').pop();
//    let fullNameSplit = fullName.split('.');
//    let extension = fullNameSplit.pop().toLowerCase();
//    let name = fullNameSplit.join('');
//
//    // check extension of fileUI
//    if (input.val()) {
//        if (extension === extensionUI){
//            $(this).closest('#dropzoneUI').find('.file-name').html(fullName);
//            $('#upload-file-errorUI').hide();
//        } else {
//            $(this).val('');
//            $(this).closest('#dropzoneUI').find('.file-name').html('');
//            $('#upload-file-extension-errorUI').show();
//            $('#upload-file-errorUI').hide();
//        }
//    }
//}


/* cancel-button */
$('#cancel-button').on('click', function() {
    $('#raw-file').closest('#dropzone').find('.file-name').html('Browse');
    $('#mhd-file').closest('#dropzone1').find('.file-name').html('Browse');
})


// loading progress bar

$('form#ct-scan-upload').on('submit', function(e) {
    current_progress = 0.1;
    step = 0.006; // the smaller this is the slower the progress bar

    interval = setInterval(function() {
        current_progress += step;
        progress = Math.round(Math.atan(current_progress) / (Math.PI / 2) * 100 * 1000 / 1000);

        $('#loader').show();
        $(".progress-bar")
            .css("width", progress + "%")
            .attr("aria-valuenow", progress);

        $('#process-percent').text(progress + "%");

        if (progress >= 99){
            progress = 99
            clearInterval(interval);
        } else if(progress >= 70) {
            step = 0.06
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

//INPUT FORM
// input type number
$('form#patient-form input[type="number"]').each(function(i, input){
     if (input.value === ''){
        input.value = 0;
     };
})

// input select


$('select').children(':first-child').each(function() {
   var thisAttr = $(this).attr('disabled');
   if(thisAttr = "disabled") {
      $(this).hide();
   }
});
