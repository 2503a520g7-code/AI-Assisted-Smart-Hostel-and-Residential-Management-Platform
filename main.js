/**
 * AIAC — Main JavaScript
 * Handles sidebar interactions, real-time table filtering, modals,
 * and AI complaint auto-suggestions.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Sidebar Toggle
  const mobileToggle = document.getElementById('mobileToggle');
  const sidebar = document.getElementById('sidebar');
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 900 && sidebar.classList.contains('open')) {
        if (!sidebar.contains(e.target) && e.target !== mobileToggle) {
          sidebar.classList.remove('open');
        }
      }
    });
  }

  // 2. Alert Dismissal
  document.querySelectorAll('.alert .close-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // 3. Client-Side Table Filter & Search
  const tableSearchInputs = document.querySelectorAll('[data-table-search]');
  tableSearchInputs.forEach(input => {
    const targetTableId = input.getAttribute('data-table-search');
    const table = document.getElementById(targetTableId);
    if (!table) return;

    input.addEventListener('input', () => {
      const query = input.value.toLowerCase().trim();
      const rows = table.querySelectorAll('tbody tr');
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    });
  });

  // 4. Modal Helpers
  window.openModal = function(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.classList.add('active');
  };

  window.closeModal = function(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.classList.remove('active');
  };

  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.classList.remove('active');
      }
    });
  });

  // 5. AI Complaint Suggestion Assistant
  const complaintSubject = document.getElementById('complaintSubject');
  const complaintDesc = document.getElementById('complaintDescription');
  const aiSuggestionBox = document.getElementById('aiSuggestionBox');
  const categorySelect = document.getElementById('complaintCategory');
  const prioritySelect = document.getElementById('complaintPriority');

  if (complaintSubject && complaintDesc && aiSuggestionBox) {
    let debounceTimer = null;

    const fetchAiSuggestion = () => {
      const subject = complaintSubject.value.trim();
      const desc = complaintDesc.value.trim();

      if (subject.length < 3 && desc.length < 5) {
        aiSuggestionBox.style.display = 'none';
        return;
      }

      fetch('/api/ai/suggest-complaint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject: subject, description: desc })
      })
      .then(res => res.json())
      .then(data => {
        if (data && data.suggested_category) {
          aiSuggestionBox.style.display = 'block';
          aiSuggestionBox.innerHTML = `
            <div style="background:#eef2ff; border:1px solid #c7d2fe; padding:0.65rem 1rem; border-radius:8px; display:flex; align-items:center; justify-content:space-between; gap:0.5rem;">
              <div>
                <span style="font-weight:700; color:#4338ca; font-size:0.85rem;">🤖 AI Suggestion:</span>
                <span style="color:#1e1b4b; font-weight:600; font-size:0.85rem;">Category: <b>${data.suggested_category}</b></span> · 
                <span style="color:#1e1b4b; font-weight:600; font-size:0.85rem;">Priority: <b>${data.suggested_priority}</b></span>
                <p style="font-size:0.75rem; color:#6366f1; margin:2px 0 0;">${data.reasoning}</p>
              </div>
              <button type="button" class="btn btn-primary btn-sm" id="applyAiSuggestionBtn" style="padding:4px 10px; font-size:0.78rem;">
                Apply
              </button>
            </div>
          `;

          const applyBtn = document.getElementById('applyAiSuggestionBtn');
          if (applyBtn) {
            applyBtn.addEventListener('click', () => {
              if (categorySelect) categorySelect.value = data.suggested_category;
              if (prioritySelect) prioritySelect.value = data.suggested_priority;
              aiSuggestionBox.style.display = 'none';
            });
          }
        }
      })
      .catch(err => console.error('AI suggestion error:', err));
    };

    complaintSubject.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(fetchAiSuggestion, 500);
    });

    complaintDesc.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(fetchAiSuggestion, 500);
    });
  }

  // 6. Payment Modal Prep
  window.preparePaymentModal = function(recordId, totalAmount, amountPaid, feeType) {
    const due = Math.max(0, totalAmount - amountPaid);
    const recInput = document.getElementById('payRecordId');
    const amtInput = document.getElementById('payAmount');
    const dueDisplay = document.getElementById('payDueDisplay');

    if (recInput) recInput.value = recordId;
    if (amtInput) {
      amtInput.value = due.toFixed(2);
      amtInput.max = due.toFixed(2);
    }
    if (dueDisplay) dueDisplay.textContent = `₹ ${due.toLocaleString()}`;

    openModal('paymentModal');
  };
});
