import os
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = 'test_uploads'
    with app.test_client() as client:
        with app.app_context():
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
        yield client
    # Cleanup
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
        os.rmdir(app.config['UPLOAD_FOLDER'])

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_file_upload(client):
    data = {
        'file': (io.BytesIO(b"test file content"), 'test.txt')
    }
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 302  # Redirect after upload
    assert os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'test.txt'))

def test_file_download(client):
    test_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test.txt')
    with open(test_file_path, 'w') as f:
        f.write('test file content')
    response = client.get('/uploads/test.txt')
    assert response.status_code == 200
    assert response.data == b'test file content'