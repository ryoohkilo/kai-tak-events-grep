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

        try:
            print(f"Navigating to {EVENTS_PAGE_URL}...")
            page.goto(EVENTS_PAGE_URL, wait_until="domcontentloaded", timeout=90000)

            # --- Handle Cookie Consent Banner ---
            try:
                print("Checking for cookie consent banner...")
                accept_button = page.locator('button:has-text("接受")')
                accept_button.wait_for(timeout=10000)
                print("Cookie banner found. Clicking 'Accept'...")
                accept_button.click()
            except PlaywrightTimeoutError:
                print("No cookie banner found or it timed out. Continuing...")
            
            # --- NEW: Scroll down to trigger lazy loading ---
            print("Scrolling down the page to load all events...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            # Wait for any network activity to settle after scrolling
            page.wait_for_load_state("networkidle", timeout=30000)

            # A more robust selector targeting the event cards
            event_list_selector = "a[href*='/tc/event/'] h3"
            print(f"Waiting for event list selector '{event_list_selector}' to appear...")
            page.wait_for_selector(event_list_selector, timeout=60000)
            print("Event list has loaded.")

            # Select the parent 'a' tags of the headers we found
            event_elements = page.query_selector_all("a[href*='/tc/event/']:has(h3)")
            
            if not event_elements:
                raise Exception("No event elements found on the page after loading.")
                
            print(f"Found {len(event_elements)} event elements. Extracting data...")
            
            formatted_events = []
            for element in event_elements:
                try:
                    title = element.query_selector("h3").inner_text()
                    link = element.get_attribute("href")
                    details = element.query_selector_all("p")
                    
                    event_date = details[0].inner_text() if len(details) > 0 else "日期未定"
                    venue = details[2].inner_text() if len(details) > 2 else "地點未定"
                    
                    full_link = BASE_URL + link if link and link.startswith('/') else link

                    formatted_event = {
                        "title": title,
                        "link": full_link,
                        "日期": event_date,
                        "地點": venue,
                    }
                    formatted_events.append(formatted_event)

                except Exception as e:
                    print(f"Could not parse an event card. Error: {e}")

            if not formatted_events:
                raise Exception("Could not extract any valid event data.")
            else:
                with open("total_events.json", "w", encoding="utf-8") as f:
                    json.dump(formatted_events, f, ensure_ascii=False, indent=2)
                print(f"Scraping complete. Saved {len(formatted_events)} events to total_events.json")

        except Exception as e:
            # --- NEW: Screenshot on Failure ---
            print(f"An error occurred. Saving a screenshot to debug_screenshot.png")
            page.screenshot(path="debug_screenshot.png", full_page=True)
            # Re-raise the exception to ensure the workflow fails correctly
            raise e

        finally:
            browser.close()

except Exception as e:
    print(f"An error occurred during the browser automation process: {e}")
    # Exit with a non-zero status code to make sure GitHub Actions marks this as a failure.
    exit(1)

