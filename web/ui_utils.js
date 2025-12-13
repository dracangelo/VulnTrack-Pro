/**
 * UI Utilities using SweetAlert2
 * Wraps common UI patterns like toasts, alerts, confirms, and loading states.
 */

const UI = {
    // Toast Notification
    toast: (message, type = 'success') => {
        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer)
                toast.addEventListener('mouseleave', Swal.resumeTimer)
            }
        });

        Toast.fire({
            icon: type,
            title: message
        });
    },

    // Standard Alert
    alert: (title, message, type = 'info') => {
        return Swal.fire({
            title: title,
            text: message,
            icon: type,
            confirmButtonColor: 'var(--accent-cyan)',
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)'
        });
    },

    // Confirmation Dialog
    confirm: async (message, title = 'Are you sure?', confirmText = 'Yes', cancelText = 'Cancel', type = 'warning') => {
        const result = await Swal.fire({
            title: title,
            text: message,
            icon: type,
            showCancelButton: true,
            confirmButtonColor: type === 'warning' ? 'var(--error-red)' : 'var(--accent-cyan)',
            cancelButtonColor: 'var(--text-secondary)',
            confirmButtonText: confirmText,
            cancelButtonText: cancelText,
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)'
        });
        return result.isConfirmed;
    },

    // Input Prompt
    prompt: async (title, inputType = 'text', placeholder = '') => {
        const { value: result } = await Swal.fire({
            title: title,
            input: inputType,
            inputPlaceholder: placeholder,
            showCancelButton: true,
            confirmButtonColor: 'var(--accent-cyan)',
            cancelButtonColor: 'var(--text-secondary)',
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)'
        });
        return result;
    },

    // Loading Overlay
    showLoading: (title = 'Loading...') => {
        Swal.fire({
            title: title,
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            },
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)'
        });
    },

    // Hide Loading
    hideLoading: () => {
        Swal.close();
    },

    // Helper for async operations with loading state
    asyncOperation: async (operation, loadingMessage = 'Processing...') => {
        UI.showLoading(loadingMessage);
        try {
            const result = await operation();
            UI.hideLoading();
            return result;
        } catch (error) {
            UI.hideLoading();
            UI.toast(error.message || 'Operation failed', 'error');
            throw error;
        }
    }
};
