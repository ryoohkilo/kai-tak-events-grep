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
            
            # Wait for the network to be idle to ensure all content is loaded
            page.wait_for_load_state("networkidle", timeout=30000)

            # A more robust selector targeting the event cards
            event_list_selector = "a[href*='/tc/event/']"
            print(f"Waiting for event list selector '{event_list_selector}' to appear...")
            page.wait_for_selector(event_list_selector, timeout=60000)
            print("Event list has loaded.")

            event_elements = page.query_selector_all(event_list_selector)
            
            if not event_elements:
                raise Exception("No event elements found on the page after loading.")
                
            print(f"Found {len(event_elements)} potential event links. Filtering and extracting data...")
            
            formatted_events = []
            for element in event_elements:
                try:
                    # --- The Definitive Fix ---
                    # First, check if there is a title. If not, it's not a real event card.
                    title_element = element.query_selector("h3")
                    if not title_element:
                        # This link doesn't have a title, so we safely skip it.
                        continue

                    title = title_element.inner_text().strip()
                    link = element.get_attribute("href")
                    
                    # Now that we know it's a real event, extract other details safely.
                    details = element.query_selector_all("p")
                    event_date = details[0].inner_text().strip() if len(details) > 0 else "日期未定"
                    event_time = details[1].inner_text().strip() if len(details) > 1 else "時間未定"
                    venue = details[2].inner_text().strip() if len(details) > 2 else "地點未定"
                    
                    category_element = element.query_selector("div[class*='-tag']")
                    category = category_element.inner_text().strip() if category_element else "一般活動"
                    
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
                    # This will now only catch truly unexpected errors.
                    print(f"Could not parse a potential event card. Error: {e}")

            if not formatted_events:
                raise Exception("Could not extract any valid event data.")
            else:
                with open("total_events.json", "w", encoding="utf-8") as f:
                    json.dump(formatted_events, f, ensure_ascii=False, indent=2)
                print(f"Scraping complete. Saved {len(formatted_events)} valid events to total_events.json")

        except Exception as e:
            print(f"An error occurred. Saving a screenshot to debug_screenshot.png")
            page.screenshot(path="debug_screenshot.png", full_page=True)
            raise e

        finally:
            browser.close()

except Exception as e:
    print(f"An error occurred during the browser automation process: {e}")
    exit(1)

