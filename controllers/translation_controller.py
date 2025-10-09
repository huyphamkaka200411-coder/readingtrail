"""
Translation Controller
Handles translation management and language switching.
"""
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
import json
import os
from functools import lru_cache

TRANSLATIONS_FILE = 'data/translations.json'

@lru_cache(maxsize=1)
def _cached_load_translations():
    """Load translations from JSON file with caching"""
    if os.path.exists(TRANSLATIONS_FILE):
        with open(TRANSLATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_translations():
    """Load translations from JSON file"""
    return _cached_load_translations()

def save_translations(translations):
    """Save translations to JSON file and clear cache"""
    with open(TRANSLATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)
    
    _cached_load_translations.cache_clear()

def get_translation(key, lang=None):
    """Get translation for a key in specified language"""
    if lang is None:
        lang = session.get('language', 'vi')
    
    translations = load_translations()
    
    if key in translations and lang in translations[key]:
        return translations[key][lang]
    
    return key

@login_required
def translate_admin():
    """Translation management admin page - requires admin authorization"""
    if not current_user.is_admin:
        flash('You do not have permission to access translation management. Admin access required.', 'danger')
        return redirect(url_for('index'))
    
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

@login_required
def delete_translation():
    """Delete a translation key - requires admin authorization"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin authorization required'}), 403
    
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
