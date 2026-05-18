// DOM Element Selectors
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatWrapper = document.getElementById('chat-wrapper');

// Main Form Submission Listener
chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const promptText = userInput.value.trim();

    if (!promptText) return;

    // 1. Render User message row
    appendUserBubble(promptText);
    userInput.value = '';

    // 2. Render Animated "Thinking/Loading" block
    const tempLoadingId = appendLoadingBubble();

    try {
        // 3. Talk directly to your Python backend API server instead of Google
        const response = await fetch('https://musical-adventure-7v5j74wxr6pjfxjvq-5001.app.github.dev/api/analyze', {
            method: "POST",
            headers: { 
                "Content-Type": "application/json" 
            },
            body: JSON.stringify({ textToAnalyze: promptText })
        });

        if (!response.ok) {
            throw new Error("Backend server returned an error error.");
        }
        
        const data = await response.json();
        
        // 4. Destroy loader UI and replace with the verified verdict data from your server
        document.getElementById(tempLoadingId).remove();
        appendAiBubble(data.analysis);

    } catch (error) {
        console.error("Connection Error:", error);
        document.getElementById(tempLoadingId).remove();
        appendAiBubble("ERROR: Could not connect to the secure verification backend. Make sure your Python server is actively running!");
    }
});

// UI Rendering Utility Functions
function appendUserBubble(text) {
    const html = `
        <div class="message user-message">
            <div class="bubble outline-bubble">
                <strong>USER:</strong> ${escapeHtml(text)}
            </div>
        </div>`;
    chatWrapper.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
}

function appendLoadingBubble() {
    const uniqueId = 'loader-' + Date.now();
    const html = `
        <div class="message ai-message" id="${uniqueId}">
            <div class="ai-avatar">A</div>
            <div class="bubble solid-bubble">
                <div class="bubble-header">
                    <span>FACTCHECK AI | SECURELY CROSS-REFERENCING WEB...</span>
                    <div class="loading-dots"><span></span><span></span><span></span></div>
                </div>
                <div style="color: var(--text-muted); font-size: 13px;">Python gateway active. Deploying live Google Search grounding queries and checking news source consensus...</div>
            </div>
        </div>`;
    chatWrapper.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
    return uniqueId;
}

function appendAiBubble(markdownText) {
    const html = `
        <div class="message ai-message">
            <div class="ai-avatar">A</div>
            <div class="bubble solid-bubble">
                <div class="bubble-header">FACTCHECK AI | VERDICT GENERATED</div>
                <div class="verdict-box">${parseSimpleFormatting(markdownText)}</div>
            </div>
        </div>`;
    chatWrapper.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
}

function scrollToBottom() { chatWrapper.scrollTop = chatWrapper.scrollHeight; }
function escapeHtml(str) { return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

function parseSimpleFormatting(text) {
    let formatted = escapeHtml(text);
    formatted = formatted.replace(/VERDICT:\s*(REAL)/gi, 'VERDICT: <span style="background: #064e3b; color: #34d399; padding: 2px 8px; border-radius: 4px; font-weight: bold;">REAL</span>');
    formatted = formatted.replace(/VERDICT:\s*(FAKE)/gi, 'VERDICT: <span style="background: #7f1d1d; color: #fca5a5; padding: 2px 8px; border-radius: 4px; font-weight: bold;">FAKE</span>');
    formatted = formatted.replace(/VERDICT:\s*(SATIRE)/gi, 'VERDICT: <span style="background: #78350f; color: #fcd34d; padding: 2px 8px; border-radius: 4px; font-weight: bold;">SATIRE</span>');
    formatted = formatted.replace(/VERDICT:\s*(MISLEADING)/gi, 'VERDICT: <span style="background: #7c2d12; color: #ffedd5; padding: 2px 8px; border-radius: 4px; font-weight: bold;">MISLEADING</span>');
    return formatted.replace(/\n/g, '<br>');
}