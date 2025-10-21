import json
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# The public URL for the events page.
EVENTS_PAGE_URL = "https://www.kaitaksportspark.com.hk/tc/event"
BASE_URL = "https://www.kaitaksportspark.com.hk"

print("Starting browser-based scraping with Playwright...")

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Navigating to {EVENTS_PAGE_URL}...")
        # Increase navigation timeout to 90 seconds for slower networks
        page.goto(EVENTS_PAGE_URL, wait_until="domcontentloaded", timeout=90000)

        # --- NEW: Handle Cookie Consent Banner ---
        # The website may show a cookie pop-up that blocks the content.
        # We look for a button with the text "接受" (Accept) and click it.
        try:
            print("Checking for cookie consent banner...")
            # Wait for the button to appear for up to 5 seconds.
            accept_button = page.locator('button:has-text("接受")')
            accept_button.wait_for(timeout=5000)
            print("Cookie banner found. Clicking 'Accept'...")
            accept_button.click()
        except PlaywrightTimeoutError:
            # If the button doesn't appear after 5 seconds, we assume it's not there.
            print("No cookie banner found, or it was already accepted. Continuing...")
        
        # We now wait for the main content to be surely loaded after handling the pop-up.
        page.wait_for_load_state("networkidle", timeout=60000)

        event_list_selector = "a.w-full"
        print(f"Waiting for event list selector '{event_list_selector}' to appear...")
        # Increase selector timeout to 60 seconds
        page.wait_for_selector(event_list_selector, timeout=60000)
        print("Event list has loaded.")

        event_elements = page.query_selector_all(event_list_selector)
        
        if not event_elements:
            print("No event elements found on the page.")
            browser.close()
            exit()
            
        print(f"Found {len(event_elements)} event elements. Extracting data...")
        
        formatted_events = []
        for element in event_elements:
            try:
                title_element = element.query_selector("h3")
                if not title_element: continue

                title = title_element.inner_text()
                link = element.get_attribute("href")
                
                details = element.query_selector_all("p")
                
                event_date = details[0].inner_text() if len(details) > 0 else "日期未定"
                event_time = details[1].inner_text() if len(details) > 1 else "時間未定"
                venue = details[2].inner_text() if len(details) > 2 else "地點未定"
                category_element = element.query_selector("div[class*='-tag']")
                category = category_element.inner_text() if category_element else "一般活動"
                
                full_link = BASE_URL + link if link and link.startswith('/') else link

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
            with open("total_events.json", "w", encoding="utf-8") as f:
                json.dump(formatted_events, f, ensure_ascii=False, indent=2)
            print(f"Scraping complete. Saved {len(formatted_events)} events to total_events.json")

except Exception as e:
    print(f"An error occurred during the browser automation process: {e}")

