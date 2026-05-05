# Dashboard

## Overview

The Sample App dashboard is the main landing page after login. It shows your key
metrics, recent activity, and quick-access widgets for reports and team activity.

## The Dashboard Looks Empty or Blank

If you open Sample App and the dashboard loads but shows nothing — no charts,
no data, no widgets, just an empty page or a white screen — this is almost always
a browser or cache issue, not a data issue.

**Steps to fix an empty or blank dashboard:**

1. Hard-refresh the page: press `Ctrl+Shift+R` on Windows/Linux or `Cmd+Shift+R`
   on Mac. This forces the browser to reload all assets from scratch.
2. Clear your browser cache and cookies, then reload. In Chrome: Settings →
   Privacy and Security → Clear Browsing Data → select Cached images and files.
3. Try an incognito or private browsing window. If the dashboard loads there, the
   issue is with your browser's stored data.
4. Try a different browser entirely (Firefox, Safari, Edge).
5. Check our status page at **status.sampleapp.com**. If there is an active
   incident, the dashboard may be affected service-wide.
6. Disable browser extensions one by one. Ad blockers and script blockers
   sometimes interfere with the dashboard's JavaScript.

If none of the above work, your account may have a data issue. Create a support
ticket and include your account email and the time the problem started.

## Dashboard Won't Load At All

If the page never finishes loading (spinner keeps spinning or you get a timeout):

- Check your internet connection.
- Verify status.sampleapp.com shows all systems operational.
- Try from a different network (e.g. switch from WiFi to mobile data).
- If you are behind a corporate firewall or VPN, ask your IT team whether
  `*.sampleapp.com` is whitelisted.

## Widgets and Charts Not Updating

Dashboard data refreshes every 5 minutes automatically. If your charts look
stale:

- Wait 5 minutes and reload.
- Check the timestamp below each widget — it shows the last data refresh time.
- If a widget shows "No data available", the underlying report may have no results
  for the selected date range. Adjust the date filter in the top-right corner.

## Customising the Dashboard

You can rearrange widgets by dragging and dropping them. To add or remove widgets,
click the **Customise** button in the top-right corner of the dashboard. Changes
are saved automatically per user — each team member can have a different layout.
