/* ============================================================
   app.js — SplitWise SPA
   ============================================================ */

// ── Estado global ────────────────────────────────────────────
const state = {
  groups: [],
  activeGroup: null,   // objeto Group completo
  activeTab: 'expenses',
  chatOpen: false,
  chatSessionId: crypto.randomUUID(),
};

// ── API client ────────────────────────────────────────────────
const api = {
  async get(path) {
    const r = await fetch(path);
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || 'Erro'); }
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || 'Erro'); }
    return r.json();
  },
  async patch(path, body) {
    const r = await fetch(path, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || 'Erro'); }
    return r.json();
  },
  async del(path) {
    const r = await fetch(path, { method: 'DELETE' });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || 'Erro'); }
    return r.json();
  },
};

// ── Toast ─────────────────────────────────────────────────────
let toastTimer;
function toast(msg, type = '') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast show' + (type ? ' ' + type : '');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.className = 'toast'; }, 3000);
}

// ── Formatação ────────────────────────────────────────────────
function fmt(n) { return 'R$ ' + Number(n).toFixed(2).replace('.', ','); }
function initials(name) { return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase(); }
function expenseIcon(desc) {
  const d = desc.toLowerCase();
  if (/jantar|almoço|comida|restaurante|pizza|lanche/.test(d)) return '🍽️';
  if (/uber|táxi|gasolina|combustível|carro|ônibus/.test(d)) return '🚗';
  if (/hotel|hostel|airbnb|hospedagem/.test(d)) return '🏨';
  if (/ingresso|cinema|show|festa/.test(d)) return '🎟️';
  if (/mercado|compra|supermercado/.test(d)) return '🛒';
  if (/passagem|voo|avião/.test(d)) return '✈️';
  return '💳';
}

// ── Navegação (telas) ────────────────────────────────────────
function showScreen(id) {
  const prev = document.querySelector('.screen.active');
  const next = document.getElementById(id);
  if (prev === next) return;

  if (id === 'screen-group') {
    prev?.classList.add('slide-out');
    next.classList.add('active');
    setTimeout(() => prev?.classList.remove('slide-out', 'active'), 300);
  } else {
    prev?.classList.remove('active');
    next.classList.add('active');
  }
}

// ── Tabs ──────────────────────────────────────────────────────
function setTab(tabName) {
  state.activeTab = tabName;
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tabName));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === `tab-${tabName}`));
  if (tabName === 'balances') renderBalances();
  if (tabName === 'members') renderMembers();
  if (tabName === 'expenses') renderExpenses();
}

// ── HOME: renderizar grupos ───────────────────────────────────
async function loadGroups() {
  try {
    const data = await api.get('/api/groups');
    state.groups = data.groups || [];
    renderGroups();
  } catch (e) {
    toast('Erro ao carregar grupos', 'error');
  }
}

function renderGroups() {
  const list = document.getElementById('groups-list');
  const empty = document.getElementById('groups-empty');

  if (!state.groups.length) {
    list.innerHTML = '';
    list.appendChild(empty);
    empty.classList.remove('hidden');
    return;
  }

  list.innerHTML = '';
  state.groups.forEach(g => {
    const card = document.createElement('div');
    card.className = 'group-card';
    card.innerHTML = `
      <div class="group-avatar">💸</div>
      <div class="group-info">
        <div class="group-name">${esc(g.name)}</div>
        <div class="group-meta">${g.participants.length} membros · ${g.total_expenses ?? g.participants.length + ' pessoas'}</div>
      </div>
      <svg class="group-arrow" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
    `;
    card.addEventListener('click', () => openGroup(g.id));
    list.appendChild(card);
  });
}

// ── GRUPO: abrir ──────────────────────────────────────────────
async function openGroup(groupId) {
  try {
    const group = await api.get(`/api/groups/${groupId}`);
    state.activeGroup = group;
    document.getElementById('group-title').textContent = group.name;
    setTab('expenses');
    showScreen('screen-group');
  } catch (e) {
    toast('Erro ao abrir grupo', 'error');
  }
}

async function refreshActiveGroup() {
  if (!state.activeGroup) return;
  try {
    state.activeGroup = await api.get(`/api/groups/${state.activeGroup.id}`);
  } catch (_) {}
}

