from datetime import timedelta

OTP_LIFETIME = timedelta(minutes=5)
MAX_OTP_ATTEMPTS = 5
SESSION_LIFETIME = timedelta(days=7)
SESSION_COOKIE = "wolsar_session"
CSRF_COOKIE = "wolsar_csrf"
