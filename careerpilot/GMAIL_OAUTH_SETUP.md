# Gmail OAuth2 Setup Guide

To enable email sending via Gmail OAuth2, follow these steps:

## 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
3. Name it "CareerPilot" or similar

## 2. Enable Gmail API

1. Go to **Library** in the sidebar
2. Search for "Gmail API"
3. Click **Enable**

## 3. Create OAuth Credentials

1. Go to **Credentials** in the sidebar
2. Click **Create Credentials** > **OAuth client ID**
3. Application type: **Desktop app** (or **Other** on older console)
4. Name it "CareerPilot Gmail"
5. Click **Create**
6. Download the JSON file

## 4. Setup the credentials file

1. Rename the downloaded JSON file to: `client_secret.json`
2. Place it in the `careerpilot` directory (same level as `.env` and `requirements.txt`)

## 5. Authorize the app

1. Start the CareerPilot server
2. Go to `http://localhost:8000/gmail/status` to check status
3. Click **Authorize** or go to `http://localhost:8000/gmail/authorize`
4. Sign in with your Google account
5. Grant permission to send emails
6. You'll be redirected back and credentials will be stored

## Files needed

```
careerpilot/
├── client_secret.json   # Downloaded from Google Cloud Console
├── .env                  # Already configured
├── requirements.txt      # Already updated
└── backend/
    └── main.py           # Already updated with Gmail OAuth
```

## Testing

After authorization, test by calling `/send-email` endpoint:

```bash
curl -X POST http://localhost:8000/send-email \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "subject": "Test", "body": "Hello!"}'
```

## Troubleshooting

- **"client_secret.json not found"**: Make sure the file is in the careerpilot directory
- **Token expired**: The credentials auto-refresh. If they fail, re-authorize via `/gmail/authorize`
- **Scopes error**: Ensure Gmail API is enabled and you downloaded the correct JSON