// ── GRUPO: despesas ───────────────────────────────────────────
function renderExpenses() {
  const list = document.getElementById('expenses-list');
  const g = state.activeGroup;
  if (!g) return;

  if (!g.expenses?.length) {
    list.innerHTML = '<div class="list-empty">Nenhuma despesa ainda.<br>Adicione a primeira!</div>';
    return;
  }

  list.innerHTML = '';
  g.expenses.forEach(e => {
    const card = document.createElement('div');
    card.className = 'expense-card';
    card.innerHTML = `
      <div class="expense-icon">${expenseIcon(e.description)}</div>
      <div class="expense-info">
        <div class="expense-desc">${esc(e.description)}</div>
        <div class="expense-meta">Pago por ${esc(e.paid_by)} · dividido entre ${e.split_among.length}</div>
      </div>
      <div>
        <div class="expense-amount">${fmt(e.amount)}</div>
        <div class="card-actions" style="justify-content:flex-end;margin-top:4px">
          <button class="btn-action" title="Editar" data-id="${e.id}" data-action="edit-expense">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button class="btn-action danger" title="Remover" data-id="${e.id}" data-action="del-expense">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
          </button>
        </div>
      </div>
    `;
    list.appendChild(card);
  });
}

// ── GRUPO: saldos ─────────────────────────────────────────────
async function renderBalances() {
  const list = document.getElementById('balances-list');
  list.innerHTML = '<div class="skeleton"></div>';

  try {
    const data = await api.get(`/api/groups/${state.activeGroup.id}/balances`);
    const balances = data.balances || [];

    if (!balances.length) {
      list.innerHTML = '<div class="list-empty">Nenhuma despesa registrada.</div>';
      return;
    }

    list.innerHTML = '';
    balances.forEach(b => {
      const isPos = b.balance > 0, isNeg = b.balance < 0;
      const card = document.createElement('div');
      card.className = 'balance-card';
      card.innerHTML = `
        <div class="balance-avatar">${initials(b.participant)}</div>
        <div style="flex:1">
          <div class="balance-name">${esc(b.participant)}</div>
          <div class="balance-status">${esc(b.status)}</div>
        </div>
        <div class="balance-amount ${isPos ? 'positive' : isNeg ? 'negative' : 'zero'}">
          ${isPos ? '+' : ''}${fmt(b.balance)}
        </div>
      `;
      list.appendChild(card);
    });
  } catch (e) {
    list.innerHTML = '<div class="list-empty">Erro ao calcular saldos.</div>';
  }
}

// ── GRUPO: liquidações otimizadas ─────────────────────────────
document.getElementById('btn-optimize').addEventListener('click', async () => {
  const section = document.getElementById('optimized-section');
  const list = document.getElementById('optimized-list');
  section.classList.remove('hidden');
  list.innerHTML = '<div class="skeleton"></div>';

  try {
    const data = await api.get(`/api/groups/${state.activeGroup.id}/optimized`);
    const txs = data.transactions || [];

    if (!txs.length) {
      list.innerHTML = '<div class="list-empty">Nenhuma transferência necessária! 🎉</div>';
      return;
    }

    list.innerHTML = '';
    txs.forEach(t => {
      const card = document.createElement('div');
      card.className = 'transfer-card';
      card.innerHTML = `
        <div style="flex:1">
          <span class="transfer-from">${esc(t.from)}</span>
          <span class="transfer-arrow"> → </span>
          <span class="transfer-to">${esc(t.to)}</span>
        </div>
        <div class="transfer-amount">${fmt(t.amount)}</div>
      `;
      list.appendChild(card);
    });
  } catch (e) {
    list.innerHTML = '<div class="list-empty">Erro ao otimizar.</div>';
  }
});

// ── GRUPO: membros ────────────────────────────────────────────
function renderMembers() {
  const list = document.getElementById('members-list');
  const g = state.activeGroup;
  if (!g) return;

  list.innerHTML = '';
  g.participants.forEach(p => {
    const card = document.createElement('div');
    card.className = 'member-card';
    card.innerHTML = `
      <div class="member-avatar">${initials(p)}</div>
      <div class="member-name">${esc(p)}</div>
      <div class="card-actions">
        <button class="btn-action" title="Renomear" data-name="${esc(p)}" data-action="rename-member">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        </button>
        <button class="btn-action danger" title="Remover" data-name="${esc(p)}" data-action="del-member">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
        </button>
      </div>
    `;
    list.appendChild(card);
  });
}

