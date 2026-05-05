# Integrations

## Available Integrations

Sample App connects with a growing list of third-party tools:

- **Slack** — send report summaries and alerts to Slack channels.
- **Zapier** — connect Sample App to 5,000+ apps without code.
- **Google Sheets** — sync report data to a live Google Sheet.
- **Webhooks** — send events to any URL in real time.
- **REST API** — build your own integrations using our API.

## Connecting an Integration

1. Go to **Settings → Integrations**.
2. Find the integration you want to connect. Use the search box to filter.
3. Click the integration tile, then click **Connect**.
4. Follow the OAuth prompts to authorise the connection. For Slack, you will be
   redirected to Slack's authorisation page. For Google Sheets, you will be
   asked to grant access to your Google account.
5. Once connected, configure sync settings from the integration detail page.

## Disconnecting an Integration

1. Go to **Settings → Integrations**.
2. Click the connected integration.
3. Click **Disconnect**.
4. Confirm the disconnection.

Disconnecting does not delete any data that was already synced. It only stops
future syncing.

## Slack Integration

Once connected, you can:

- Subscribe Slack channels to receive report summaries on a schedule.
- Set up threshold alerts (e.g. "notify #ops-team when metric X drops below Y").
- Use the `/sampleapp` slash command in Slack to query reports directly.

To configure Slack notifications, go to **Settings → Integrations → Slack →
Manage Notifications**.

## Google Sheets Integration

The Google Sheets integration creates a live sync between a Sample App report
and a Google Sheet. Every time the report is refreshed, the sheet updates
automatically.

1. Connect the integration (see above).
2. Open the report you want to sync.
3. Click **Export → Sync to Google Sheets**.
4. Select or create a Google Sheet.
5. Click **Start Sync**.

## Webhooks

Webhooks let you receive real-time event notifications at any URL you control.

1. Go to **Settings → Integrations → Webhooks**.
2. Click **Add Webhook**.
3. Enter the destination URL.
4. Select the events to subscribe to (e.g. `ticket.created`, `report.exported`).
5. Click **Save**.

Sample App sends a POST request with a JSON payload to your URL for each
subscribed event. Payloads are signed with an HMAC-SHA256 signature using your
webhook secret, which you can find on the webhook detail page.

## API Access

Full API documentation is available at **docs.sampleapp.com/api**. API keys
are managed under **Settings → API Keys**. Each key can be scoped to specific
permissions (read-only, read-write, admin).

Keep API keys secret. If a key is compromised, rotate it immediately from
**Settings → API Keys → Revoke**.
