// ==========================================================================
// Go Absent - Dashboard Logic with Centered SweetAlert2
// ==========================================================================

let allRequests = [];
let allUsers = [];
let webhookStatusData = null;

// Thông báo trung tâm màn hình chuẩn SweetAlert2 (với icon hoạt họa success / error)
function showAlert(message, isError = false) {
  Swal.fire({
    icon: isError ? 'error' : 'success',
    title: isError ? 'Thất bại' : 'Thành công',
    text: message,
    position: 'center',
    width: '380px',
    padding: '1.25rem',
    showConfirmButton: true,
    confirmButtonText: 'Đóng',
    confirmButtonColor: isError ? '#dc3545' : '#0f172a',
    timer: 2500,
    timerProgressBar: true
  });
}

// Khởi động khi tải xong trang
window.addEventListener('DOMContentLoaded', () => {
  loadData();
  checkWebhookStatus(false);

  // Tự động làm mới mỗi 10 giây
  setInterval(() => {
    loadData(false);
  }, 10000);
});

// Chuyển Tab (Yêu cầu xin vắng / Quản lý nhân sự)
function switchTab(tabName) {
  const btnReq = document.getElementById('tab-btn-requests');
  const btnUsers = document.getElementById('tab-btn-users');
  const btnReqMob = document.getElementById('tab-btn-requests-mobile');
  const btnUsersMob = document.getElementById('tab-btn-users-mobile');
  const secReq = document.getElementById('section-requests');
  const secUsers = document.getElementById('section-users');

  if (tabName === 'requests') {
    if (btnReq) btnReq.className = 'btn btn-sm btn-dark fw-semibold';
    if (btnUsers) btnUsers.className = 'btn btn-sm btn-light text-secondary fw-semibold';
    if (btnReqMob) btnReqMob.className = 'btn btn-sm btn-dark flex-fill fw-semibold';
    if (btnUsersMob) btnUsersMob.className = 'btn btn-sm btn-light text-secondary flex-fill fw-semibold';
    secReq.classList.remove('d-none');
    secUsers.classList.add('d-none');
  } else {
    if (btnReq) btnReq.className = 'btn btn-sm btn-light text-secondary fw-semibold';
    if (btnUsers) btnUsers.className = 'btn btn-sm btn-dark fw-semibold';
    if (btnReqMob) btnReqMob.className = 'btn btn-sm btn-light text-secondary flex-fill fw-semibold';
    if (btnUsersMob) btnUsersMob.className = 'btn btn-sm btn-dark flex-fill fw-semibold';
    secReq.classList.add('d-none');
    secUsers.classList.remove('d-none');
  }
}

// 1. Tải danh sách đơn và nhân sự từ REST API
async function loadData(showLoadingAnim = true) {
  const icon = document.getElementById('refresh-icon');
  if (showLoadingAnim && icon) icon.classList.add('fa-spin');

  try {
    const [resLeaves, resUsers] = await Promise.all([
      fetch('/api/v1/leaves'),
      fetch('/api/v1/users')
    ]);

    const dataLeaves = await resLeaves.json();
    const dataUsers = await resUsers.json();

    allRequests = dataLeaves.data || [];
    allUsers = dataUsers.data || [];

    updateKPIs();
    renderRequests(allRequests);
    renderUsers(allUsers);
  } catch (err) {
    console.error('Lỗi khi tải dữ liệu từ API:', err);
  } finally {
    if (showLoadingAnim && icon) {
      setTimeout(() => icon.classList.remove('fa-spin'), 400);
    }
  }
}

// 2. Cập nhật 4 thẻ thống kê số lượng
function updateKPIs() {
  const total = allRequests.length;
  const pending = allRequests.filter(r => r.status === 'PENDING').length;
  const approved = allRequests.filter(r => r.status === 'APPROVED').length;
  const rejected = allRequests.filter(r => r.status === 'REJECTED').length;

  document.getElementById('stat-total').innerText = total;
  document.getElementById('stat-pending').innerText = pending;
  document.getElementById('stat-approved').innerText = approved;
  document.getElementById('stat-rejected').innerText = rejected;
}