// ── Delegação de eventos (lista) ──────────────────────────────
document.getElementById('tab-expenses').addEventListener('click', async e => {
  const btn = e.target.closest('[data-action]');
  if (!btn) return;
  const { action, id } = btn.dataset;

  if (action === 'edit-expense') {
    const exp = state.activeGroup.expenses.find(ex => ex.id === id);
    if (exp) openExpenseModal(exp);
  }
  if (action === 'del-expense') {
    if (!confirm('Remover esta despesa?')) return;
    try {
      await api.del(`/api/groups/${state.activeGroup.id}/expenses/${id}`);
      toast('Despesa removida', 'success');
      await refreshAndRender();
    } catch (err) { toast(err.message, 'error'); }
  }
});

document.getElementById('tab-members').addEventListener('click', async e => {
  const btn = e.target.closest('[data-action]');
  if (!btn) return;
  const { action, name } = btn.dataset;

  if (action === 'rename-member') openRenameModal(name);
  if (action === 'del-member') {
    if (!confirm(`Remover "${name}" do grupo?`)) return;
    try {
      await api.del(`/api/groups/${state.activeGroup.id}/participants/${encodeURIComponent(name)}`);
      toast(`${name} removido`, 'success');
      await refreshAndRender();
    } catch (err) { toast(err.message, 'error'); }
  }
});

async function refreshAndRender() {
  await refreshActiveGroup();
  if (state.activeTab === 'expenses') renderExpenses();
  if (state.activeTab === 'members') renderMembers();
  if (state.activeTab === 'balances') renderBalances();
}

// ── Modal helper ──────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id).classList.add('open');
  document.getElementById('modal-overlay').classList.add('open');
}
function closeModal(id) {
  document.getElementById(id).classList.remove('open');
  // fecha overlay se nenhum outro modal estiver aberto
  if (!document.querySelector('.modal.open')) {
    document.getElementById('modal-overlay').classList.remove('open');
  }
}

document.getElementById('modal-overlay').addEventListener('click', () => {
  document.querySelectorAll('.modal.open').forEach(m => m.classList.remove('open'));
  document.getElementById('modal-overlay').classList.remove('open');
});
document.querySelectorAll('.modal-close').forEach(btn => {
  btn.addEventListener('click', () => closeModal(btn.dataset.modal));
});

// ── MODAL: Novo grupo ─────────────────────────────────────────
function setupNewGroupModal() {
  const open = () => {
    document.getElementById('form-new-group').reset();
    const inputs = document.getElementById('participants-inputs');
    inputs.innerHTML = `
      <input class="field-input mb-2" name="participant" placeholder="Nome" required />
      <input class="field-input mb-2" name="participant" placeholder="Nome" required />
    `;
    openModal('modal-new-group');
  };
  document.getElementById('btn-new-group').addEventListener('click', open);
  document.getElementById('btn-new-group-2')?.addEventListener('click', open);

  document.getElementById('btn-add-participant-field').addEventListener('click', () => {
    const inp = document.createElement('input');
    inp.className = 'field-input mb-2';
    inp.name = 'participant';
    inp.placeholder = 'Nome';
    inp.required = true;
    document.getElementById('participants-inputs').appendChild(inp);
  });

  document.getElementById('form-new-group').addEventListener('submit', async e => {
    e.preventDefault();
    const name = e.target.name.value.trim();
    const participants = [...e.target.querySelectorAll('[name=participant]')]
      .map(i => i.value.trim()).filter(Boolean);

    try {
      await api.post('/api/groups', { name, participants });
      toast('Grupo criado!', 'success');
      closeModal('modal-new-group');
      await loadGroups();
    } catch (err) { toast(err.message, 'error'); }
  });
}

