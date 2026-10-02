# -*- coding: utf-8 -*-
"""
اسکریپت دائمی و جامع پاکسازی کلمات انگلیسی داخل پرانتز و گیومه در فایل‌های خلاصه
این اسکریپت با حفظ ۱۰۰٪ فرمول‌های ریاضی KaTeX ($...$ و $$...$$)،
کال‌اوت‌های ابسیدین (> [!callout])، لینک‌ها ([[...]])، کدهای Markdown و جداول،
فقط پرانتزها و گیومه‌هایی که شامل کلمات انگلیسی هستند را پاکسازی می‌کند.
همچنین لاگ دقیق تغییرات را در فایل log_cleaned_english.txt ثبت می‌نماید.
"""

import os
import glob
import re
import sys
import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(SCRIPT_DIR) == "4-خلاصه":
    SUMMARY_DIR = SCRIPT_DIR
else:
    candidate = os.path.join(r"D:\کنکور ارشد مدیریت\4-خلاصه")
    SUMMARY_DIR = candidate if os.path.exists(candidate) else SCRIPT_DIR

LOG_FILE = os.path.join(SUMMARY_DIR, "log_cleaned_english.txt")

def read_file(path):
    for enc in ['utf-8-sig', 'utf-8', 'utf-16', 'utf-16-le', 'cp1256']:
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read(), enc
        except:
            continue
    return None, None

def write_file(path, content, enc):
    target_enc = 'utf-8-sig' if enc in ['utf-8-sig', 'utf-16', 'utf-16-le'] else 'utf-8'
    with open(path, 'w', encoding=target_enc) as f:
        f.write(content)

