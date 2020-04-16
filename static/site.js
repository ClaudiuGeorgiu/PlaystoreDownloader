'use strict';

jQuery(function ($) {

    const packageNameItem = $('#package-name');
    const wrongPackageNameMsg = $('#wrong-package-name');
    const downloadButtonItem = $('#download-button');

    const timeoutArray = [];
    timeoutArray.push = function () {
        // Hold only the last 10 timeouts.
        if (this.length >= 10) {
            this.shift();
        }
        return Array.prototype.push.apply(this, arguments);
    };

    $.fn.placeholderTypewriter = function (action) {
        return this.each(function () {
            const that = $(this);

            const settings = {
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

                const timeouts = that.data('timeouts') || timeoutArray;

                const text = settings.text[index];

                const placeholder = $target.attr('placeholder');
                $target.attr('placeholder', placeholder + text[cursorPosition]);

                // Type next character.
                if (cursorPosition < text.length - 1) {
                    timeouts.push(setTimeout(function () {
                        typeString($target, index, cursorPosition + 1, callback);
                    }, Math.round(150 - Math.random() * 75)));
                    that.data('timeouts', timeouts);
                    return;
                }

                // Callback when text animation for the current string is finished.
                callback();
            }

            function deleteString($target, callback) {

                const timeouts = that.data('timeouts') || timeoutArray;

                const placeholder = $target.attr('placeholder');
                const length = placeholder.length;

                // Delete last character
                $target.attr('placeholder', placeholder.substr(0, length - 1));

                // Delete previous character.
                if (length > 1) {
                    timeouts.push(setTimeout(function () {
                        deleteString($target, callback);
                    }, Math.round(75 - Math.random() * 50)));
                    that.data('timeouts', timeouts);
                    return;
                }

                // Callback when text animation for the current string is finished.
                callback();
            }

            function loopTyping($target, index) {

                const timeouts = that.data('timeouts') || timeoutArray;

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

    const socket = io.connect(document.location.protocol + '//' + document.location.host);
    socket.on('download_progress', function (progress) {
        const downloadProgressContainer = $('#download-progress-container');
        if (parseFloat(downloadProgressContainer.css('opacity')) === 0) {
            downloadProgressContainer.fadeTo(500, 1);
        }

        const downloadProgressItem = $('#download-progress');
        downloadProgressItem.width(progress + '%');
        if (progress === 100) {
            downloadButtonItem.css('padding', '').html('<i class="fas fa-check"></i>');
            downloadProgressItem.removeClass('progress-bar-animated');
        }
    });

    socket.on('download_success', function (message) {
        Swal.fire({
            titleText: 'Successful download',
            icon: 'success',
            text: message,
            showConfirmButton: true
        });
    });

    socket.on('download_bad_package', function (message) {
        Swal.fire({
            titleText: 'No application found',
            icon: 'error',
            text: message,
            showConfirmButton: true
        }).then(function () {
            packageNameItem.removeClass('is-valid').addClass('is-invalid').css('color', 'red').prop('disabled', false);
            downloadButtonItem.removeClass('btn-outline-secondary btn-outline-success')
                .addClass('btn-outline-danger').prop('disabled', false).css('padding', '5px 12px 0 12px')
                .html('<i class="material-icons" style="font-size: 25px;">file_download</i>');
        });
    });

    socket.on('download_error', function (message) {
        Swal.fire({
            titleText: 'Download error',
            icon: 'error',
            text: message,
            showConfirmButton: true
        }).then(function () {
            window.location.reload();
        });
    });

    function startDownload() {
        const packageName = packageNameItem.val();

        if (/^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$/i.test(packageName)) {
            packageNameItem.removeClass('is-invalid').addClass('is-valid').css('color', '').prop('disabled', true);
            downloadButtonItem.removeClass('btn-outline-secondary btn-outline-danger')
                .addClass('btn-outline-success').prop('disabled', true).css('padding', '')
                .html('<i class="fas fa-sync fa-spin"></i>');
            wrongPackageNameMsg.fadeTo(500, 0);
            socket.emit('start_download', packageName);
        } else {
            packageNameItem.removeClass('is-valid').addClass('is-invalid').css('color', 'red');
            downloadButtonItem.removeClass('btn-outline-secondary btn-outline-success')
                .addClass('btn-outline-danger');
            wrongPackageNameMsg.fadeTo(500, 1);
        }
    }

    packageNameItem.focus(function () {
        $(this).placeholderTypewriter('stop').attr('placeholder', '').removeClass('is-invalid').css('color', '');
        downloadButtonItem.removeClass('btn-outline-danger').addClass('btn-outline-secondary');
        wrongPackageNameMsg.fadeTo(500, 0);
    }).focusout(function () {
        if ($(this).val() === '') {
            $(this).placeholderTypewriter('start');
        }
    }).on('input', function () {
        $(this).placeholderTypewriter('stop').attr('placeholder', '').removeClass('is-invalid').css('color', '');
        downloadButtonItem.removeClass('btn-outline-danger').addClass('btn-outline-secondary');
        if (parseFloat(wrongPackageNameMsg.css('opacity')) === 1) {
            wrongPackageNameMsg.fadeTo(500, 0);
        }
    }).keypress(function (e) {
        // If enter was pressed.
        if (e.which === 13) {
            startDownload();
        }
    }).placeholderTypewriter('start');

    downloadButtonItem.click(startDownload);
});
