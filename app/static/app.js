// Vanilla JavaScript for Närvarorapportering
// Handles NFC input, form submissions, and UI interactions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize NFC input handling
    const nfcInputs = document.querySelectorAll('#nfc-input');
    nfcInputs.forEach(input => {
        setupNFCInput(input);
    });
    
    // Initialize form enhancements
    setupFormEnhancements();
    
    // Initialize admin forms
    setupAdminForms();
    
    // Initialize mobile menu
    setupMobileMenu();
});

function setupNFCInput(input) {
    const statusDiv = input.parentNode.querySelector('#nfc-status') || 
                     input.parentNode.querySelector('.nfc-status');
    
    if (!statusDiv) return;
    
    // Focus on NFC input for keyboard wedge readers
    input.focus();
    
    input.addEventListener('input', function() {
        const rawUid = this.value.trim();
        if (rawUid.length > 0) {
            statusDiv.innerHTML = 'Skannar...';
            
            fetch('/auth/nfc-scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'rawUid=' + encodeURIComponent(rawUid)
            })
            .then(response => response.json())
            .then(data => {
                handleNFCResponse(data, statusDiv, rawUid);
            })
            .catch(error => {
                statusDiv.innerHTML = '<span class="error">✗ Nätverksfel</span>';
                input.value = '';
            });
        }
    });
}

function handleNFCResponse(data, statusDiv, rawUid) {
    if (data.result === 'success') {
        statusDiv.innerHTML = '<span class="success">✓ Lyckades!</span>';
        setTimeout(() => {
            if (window.location.pathname === '/') {
                window.location.href = '/home';
            } else {
                window.location.reload();
            }
        }, 1000);
    } else if (data.result === 'ambiguous') {
        statusDiv.innerHTML = '<span class="warning">⚠ Flera aktiva larm. Omdirigerar...</span>';
        setTimeout(() => {
            const url = data.tag_id ? 
                `/nfc/department-selection?tag_id=${data.tag_id}` : 
                '/nfc/department-selection';
            window.location.href = url;
        }, 1000);
    } else {
        statusDiv.innerHTML = '<span class="error">✗ ' + (data.reason || 'Okänt fel') + '</span>';
    }
    
    // Clear input
    const nfcInput = statusDiv.parentNode.querySelector('#nfc-input');
    if (nfcInput) nfcInput.value = '';
}

function setupFormEnhancements() {
    // Only apply auto-submit on login page (not on admin pages)
    if (window.location.pathname === '/' && !window.location.pathname.includes('/admin/')) {
        // Auto-focus password after 4 digits in ID field
        const idInput = document.getElementById('id');
        const passwordInput = document.getElementById('password');
        
        if (idInput && passwordInput) {
            idInput.addEventListener('input', function() {
                if (this.value.length === 4) {
                    passwordInput.focus();
                }
            });
            
            // Auto-submit after password
            passwordInput.addEventListener('input', function() {
                if (this.value.length === 4) {
                    const form = this.closest('form');
                    if (form) form.submit();
                }
            });
        }
    }
}

function setupAdminForms() {
    // Set current time as default for alarm occurred_at
    const occurredAtInput = document.getElementById('occurred_at');
    if (occurredAtInput && !occurredAtInput.value) {
        const now = new Date();
        // Format as YYYY-MM-DDTHH:MM for datetime-local input
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const localDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
        occurredAtInput.value = localDateTime;
    }
}

// Global functions for admin actions
function markAttendance(alarmId, departmentId, button) {
    button.disabled = true;
    button.textContent = 'Markerar...';
    
    fetch(`/attendance/${alarmId}/${departmentId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.textContent = '✓ Närvaro markerad';
            button.className = 'success';
            button.disabled = true;
        } else {
            button.textContent = '✗ Fel';
            button.className = 'error';
            setTimeout(() => {
                button.textContent = 'Markera närvaro';
                button.className = 'attendance-btn';
                button.disabled = false;
            }, 2000);
        }
    })
    .catch(error => {
        button.textContent = '✗ Nätverksfel';
        button.className = 'error';
        setTimeout(() => {
            button.textContent = 'Markera närvaro';
            button.className = 'attendance-btn';
            button.disabled = false;
        }, 2000);
    });
}

function deleteUser(userId) {
    if (confirm('Är du säker på att du vill ta bort användare ' + userId + '?')) {
        submitAdminAction('admin/users', 'delete', {id: userId});
    }
}

function revokeTag(tagId) {
    if (confirm('Är du säker på att du vill återkalla denna tagg?')) {
        submitAdminAction('admin/tags', 'revoke', {tag_id: tagId});
    }
}

function closeAlarm(alarmId) {
    if (confirm('Är du säker på att du vill stänga detta larm?')) {
        submitAdminAction('admin/alarms', 'close', {alarm_id: alarmId});
    }
}

function submitAdminAction(route, action, data) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/${route}`;
    
    const actionInput = document.createElement('input');
    actionInput.type = 'hidden';
    actionInput.name = 'action';
    actionInput.value = action;
    form.appendChild(actionInput);
    
    Object.keys(data).forEach(key => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = data[key];
        form.appendChild(input);
    });
    
    document.body.appendChild(form);
    form.submit();
}

// Mobile menu functionality
function setupMobileMenu() {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    
    console.log('Hamburger found:', !!hamburger);
    console.log('Nav links found:', !!navLinks);
    
    if (hamburger && navLinks) {
        hamburger.addEventListener('click', function() {
            console.log('Hamburger clicked!');
            toggleMobileMenu();
        });
        
        // Close menu when clicking on a link
        const links = navLinks.querySelectorAll('a');
        links.forEach(link => {
            link.addEventListener('click', closeMobileMenu);
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!hamburger.contains(event.target) && !navLinks.contains(event.target)) {
                closeMobileMenu();
            }
        });
    }
}

function toggleMobileMenu() {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    
    console.log('Toggling mobile menu. Current state:', navLinks.classList.contains('active'));
    console.log('Hamburger element:', hamburger);
    console.log('Nav links element:', navLinks);
    
    if (hamburger && navLinks) {
        hamburger.classList.toggle('active');
        navLinks.classList.toggle('active');
        
        console.log('After toggle - active class:', navLinks.classList.contains('active'));
        console.log('Nav links classes:', navLinks.className);
        console.log('Nav links style:', navLinks.style.cssText);
    } else {
        console.log('Missing elements - hamburger:', !!hamburger, 'navLinks:', !!navLinks);
    }
}

function closeMobileMenu() {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    
    if (hamburger && navLinks) {
        hamburger.classList.remove('active');
        navLinks.classList.remove('active');
    }
}
