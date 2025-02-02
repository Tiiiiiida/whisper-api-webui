# Whisper API WebUI

A simple web app for transcribing audio using the OpenAI Whisper API (and compatible services like Groq). The app automatically compresses and splits audio files to fit API size limits. It is secure, user-friendly, and ready for public deployment.

## Features

- Uses OpenAI Whisper API.
- Automatically compresses and splits audio files larger than 25MB to meet API size limits.
- Displays real-time transcription progress in the UI.
- Password-protected panel access, deployable on public networks.

## Deployment

### Docker Deployment

1. **Edit the `docker-compose.yml` file and set the required environment variables:**

   - **`OPENAI_API_KEY`**: Your OpenAI API key.
   - **`API_BASE_URL`**: The base URL for the API (default is `https://api.openai.com`). Compatible services like Groq can also be used.
   - **`SECRET_KEY`**: A random string used to secure the app sessions.
   - **`ACCESS_PASSWORD_HASH`**: The hashed password for login.
2. **Generate the password and its hash:**
   Use `password_gen.py` to generate a hashed password:

   ```bash
   python password_gen.py
   ```

   - Input the desired password when prompted.
   - Copy the resulting hash and paste it into the `ACCESS_PASSWORD_HASH` field in the `docker-compose.yml` file.
3. **Start the app:**

   ```bash
   docker-compose up -d
   ```
4. **Access the app in your browser:**

   ```
   http://localhost:5000
   ```
5. **Log in with the password you set.**

## Notes

- This is a lightweight panel designed for transcription purposes.
- Uploaded files and transcription results are not stored; they are deleted immediately after processing.
- The OpenAI API endpoint and API Key are stored securely on the server and are not visible or editable by users.
- The list of available Whisper models is automatically fetched from the OpenAI API and filtered to show only models containing "whisper".

## Screenshots
