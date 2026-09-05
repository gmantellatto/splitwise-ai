/**
 * app.js — Frontend: SSE, render de mensagens, seletor de grupo.
 * Arquivo completo — infraestrutura, não conceito da prova.
 */

const messagesEl = document.getElementById('messages');
const form       = document.getElementById('chat-form');
const inputEl    = document.getElementById('user-input');
const sendBtn    = document.getElementById('send-btn');
const groupSel   = document.getElementById('group-select');

let activeGroupId = null;

// ── Carregar grupos ao iniciar ──
async function loadGroups() {
  try {
    const res  = await fetch('/api/groups');
    const data = await res.json();
    groupSel.innerHTML = '<option value="">Nenhum grupo</option>';
    data.groups.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g.id;
      opt.textContent = `${g.name} (${g.participants.join(', ')})`;
      groupSel.appendChild(opt);
    });
  } catch (e) {
    console.warn('Não foi possível carregar grupos:', e);
  }
}

groupSel.addEventListener('change', () => {
  activeGroupId = groupSel.value || null;
});

// ── Renderizar mensagens ──
function addMessage(role) {
  const wrapper = document.createElement('div');
  wrapper.className = `message ${role}`;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  wrapper.appendChild(bubble);
  messagesEl.appendChild(wrapper);
  scrollToBottom();
  return bubble;
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// Auto-resize do textarea
inputEl.addEventListener('input', () => {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 112) + 'px';
});

// Enviar com Enter (Shift+Enter = nova linha)
inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

// ── Submit — chama /api/chat e consome o SSE ──
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const message = inputEl.value.trim();
  if (!message) return;

  // Mostra mensagem do usuário
  const userBubble = addMessage('user');
  userBubble.textContent = message;

  // Limpa input e desabilita envio durante stream
  inputEl.value = '';
  inputEl.style.height = 'auto';
  sendBtn.disabled = true;

  // Cria bolha do assistente com cursor piscando
  const aiBubble = addMessage('assistant');
  aiBubble.classList.add('streaming');
  aiBubble.textContent = '';

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, group_id: activeGroupId })
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    // Consome o stream SSE
    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let   buffer  = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // guarda linha incompleta

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const raw = line.slice(6).trim();
        if (raw === '[DONE]') break;

        try {
          const event = JSON.parse(raw);
          if (event.error) {
            aiBubble.textContent += `\n⚠️ ${event.error}`;
          } else if (event.text) {
            aiBubble.textContent += event.text;
            scrollToBottom();
          }
        } catch (_) { /* chunk JSON inválido — ignorar */ }
      }
    }

  } catch (err) {
    aiBubble.textContent = `Erro de conexão: ${err.message}`;
  } finally {
    aiBubble.classList.remove('streaming');
    sendBtn.disabled = false;
    inputEl.focus();
    // Recarrega grupos caso um novo tenha sido criado
    loadGroups();
  }
});

// Inicia
loadGroups();
