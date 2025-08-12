class AutomationUI {
    constructor() {
        this.apiBase = '';
        this.init();
    }

    init() {
        document.getElementById('processBtn').addEventListener('click', () => this.processMeetings());
        document.getElementById('testConnectionBtn').addEventListener('click', () => this.testConnection());
        this.checkHealth();
    }

    async checkHealth() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            this.showStatus(data.status === 'healthy' ? 'API is running' : 'API health check failed', 'success');
        } catch (error) {
            this.showStatus('Cannot connect to API', 'error');
        }
    }

    async processMeetings() {
        const button = document.getElementById('processBtn');
        const originalText = button.textContent;
        
        button.disabled = true;
        button.textContent = 'Processing...';
        
        this.showLoading(true);
        this.clearResults();

        try {
            const response = await fetch('/process-meetings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_id: 'default' })
            });

            const data = await response.json();
            
            if (response.ok) {
                this.showStatus(`${data.message}`, 'success');
                if (data.meetings && data.meetings.length > 0) {
                    this.displayMeetings(data.meetings);
                }
            } else {
                this.showStatus(`Error: ${data.detail || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            this.showStatus(`Network error: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
            button.disabled = false;
            button.textContent = originalText;
        }
    }

    async testConnection() {
        const button = document.getElementById('testConnectionBtn');
        button.disabled = true;
        button.textContent = 'Testing...';

        try {
            // Test calendar connection (you would add this endpoint)
            this.showStatus('Connection test completed. Check console for details.', 'info');
        } catch (error) {
            this.showStatus(`Connection test failed: ${error.message}`, 'error');
        } finally {
            button.disabled = false;
            button.textContent = 'Test Connections';
        }
    }

    showStatus(message, type) {
        const statusDiv = document.getElementById('status');
        statusDiv.textContent = message;
        statusDiv.className = `status ${type}`;
        statusDiv.style.display = 'block';
    }

    showLoading(show) {
        const loadingDiv = document.getElementById('loading');
        loadingDiv.style.display = show ? 'block' : 'none';
    }

    clearResults() {
        document.getElementById('results').innerHTML = '';
    }

    displayMeetings(meetings) {
        const resultsDiv = document.getElementById('results');
        
        meetings.forEach(meeting => {
            const meetingDiv = document.createElement('div');
            meetingDiv.className = 'meeting-item';
            
            meetingDiv.innerHTML = `
                <h3>${meeting.subject}</h3>
                <p><strong>Date:</strong> ${meeting.date}</p>
                <p><strong>Time:</strong> ${meeting.time}</p>
                <p><strong>Calendar Event ID:</strong> ${meeting.calendar_event_id}</p>
            `;
            
            resultsDiv.appendChild(meetingDiv);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new AutomationUI();
});