# Web File Manager

A lightweight, web-based file manager built with Flask. This application allows users to upload, download, and manage files through a simple and intuitive web interface. It is designed for local network use and can be easily extended for more advanced use cases.

---

## Features

- **File Uploads**: Upload files to the server with a size limit of 16MB.
- **File Downloads**: Securely download files from the server.
- **Error Handling**: Custom 404 error page for missing files.
- **Lightweight**: Minimal dependencies for easy setup and deployment.
- **Dynamic File Listing**: Automatically lists all uploaded files on the home page.

---

## Screenshots

### Home Page
Displays a list of uploaded files with download links.

![Home Page Screenshot](screenshot1.pg)

### Upload Page
Allows users to upload files to the server.

![Upload Page Screenshot](screenshot2.png)

---

## Installation

### Prerequisites
- Python 3.7 or higher
- `pip` (Python package manager)

### Steps
1. Clone the repository:
   ```bash
   git https://github.com/hiddent3erminal/Web-File-Manager.git
   cd Web-File-Manager

## INstalation Dependencies:
    pip install -r requirements.txt

##  How to run
    python3 app.py
    then open your browser and go to 'http://127.0.0.1:5000'

### Usage:
#    Uploading Files
        Navigate to the "Upload" page.
        Select a file using the file input field.
        Click the "Upload File" button to upload the file to the server.
#    Downloading Files
        On the home page, click on the file name to download it.
        Project Structure

### project structure 
    Web-File-Manager/
├── [app.py](http://_vscodecontentref_/1)                 # Main Flask application
├── [requirements.txt](http://_vscodecontentref_/2)       # Python dependencies
├── templates/             # HTML templates
│   ├── base.html          # Base layout for all pages
│   ├── index.html         # Home page template
│   ├── upload.html        # Upload page template
│   └── 404.html           # Custom 404 error page
├── uploads/               # Directory for uploaded files (created at runtime)
├── [README.md](http://_vscodecontentref_/3)              # Project documentation
└── LICENSE                # License file

### Limitations
    The application is designed for local use and is not production-ready.
    File size is limited to 16MB by default (can be configured in app.py).

# Future Improvements
    Add user authentication for secure file access.
    Implement file deletion functionality.
    Enhance the UI with a modern CSS framework (e.g., Bootstrap or Tailwind CSS).
    Add support for file previews (e.g., images, PDFs).
    Add logging for better monitoring and debugging.

# License
    This project is licensed under the MIT License.

# Contributing
    Contributions are welcome! Please follow these steps:
    Fork the repository.
    Create a new branch for your feature or bug fix.
    Commit your changes and push them to your fork.
    Submit a pull request.
