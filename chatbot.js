/**
 * AIAC Virtual Concierge Chatbot Widget
 * Floating assistant for instant answers on hostel rules, timings, outpasses, mess, and laundry.
 */

document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('chatbotToggle');
  const chatWindow = document.getElementById('chatbotWindow');
  const closeBtn = document.getElementById('chatCloseBtn');
  const chatInput = document.getElementById('chatInput');
  const chatSendBtn = document.getElementById('chatSendBtn');
  const chatMessages = document.getElementById('chatMessages');

  if (!toggleBtn || !chatWindow) return;

  toggleBtn.addEventListener('click', () => {
    chatWindow.classList.toggle('open');
    if (chatWindow.classList.contains('open') && chatInput) {
      chatInput.focus();
    }
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      chatWindow.classList.remove('open');
    });
  }

  const appendMessage = (sender, text) => {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${sender}`;
    // Simple markdown link & bold converter
    let formatted = text
      .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
      .replace(/\*(.*?)\*/g, '<i>$1</i>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br/>');
    msgDiv.innerHTML = formatted;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  };

  const sendMessage = (text) => {
    const msg = (text || (chatInput ? chatInput.value : '')).trim();
    if (!msg) return;

    appendMessage('user', msg);
    if (chatInput) chatInput.value = '';

    // Show typing placeholder
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'chat-msg bot typing';
    typingIndicator.innerHTML = '<i>AIAC is thinking...</i>';
    chatMessages.appendChild(typingIndicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    fetch('/api/ai/chatbot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    })
    .then(res => res.json())
    .then(data => {
      typingIndicator.remove();
      if (data && data.reply) {
        appendMessage('bot', data.reply);
      } else {
        appendMessage('bot', "I'm having trouble processing that right now. Please check hostel contacts.");
      }
    })
    .catch(err => {
      typingIndicator.remove();
      appendMessage('bot', "Connection error. Please try again.");
    });
  };

  if (chatSendBtn) {
    chatSendBtn.addEventListener('click', () => sendMessage());
  }

  if (chatInput) {
    chatInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        sendMessage();
      }
    });
  }

  // Quick prompt chip buttons
  document.querySelectorAll('.chip-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const prompt = btn.getAttribute('data-prompt');
      if (prompt) {
        sendMessage(prompt);
      }
    });
  });
});
