#!/usr/bin/env python3
"""Einfache Tests für die Flask-App."""

import tempfile
import os
import shutil
from app import app

# Cleanup before tests
if os.path.exists('transfer'):
    shutil.rmtree('transfer')
os.mkdir('transfer')
if os.path.exists('slugs.json'):
    os.remove('slugs.json')

def test_app():
    client = app.test_client()

    # Test 1: GET /api/files (leer)
    response = client.get('/api/files')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 0
    print("✅ Test 1: GET /api/files (leer) passed")

    # Test 2: POST /api/upload (Textdatei)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content")
        temp_file = f.name

    with open(temp_file, 'rb') as f:
        response = client.post('/api/upload', data={'file': f}, content_type='multipart/form-data')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    filename = data['filename']
    print("✅ Test 2: POST /api/upload passed")

    # Test 3: GET /api/files (nach Upload)
    response = client.get('/api/files')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == filename
    print("✅ Test 3: GET /api/files (nach Upload) passed")

    # Test 4: GET /api/storage
    response = client.get('/api/storage')
    assert response.status_code == 200
    data = response.get_json()
    assert 'total' in data
    print("✅ Test 4: GET /api/storage passed")

    # Test 5: GET /download/<filename>
    response = client.get(f'/download/{filename}')
    assert response.status_code == 200
    print("✅ Test 5: GET /download/<filename> passed")

    # Test 6: DELETE /api/files/<filename>
    response = client.delete(f'/api/files/{filename}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    print("✅ Test 6: DELETE /api/files/<filename> passed")

    # Test 7: GET /api/files (nach Löschen)
    response = client.get('/api/files')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 0
    print("✅ Test 7: GET /api/files (nach Löschen) passed")

    # Test 8: POST /api/upload disallowed file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.exe', delete=False) as f:
        f.write("Test exe")
        temp_exe = f.name

    with open(temp_exe, 'rb') as f:
        response = client.post('/api/upload', data={'file': f}, content_type='multipart/form-data')

    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    print("✅ Test 8: POST /api/upload disallowed file passed")

    # Cleanup
    os.unlink(temp_file)
    os.unlink(temp_exe)

    print("Alle Tests bestanden!")

if __name__ == '__main__':
    test_app()