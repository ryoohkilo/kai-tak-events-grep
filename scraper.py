import json
from playwright.sync_api import sync_playwright

# The public URL for the events page. This is stable and unlikely to change.
EVENTS_PAGE_URL = "https://www.kaitaksportspark.com.hk/tc/event"
BASE_URL = "https://www.kaitaksportspark.com.hk"

print("Starting browser-based scraping with Playwright...")

try:
    with sync_playwright() as p:
        # Launch a headless Chromium browser.
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Navigating to {EVENTS_PAGE_URL}...")
        page.goto(EVENTS_PAGE_URL, wait_until="networkidle", timeout=60000)

        # This is the crucial step: Wait for the event cards to be rendered by JavaScript.
        # We target a class name that is specific to the event list items.
        event_list_selector = "a.w-full"
        print(f"Waiting for event list selector '{event_list_selector}' to appear...")
        page.wait_for_selector(event_list_selector, timeout=30000)
        print("Event list has loaded.")

        # Find all the event card elements.
        event_elements = page.query_selector_all(event_list_selector)
        
        if not event_elements:
            print("No event elements found on the page.")
            browser.close()
            exit()
            
        print(f"Found {len(event_elements)} event elements. Extracting data...")
        
        formatted_events = []
        for element in event_elements:
            try:
                # Extract data directly from the visible HTML content.
                title = element.query_selector("h3").inner_text()
                link = element.get_attribute("href")
                
                # The details (date, time, venue, category) are in p tags.
                details = element.query_selector_all("p")
                
                event_date = details[0].inner_text() if len(details) > 0 else "日期未定"
                event_time = details[1].inner_text() if len(details) > 1 else "時間未定"
                venue = details[2].inner_text() if len(details) > 2 else "地點未定"
                category = element.query_selector("div[class*='-tag']").inner_text() if element.query_selector("div[class*='-tag']") else "一般活動"
                
                full_link = BASE_URL + link if link.startswith('/') else link

                formatted_event = {
                    "title": title,
                    "link": full_link,
                    "日期": event_date,
                    "時間": event_time,
                    "地點": venue,
                    "類別": category
                }
                formatted_events.append(formatted_event)

            except Exception as e:
                print(f"Could not parse an event card. Error: {e}")

        browser.close()

        if not formatted_events:
            print("Could not extract any valid event data, though elements were found.")
        else:
            # Save the detailed events to total_events.json
            with open("total_events.json", "w", encoding="utf-8") as f:
                json.dump(formatted_events, f, ensure_ascii=False, indent=2)
            print(f"Scraping complete. Saved {len(formatted_events)} events to total_events.json")

except Exception as e:
    print(f"An error occurred during the browser automation process: {e}")

