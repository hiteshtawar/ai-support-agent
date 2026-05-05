"""Hardcoded FAQ data for Sample Company's support agent."""

FAQ_ENTRIES: list[dict] = [
    {
        "id": 1,
        "question": "Why won't my dashboard load?",
        "answer": (
            "If your dashboard isn't loading, try these steps: "
            "1) Hard-refresh with Ctrl+Shift+R (Cmd+Shift+R on Mac). "
            "2) Clear your browser cache and cookies. "
            "3) Try a different browser or incognito mode. "
            "4) Check our status page at status.sampleapp.com for any active incidents. "
            "If the issue persists, please create a support ticket."
        ),
        "keywords": [
            "dashboard",
            "load",
            "loading",
            "blank",
            "white screen",
            "not working",
            "broken",
        ],
    },
    {
        "id": 2,
        "question": "How do I export a report?",
        "answer": (
            "To export a report in Sample App: "
            "1) Navigate to the Reports section in the left sidebar. "
            "2) Open the report you want to export. "
            "3) Click the 'Export' button in the top-right corner. "
            "4) Choose your format: CSV, PDF, or Excel. "
            "5) The file will download automatically."
        ),
        "keywords": ["export", "report", "download", "csv", "pdf", "excel", "reports"],
    },
    {
        "id": 3,
        "question": "How do I cancel my plan?",
        "answer": (
            "To cancel your Sample App subscription: "
            "1) Go to Settings → Billing. "
            "2) Click 'Manage Subscription'. "
            "3) Select 'Cancel Plan' and follow the prompts. "
            "Your access continues until the end of the current billing period. "
            "Need help? Our team is happy to discuss alternatives before you go."
        ),
        "keywords": [
            "cancel",
            "cancellation",
            "plan",
            "subscription",
            "unsubscribe",
            "stop",
            "end",
        ],
    },
    {
        "id": 4,
        "question": "How do I reset my password?",
        "answer": (
            "To reset your password: "
            "1) Go to sampleapp.com/login. "
            "2) Click 'Forgot password?' below the login form. "
            "3) Enter your email address. "
            "4) Check your inbox for a reset link (check spam if it doesn't arrive within 2 minutes). "
            "5) Click the link and set a new password."
        ),
        "keywords": [
            "password",
            "reset",
            "forgot",
            "login",
            "sign in",
            "locked out",
            "access",
        ],
    },
    {
        "id": 5,
        "question": "How do I invite a team member?",
        "answer": (
            "To invite someone to your Sample App workspace: "
            "1) Go to Settings → Team. "
            "2) Click 'Invite Member'. "
            "3) Enter their email address and choose their role (Admin, Editor, or Viewer). "
            "4) Click 'Send Invite'. "
            "They'll receive an email with a link to join your workspace."
        ),
        "keywords": [
            "invite",
            "team",
            "member",
            "add user",
            "colleague",
            "share",
            "collaborate",
            "role",
        ],
    },
    {
        "id": 6,
        "question": "Why is my invoice wrong or missing?",
        "answer": (
            "For billing and invoice issues: "
            "1) Go to Settings → Billing → Invoice History to view all past invoices. "
            "2) If an invoice looks incorrect, check that your billing details are up to date under 'Payment Method'. "
            "3) For missing invoices, allow up to 24 hours after a payment for them to appear. "
            "4) If you still have an issue, create a support ticket and include the billing period in question."
        ),
        "keywords": [
            "invoice",
            "billing",
            "charge",
            "payment",
            "receipt",
            "overcharged",
            "bill",
            "cost",
        ],
    },
    {
        "id": 7,
        "question": "How do I upgrade my plan?",
        "answer": (
            "To upgrade your Sample App plan: "
            "1) Go to Settings → Billing. "
            "2) Click 'Change Plan'. "
            "3) Select the plan you want to upgrade to. "
            "4) Confirm your payment details and click 'Upgrade Now'. "
            "The upgrade takes effect immediately and you'll be charged a prorated amount."
        ),
        "keywords": [
            "upgrade",
            "plan",
            "tier",
            "pro",
            "business",
            "enterprise",
            "more features",
            "higher",
        ],
    },
    {
        "id": 8,
        "question": "How do I connect an integration?",
        "answer": (
            "To connect a third-party integration in Sample App: "
            "1) Go to Settings → Integrations. "
            "2) Browse or search for the integration you want (e.g., Slack, Zapier, Google Sheets). "
            "3) Click the integration and then 'Connect'. "
            "4) Follow the OAuth prompts to authorize the connection. "
            "5) Once connected, configure any sync settings from the integration detail page."
        ),
        "keywords": [
            "integration",
            "connect",
            "slack",
            "zapier",
            "google",
            "api",
            "sync",
            "third-party",
            "webhook",
        ],
    },
    {
        "id": 9,
        "question": "Why am I not receiving email notifications?",
        "answer": (
            "If you're missing email notifications from Sample App: "
            "1) Check your spam/junk folder for emails from noreply@sampleapp.com. "
            "2) Add noreply@sampleapp.com to your email whitelist/contacts. "
            "3) Go to Settings → Notifications and verify your preferences are enabled. "
            "4) Confirm your email address is correct under Settings → Profile. "
            "5) If using a company email, check with your IT team about email filtering rules."
        ),
        "keywords": [
            "email",
            "notification",
            "notifications",
            "not receiving",
            "missing",
            "alerts",
            "no email",
        ],
    },
    {
        "id": 10,
        "question": "How do I delete my account?",
        "answer": (
            "To permanently delete your Sample App account: "
            "1) Go to Settings → Profile → Danger Zone. "
            "2) Click 'Delete Account'. "
            "3) You'll be asked to type your email address to confirm. "
            "4) Click 'Permanently Delete'. "
            "Warning: this is irreversible. All your data, reports, and team members will be removed. "
            "Consider exporting your data before proceeding."
        ),
        "keywords": [
            "delete",
            "account",
            "remove",
            "close",
            "deactivate",
            "permanently",
            "data",
        ],
    },
]
