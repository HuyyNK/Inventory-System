async function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('error-message');

    if (!username || !password) {
        errorMessage.textContent = 'Vui lòng nhập tài khoản và mật khẩu';
        return;
    }

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const result = await response.json();
        if (response.ok) {
            // Giả định chuyển hướng tới dashboard hoặc hiển thị thông báo
            errorMessage.style.color = 'green';
            errorMessage.textContent = 'Đăng nhập thành công!';
            // Ví dụ: window.location.href = '/dashboard';
        } else {
            errorMessage.textContent = result.detail || 'Tài khoản hoặc mật khẩu không đúng';
        }
    } catch (error) {
        errorMessage.textContent = 'Lỗi hệ thống, vui lòng thử lại';
    }
}