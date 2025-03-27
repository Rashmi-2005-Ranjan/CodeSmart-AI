let voiceSolutionUrl = '';

document.addEventListener('DOMContentLoaded', () => {
    // Check if user is logged in
    chrome.storage.local.get('user', (data) => {
        if (!data.user) {
            chrome.runtime.sendMessage({ action: 'setPopup', popup: 'login.html' }, () => {
                window.location.href = 'login.html';
            });
            return;
        }

        // Display personalized greeting
        const username = data.user.username || 'User';
        document.getElementById('greeting').textContent = `Hi ${username}, Welcome to CodeSmart Assistant!`;
    });

    // Add logout functionality
    document.getElementById('logout_button').addEventListener('click', () => {
        chrome.runtime.sendMessage({ action: 'logout' }, () => {
            window.location.href = 'login.html';
        });
    });

    // Function to extract problem name from URL
    function getProblemName(url) {
        const match = url.match(/leetcode\.com\/problems\/([\w-]+)\//);
        return match ? match[1].replace(/-/g, ' ') : 'Unknown Problem';
    }

    // Fetch current LeetCode URL and pre-fill problem name
    function fetchLeetCodeURL(callback) {
        chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
            if (tabs.length === 0) return;

            const currentTab = tabs[0];
            if (currentTab && currentTab.url.includes("leetcode.com/problems/")) {
                const problemName = getProblemName(currentTab.url);
                console.log("Extracted Problem Name:", problemName);
                callback(problemName);
            } else {
                callback(null);
            }
        });
    }

    // Pre-fill problem name if on a LeetCode problem page
    fetchLeetCodeURL((problemName) => {
        if (problemName) {
            document.getElementById('problem_name').value = problemName;
        }
    });

    // Form submission logic
    document.getElementById('assistForm').addEventListener('submit', async (event) => {
        event.preventDefault();

        const problemId = document.getElementById('problem_id').value;
        const requestType = document.getElementById('request_type').value;
        const userCode = document.getElementById('user_code').value;
        const errorMessage = document.getElementById('error_message').value;
        const problemName = document.getElementById('problem_name').value; // Get user-provided problem name

        document.getElementById('response_text').textContent = 'Fetching response...';
        document.getElementById('audio_container').style.display = 'none';

        const requestBody = {
            problem_id: problemId,
            request_type: requestType,
            user_id: "user123",
            problem_name: problemName || "Unknown Problem" // Use user-provided problem name
        };

        if (userCode.trim()) {
            requestBody.user_code = userCode;
        }

        if (requestType === 'error_explanation' && errorMessage.trim()) {
            requestBody.error_message = errorMessage;
        }

        try {
            const response = await fetch('http://127.0.0.1:8000/assist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const text = await response.text();
                throw new Error(`Server error: ${response.status} - ${text}`);
            }

            const data = await response.json();

            if (data.error) {
                document.getElementById('response_text').textContent = `Error: ${data.error}`;
                return;
            }

            if (requestType === 'solution') {
                document.getElementById('response_text').textContent = data.solution;
                voiceSolutionUrl = `http://127.0.0.1:8000${data.voice_solution_url}`;
                console.log('Voice Solution URL set to:', voiceSolutionUrl);
                fetch(voiceSolutionUrl)
                    .then(res => {
                        if (res.ok) {
                            console.log('Audio file is accessible:', voiceSolutionUrl);
                        } else {
                            console.error('Audio file not accessible:', res.status, res.statusText);
                        }
                    })
                    .catch(err => console.error('Error checking audio file:', err));
                document.getElementById('audio_container').style.display = 'block';
            } else if (requestType === 'learning_resources') {
                let resourcesHtml = '<ul>';
                data.learning_resources.forEach(resource => {
                    resourcesHtml += `<li><a href="${resource.url}" target="_blank" style="color: #007bff;">${resource.description}</a></li>`;
                });
                resourcesHtml += '</ul>';
                document.getElementById('response_text').innerHTML = resourcesHtml;
            } else {
                document.getElementById('response_text').textContent = data[requestType] || "No response available.";
            }
        } catch (error) {
            console.error('Fetch error:', error);
            document.getElementById('response_text').textContent = `Error: Failed to fetch response. ${error.message}`;
        }
    });

    // Add event listener for the play button
    document.getElementById('play_audio_button').addEventListener('click', playVoiceSolution);

    function playVoiceSolution() {
        const audioElement = document.getElementById('voice_solution');
        const audioSource = document.getElementById('audio_source');

        if (!voiceSolutionUrl) {
            console.error('No voice solution URL available');
            document.getElementById('response_text').textContent = 'Error: No audio available';
            return;
        }

        console.log('Playing audio from:', voiceSolutionUrl); // Debug
        audioSource.src = voiceSolutionUrl; // Set the source element’s src
        audioElement.load(); // Reload the audio element to recognize the new source

        audioElement.play()
            .then(() => {
                console.log('Audio playback started successfully');
                audioElement.style.display = 'block'; // Show controls when playing
            })
            .catch(error => {
                console.error('Audio playback failed:', error);
                document.getElementById('response_text').textContent = `Error: Failed to play audio - ${error.message}`;
            });
    }

    document.getElementById('request_type').addEventListener('change', toggleFields);

    function toggleFields() {
        const requestType = document.getElementById('request_type').value;
        document.getElementById('error_message_group').style.display = requestType === 'error_explanation' ? 'block' : 'none';
        document.getElementById('user_code_group').style.display = ['hint', 'suggestion', 'error_explanation', 'code_insights'].includes(requestType) ? 'block' : 'none';
        document.getElementById('problem_name_group').style.display = requestType === 'learning_resources' ? 'block' : 'none';
        // Make problem_name required only when learning_resources is selected
        document.getElementById('problem_name').required = requestType === 'learning_resources';
    }

    toggleFields();
});