// ── MODAL: Despesa (nova/editar) ──────────────────────────────
function openExpenseModal(existing = null) {
  const g = state.activeGroup;
  document.getElementById('modal-expense-title').textContent = existing ? 'Editar despesa' : 'Nova despesa';
  document.getElementById('expense-id-field').value = existing?.id || '';
  document.getElementById('expense-desc').value = existing?.description || '';
  document.getElementById('expense-amount').value = existing?.amount || '';

  // Paid-by select
  const paidBy = document.getElementById('expense-paid-by');
  paidBy.innerHTML = g.participants.map(p =>
    `<option value="${esc(p)}" ${existing?.paid_by === p ? 'selected' : ''}>${esc(p)}</option>`
  ).join('');

  // Split checkboxes
  const splitBox = document.getElementById('expense-split-checkboxes');
  splitBox.innerHTML = g.participants.map(p => {
    const checked = existing ? existing.split_among.includes(p) : true;
    return `<label class="check-chip ${checked ? 'checked' : ''}">
      <input type="checkbox" value="${esc(p)}" ${checked ? 'checked' : ''}>
      ${esc(p)}
    </label>`;
  }).join('');

  // Toggle chip style on change
  splitBox.querySelectorAll('input[type=checkbox]').forEach(cb => {
    cb.addEventListener('change', () => {
      cb.closest('.check-chip').classList.toggle('checked', cb.checked);
    });
  });

  openModal('modal-expense');
}

document.getElementById('btn-add-expense').addEventListener('click', () => openExpenseModal());

document.getElementById('form-expense').addEventListener('submit', async e => {
  e.preventDefault();
  const g = state.activeGroup;
  const expId = document.getElementById('expense-id-field').value;
  const description = document.getElementById('expense-desc').value.trim();
  const amount = parseFloat(document.getElementById('expense-amount').value);
  const paid_by = document.getElementById('expense-paid-by').value;
  const split_among = [...document.getElementById('expense-split-checkboxes').querySelectorAll('input:checked')]
    .map(cb => cb.value);

  if (!split_among.length) { toast('Selecione ao menos 1 pessoa para dividir', 'error'); return; }

  try {
    if (expId) {
      await api.patch(`/api/groups/${g.id}/expenses/${expId}`, { description, amount, paid_by, split_among });
      toast('Despesa atualizada', 'success');
    } else {
      await api.post(`/api/groups/${g.id}/expenses`, { description, amount, paid_by, split_among });
      toast('Despesa adicionada!', 'success');
    }
    closeModal('modal-expense');
    await refreshAndRender();
  } catch (err) { toast(err.message, 'error'); }
});

// ── MODAL: Adicionar membro ───────────────────────────────────
document.getElementById('btn-add-member').addEventListener('click', () => {
  document.getElementById('new-member-name').value = '';
  openModal('modal-add-member');
});

document.getElementById('form-add-member').addEventListener('submit', async e => {
  e.preventDefault();
  const participant = document.getElementById('new-member-name').value.trim();
  try {
    await api.post(`/api/groups/${state.activeGroup.id}/participants`, { participant });
    toast(`${participant} adicionado!`, 'success');
    closeModal('modal-add-member');
    await refreshAndRender();
  } catch (err) { toast(err.message, 'error'); }
});

// ── MODAL: Renomear membro ────────────────────────────────────
function openRenameModal(oldName) {
  document.getElementById('rename-old-name').value = oldName;
  document.getElementById('rename-display-old').value = oldName;
  document.getElementById('rename-new-name').value = '';
  openModal('modal-rename-member');
}

document.getElementById('form-rename-member').addEventListener('submit', async e => {
  e.preventDefault();
  const old_name = document.getElementById('rename-old-name').value;
  const new_name = document.getElementById('rename-new-name').value.trim();
  try {
    await api.patch(`/api/groups/${state.activeGroup.id}/participants`, { old_name, new_name });
    toast(`Renomeado para ${new_name}`, 'success');
    closeModal('modal-rename-member');
    await refreshAndRender();
  } catch (err) { toast(err.message, 'error'); }
});

// ── Botão Voltar ──────────────────────────────────────────────
document.getElementById('btn-back').addEventListener('click', async () => {
  showScreen('screen-home');
  state.activeGroup = null;
  await loadGroups();
});