// 3. Render danh sách yêu cầu xin vắng (Desktop Table & Mobile Cards)
function renderRequests(list, isFiltered = false) {
  const dataContainer = document.getElementById('requests-data-container');
  const emptyState = document.getElementById('requests-empty-state');
  const tbody = document.getElementById('requests-tbody');
  const mobileList = document.getElementById('requests-mobile-list');
  const emptyTitle = document.getElementById('requests-empty-title');
  const emptyDesc = document.getElementById('requests-empty-desc');
  const emptyAction = document.getElementById('requests-empty-action');

  if (!list || list.length === 0) {
    if (dataContainer) dataContainer.classList.add('d-none');
    if (emptyState) emptyState.classList.remove('d-none');

    if (isFiltered) {
      if (emptyTitle) emptyTitle.innerText = 'Không tìm thấy yêu cầu nào';
      if (emptyDesc) emptyDesc.innerText = 'Không có đơn nào khớp với bộ lọc hoặc từ khóa tìm kiếm.';
      if (emptyAction) {
        emptyAction.innerHTML = `
          <button class="btn btn-outline-dark btn-sm px-3 fw-semibold" onclick="resetRequestFilters()">
            <i class="fa-solid fa-rotate-left me-1"></i> Đặt lại bộ lọc
          </button>
        `;
      }
    } else {
      if (emptyTitle) emptyTitle.innerText = 'Chưa có yêu cầu xin vắng nào';
      if (emptyDesc) emptyDesc.innerText = 'Các yêu cầu xin vắng từ nhân viên sẽ hiển thị tại đây.';
      if (emptyAction) {
        emptyAction.innerHTML = `
          <button class="btn btn-dark btn-sm px-3 fw-semibold" onclick="openCreateLeaveModal()">
            <i class="fa-solid fa-plus me-1"></i> Tạo yêu cầu xin vắng
          </button>
        `;
      }
    }
    return;
  }

  if (dataContainer) dataContainer.classList.remove('d-none');
  if (emptyState) emptyState.classList.add('d-none');

  const sorted = [...list].sort((a, b) => b.id - a.id);

  // A. Desktop Table
  tbody.innerHTML = sorted.map(req => {
    const reqCode = `NP${String(req.id).padStart(5, '0')}`;
    const statusBadge = getStatusBadge(req.status);
    const actionsHtml = getActionsHtml(req);
    const userName = req.user_name || 'Không rõ';
    const userInitial = userName.trim().charAt(0).toUpperCase() || 'U';

    const reviewerInfo = req.reviewed_by 
      ? `<div><strong>${escapeHtml(req.reviewed_by)}</strong></div><small class="text-secondary">${req.reviewed_at || ''}</small>` 
      : '<span class="text-muted">-</span>';

    return `
      <tr>
        <td><span class="badge bg-light text-dark border font-monospace px-2 py-1">${reqCode}</span></td>
        <td>
          <div class="d-flex align-items-center gap-2">
            <div class="user-avatar">${userInitial}</div>
            <div>
              <div class="fw-semibold text-dark">${escapeHtml(userName)}</div>
              <small class="text-secondary">ID: ${req.user_id}</small>
            </div>
          </div>
        </td>
        <td><div style="max-width: 320px; line-height: 1.4;">${escapeHtml(req.reason || '')}</div></td>
        <td><small class="text-secondary">${req.created_at || ''}</small></td>
        <td>${statusBadge}</td>
        <td>${reviewerInfo}</td>
        <td class="text-center">${actionsHtml}</td>
      </tr>
    `;
  }).join('');

  // B. Mobile Cards
  mobileList.innerHTML = sorted.map(req => {
    const reqCode = `NP${String(req.id).padStart(5, '0')}`;
    const statusBadge = getStatusBadge(req.status);
    const userName = req.user_name || 'Không rõ';
    const userInitial = userName.trim().charAt(0).toUpperCase() || 'U';

    let actionButtons = '';
    if (req.status === 'PENDING') {
      actionButtons = `
        <div class="d-flex gap-2">
          <button class="btn btn-sm btn-success px-3 fw-semibold" onclick="openReviewModal(${req.id}, 'APPROVED')">
            Duyệt
          </button>
          <button class="btn btn-sm btn-outline-danger px-2 fw-semibold" onclick="openReviewModal(${req.id}, 'REJECTED')">
            Từ chối
          </button>
        </div>
      `;
    } else {
      actionButtons = `<span class="badge bg-light text-secondary border">Đã xử lý</span>`;
    }

    return `
      <div class="card border rounded-3 p-3 mobile-card shadow-sm">
        <div class="d-flex align-items-center justify-content-between mb-2">
          <span class="badge bg-light text-dark border font-monospace">${reqCode}</span>
          ${statusBadge}
        </div>
        <div class="d-flex align-items-center gap-2 mb-2">
          <div class="user-avatar">${userInitial}</div>
          <div>
            <div class="fw-bold text-dark">${escapeHtml(userName)}</div>
            <small class="text-secondary">Telegram ID: ${req.user_id}</small>
          </div>
        </div>
        <div class="p-2 bg-light rounded-2 text-dark small mb-3 border">
          ${escapeHtml(req.reason || '')}
        </div>
        <div class="d-flex align-items-center justify-content-between pt-2 border-top">
          <small class="text-secondary">${req.created_at || ''}</small>
          ${actionButtons}
        </div>
      </div>
    `;
  }).join('');
}

