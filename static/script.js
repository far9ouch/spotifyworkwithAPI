document.addEventListener('DOMContentLoaded', () => {
    const musicLink = document.getElementById('musicLink');
    const convertBtn = document.getElementById('convertBtn');
    const status = document.getElementById('status');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    let originalButtonText = convertBtn.innerHTML;

    function updateProgress(percent) {
        progressBar.style.width = `${percent}%`;
        progressText.textContent = `${percent}%`;
    }

    function showLoading() {
        convertBtn.disabled = true;
        convertBtn.innerHTML = '<div class="loading"></div>Converting...';
        progressContainer.classList.remove('hidden');
        updateProgress(0);
    }

    function hideLoading() {
        convertBtn.disabled = false;
        convertBtn.innerHTML = originalButtonText;
        progressContainer.classList.add('hidden');
    }

    function simulateProgress() {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) {
                clearInterval(interval);
                progress = 90;
            }
            updateProgress(Math.min(Math.round(progress), 90));
        }, 500);
        return interval;
    }

    musicLink.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            convertBtn.click();
        }
    });

    convertBtn.addEventListener('click', async () => {
        const link = musicLink.value.trim();
        
        if (!link) {
            status.textContent = 'Please enter a valid link';
            status.style.color = '#ff6b6b';
            return;
        }

        try {
            showLoading();
            status.textContent = 'Starting conversion...';
            status.style.color = '#fff';

            const progressInterval = simulateProgress();

            console.log('Sending request for:', link);
            const response = await fetch('/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: link })
            });

            clearInterval(progressInterval);
            console.log('Response status:', response.status);
            
            if (response.ok) {
                updateProgress(100);
                console.log('Response is OK, getting blob...');
                const blob = await response.blob();
                console.log('Blob size:', blob.size);
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                
                const contentDisposition = response.headers.get('content-disposition');
                console.log('Content-Disposition:', contentDisposition);
                
                const filename = contentDisposition 
                    ? contentDisposition.split('filename=')[1].replace(/"/g, '')
                    : 'audio.mp3';
                    
                console.log('Filename:', filename);
                a.download = filename;
                
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                status.textContent = 'Download complete!';
                status.style.color = '#4CAF50';
                musicLink.value = '';
            } else {
                console.log('Response not OK, getting error...');
                const error = await response.json();
                status.textContent = error.error || 'Conversion failed';
                status.style.color = '#ff6b6b';
                updateProgress(0);
            }
        } catch (error) {
            console.error('Error details:', error);
            status.textContent = 'An error occurred during conversion';
            status.style.color = '#ff6b6b';
            updateProgress(0);
        } finally {
            hideLoading();
        }
    });
}); 