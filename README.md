# KornerCloud
 
A self-hosted personal cloud server with secure login, two-factor authentication, and separate spaces for files and media — built with Django, containerized with Docker, and themed like a quiet night sky.
 
![KornerCloud Login](docs/screenshots/login.png)
 
## Features
 
- **Single secure account** — one user (`YouKnow`), forced to change the default password on first login
  
- **Two-factor authentication** — TOTP via Google Authenticator, with a one-time QR code setup on first use

- **Brute-force protection** — failed login attempts lock out by IP address (`django-axes`)

- **Files and Media, kept separate** — the Files page accepts anything except media types (zip, pdf, docs, executables, etc.); the Media page accepts only images, video, and audio

- **Built for large files**

- **Bulk actions** — multi-select download (bundled as a ZIP) and delete, using a deliberate two-click confirm pattern

- **Media lightbox** — full-size preview with swipe gestures and keyboard navigation

- **Responsive design** — works on desktop and mobile, down to small phone screens

- **One-command setup** — `docker compose up --build` and you're running
## Screenshots
 
| Login | 2FA Setup |
|---|---|
| ![Login](docs/screenshots/login.png) | ![2FA Setup](docs/screenshots/2fa-setup.png) |
 
| Cloud Home | Files |
|---|---|
| ![Cloud Home](docs/screenshots/cloud-home.png) | ![Files](docs/screenshots/files-page.png) |
 
| Media Grid | Media Lightbox |
|---|---|
| ![Media Grid](docs/screenshots/media-grid.png) | ![Media Lightbox](docs/screenshots/media-lightbox.png) |
 
## Getting Started
 
### Prerequisites
 
- **Docker** — Docker Desktop on Windows/Mac, or Docker Engine + Compose v2 on Linux
- **Git** — to clone the repository

That's it. Python is optional to install on your machine, because everything runs inside containers.
### 1. Clone the repository
 
```bash
git clone https://github.com/yourusername/KornerCloud.git
cd KornerCloud
```
 
### 2. Configure your environment
 
Copy (rename) the example environment file:
 
```bash
cp core/env_example core/.env
```
 
Open `core/.env` and generate a `SECRET_KEY`. Run this in your terminal:
 
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
 
If you don't have Python installed, use Docker instead (Windows users: run this in **cmd**, not PowerShell):
 
```bash
docker run --rm python:3.14-slim python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
 
Paste the printed value into `core/.env`, as a `SECRET_KEY`:
 
```dotenv
DEBUG=False
SECRET_KEY=paste-your-generated-key-here
``` 
 ### 3. Build and run
 
From the repository root (where `docker-compose.yml` lives):
 
```bash
docker compose up --build
```
 
The first run will build the image, apply database migrations (including creating the default `YouKnow` account), and start the app. You'll see a number of Gunicorn workers boot up — that's normal.
 
Once it's running, open your browser to:
 
```
http://<your-machine-ip>:1212
```
 
On the same machine, `http://localhost:1212` also works.
 
### 4. First login
 
KornerCloud ships with one pre-created account:
 
- **Username:** `YouKnow`
- **Password:** `YouKnow12?`
Logging in with the default password triggers a forced password change — you'll be redirected to set a new one immediately. After that, log in again with your new password.
 
Next comes two-factor setup: a QR code appears **once**. Scan it with Google Authenticator (or any TOTP app), then enter the 6-digit code to complete login. From then on, only the 6-digit code is needed — the QR code won't appear again.