function getStatusBadge(status) {
  if (status === 'APPROVED') {
    return '<span class="badge bg-success-subtle text-success border border-success-subtle">Đã chấp thuận</span>';
  } else if (status === 'REJECTED') {
    return '<span class="badge bg-danger-subtle text-danger border border-danger-subtle">Đã từ chối</span>';
  } else if (status === 'CANCELLED') {
    return '<span class="badge bg-secondary-subtle text-secondary border">Đã hủy</span>';
  }
  return '<span class="badge bg-warning-subtle text-warning border border-warning-subtle">Chờ xét duyệt</span>';
}

function getActionsHtml(req) {
  if (req.status === 'PENDING') {
    return `
      <div class="d-inline-flex gap-1">
        <button class="btn btn-sm btn-success px-2 py-1" onclick="openReviewModal(${req.id}, 'APPROVED')">
          Duyệt
        </button>
        <button class="btn btn-sm btn-outline-danger px-2 py-1" onclick="openReviewModal(${req.id}, 'REJECTED')">
          Từ chối
        </button>
      </div>
    `;
  }
  return '<span class="text-secondary small">Đã xong</span>';
}

// 4. Lọc đơn
function filterRequests() {
  const query = document.getElementById('search-input').value.toLowerCase().trim();
  const statusFilter = document.getElementById('status-filter').value;
  const isFiltered = Boolean(query || statusFilter !== 'ALL');

  const filtered = allRequests.filter(req => {
    const matchesStatus = (statusFilter === 'ALL') || (req.status === statusFilter);
    const reqCode = `np${String(req.id).padStart(5, '0')}`;
    const matchesQuery = !query || 
      reqCode.includes(query) ||
      (req.user_name && req.user_name.toLowerCase().includes(query)) ||
      (req.reason && req.reason.toLowerCase().includes(query));

    return matchesStatus && matchesQuery;
  });

  renderRequests(filtered, isFiltered);
}

function resetRequestFilters() {
  const searchInput = document.getElementById('search-input');
  const statusFilter = document.getElementById('status-filter');
  if (searchInput) searchInput.value = '';
  if (statusFilter) statusFilter.value = 'ALL';
  filterRequests();
}

