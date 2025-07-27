document.addEventListener('DOMContentLoaded', () => {
    const themeSwitcher = document.getElementById('theme-switcher');
    const body = document.body;
    const uploadForm = document.getElementById('upload-form');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const transcriptText = document.getElementById('transcript-text');
    const summaryText = document.getElementById('summary-text');
    const errorText = document.getElementById('error-text');
    const progressBar = document.getElementById('progress-bar');
    const loadingStatus = document.getElementById('loading-status');
    const audioFileInput = document.getElementById('audio_file');
    const fileNameSpan = document.getElementById('file-name');

    // Theme switcher
    themeSwitcher.addEventListener('click', () => {
        body.classList.toggle('dark-theme');
        body.classList.toggle('light-theme');
    });

    // Update file name display
    audioFileInput.addEventListener('change', () => {
        if (audioFileInput.files.length > 0) {
            fileNameSpan.textContent = audioFileInput.files[0].name;
        } else {
            fileNameSpan.textContent = 'No file chosen';
        }
    });

    // Form submission
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(uploadForm);
        const audioFile = formData.get('audio_file');
        if (!audioFile || !audioFile.name) {
            showError('Please select an audio file.');
            return;
        }

        resetUI();

        try {
            // First, upload the file to get a filename
            const uploadResponse = await fetch('/upload', {
                method: 'POST',
                body: formData,
            });

            const uploadResult = await uploadResponse.json();

            if (uploadResult.error) {
                showError(uploadResult.error);
                return;
            }

            // Now, start the processing event stream
            const eventSource = new EventSource(`/process/${uploadResult.filename}`);

            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);

                if (data.error) {
                    showError(data.error);
                    eventSource.close();
                    return;
                }

                if (data.percent) {
                    progressBar.style.width = data.percent + '%';
                    loadingStatus.textContent = data.status;
                }

                if (data.percent === 100) {
                    transcriptText.textContent = data.transcript;
                    summaryText.textContent = data.summary;
                    resultsDiv.classList.remove('hidden');
                    loadingDiv.classList.add('hidden');
                    eventSource.close();
                }
            };

            eventSource.onerror = function() {
                showError('An error occurred while processing the file.');
                eventSource.close();
            };

        } catch (err) {
            showError('An unexpected error occurred during upload.');
            console.error(err);
        }
    });

    function resetUI() {
        loadingDiv.classList.remove('hidden');
        resultsDiv.classList.add('hidden');
        errorDiv.classList.add('hidden');
        progressBar.style.width = '0%';
        loadingStatus.textContent = 'Uploading file...';
    }

    function showError(message) {
        errorText.textContent = message;
        errorDiv.classList.remove('hidden');
        resultsDiv.classList.add('hidden');
        loadingDiv.classList.add('hidden');
    }
});
