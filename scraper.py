import requests
import json

# The direct API endpoint the website uses to get event data.
# This is more reliable than trying to find the URL dynamically.
API_URL = "https://prod-api.kaitaksportspark.com.hk/graphql"

# The base URL to construct full event links
BASE_URL = "https://www.kaitaksportspark.com.hk"

# This is the specific "query" the website sends to the API to ask for the event list.
GRAPHQL_QUERY = {
    "operationName": "GetEvents",
    "variables": {
        "language": "tc",
        "limit": 100,  # Get up to 100 events
        "offset": 0
    },
    "query": """
        query GetEvents($language: String, $limit: Int, $offset: Int) {
          events(language: $language, limit: $limit, offset: $offset) {
            items {
              id
              title
              slug
              eventDate
              eventTime
              venue
              category {
                id
                title
                slug
              }
            }
          }
        }
    """
}

print("Fetching event data from the official API...")

try:
    # Make a POST request to the GraphQL API with our query
    response = requests.post(API_URL, json=GRAPHQL_QUERY, timeout=15)
    
    # This will raise an error if the request failed (e.g., 404, 500)
    response.raise_for_status()
    
    # Parse the JSON response from the API
    data = response.json()
    
    # The events are nested inside the JSON structure
    event_items = data.get("data", {}).get("events", {}).get("items", [])
    
    if not event_items:
        print("API returned a successful response, but no events were found.")
    else:
        print(f"Successfully found {len(event_items)} events.")
        
        # Format the events into the structure our dashboard expects
        formatted_events = []
        for item in event_items:
            # Construct the full link to the event page
            full_link = f"{BASE_URL}/tc/event/{item.get('slug', '')}"
            
            # Map the API data to the keys our frontend uses (e.g., '日期' for date)
            formatted_event = {
                "title": item.get("title"),
                "link": full_link,
                "日期": item.get("eventDate"),
                "時間": item.get("eventTime"),
                "地點": item.get("venue"),
                # Get the category title, default to "General" if not available
                "類別": item.get("category", {}).get("title") if item.get("category") else "一般活動"
            }
            formatted_events.append(formatted_event)
            
        # Save the detailed events to total_events.json
        with open("total_events.json", "w", encoding="utf-8") as f:
            json.dump(formatted_events, f, ensure_ascii=False, indent=2)
        print("Saved detailed event data to total_events.json")

except requests.exceptions.RequestException as e:
    print(f"An error occurred while fetching data from the API: {e}")
except json.JSONDecodeError:
    print("Failed to parse the JSON response from the API. The API might be down or has changed.")