// 5. Render danh sách nhân sự
function renderUsers(users, isFiltered = false) {
  const dataContainer = document.getElementById('users-data-container');
  const emptyState = document.getElementById('users-empty-state');
  const tbody = document.getElementById('users-tbody');
  const mobileList = document.getElementById('users-mobile-list');
  const emptyTitle = document.getElementById('users-empty-title');
  const emptyDesc = document.getElementById('users-empty-desc');
  const emptyAction = document.getElementById('users-empty-action');

  if (!users || users.length === 0) {
    if (dataContainer) dataContainer.classList.add('d-none');
    if (emptyState) emptyState.classList.remove('d-none');

    if (isFiltered) {
      if (emptyTitle) emptyTitle.innerText = 'Không tìm thấy nhân sự';
      if (emptyDesc) emptyDesc.innerText = 'Không có nhân sự nào khớp với từ khóa tìm kiếm.';
      if (emptyAction) {
        emptyAction.classList.remove('d-none');
        emptyAction.innerHTML = `
          <button class="btn btn-outline-dark btn-sm px-3 fw-semibold" onclick="resetUserFilters()">
            <i class="fa-solid fa-rotate-left me-1"></i> Xóa tìm kiếm
          </button>
        `;
      }
    } else {
      if (emptyTitle) emptyTitle.innerText = 'Chưa có nhân sự trong hệ thống';
      if (emptyDesc) emptyDesc.innerText = 'Nhân viên gửi tin nhắn /start đến Bot Telegram sẽ tự động xuất hiện tại đây.';
      if (emptyAction) {
        emptyAction.classList.add('d-none');
        emptyAction.innerHTML = '';
      }
    }
    return;
  }

  if (dataContainer) dataContainer.classList.remove('d-none');
  if (emptyState) emptyState.classList.add('d-none');

  tbody.innerHTML = users.map(user => {
    const isMgr = user.role === 'manager';
    const roleBadge = isMgr 
      ? '<span class="badge bg-dark">Quản lý</span>'
      : '<span class="badge bg-light text-dark border">Nhân viên</span>';

    const actionBtn = isMgr
      ? `<button class="btn btn-sm btn-outline-secondary" onclick="changeRole('${user.telegram_id}', 'staff')">
           Chuyển làm Nhân viên
         </button>`
      : `<button class="btn btn-sm btn-outline-dark" onclick="changeRole('${user.telegram_id}', 'manager')">
           Đặt làm Quản lý
         </button>`;

    const usernameText = user.username ? `@${escapeHtml(user.username)}` : '<span class="text-muted">-</span>';
    const userInitial = (user.name || 'U').trim().charAt(0).toUpperCase();

    return `
      <tr>
        <td><span class="badge bg-light text-dark border font-monospace">${user.telegram_id}</span></td>
        <td>
          <div class="d-flex align-items-center gap-2">
            <div class="user-avatar">${userInitial}</div>
            <div class="fw-semibold text-dark">${escapeHtml(user.name || '')}</div>
          </div>
        </td>
        <td>${usernameText}</td>
        <td>${roleBadge}</td>
        <td><small class="text-secondary">${user.created_at || '-'}</small></td>
        <td class="text-center">${actionBtn}</td>
      </tr>
    `;
  }).join('');

  mobileList.innerHTML = users.map(user => {
    const isMgr = user.role === 'manager';
    const roleBadge = isMgr 
      ? '<span class="badge bg-dark">Quản lý</span>'
      : '<span class="badge bg-light text-dark border">Nhân viên</span>';

    const actionBtn = isMgr
      ? `<button class="btn btn-sm btn-outline-secondary w-100" onclick="changeRole('${user.telegram_id}', 'staff')">
           Chuyển làm Nhân viên
         </button>`
      : `<button class="btn btn-sm btn-dark w-100" onclick="changeRole('${user.telegram_id}', 'manager')">
           Đặt làm Quản lý
         </button>`;

    const usernameText = user.username ? `@${escapeHtml(user.username)}` : 'Không có';
    const userInitial = (user.name || 'U').trim().charAt(0).toUpperCase();

    return `
      <div class="card border rounded-3 p-3 mobile-card shadow-sm">
        <div class="d-flex align-items-center justify-content-between mb-2">
          <span class="badge bg-light text-dark border font-monospace">${user.telegram_id}</span>
          ${roleBadge}
        </div>
        <div class="d-flex align-items-center gap-2 mb-2">
          <div class="user-avatar">${userInitial}</div>
          <div>
            <div class="fw-bold text-dark">${escapeHtml(user.name || '')}</div>
            <small class="text-secondary">${usernameText}</small>
          </div>
        </div>
        <small class="text-secondary mb-3 d-block">Ngày tham gia: ${user.created_at || '-'}</small>
        ${actionBtn}
      </div>
    `;
  }).join('');
}

