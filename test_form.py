from flask import Flask, render_template, request, redirect, url_for, flash
from app import app
from flask_login import current_user

# Test form route
@app.route('/test-form')
def test_form():
    """Simple test form for debugging form submission issues"""
    return render_template('test_form.html', user=current_user)