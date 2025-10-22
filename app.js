// Kai Tak Sports Park Dashboard JavaScript

// Helper function to parse various Chinese date formats
function parseChineseDate(dateStr) {
  if (!dateStr || dateStr === "日期未定") return null;

  let year, month, startDay, endDay;

  // Format: "2025年9月27日至2026年10月13日" (cross-year)
  let match = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})日至(\d{4})年(\d{1,2})月(\d{1,2})日/);
  if (match) {
    return {
      start: new Date(parseInt(match[1]), parseInt(match[2]) - 1, parseInt(match[3])),
      end: new Date(parseInt(match[4]), parseInt(match[5]) - 1, parseInt(match[6]))
    };
  }

  // Format: "2025年9月27日至10月13日" (cross-month)
  match = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})日至(\d{1,2})月(\d{1,2})日/);
  if (match) {
    return {
      start: new Date(parseInt(match[1]), parseInt(match[2]) - 1, parseInt(match[3])),
      end: new Date(parseInt(match[1]), parseInt(match[4]) - 1, parseInt(match[5]))
    };
  }
  
  // Format: "2025年10月4至7日" (same-month range)
  match = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})至(\d{1,2})日/);
  if (match) {
    year = parseInt(match[1]);
    month = parseInt(match[2]) - 1;
    startDay = parseInt(match[3]);
    endDay = parseInt(match[4]);
    return { start: new Date(year, month, startDay), end: new Date(year, month, endDay) };
  }

  // Format: "2025年10月14及15日" (same-month, non-consecutive)
  match = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})及(\d{1,2})日/);
  if (match) {
    year = parseInt(match[1]);
    month = parseInt(match[2]) - 1;
    startDay = parseInt(match[3]);
    endDay = parseInt(match[4]);
    return { start: new Date(year, month, startDay), end: new Date(year, month, endDay) };
  }

  // Format: "2025年10月5日" (single day)
  match = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
  if (match) {
    year = parseInt(match[1]);
    month = parseInt(match[2]) - 1;
    startDay = parseInt(match[3]);
    const date = new Date(year, month, startDay);
    return { start: date, end: date };
  }

  return null; // Return null if no format matches
}


// Check if a parsed period or date string includes today
function isEventToday(dateStr) {
    try {
        const period = parseChineseDate(dateStr);
        if (!period) return false;

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const { start, end } = period;
        // Ensure start and end are valid dates before proceeding
        if (isNaN(start.getTime()) || isNaN(end.getTime())) {
            return false;
        }

        start.setHours(0, 0, 0, 0);
        end.setHours(0, 0, 0, 0);

        return today.getTime() >= start.getTime() && today.getTime() <= end.getTime();
    } catch (e) {
        console.error("Error parsing date:", dateStr, e);
        return false; // Safely return false if any error occurs
    }
}


function createEventCard(event, additionalClass = '') {
  const card = document.createElement('div');
  card.className = `event-card ${additionalClass}`;

  const category = event.類別 || '一般活動';
  
  // Define a color map for categories
  const categoryColors = {
      '演唱會': 'var(--color-bg-5)',
      '體育活動': 'var(--color-bg-3)',
      '社區活動': 'var(--color-bg-2)',
      '展覽及會議': 'var(--color-bg-1)',
      '一般活動': 'var(--color-bg-8)',
  };
  
  card.style.background = categoryColors[category] || 'var(--color-bg-8)';

  card.innerHTML = `
    <a href="${event.link || '#'}" target="_blank" class="event-link">
      <div class="event-type">${category}</div>
      <h3 class="event-name">${event.title || '無標題'}</h3>
      <div class="event-details">
        <div class="event-date">📅 ${event.日期 || '日期未定'}</div>
        <div class="event-venue">📍 ${event.地點 || '地點未定'}</div>
      </div>
    </a>
  `;
  return card;
}

// Fetch events and render into both lists
async function fetchAndUpdateEvents() {
  console.log('Fetching events...');
  try {
    const remoteUrl = 'https://cdn.jsdelivr.net/gh/ryoohkilo/kai-tak-events-grep@main/total_events.json';
    const resp = await fetch(`${remoteUrl}?t=${new Date().getTime()}`);

    if (!resp.ok) {
      throw new Error('Failed to fetch events from GitHub: ' + resp.status);
    }
    
    const events = await resp.json();

    const todayList = document.getElementById('todayEventsList');
    const allEventsList = document.getElementById('allEventsList');

    if (!todayList || !allEventsList) {
        console.error("Event list containers not found!");
        return;
    }

    todayList.innerHTML = '';
    allEventsList.innerHTML = '';

    if (!Array.isArray(events) || events.length === 0) {
      todayList.innerHTML = '<div class="no-events">今日沒有活動</div>';
      allEventsList.innerHTML = '<div class="no-events">暫時沒有最新活動</div>';
      return;
    }

    const todayEvents = events.filter(e => isEventToday(e.日期));

    if (todayEvents.length > 0) {
      todayEvents.forEach(ev => todayList.appendChild(createEventCard(ev, 'today')));
    } else {
      todayList.innerHTML = '<div class="no-events">今日沒有活動</div>';
    }

    events.forEach(e => allEventsList.appendChild(createEventCard(e)));

  } catch (err) {
    console.error('事件資訊載入失敗！', err);
    const todayList = document.getElementById('todayEventsList');
    const allEventsList = document.getElementById('allEventsList');
    if(todayList) todayList.innerHTML = '<div class="no-events">無法載入活動資訊</div>';
    if(allEventsList) allEventsList.innerHTML = '<div class="no-events">無法載入活動資訊</div>';
  }
}


// Initialize UI
document.addEventListener('DOMContentLoaded', () => {
  // Clock + date
  const timeEl = document.getElementById('currentTime');
  const dateEl = document.getElementById('currentDate');
  function updateClock() {
    const now = new Date();
    if (timeEl) timeEl.textContent = now.toLocaleTimeString('zh-HK', { timeZone: 'Asia/Hong_Kong', hour12: false });
    if (dateEl) {
      const y = now.getFullYear();
      const m = now.getMonth() + 1;
      const d = now.getDate();
      if (dateEl) dateEl.textContent = `${y}年${m}月${d}日`;
    }
  }

  updateClock();
  setInterval(updateClock, 1000);

  fetchAndUpdateEvents();
});

