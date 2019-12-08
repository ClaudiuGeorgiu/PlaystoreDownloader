'use strict';

$(document).ready(function () {

    let timeoutArray = [];
    timeoutArray.push = function () {
        // Hold only the last 10 timeouts.
        if (this.length >= 10) {
            this.shift();
        }
        return Array.prototype.push.apply(this, arguments);
    };

    $.fn.placeholderTypewriter = function (action) {
        return this.each(function () {
            let that = $(this);

            let settings = {
                pause: 1500,
                text: [
                    'com.spotify.music',
                    'org.mozilla.firefox',
                    'com.instagram.android',
                    'com.reddit.frontpage',
                    'org.videolan.vlc',
                    'com.pinterest',
                    'com.whatsapp',
                    'flipboard.app',
                    'com.twitter.android',
                    'bbc.mobile.news.ww',
                    'com.ebay.mobile',
                    'com.dropbox.android'
                ]
            };

            function typeString($target, index, cursorPosition, callback) {

                let timeouts = that.data('timeouts') || timeoutArray;

                let text = settings.text[index];

                let placeholder = $target.attr('placeholder');
                $target.attr('placeholder', placeholder + text[cursorPosition]);

                // Type next character.
                if (cursorPosition < text.length - 1) {
                    timeouts.push(setTimeout(function () {
                        typeString($target, index, cursorPosition + 1, callback);
                    }, parseInt(150 - Math.random() * 75)));
                    that.data('timeouts', timeouts);
                    return;
                }

                // Callback when text animation for the current string is finished.
                callback();
            }

            function deleteString($target, callback) {

                let timeouts = that.data('timeouts') || timeoutArray;

                let placeholder = $target.attr('placeholder');
                let length = placeholder.length;

                // Delete last character
                $target.attr('placeholder', placeholder.substr(0, length - 1));

                // Delete previous character.
                if (length > 1) {
                    timeouts.push(setTimeout(function () {
                        deleteString($target, callback);
                    }, parseInt(75 - Math.random() * 50)));
                    that.data('timeouts', timeouts);
                    return;
                }

                // Callback when text animation for the current string is finished.
                callback();
            }

            function loopTyping($target, index) {

                let timeouts = that.data('timeouts') || timeoutArray;

                // Pause before deleting string.
                timeouts.push(setTimeout(function () {
                    deleteString($target, function () {
                        typeString($target, index, 0, function () {
                            // Start the loop again for the next string.
                            loopTyping($target, (index + 1) % settings.text.length);
                        });
                    });
                }, settings.pause));

                that.data('timeouts', timeouts);
            }

            if (action === 'start') {
                loopTyping(that, 0);
            } else if (action === 'stop') {
                for (let i = that.data('timeouts').length; i >= 0; i--) {
                    clearTimeout(that.data('timeouts')[i]);
                }
            }
        });
    };

    let wrongPackageNameMsg = $('#wrong-package-name');

    let socket = io.connect(document.location.protocol + '//' + document.location.host);
    socket.on('download_progress', function (progress) {
        if (parseFloat($('#download-progress-container').css('opacity')) === 0) {
            $('#download-progress-container').fadeTo(500, 1);
        }
        $('#download-progress').width(progress + '%');
        if (progress === 100) {
            $('#download-button').css('padding', '').html('<i class="fas fa-check"></i>');
            $('#download-progress').removeClass('progress-bar-animated');
        }
    });

    socket.on('download_success', function (message) {
        swal({
            animation: true,
            titleText: 'Successful download',
            type: 'success',
            text: message,
            showConfirmButton: true
        }).then(swal.noop);
    });

    socket.on('download_bad_package', function (message) {
        swal({
            animation: true,
            titleText: 'No application found',
            type: 'error',
            text: message,
            showConfirmButton: true
        }).then(function () {
            $('#package-name').removeClass('is-valid').addClass('is-invalid').css('color', 'red').prop('disabled', false);
            $('#download-button').removeClass('btn-outline-secondary btn-outline-success')
                .addClass('btn-outline-danger').prop('disabled', false).css('padding', '5px 12px 0 12px')
                .html('<i class="material-icons" style="font-size: 25px;">file_download</i>');
        });
    });

    socket.on('download_error', function (message) {
        swal({
            animation: true,
            titleText: 'Download error',
            type: 'error',
            text: message,
            showConfirmButton: true
        }).then(function () {
            window.location.reload(true);
        });
    });

    function startDownload() {
        let packageName = $('#package-name').val();

        if (/^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$/i.test(packageName)) {
            $('#package-name').removeClass('is-invalid').addClass('is-valid').css('color', '').prop('disabled', true);
            $('#download-button').removeClass('btn-outline-secondary btn-outline-danger')
                .addClass('btn-outline-success').prop('disabled', true).css('padding', '')
                .html('<i class="fas fa-sync fa-spin"></i>');
            wrongPackageNameMsg.fadeTo(500, 0);
            socket.emit('start_download', packageName);
        } else {
            $('#package-name').removeClass('is-valid').addClass('is-invalid').css('color', 'red');
            $('#download-button').removeClass('btn-outline-secondary btn-outline-success')
                .addClass('btn-outline-danger');
            wrongPackageNameMsg.fadeTo(500, 1);
        }
    }

    $('#package-name').focus(function () {
        $(this).placeholderTypewriter('stop').attr('placeholder', '').removeClass('is-invalid').css('color', '');
        $('#download-button').removeClass('btn-outline-danger').addClass('btn-outline-secondary');
        wrongPackageNameMsg.fadeTo(500, 0);
    }).focusout(function () {
        if ($(this).val() === '') {
            $(this).placeholderTypewriter('start');
        }
    }).on('input', function () {
        $(this).placeholderTypewriter('stop').attr('placeholder', '').removeClass('is-invalid').css('color', '');
        $('#download-button').removeClass('btn-outline-danger').addClass('btn-outline-secondary');
        if (parseFloat(wrongPackageNameMsg.css('opacity')) === 1) {
            wrongPackageNameMsg.fadeTo(500, 0);
        }
    }).keypress(function (e) {
        // If enter was pressed.
        if (e.which === 13) {
            startDownload();
        }
    }).placeholderTypewriter('start');

    $('#download-button').click(startDownload);
});