// ── Botão Excluir grupo ───────────────────────────────────────
document.getElementById('btn-delete-group').addEventListener('click', async () => {
  const g = state.activeGroup;
  if (!g) return;
  if (!confirm(`Excluir o grupo "${g.name}" e todas as suas despesas? Esta ação é irreversível.`)) return;
  try {
    await api.del(`/api/groups/${g.id}`);
    toast('Grupo excluído', 'success');
    showScreen('screen-home');
    state.activeGroup = null;
    await loadGroups();
  } catch (err) { toast(err.message, 'error'); }
});

// ── Botão Desfazer ────────────────────────────────────────────
document.getElementById('btn-undo').addEventListener('click', async () => {
  if (!state.activeGroup) return;
  try {
    await api.post(`/api/groups/${state.activeGroup.id}/undo`);
    toast('Ação desfeita!', 'success');
    await refreshAndRender();
  } catch (err) { toast(err.message, 'error'); }
});

// ── Tabs ──────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.getElementById('optimized-section')?.classList.add('hidden');
    setTab(tab.dataset.tab);
  });
});

// ── Chat panel ────────────────────────────────────────────────
const fab          = document.getElementById('fab');
const chatPanel    = document.getElementById('chat-panel');
const chatBackdrop = document.getElementById('chat-backdrop');

function openChat() {
  state.chatOpen = true;
  chatPanel.classList.add('open');
  chatBackdrop.classList.add('open');
  chatPanel.setAttribute('aria-hidden', 'false');
  // Mostra grupo ativo no header do chat
  const label = document.getElementById('chat-group-label');
  label.textContent = state.activeGroup ? `Grupo: ${state.activeGroup.name}` : '';
  document.getElementById('chat-input').focus();
}

function closeChat() {
  state.chatOpen = false;
  chatPanel.classList.remove('open');
  chatBackdrop.classList.remove('open');
  chatPanel.setAttribute('aria-hidden', 'true');
}

fab.addEventListener('click', () => state.chatOpen ? closeChat() : openChat());
chatBackdrop.addEventListener('click', closeChat);
document.getElementById('btn-close-chat').addEventListener('click', closeChat);

// Auto-resize textarea do chat
const chatInput = document.getElementById('chat-input');
chatInput.addEventListener('input', () => {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 112) + 'px';
});
chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); document.getElementById('chat-form').requestSubmit(); }
});

// Chat: submit
document.getElementById('chat-form').addEventListener('submit', async e => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  const messagesEl = document.getElementById('chat-messages');

  // Bolha do usuário
  const userMsg = document.createElement('div');
  userMsg.className = 'chat-msg user';
  userMsg.innerHTML = `<div class="chat-bubble">${esc(message)}</div>`;
  messagesEl.appendChild(userMsg);

  chatInput.value = '';
  chatInput.style.height = 'auto';

  const sendBtn = document.querySelector('.chat-send-btn');
  sendBtn.disabled = true;

  // Bolha do assistente
  const aiBubble = document.createElement('div');
  aiBubble.className = 'chat-bubble streaming';
  const aiMsg = document.createElement('div');
  aiMsg.className = 'chat-msg assistant';
  aiMsg.appendChild(aiBubble);
  messagesEl.appendChild(aiMsg);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        group_id: state.activeGroup?.id || null,
        session_id: state.chatSessionId,
      }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let   buffer  = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const raw = line.slice(6).trim();
        if (raw === '[DONE]') break;
        try {
          const ev = JSON.parse(raw);
          if (ev.text) { aiBubble.textContent += ev.text; messagesEl.scrollTop = messagesEl.scrollHeight; }
          if (ev.error) aiBubble.textContent += `\n⚠️ ${ev.error}`;
        } catch (_) {}
      }
    }

    // Recarrega dados do grupo após resposta da IA (pode ter criado/editado algo)
    if (state.activeGroup) await refreshAndRender();
    else await loadGroups();

  } catch (err) {
    aiBubble.textContent = `Erro: ${err.message}`;
  } finally {
    aiBubble.classList.remove('streaming');
    sendBtn.disabled = false;
    chatInput.focus();
  }
});

// ── Utilitário: escape HTML ───────────────────────────────────
function esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Init ──────────────────────────────────────────────────────
setupNewGroupModal();
loadGroups();