function filterUsers() {
  const q = document.getElementById('user-search-input').value.toLowerCase().trim();
  const isFiltered = Boolean(q);
  const filtered = allUsers.filter(u => {
    return !q || 
      String(u.telegram_id).toLowerCase().includes(q) ||
      (u.name && u.name.toLowerCase().includes(q)) ||
      (u.username && u.username.toLowerCase().includes(q));
  });
  renderUsers(filtered, isFiltered);
}

function resetUserFilters() {
  const input = document.getElementById('user-search-input');
  if (input) input.value = '';
  filterUsers();
}

// ==========================================================================
// SWEETALERT2 MODALS (TRUNG TÂM MÀN HÌNH, ICON CHUẨN SWEETALERT2)
// ==========================================================================

// 6. Modal xác nhận Duyệt / Từ chối đơn
function openReviewModal(reqId, action) {
  const isApprove = action === 'APPROVED';
  const reqCode = `NP${String(reqId).padStart(5, '0')}`;

  Swal.fire({
    icon: isApprove ? 'question' : 'warning',
    title: isApprove ? 'Duyệt đơn xin nghỉ' : 'Từ chối đơn xin nghỉ',
    html: `Bạn có chắc chắn muốn <b class="${isApprove ? 'text-success' : 'text-danger'}">${isApprove ? 'chấp thuận' : 'từ chối'}</b> yêu cầu xin vắng <code>#${reqCode}</code> không?`,
    position: 'center',
    width: '380px',
    showCancelButton: true,
    confirmButtonColor: isApprove ? '#198754' : '#dc3545',
    cancelButtonColor: '#6c757d',
    confirmButtonText: isApprove ? 'Chấp thuận' : 'Từ chối',
    cancelButtonText: 'Hủy'
  }).then((result) => {
    if (result.isConfirmed) {
      submitReview(reqId, action);
    }
  });
}

async function submitReview(reqId, action) {
  try {
    const res = await fetch(`/api/v1/leaves/${reqId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: action,
        reviewer: 'Quản trị viên (Web)'
      })
    });

    const result = await res.json();
    if (result.success) {
      showAlert(action === 'APPROVED' ? 'Đã chấp thuận yêu cầu thành công!' : 'Đã từ chối yêu cầu thành công!');
      loadData();
    } else {
      showAlert(result.message || 'Thao tác thất bại!', true);
    }
  } catch (err) {
    showAlert('Lỗi kết nối máy chủ!', true);
  }
}

// 7. Modal đổi vai trò nhân sự
function changeRole(telegramId, newRole) {
  const isManager = newRole === 'manager';
  Swal.fire({
    icon: 'question',
    title: 'Cập nhật quyền hạn',
    text: `Bạn có muốn đổi vai trò nhân sự ID ${telegramId} thành "${isManager ? 'Quản lý' : 'Nhân viên'}"?`,
    position: 'center',
    width: '380px',
    showCancelButton: true,
    confirmButtonColor: '#0f172a',
    cancelButtonColor: '#6c757d',
    confirmButtonText: 'Đồng ý',
    cancelButtonText: 'Hủy'
  }).then(async (result) => {
    if (result.isConfirmed) {
      try {
        const res = await fetch(`/api/v1/users/${telegramId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role: newRole })
        });
        const json = await res.json();
        if (json.success) {
          showAlert('Cập nhật quyền thành công!');
          loadData();
        } else {
          showAlert(json.message || 'Lỗi cập nhật quyền!', true);
        }
      } catch (e) {
        showAlert('Lỗi kết nối máy chủ!', true);
      }
    }
  });
}

