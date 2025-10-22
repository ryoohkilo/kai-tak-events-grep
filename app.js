// Kai Tak Sports Park Dashboard JavaScript

// Helper function to parse Chinese date format
function parseChineseDate(dateStr) {
    if (!dateStr) return null;
    
    // Handle date ranges like "2025年10月4至7日"
    if (dateStr.includes('至')) {
        const [fullStr, year, month, startDay, endDay] = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})至(\d{1,2})日/) || [];
        if (fullStr) {
            return {
                start: new Date(parseInt(year), parseInt(month) - 1, parseInt(startDay)),
                end: new Date(parseInt(year), parseInt(month) - 1, parseInt(endDay))
            };
        }
    }
    
    // Handle date ranges with "及" like "2025年10月14及15日"
    if (dateStr.includes('及')) {
        const [fullStr, year, month, day1, day2] = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})及(\d{1,2})日/) || [];
        if (fullStr) {
            return {
                start: new Date(parseInt(year), parseInt(month) - 1, parseInt(day1)),
                end: new Date(parseInt(year), parseInt(month) - 1, parseInt(day2))
            };
        }
    }
    
    // Handle single dates
    const match = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
    if (match) {
        const [_, year, month, day] = match;
        const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
        return { start: date, end: date };
    }
    
    return null;
}

// Check if event is today
// Consolidated app.js

// Parse Chinese date strings into {start: Date, end: Date} or null
function parseChineseDate(dateStr) {
  if (!dateStr) return null;
  const s = String(dateStr).trim().replace(/\s+/g, '');

  // 1) Empty or unknown
  if (s === '' || /日期待定|待定|TBD/i.test(s)) return null;

  // 2) Full range with years on both sides: 2025年9月27日至2026年10月13日
  let m = s.match(/(\d{4})年(\d{1,2})月(\d{1,2})日至(\d{4})年(\d{1,2})月(\d{1,2})日/);
  if (m) {
    const [, sy, sm, sd, ey, em, ed] = m;
    return { start: new Date(parseInt(sy), parseInt(sm) - 1, parseInt(sd)), end: new Date(parseInt(ey), parseInt(em) - 1, parseInt(ed)) };
  }

  // 3) Range with year at start, end has month/day: 2025年9月27日至10月13日
  m = s.match(/(\d{4})年(\d{1,2})月(\d{1,2})日至(\d{1,2})月(\d{1,2})日/);
  if (m) {
    const [, y, sm, sd, em, ed] = m;
    return { start: new Date(parseInt(y), parseInt(sm) - 1, parseInt(sd)), end: new Date(parseInt(y), parseInt(em) - 1, parseInt(ed)) };
  }

  // 4) Range same month: 2025年10月4至7日
  m = s.match(/(\d{4})年(\d{1,2})月(\d{1,2})至(\d{1,2})日/);
  if (m) {
    const [, y, mon, d1, d2] = m;
    return { start: new Date(parseInt(y), parseInt(mon) - 1, parseInt(d1)), end: new Date(parseInt(y), parseInt(mon) - 1, parseInt(d2)) };
  }

  // 5) '及' two specific days in same month: 2025年12月6及7日
  m = s.match(/(\d{4})年(\d{1,2})月(\d{1,2})及(\d{1,2})日/);
  if (m) {
    const [, y, mon, d1, d2] = m;
    return { start: new Date(parseInt(y), parseInt(mon) - 1, parseInt(d1)), end: new Date(parseInt(y), parseInt(mon) - 1, parseInt(d2)) };
  }

  // 6) Single date: 2025年10月5日
  m = s.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
  if (m) {
    const [, y, mon, d] = m;
    const date = new Date(parseInt(y), parseInt(mon) - 1, parseInt(d));
    return { start: date, end: date };
  }

  // If nothing matched, return null so caller can treat as unknown
  return null;
}

