# Final Simple Tiffin Tracker

## Important URLs

Use this URL in app.py:

https://script.google.com/macros/s/AKfycbwNDaOEZFBKknrZc_bzIgulNtZ55LjB9jzeNJ0WuaPusjHyQBZuXYkf7GIEEpoKG4fw/exec

Do NOT use this Apps Script library URL:

https://script.google.com/macros/library/d/1nflGibR8fG07HOC_HUVvyTAqHQd4y4T481CYwvjw9gP71sg8CDW9BU4b/2

## Setup

1. Open the Google Sheet.
2. Extensions -> Apps Script.
3. Replace all Code.gs content with the provided Code.gs.
4. Save.
5. Deploy -> Manage deployments.
6. Edit the Web App deployment.
7. Select "New version".
8. Execute as: Me.
9. Who has access: Anyone.
10. Deploy.

Open the /exec URL in an incognito browser.

It should return JSON with:

- message = Tiffin API is working
- code_version = 2026-09-16-v3
- sheet_name = Monthly Tracker

The Apps Script now automatically creates:
- Monthly Tracker tab if missing
- Date header
- configured user columns
- today's row

So you do not need to manually prepare today's date.

## Run Streamlit

pip install -r requirements.txt
streamlit run app.py

Sample users:
- sahil / 1234
- prateek / 5678
- aparna / 1111