// 8. Modal Tạo yêu cầu xin vắng
function openCreateLeaveModal() {
  let userOptions = '<option value="">-- Chọn nhân viên trong hệ thống --</option>';
  allUsers.forEach(u => {
    userOptions += `<option value="${u.telegram_id}" data-name="${escapeHtml(u.name || '')}" data-username="${escapeHtml(u.username || '')}">${escapeHtml(u.name || 'Người dùng')} (ID: ${u.telegram_id})</option>`;
  });
  userOptions += '<option value="__MANUAL__">+ Nhập nhân viên mới thủ công</option>';

  Swal.fire({
    title: 'Tạo yêu cầu xin vắng',
    html: `
      <div class="text-start">
        <div class="mb-3">
          <label class="form-label small fw-semibold">Chọn nhân viên:</label>
          <select id="swal-user-select" class="form-select form-select-sm" onchange="toggleSwalManualFields()">
            ${userOptions}
          </select>
        </div>
        <div id="swal-manual-box" class="d-none">
          <div class="mb-2">
            <label class="form-label small fw-semibold">Họ và tên: <span class="text-danger">*</span></label>
            <input id="swal-manual-name" class="form-control form-control-sm" placeholder="Nguyễn Văn A">
          </div>
          <div class="row g-2 mb-2">
            <div class="col-6">
              <label class="form-label small fw-semibold">Telegram ID: <span class="text-danger">*</span></label>
              <input id="swal-manual-id" class="form-control form-control-sm" placeholder="123456789">
            </div>
            <div class="col-6">
              <label class="form-label small fw-semibold">Username:</label>
              <input id="swal-manual-username" class="form-control form-control-sm" placeholder="nguyenvana">
            </div>
          </div>
        </div>
        <div class="mb-2">
          <label class="form-label small fw-semibold">Lý do xin vắng: <span class="text-danger">*</span></label>
          <textarea id="swal-leave-reason" class="form-control form-control-sm" rows="3" placeholder="Nhập lý do xin nghỉ phép..."></textarea>
        </div>
      </div>
    `,
    position: 'center',
    width: '400px',
    showCancelButton: true,
    confirmButtonText: 'Gửi yêu cầu',
    cancelButtonText: 'Hủy bỏ',
    confirmButtonColor: '#0f172a',
    cancelButtonColor: '#6c757d',
    focusConfirm: false,
    preConfirm: () => {
      const select = document.getElementById('swal-user-select');
      const reason = document.getElementById('swal-leave-reason').value.trim();
      if (!reason) {
        Swal.showValidationMessage('Vui lòng nhập lý do xin vắng!');
        return false;
      }

      let userId = '', userName = '', username = '';
      if (select.value === '__MANUAL__') {
        userId = document.getElementById('swal-manual-id').value.trim();
        userName = document.getElementById('swal-manual-name').value.trim();
        username = document.getElementById('swal-manual-username').value.trim();
        if (!userId || !userName) {
          Swal.showValidationMessage('Vui lòng nhập đủ họ tên và Telegram ID!');
          return false;
        }
      } else if (select.value) {
        const opt = select.selectedOptions[0];
        userId = select.value;
        userName = opt.dataset.name || 'Nhân viên';
        username = opt.dataset.username || '';
      } else {
        Swal.showValidationMessage('Vui lòng chọn nhân viên!');
        return false;
      }

      return { user_id: userId, user_name: userName, username, reason };
    }
  }).then(async (result) => {
    if (result.isConfirmed && result.value) {
      submitCreateLeave(result.value);
    }
  });
}

function toggleSwalManualFields() {
  const select = document.getElementById('swal-user-select');
  const box = document.getElementById('swal-manual-box');
  if (select && box) {
    if (select.value === '__MANUAL__') {
      box.classList.remove('d-none');
    } else {
      box.classList.add('d-none');
    }
  }
}

async function submitCreateLeave(payload) {
  try {
    const res = await fetch('/api/v1/leaves', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.success) {
      showAlert('Tạo yêu cầu xin vắng thành công!');
      loadData();
    } else {
      showAlert(result.message || 'Lỗi tạo yêu cầu!', true);
    }
  } catch (e) {
    showAlert('Lỗi kết nối máy chủ!', true);
  }
}

