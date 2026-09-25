const { Plugin } = require('obsidian');

module.exports = class EditorZoomPlugin extends Plugin {
  async onload() {
    this.settings = Object.assign({ fontSize: 16 }, await this.loadData());
    
    // ایجاد تگ استایل اختصاصی برای تضمین تغییر فونت متن یادداشت‌ها
    this.styleEl = document.createElement('style');
    this.styleEl.id = 'editor-text-zoom-style';
    document.head.appendChild(this.styleEl);
    this.applyFontSize(this.settings.fontSize);

    // ۱. کنترل مستقیم کلیدهای Ctrl + و Ctrl - برای زوم فقط متن (بدون بزرگ شدن کل برنامه)
    this.registerDomEvent(window, 'keydown', (evt) => {
      if (evt.ctrlKey && !evt.altKey) {
        // کلیدهای مثبت و مساوی (Ctrl + / Ctrl =)
        if (evt.key === '=' || evt.key === '+' || evt.code === 'Equal' || evt.code === 'NumpadAdd') {
          evt.preventDefault();
          evt.stopPropagation();
          this.settings.fontSize = Math.min(this.settings.fontSize + 1, 45);
          this.applyFontSize(this.settings.fontSize);
          this.saveData(this.settings);
          return;
        }
        // کلید منفی (Ctrl -)
        if (evt.key === '-' || evt.code === 'Minus' || evt.code === 'NumpadSubtract') {
          evt.preventDefault();
          evt.stopPropagation();
          this.settings.fontSize = Math.max(this.settings.fontSize - 1, 10);
          this.applyFontSize(this.settings.fontSize);
          this.saveData(this.settings);
          return;
        }
        // کلید صفر (Ctrl 0 برای ریست)
        if (evt.key === '0' || evt.code === 'Digit0' || evt.code === 'Numpad0') {
          evt.preventDefault();
          evt.stopPropagation();
          this.settings.fontSize = 16;
          this.applyFontSize(16);
          this.saveData(this.settings);
          return;
        }
      }
    }, { capture: true, passive: false });

    // ۲. کنترل اسکرول تاچ‌پد / چرخ ماوس با کلید Ctrl
    this.registerDomEvent(window, 'wheel', (evt) => {
      if (!evt.ctrlKey) return;

      let el = evt.target;
      if (el && el.nodeType === 3) el = el.parentElement;
      if (!el || typeof el.closest !== 'function') return;

      // اگر روی منوها و سایدبار بود کاری نکن
      if (el.closest('.workspace-ribbon, .workspace-sidedock, .status-bar, .titlebar, .workspace-tab-header-container, .modal')) {
        return;
      }

      evt.preventDefault();
      evt.stopPropagation();

      // زوم عکس در صورتی که نشانگر روی عکس باشد
      const img = el.tagName === 'IMG' ? el : (el.closest('.image-embed, .cm-embed-block')?.querySelector('img') || el.querySelector('img'));
      if (img && (el.tagName === 'IMG' || el.closest('.image-embed'))) {
        const targetImg = el.tagName === 'IMG' ? el : img;
        let w = targetImg.getBoundingClientRect().width || 300;
        const delta = evt.deltaY < 0 ? 35 : -35;
        const newW = Math.max(80, Math.min(w + delta, 2200));
        targetImg.style.width = newW + 'px';
        targetImg.style.maxWidth = 'none';
        return;
      }

      // در غیر این صورت زوم متن
      if (evt.deltaY < 0) {
        this.settings.fontSize = Math.min(this.settings.fontSize + 1, 45);
      } else if (evt.deltaY > 0) {
        this.settings.fontSize = Math.max(this.settings.fontSize - 1, 10);
      }

      this.applyFontSize(this.settings.fontSize);
      this.saveData(this.settings);
    }, { capture: true, passive: false });

    // ۳. دستورات در پالت دستورات ابسیدین
    this.addCommand({
      id: 'increase-text-font-size',
      name: 'Increase text font size (بزرگ‌تر کردن فونت متن)',
      callback: () => {
        this.settings.fontSize = Math.min(this.settings.fontSize + 1, 45);
        this.applyFontSize(this.settings.fontSize);
        this.saveData(this.settings);
      }
    });

    this.addCommand({
      id: 'decrease-text-font-size',
      name: 'Decrease text font size (کوچک‌تر کردن فونت متن)',
      callback: () => {
        this.settings.fontSize = Math.max(this.settings.fontSize - 1, 10);
        this.applyFontSize(this.settings.fontSize);
        this.saveData(this.settings);
      }
    });

    this.addCommand({
      id: 'reset-text-font-size',
      name: 'Reset text font size (اندازه پیش‌فرض متن)',
      callback: () => {
        this.settings.fontSize = 16;
        this.applyFontSize(16);
        this.saveData(this.settings);
      }
    });
  }

  applyFontSize(size) {
    try {
      if (this.app && this.app.vault && this.app.vault.setConfig) {
        this.app.vault.setConfig('baseFontSize', size);
      }
    } catch (e) {}
    document.documentElement.style.setProperty('--font-text-size', size + 'px');
    if (this.styleEl) {
      this.styleEl.textContent = `
        .markdown-source-view,
        .markdown-rendered,
        .cm-content,
        .view-content,
        .markdown-preview-view {
          font-size: ${size}px !important;
        }
      `;
    }
  }

  onunload() {
    if (this.styleEl) this.styleEl.remove();
    document.documentElement.style.removeProperty('--font-text-size');
  }
};
