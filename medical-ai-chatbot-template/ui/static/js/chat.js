// Simple working chat functionality
let isTyping = false;

function initializeChat() {
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    
    if (userInput && sendBtn) {
        userInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        sendBtn.addEventListener('click', sendMessage);
    }
    
    // Initialize quick questions
    const quickBtns = document.querySelectorAll('.quick-question-btn');
    quickBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const question = this.dataset.question;
            if (question && userInput) {
                userInput.value = question;
                sendMessage();
            }
        });
    });
}

async function sendMessage() {
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    
    if (!userInput || isTyping) return;
    
    const message = userInput.value.trim();
    if (!message) return;
    
    // Clear input
    userInput.value = '';
    isTyping = true;
    
    // Add user message
    addUserMessage(message);
    
    // Show loading
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<div class="spinner"></div>';
    }
    
    try {
        // Send to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addBotMessage(data.ai_response || 'No response received');
        } else {
            addBotMessage('Sorry, I encountered an error. Please try again.');
        }
        
    } catch (error) {
        console.error('Chat error:', error);
        addBotMessage('Connection error. Please check your internet connection.');
    } finally {
        isTyping = false;
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
        userInput.focus();
    }
}

function addUserMessage(message) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message-container user-message';
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <div class="avatar-bg">
                <i class="fas fa-user"></i>
            </div>
        </div>
        <div class="message-bubble">
            <div class="message-header">
                <span class="sender-name">You</span>
                <span class="message-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="message-content">
                <p>${escapeHtml(message)}</p>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addBotMessage(message) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message-container bot-message';
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <div class="avatar-bg">
                <i class="fas fa-robot"></i>
            </div>
            <div class="online-indicator"></div>
        </div>
        <div class="message-bubble">
            <div class="message-header">
                <span class="sender-name">Medical AI Assistant</span>
                <span class="message-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="message-content">
                <p>${escapeHtml(message)}</p>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', initializeChat);

// Export for global access
window.sendMessage = sendMessage;