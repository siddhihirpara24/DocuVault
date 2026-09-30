/**
 * Personal Document Organizer - Main Client JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Bootstrap Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. Responsive Sidebar Toggle for Mobile Devices
    const sidebarToggleBtn = document.getElementById('sidebarToggle');
    const appSidebar = document.querySelector('.app-sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    if (sidebarToggleBtn && appSidebar) {
        sidebarToggleBtn.addEventListener('click', function () {
            appSidebar.classList.toggle('show');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('show');
            }
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function () {
            appSidebar.classList.remove('show');
            sidebarOverlay.classList.remove('show');
        });
    }

    // 3. Dynamic Delete Confirmation Modal Handler
    const deleteModal = document.getElementById('deleteConfirmModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const actionUrl = button.getAttribute('data-action-url');
            const itemName = button.getAttribute('data-item-name') || 'this item';
            const itemType = button.getAttribute('data-item-type') || 'document';

            const deleteForm = deleteModal.querySelector('#deleteConfirmForm');
            const targetNameSpan = deleteModal.querySelector('#deleteTargetName');
            const targetTypeSpan = deleteModal.querySelector('#deleteTargetType');

            if (deleteForm) {
                deleteForm.action = actionUrl;
            }
            if (targetNameSpan) {
                targetNameSpan.textContent = `"${itemName}"`;
            }
            if (targetTypeSpan) {
                targetTypeSpan.textContent = itemType;
            }
        });
    }

    // 4. File Upload Validation (Size & Extension)
    const fileInput = document.getElementById('document_file');
    const fileFeedback = document.getElementById('file_feedback');
    const maxSizeBytes = 10 * 1024 * 1024; // 10 MB
    const allowedExtensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'];

    if (fileInput) {
        fileInput.addEventListener('change', function () {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const fileName = file.name;
                const fileSize = file.size;
                const fileExt = fileName.split('.').pop().toLowerCase();

                let errorMsg = null;

                if (!allowedExtensions.includes(fileExt)) {
                    errorMsg = `File type ".${fileExt}" is not allowed. Please choose PDF, JPG, JPEG, PNG, DOC, or DOCX.`;
                } else if (fileSize > maxSizeBytes) {
                    const sizeMB = (fileSize / (1024 * 1024)).toFixed(2);
                    errorMsg = `File size (${sizeMB} MB) exceeds maximum limit of 10 MB.`;
                }

                if (errorMsg) {
                    this.classList.add('is-invalid');
                    this.classList.remove('is-valid');
                    if (fileFeedback) {
                        fileFeedback.textContent = errorMsg;
                        fileFeedback.className = 'invalid-feedback d-block';
                    }
                    this.value = ''; // Reset input
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                    if (fileFeedback) {
                        const sizeKB = (fileSize / 1024).toFixed(1);
                        fileFeedback.textContent = `Selected: ${fileName} (${sizeKB} KB) - Valid file`;
                        fileFeedback.className = 'valid-feedback d-block';
                    }
                }
            }
        });
    }

    // 5. Password Show/Hide Toggle
    const togglePasswordBtns = document.querySelectorAll('.toggle-password');
    togglePasswordBtns.forEach(function (btn) {
        btn.addEventListener('click', function () {
            const targetId = this.getAttribute('data-target');
            const targetInput = document.getElementById(targetId);
            const icon = this.querySelector('i');

            if (targetInput) {
                if (targetInput.type === 'password') {
                    targetInput.type = 'text';
                    if (icon) {
                        icon.classList.remove('bi-eye');
                        icon.classList.add('bi-eye-slash');
                    }
                } else {
                    targetInput.type = 'password';
                    if (icon) {
                        icon.classList.remove('bi-eye-slash');
                        icon.classList.add('bi-eye');
                    }
                }
            }
        });
    });

    // 6. Auto-dismiss Flash Alerts after 5 seconds (optional smooth fade)
    setTimeout(function () {
        const autoDismissAlerts = document.querySelectorAll('.alert-dismissible');
        autoDismissAlerts.forEach(function (alertEl) {
            const bsAlert = new bootstrap.Alert(alertEl);
            bsAlert.close();
        });
    }, 6000);
});