def clean_content(content):
    log_entries = []
    
    # 1. حفاظت کامل از فرمول‌های ریاضی، کدها، لینک‌ها و کال‌اوت‌ها
    protected_tokens = []
    
    def protect(match):
        idx = len(protected_tokens)
        protected_tokens.append(match.group(0))
        return f"__PROTECTED_TOKEN_{idx}__"

    # فرمول‌های دو دلاری $$...$$
    temp = re.sub(r'\$\$.*?\$\$', protect, content, flags=re.DOTALL)
    # فرمول‌های تک دلاری $...$
    temp = re.sub(r'\$[^\$\n]+?\$', protect, temp)
    # بلوک‌های کد ```...```
    temp = re.sub(r'```.*?```', protect, temp, flags=re.DOTALL)
    # کد اینلاین `...`
    temp = re.sub(r'`[^`\n]+?`', protect, temp)
    # لینک‌های ابسیدین [[...]]
    temp = re.sub(r'\[\[.*?\]\]', protect, temp)
    # تگ‌های کال‌اوت ابسیدین مثل > [!question] یا [!success]
    temp = re.sub(r'\[\![a-zA-Z0-9_\-]+\]', protect, temp)

    # 2. گیومه‌های فارسی حاوی کلمات انگلیسی: «...English...»
    def clean_guillemets(match):
        full = match.group(0)
        inner = match.group(1)
        # اگر داخل گیومه فقط واژگان انگلیسی بود، کل گیومه حذف می‌شود
        if re.match(r'^[a-zA-Z0-9\s\-\,\.\&\/\+\'\"]+$', inner.strip()):
            log_entries.append(f"حذف گیومه انگلیسی کامل: {full}")
            return ""
        # اگر ترکیب فارسی و انگلیسی بود، کلمات انگلیسی حذف می‌شوند
        cleaned_inner = re.sub(r'\b[a-zA-Z]{2,}\b', '', inner)
        cleaned_inner = re.sub(r'\s+', ' ', cleaned_inner).strip()
        log_entries.append(f"حذف واژه انگلیسی از گیومه: {full} -> «{cleaned_inner}»")
        return f"«{cleaned_inner}»"

    temp = re.sub(r'«([^»\n]*[a-zA-Z]{2,}[^»\n]*)»', clean_guillemets, temp)

    # 3. پرانتزهای انگلیسی معادل اصطلاحات:
    # الف) پرانتز انگلیسی خالص مثل: (Political System Metaphor)، (Interests)، (Active Recall)
    def clean_pure_eng_paren(match):
        full = match.group(0)
        inner = match.group(1).strip()
        if not re.search(r'[a-zA-Z]{2,}', inner):
            return full
        log_entries.append(f"حذف پرانتز انگلیسی معادل: {full.strip()}")
        return ""

    temp = re.sub(r'\s*\(\s*([a-zA-Z0-9\s\-\,\.\&\/\+\'\"]{2,})\s*\)', clean_pure_eng_paren, temp)

    # ب) پرانتزهای ترکیبی (متن فارسی + واژه انگلیسی)
    def clean_mixed_paren(match):
        full = match.group(0)
        inner = match.group(1)
        cleaned_inner = re.sub(r'\b[a-zA-Z]{2,}\b', '', inner)
        cleaned_inner = re.sub(r'[\-\:\,\;]\s*$', '', cleaned_inner)
        cleaned_inner = re.sub(r'^\s*[\-\:\,\;]', '', cleaned_inner)
        cleaned_inner = re.sub(r'\s*یا\s*$', '', cleaned_inner)
        cleaned_inner = re.sub(r'^\s*یا\s*', '', cleaned_inner)
        cleaned_inner = re.sub(r'\s+', ' ', cleaned_inner).strip()
        if not cleaned_inner:
            log_entries.append(f"حذف پرانتز ترکیبی (خالی‌شده): {full.strip()}")
            return ""
        log_entries.append(f"پاکسازی بخش انگلیسی از پرانتز: {full.strip()} -> ({cleaned_inner})")
        return f"({cleaned_inner})"

    temp = re.sub(r'\(([^)\n]*[a-zA-Z]{2,}[^)\n]*)\)', clean_mixed_paren, temp)

    # 4. بازگردانی توکن‌های ریاضی و کدهای محافظت‌شده
    for idx, orig in enumerate(protected_tokens):
        temp = temp.replace(f"__PROTECTED_TOKEN_{idx}__", orig)

    # تمیزکاری فاصله‌ها و علائم معلق
    temp = re.sub(r'\s*\(\s*یا\s*\)', '', temp)
    temp = re.sub(r'\s*یا\s*\)', ')', temp)
    temp = re.sub(r'\s+\)', ')', temp)
    temp = re.sub(r'\(\s*\)', '', temp)
    temp = re.sub(r'  +', ' ', temp)
    temp = re.sub(r' +([\:،؛\.])', r'\1', temp)

    return temp, log_entries

def main():
    md_files = glob.glob(os.path.join(SUMMARY_DIR, "**", "*.md"), recursive=True)
    
    total_cleaned = 0
    all_logs = []
    all_logs.append(f"گزارش پاکسازی کلمات انگلیسی - تاریخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    all_logs.append("="*70)

    for file_path in md_files:
        # فایل‌های پوشه لغات زبان را تغییر نمی‌دهیم تا دایره واژگان حفظ شود
        if "Vocabulary" in file_path or ".obsidian" in file_path or "README.md" in file_path:
            continue

        content, enc = read_file(file_path)
        if not content:
            continue

        new_content, logs = clean_content(content)
        if logs:
            total_cleaned += len(logs)
            rel_name = os.path.relpath(file_path, SUMMARY_DIR)
            all_logs.append(f"\n📁 فایل: {rel_name} ({len(logs)} مورد اصلاح شد)")
            for entry in logs:
                all_logs.append(f"  • {entry}")
            
            write_file(file_path, new_content, enc)

    all_logs.append("\n" + "="*70)
    all_logs.append(f"مجموع کل موارد پاکسازی‌شده در این اجرا: {total_cleaned} مورد")

    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(all_logs))

    print(f"SUCCESS: {total_cleaned} items cleaned.")
    print(f"Log saved to: {LOG_FILE}")

if __name__ == "__main__":
    main()