// 9. Quản lý Chế độ hoạt động (Localhost GetUpdates / NGROK Webhook)
async function checkWebhookStatus(autoPromptIfMissing = false) {
  try {
    const res = await fetch('/api/v1/webhook');
    const json = await res.json();
    webhookStatusData = json.data || json || {};
    
    // Đảm bảo các thuộc tính ở cấp cao nhất cũng được gán vào webhookStatusData
    if (json.mode) webhookStatusData.mode = json.mode;
    if (json.allow_webhook_config !== undefined) webhookStatusData.allow_webhook_config = json.allow_webhook_config;
    if (json.ngrok_url) webhookStatusData.ngrok_url = json.ngrok_url;

    const dot = document.getElementById('webhook-status-dot');
    const text = document.getElementById('webhook-status-text');
    const btn = document.getElementById('btn-webhook') || document.getElementById('btn-webhook-status');

    if (webhookStatusData.mode === 'polling' || webhookStatusData.allow_webhook_config === false) {
      // 1. Chế độ Localhost (GetUpdates)
      if (dot) dot.className = 'badge rounded-circle p-1 bg-info';
      if (text) text.innerHTML = '<i class="fa-solid fa-laptop me-1 text-info"></i>Localhost: GetUpdates';
      if (btn) btn.title = 'Đang chạy Localhost (GetUpdates) - Webhook bị vô hiệu hóa';
    } else {
      // 2. Chế độ NGROK (Webhook)
      if (btn) btn.title = 'Cài đặt Telegram Webhook (Chế độ NGROK)';
      if (webhookStatusData.is_active && webhookStatusData.url) {
        if (dot) dot.className = 'badge rounded-circle p-1 bg-success';
        if (text) text.innerHTML = '<i class="fa-solid fa-bolt me-1 text-success"></i>Webhook: Bật';
      } else {
        if (dot) dot.className = 'badge rounded-circle p-1 bg-warning';
        if (text) text.innerHTML = '<i class="fa-solid fa-bolt me-1 text-warning"></i>Webhook: Tắt';

        if (autoPromptIfMissing) {
          openWebhookModal();
        }
      }
    }
  } catch (err) {
    console.error('Lỗi kiểm tra Webhook/Chế độ:', err);
  }
}

function handleWebhookClick() {
  openWebhookModal();
}

