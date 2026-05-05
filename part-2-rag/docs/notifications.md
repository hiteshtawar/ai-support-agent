# Notifications

## Types of Notifications

Sample App sends notifications through two channels:

- **Email** — for important account events, scheduled reports, and ticket updates.
- **In-app** — for real-time activity within your workspace, shown in the bell
  icon in the top navigation bar.

## Configuring Notification Preferences

1. Go to **Settings → Notifications**.
2. Toggle each notification type on or off:
   - **Report ready** — when a scheduled or background export finishes.
   - **Ticket updates** — when a support ticket you created is updated.
   - **Team activity** — when a team member joins, leaves, or changes role.
   - **Billing alerts** — payment confirmations, upcoming renewal reminders, failed payments.
   - **Threshold alerts** — when a metric crosses a value you have configured.
3. Changes save automatically.

## Not Receiving Email Notifications

If you are not getting emails from Sample App:

1. **Check spam and junk folders.** Emails come from `noreply@sampleapp.com`.
   Mark them as "Not spam" to train your email client.
2. **Add `noreply@sampleapp.com` to your contacts or whitelist.** This tells
   your email provider to always deliver messages from this address.
3. **Verify your email address is correct** under Settings → Profile. If it is
   wrong, update it and re-confirm.
4. **Check your notification preferences** under Settings → Notifications. The
   specific notification type may be turned off.
5. **Corporate email filtering.** If you use a company email address, your IT
   team may have filtering rules that block external senders. Ask them to whitelist
   `sampleapp.com` and `noreply@sampleapp.com`.
6. **Check if your inbox is full.** A full inbox silently rejects incoming mail
   on some providers.

If you have gone through all the above and emails are still not arriving, create
a support ticket. Include your email address and the type of notification you
expect to receive.

## Threshold Alerts

Threshold alerts notify you when a metric in your reports crosses a value you set.

1. Open a report.
2. Click **Alerts** in the report toolbar.
3. Click **Add Alert**.
4. Set the metric, condition (above/below), and threshold value.
5. Choose the notification channel: email, Slack (if connected), or both.
6. Click **Save Alert**.

Alerts are evaluated every time the report data refreshes (every 5 minutes).

## Unsubscribing from All Emails

Every email from Sample App includes an **Unsubscribe** link in the footer. Clicking
it disables all marketing and non-critical email notifications. Billing and
security emails (password resets, payment failures) are always sent regardless
of unsubscribe status because they are critical account communications.

To re-enable notifications after unsubscribing, go to **Settings → Notifications**
and toggle them back on.
