"""
Translation Controller
Handles translation management and language switching.
"""
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required
import json
import os

TRANSLATIONS_FILE = 'data/translations.json'

def load_translations():
    """Load translations from JSON file"""
    if os.path.exists(TRANSLATIONS_FILE):
        with open(TRANSLATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_translations(translations):
    """Save translations to JSON file"""
    with open(TRANSLATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)

def get_translation(key, lang=None):
    """Get translation for a key in specified language"""
    if lang is None:
        lang = session.get('language', 'vi')
    
    translations = load_translations()
    
    if key in translations and lang in translations[key]:
        return translations[key][lang]
    
    return key

def translate_admin():
    """Translation management admin page"""
    translations = load_translations()
    
    if request.method == 'POST':
        key = request.form.get('key', '').strip()
        vi_text = request.form.get('vi_text', '').strip()
        en_text = request.form.get('en_text', '').strip()
        
        if not key:
            flash('Translation key is required', 'danger')
            return redirect(url_for('translate_admin'))
        
        if not vi_text or not en_text:
            flash('Both Vietnamese and English translations are required', 'danger')
            return redirect(url_for('translate_admin'))
        
        translations[key] = {
            'vi': vi_text,
            'en': en_text
        }
        
        save_translations(translations)
        flash(f'Translation "{key}" saved successfully!', 'success')
        return redirect(url_for('translate_admin'))
    
    return render_template('translate_admin.html', translations=translations)

def delete_translation():
    """Delete a translation key"""
    key = request.form.get('key')
    
    if not key:
        return jsonify({'success': False, 'message': 'Key is required'}), 400
    
    translations = load_translations()
    
    if key in translations:
        del translations[key]
        save_translations(translations)
        return jsonify({'success': True, 'message': f'Translation "{key}" deleted'})
    
    return jsonify({'success': False, 'message': 'Translation not found'}), 404

def toggle_language():
    """Toggle between Vietnamese and English"""
    current_lang = session.get('language', 'vi')
    new_lang = 'en' if current_lang == 'vi' else 'vi'
    session['language'] = new_lang
    
    return redirect(request.referrer or url_for('index'))

def set_language(lang):
    """Set language to specific value"""
    if lang in ['vi', 'en']:
        session['language'] = lang
    
    return redirect(request.referrer or url_for('index'))