// Check if a parsed period or date string includes today
function isEventToday(dateStr) {
  if (!dateStr) return false;
  const period = parseChineseDate(dateStr);
  if (!period) return false;

  // Use system local date (assume HK system time or user using correct timezone)
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  // Normalize time parts
  const start = new Date(period.start.getFullYear(), period.start.getMonth(), period.start.getDate());
  const end = new Date(period.end.getFullYear(), period.end.getMonth(), period.end.getDate());

  return today.getTime() >= start.getTime() && today.getTime() <= end.getTime();
}

function createEventCard(event, additionalClass = '') {
  const card = document.createElement('div');
  // Determine type-specific class
  let typeClass = '';
  if (event.類別 === '運動賽事') typeClass = 'sports';
  else if (event.類別 === '娛樂活動') typeClass = 'entertainment';
  else if (event.類別 === '演唱會') typeClass = 'concert';
  card.className = `event-card ${typeClass} ${additionalClass}`.trim();
  const title = (event.title || '').split('\n').join(' ');
  const dateText = event.日期 || '日期待定';
  const timeText = event.時間 || '時間待定';
  const venue = event.地點 || '啟德體育園';

  // simple type mapping
  let eventTypeText = '娛樂活動';
  if (event.類別 === '運動賽事') eventTypeText = '體育賽事';
  if (event.類別 === '演唱會') eventTypeText = '音樂會';

  card.innerHTML = `
    <a href="${event.link || '#'}" target="_blank" class="event-link">
      <div class="event-type">${eventTypeText}</div>
      <h3 class="event-name">${title}</h3>
      <div class="event-details">
        <div class="event-date">${dateText}</div>
        <div class="event-time">${timeText}</div>
        <div class="event-venue">${venue}</div>
      </div>
    </a>
  `;
  return card;
}

// Fetch events and render into both lists
async function fetchAndUpdateEvents() {
  console.log('Fetching events...');
  try {
    // Prefer local copy first
    let resp = await fetch('./total_events.json');
    if (!resp.ok) {
      console.warn('Local total_events.json not available, fetching remote');
      resp = await fetch('https://raw.githubusercontent.com/ryoohkilo/kai-tak-events-scraper/main/total_events.json');
    }

    if (!resp.ok) throw new Error('Failed to fetch events: ' + resp.status);
    const text = await resp.text();
    let events;
    try {
      events = JSON.parse(text);
    } catch (err) {
      console.error('Failed to parse events JSON:', err, 'response snippet:', text.slice(0, 1000));
      return;
    }

    console.log('Loaded', events.length, 'events');

    // Today's list container
    const todayList = document.getElementById('todayEventsList');
    if (todayList) {
      todayList.innerHTML = '';
      const todayEvents = events.filter(e => {
        const parsed = parseChineseDate(e.日期);
        const isToday = isEventToday(e.日期);
        console.log('Event:', (e.title||'').split('\n').join(' '));
        console.log('  raw date:', e.日期, 'parsed:', parsed, 'isToday:', isToday);
        return isToday;
      });

      if (todayEvents.length > 0) {
        todayEvents.forEach(ev => todayList.appendChild(createEventCard(ev, 'today')));
      } else {
        todayList.innerHTML = '<div class="no-events">今日沒有活動</div>';
      }
    }

    // All events
    const allEventsList = document.getElementById('allEventsList');
    if (allEventsList) {
      allEventsList.innerHTML = '';
      events.forEach(e => allEventsList.appendChild(createEventCard(e)));
    }
  } catch (err) {
    console.error('事件資訊載入失敗！', err);
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
      const wk = ['日','一','二','三','四','五','六'][now.getDay()];
      dateEl.textContent = `${y}年${m}月${d}日（星期${wk}）`;
    }
  }
  updateClock();
  setInterval(updateClock, 1000);

  // initial load
  fetchAndUpdateEvents();
  setInterval(fetchAndUpdateEvents, 5 * 60 * 1000);
});