function openWebhookModal() {
  if (!webhookStatusData) {
    checkWebhookStatus(false);
    return;
  }

  // Nếu đang chạy Localhost (GetUpdates) -> Chặn và giải thích rõ
  if (webhookStatusData.mode === 'polling' || webhookStatusData.allow_webhook_config === false) {
    Swal.fire({
      icon: 'info',
      title: 'Chế độ Localhost (GetUpdates)',
      html: `
        <div class="text-start">
          <div class="alert alert-primary py-2 px-3 small mb-3">
            <i class="fa-solid fa-circle-info me-1"></i>
            <strong>Hệ thống đang chạy trên Localhost</strong>
          </div>
          <p class="small text-secondary mb-2">
            Hệ thống đang tự động lắng nghe và nhận sự kiện qua cơ chế <strong>GetUpdates (Long-Polling)</strong> của Telegram.
          </p>
          <div class="alert alert-warning py-2 px-3 small mb-3">
            <i class="fa-solid fa-ban me-1"></i>
            <strong>Không thể cấu hình Webhook:</strong> Ở chế độ Localhost, máy tính không có địa chỉ HTTPS công khai nên Telegram không thể đẩy webhook về. Webhook đã được tự động khóa.
          </div>
          <div class="bg-light p-2 rounded small text-muted border">
            💡 <em>Để sử dụng Webhook, vui lòng tắt ứng dụng và khởi động lại qua file <strong>start.bat</strong> rồi chọn <strong>[2] Mở NGROK</strong>.</em>
          </div>
        </div>
      `,
      confirmButtonText: 'Đã hiểu',
      confirmButtonColor: '#0f172a'
    });
    return;
  }

  const isActive = webhookStatusData && webhookStatusData.is_active && webhookStatusData.url;
  const currentUrl = isActive ? webhookStatusData.url : '';
  const ngrokUrl = webhookStatusData && webhookStatusData.ngrok_url ? webhookStatusData.ngrok_url : '';
  
  let suggestedUrl = '';
  if (ngrokUrl) {
    suggestedUrl = `${ngrokUrl}/webhook`;
  } else {
    let origin = window.location.origin;
    if (origin.startsWith('http://') && !origin.includes('localhost') && !origin.includes('127.0.0.1')) {
      origin = origin.replace('http://', 'https://');
    }
    suggestedUrl = `${origin}/webhook`;
  }

  const inputVal = currentUrl || suggestedUrl;

  Swal.fire({
    title: 'Cấu hình Telegram Webhook',
    html: `
      <div class="text-start">
        <div class="alert ${isActive ? 'alert-success' : 'alert-warning'} py-2 small mb-3">
          ${isActive 
            ? `<strong>Đang kết nối Webhook:</strong><br><code class="text-break">${escapeHtml(currentUrl)}</code>` 
            : '<strong>Chưa kích hoạt Webhook.</strong> Vui lòng điền URL Ngrok HTTPS bên dưới để nhận tin.'}
        </div>
        ${ngrokUrl ? `
          <div class="alert alert-info py-1 px-2 small mb-2">
            <i class="fa-solid fa-satellite-dish me-1"></i> <strong>Đã tìm thấy Ngrok Tunnel:</strong><br>
            <code class="text-break">${escapeHtml(ngrokUrl)}</code>
          </div>
        ` : ''}
        <div class="mb-3">
          <label class="form-label small fw-semibold">Địa chỉ URL Webhook (HTTPS):</label>
          <input id="swal-webhook-url" class="form-control form-control-sm" value="${escapeHtml(inputVal)}" placeholder="https://xxxx.ngrok-free.app/webhook">
          <div class="form-text small text-muted">Telegram yêu cầu giao thức HTTPS công khai.</div>
        </div>
      </div>
    `,
    position: 'center',
    width: '420px',
    showCancelButton: true,
    showDenyButton: isActive,
    confirmButtonText: 'Lưu Webhook',
    denyButtonText: 'Hủy Webhook',
    cancelButtonText: 'Đóng',
    confirmButtonColor: '#0f172a',
    denyButtonColor: '#dc3545',
    cancelButtonColor: '#6c757d',
    preConfirm: () => {
      const url = document.getElementById('swal-webhook-url').value.trim();
      if (!url) {
        Swal.showValidationMessage('Vui lòng nhập URL Webhook!');
        return false;
      }
      if (!url.startsWith('https://')) {
        Swal.showValidationMessage('URL Webhook phải bắt đầu bằng https://');
        return false;
      }
      return url;
    }
  }).then(async (result) => {
    if (result.isConfirmed && result.value) {
      saveWebhook(result.value);
    } else if (result.isDenied) {
      deleteWebhook();
    }
  });
}

async function saveWebhook(url) {
  try {
    const res = await fetch('/api/v1/webhook', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url })
    });
    const result = await res.json();
    if (result.success) {
      showAlert('Đăng ký Webhook thành công!');
      checkWebhookStatus(false);
    } else {
      showAlert(result.message || 'Lỗi đăng ký Webhook', true);
    }
  } catch (e) {
    showAlert('Lỗi kết nối máy chủ!', true);
  }
}

async function deleteWebhook() {
  try {
    const res = await fetch('/api/v1/webhook', { method: 'DELETE' });
    const result = await res.json();
    if (result.success) {
      showAlert('Đã hủy Webhook thành công!');
      checkWebhookStatus(false);
    } else {
      showAlert(result.message || 'Lỗi khi hủy Webhook', true);
    }
  } catch (e) {
    showAlert('Lỗi kết nối máy chủ!', true);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
