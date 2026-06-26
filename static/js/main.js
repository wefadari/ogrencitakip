/**
 * main.js - EduTrack Ana JavaScript Dosyası
 * Sidebar, animasyonlar ve genel etkileşimler
 */

document.addEventListener('DOMContentLoaded', () => {

    // ===== SIDEBAR YÖNETİMİ =====
    const sidebar = document.getElementById('sidebar');
    const menuBtn = document.getElementById('menuBtn');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const overlay = document.getElementById('sidebarOverlay');

    function openSidebar() {
        sidebar?.classList.add('open');
        overlay?.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar?.classList.remove('open');
        overlay?.classList.remove('active');
        document.body.style.overflow = '';
    }

    menuBtn?.addEventListener('click', openSidebar);
    sidebarToggle?.addEventListener('click', closeSidebar);
    overlay?.addEventListener('click', closeSidebar);

    // ===== FLASH MESAJLARI OTOMATİK KAPAMA =====
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-10px)';
            flash.style.transition = 'all 0.3s ease';
            setTimeout(() => flash.remove(), 300);
        }, 4000);
    });

    // ===== KART ANİMASYONLARI =====
    const animatedElements = document.querySelectorAll(
        '.stat-card, .student-card, .dstat-card, .letter-card, .quick-action-card, .record-card'
    );

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, i) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }, i * 50);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        animatedElements.forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(15px)';
            el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            observer.observe(el);
        });
    }

    // ===== FORM SUBMIT LOADING =====
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('[type="submit"]');
            if (submitBtn && !submitBtn.dataset.noLoader) {
                const original = submitBtn.innerHTML;
                submitBtn.innerHTML = '⏳ Yükleniyor...';
                submitBtn.disabled = true;

                // 10 saniye sonra geri al (hata durumunda)
                setTimeout(() => {
                    submitBtn.innerHTML = original;
                    submitBtn.disabled = false;
                }, 10000);
            }
        });
    });

    // ===== TOOLTIP =====
    document.querySelectorAll('[title]').forEach(el => {
        el.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'custom-tooltip';
            tooltip.textContent = this.title;
            tooltip.style.cssText = `
                position: fixed;
                background: #1a1b2e;
                color: #e8eaf6;
                padding: 4px 10px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                pointer-events: none;
                z-index: 9999;
                border: 1px solid #2a2b45;
                box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            `;
            document.body.appendChild(tooltip);

            const rect = this.getBoundingClientRect();
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 8) + 'px';
            tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';

            this._tooltip = tooltip;
        });

        el.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                this._tooltip = null;
            }
        });
    });

    // ===== SAYAÇ ANİMASYONU =====
    function animateCount(element, target, duration = 1000) {
        const start = 0;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            element.textContent = Math.round(start + (target - start) * eased);

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }

    // Stat sayılarını anime et
    document.querySelectorAll('.stat-number, .dstat-value').forEach(el => {
        const value = parseInt(el.textContent);
        if (!isNaN(value) && value > 0) {
            el.textContent = '0';
            setTimeout(() => animateCount(el, value, 800), 300);
        }
    });

    // ===== HARF KARTLARI EFEKT =====
    document.querySelectorAll('.letter-card').forEach(card => {
        card.addEventListener('click', function() {
            // Ripple efekti
            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                background: rgba(255,255,255,0.3);
                transform: scale(0);
                animation: ripple 0.4s ease-out;
                pointer-events: none;
                left: 50%;
                top: 50%;
                margin-left: -20px;
                margin-top: -20px;
            `;
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 400);
        });
    });

    // Ripple keyframe
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            from { transform: scale(0); opacity: 1; }
            to { transform: scale(3); opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    // ===== WPM GİRİŞİ RENK GÜNCELLEMESİ =====
    const wpmInput = document.getElementById('words_per_minute');
    if (wpmInput) {
        wpmInput.addEventListener('input', function() {
            const val = parseInt(this.value);
            if (val >= 45) this.style.color = '#339AF0';
            else if (val >= 30) this.style.color = '#51CF66';
            else if (val >= 20) this.style.color = '#FFD43B';
            else if (val >= 10) this.style.color = '#FFA94D';
            else this.style.color = '#FF6B6B';
        });
    }

    console.log('📚 EduTrack yüklendi!');
});
