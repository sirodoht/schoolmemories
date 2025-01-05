// Setup for drag and drop uploading
document.getElementById('js-show').style.display = 'inline';
document.getElementById('js-status').style.color = '#f00';

// Get body element, used for drag and drop onto it
var bodyElem = document.querySelector('textarea[name="body"]');

// Prevent default drag and drop behaviours
[
    'drag',
    'dragstart',
    'dragend',
    'dragover',
    'dragenter',
    'dragleave',
    'drop',
].forEach(function (event) {
    bodyElem.addEventListener(event, function (e) {
        e.preventDefault();
        e.stopPropagation();
    });
});

function injectImageMarkdown(textInputElem, imageName, imageURL) {
    // Build markdown image code
    var markdownImageCode = '![' + imageName + '](' + imageURL + ')';

    // Inject markdown image code in cursor position
    if (textInputElem.selectionStart || textInputElem.selectionStart == '0') {
        var startPos = textInputElem.selectionStart;
        var endPos = textInputElem.selectionEnd;
        textInputElem.value = textInputElem.value.substring(0, startPos)
            + markdownImageCode
            + '\n'
            + textInputElem.value.substring(endPos, textInputElem.value.length);

        // Set cursor location to after markdownImageCode +1 for the new line
        textInputElem.selectionEnd = endPos + markdownImageCode.length + 1;
    } else {
        // There is no cursor, just append
        textInputElem.value += markdownImageCode;
    }
}

bodyElem.addEventListener('drop', function (e) {
    // Only upload one file at a time
    if (e.dataTransfer.files.length === 1) {

        // Prepare form data
        var formData = new FormData();
        var name = e.dataTransfer.files[0].name;
        formData.append("file", e.dataTransfer.files[0]);

        // Upload request
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function alertContents() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    // success, inject markdown snippet
                    injectImageMarkdown(bodyElem, name, xhr.responseURL);
                } else {
                    alert('Image could not be uploaded. ' + xhr.responseText);
                }

                // Re-enable textarea
                bodyElem.disabled = false;

                // Update status message
                document.getElementById('js-status').innerText = '';
            } else {
                // This branch runs first
                // Uplading, so disable textarea and show status message
                bodyElem.disabled = true;
                document.getElementById('js-status').innerText = 'UPLOADING...';
            }
        };

        xhr.open('POST', '/images/list/?raw=true');
        xhr.setRequestHeader('X-CSRFToken', '{{ csrf_token }}');
        xhr.send(formData);
    }
});
