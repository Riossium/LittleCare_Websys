/**
 * LittleCare AI Healthcare Assistant Frontend Controller
 */

document.addEventListener('DOMContentLoaded', function () {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    const authToggle = document.getElementById('auth-records-toggle');
    const babySelect = document.getElementById('chat-baby-select');
    const convIdInput = document.getElementById('conversation-id');
    const newChatBtn = document.getElementById('btn-new-chat');

    if (!chatForm || !chatInput || !messagesContainer) return;

    // Scroll to bottom on load
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;

        // Append user bubble
        appendMessage('user', message);
        chatInput.value = '';

        // Show typing indicator
        const typingEl = appendTypingIndicator();
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Fetch CSRF token
        const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';

        fetch('/ai-assistant/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                message: message,
                baby_id: babySelect ? babySelect.value : null,
                authorize_records: authToggle ? authToggle.checked : false,
                conversation_id: convIdInput ? convIdInput.value : null
            })
        })
        .then(res => res.json())
        .then(data => {
            typingEl.remove();
            if (data.error) {
                appendMessage('assistant', `⚠️ ${data.error}`);
            } else {
                if (convIdInput && data.conversation_id) {
                    convIdInput.value = data.conversation_id;
                }
                appendAssistantResponse(data.answer, data.suggested_actions, data.articles, data.source);
            }
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        })
        .catch(err => {
            typingEl.remove();
            appendMessage('assistant', 'Sorry, I encountered a temporary connection issue. Please try again.');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });
    });

    function appendMessage(sender, text) {
        const div = document.createElement('div');
        div.className = `message-bubble ${sender === 'user' ? 'message-user' : 'message-assistant'}`;
        div.innerHTML = formatMarkdown(text);
        messagesContainer.appendChild(div);
        return div;
    }

    function appendTypingIndicator() {
        const div = document.createElement('div');
        div.className = 'message-bubble message-assistant';
        div.id = 'typing-indicator';
        div.innerHTML = '<span class="spinner-grow spinner-grow-sm text-primary" role="status"></span> <small class="text-muted ms-2">LittleCare AI is reviewing pediatric references...</small>';
        messagesContainer.appendChild(div);
        return div;
    }

    function appendAssistantResponse(answer, actions, articles, source) {
        const div = document.createElement('div');
        div.className = 'message-bubble message-assistant';

        let html = formatMarkdown(answer);

        // Render Suggested Actions
        if (actions && actions.length > 0) {
            html += '<div class="mt-3 pt-2 border-top"><small class="text-muted fw-bold d-block mb-1">Suggested Next Steps:</small>';
            actions.forEach(a => {
                html += `<a href="${a.url}" class="action-pill"><i class="bi ${a.icon || 'bi-arrow-right-circle'}"></i> ${a.label}</a>`;
            });
            html += '</div>';
        }

        // Render Relevant Articles
        if (articles && articles.length > 0) {
            html += '<div class="mt-3 pt-2 border-top"><small class="text-muted fw-bold d-block mb-2"><i class="bi bi-journal-medical text-primary"></i> Recommended Health Library Reading:</small><div class="list-group list-group-flush">';
            articles.forEach(art => {
                html += `<a href="/articles/${art.slug}" class="list-group-item list-group-item-action py-2 px-2 rounded-3 mb-1 bg-light border-0">
                    <span class="badge badge-blue me-1">${art.category}</span>
                    <strong class="text-dark small">${art.title}</strong>
                </a>`;
            });
            html += '</div></div>';
        }

        div.innerHTML = html;
        messagesContainer.appendChild(div);
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let escaped = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Markdown conversions
        escaped = escaped.replace(/^### (.*$)/gim, '<h6 class="fw-bold mt-2 mb-1 text-primary">$1</h6>');
        escaped = escaped.replace(/^## (.*$)/gim, '<h5 class="fw-bold mt-2 mb-1 text-primary">$1</h5>');
        escaped = escaped.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
        escaped = escaped.replace(/\*(.*?)\*/gim, '<em>$1</em>');
        escaped = escaped.replace(/^\- (.*$)/gim, '<li>$1</li>');
        escaped = escaped.replace(/(<li>.*<\/li>)/gim, '<ul class="mb-2 ps-3">$1</ul>');
        escaped = escaped.replace(/\n\n/g, '<p class="mb-2"></p>');
        escaped = escaped.replace(/\n/g, '<br>');

        return escaped;
    }

    if (newChatBtn) {
        newChatBtn.addEventListener('click', function () {
            const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';
            fetch('/ai-assistant/conversations/new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(res => res.json())
            .then(data => {
                window.location.href = `/ai-assistant/?conv_id=${data.conversation_id}`;
            });
        });
    }
});
