"""
ai_engine.py - AI-Assisted Intelligence for AIAC Smart Hostel Platform.
Provides:
1. Automated complaint categorization and priority recommendation (NLP heuristics).
2. AIAC FAQ Chatbot assistant for students and staff.
3. Hostel maintenance & complaint trend summarization for Warden Reports.
"""

import re
from typing import Dict, Any, List

# Keyword maps for complaint classification
CATEGORY_KEYWORDS = {
    'Electricity': [
        'electric', 'power', 'plug', 'socket', 'switch', 'spark', 'bulb', 'light', 'fan',
        'short circuit', 'ac', 'voltage', 'trip', 'mcb', 'wire', 'wiring', 'tube light',
        'geyser', 'heater', 'current', 'shock'
    ],
    'Plumbing': [
        'water', 'tap', 'leak', 'pipe', 'flush', 'toilet', 'drain', 'drainage', 'sink',
        'basin', 'shower', 'bathroom', 'clog', 'clogged', 'tank', 'overflow', 'plumbing',
        'sewage', 'gutter', 'drip', 'no water'
    ],
    'Cleanliness': [
        'clean', 'dirt', 'dirty', 'trash', 'garbage', 'dustbin', 'sweep', 'sweeping',
        'mop', 'mopping', 'smell', 'odor', 'cockroach', 'insects', 'pest', 'mosquito',
        'corridor', 'litter', 'hygiene', 'washroom'
    ],
    'Wi-Fi / Internet': [
        'wifi', 'wi-fi', 'internet', 'lan', 'ethernet', 'router', 'network', 'speed',
        'connection', 'disconnect', 'bandwidth', 'slow net', 'portal', 'login page', 'hotspot'
    ],
    'Mess Food': [
        'mess', 'food', 'meal', 'lunch', 'dinner', 'breakfast', 'snack', 'roti', 'rice',
        'dal', 'curry', 'hygiene in food', 'undercooked', 'raw', 'salty', 'spoiled',
        'caterer', 'diet', 'taste', 'quality of food', 'insect in food'
    ],
    'Laundry': [
        'dhobi', 'laundry', 'cloth', 'clothes', 'washing', 'iron', 'ironing', 'delivery',
        'dry clean', 'lost cloth', 'torn', 'stain', 'pickup', 'garment'
    ],
    'Security': [
        'security', 'guard', 'gate', 'lock', 'theft', 'stolen', 'missing', 'intruder',
        'trespass', 'harass', 'threat', 'cctv', 'id card', 'entry'
    ],
    'Room Maintenance': [
        'door', 'window', 'cupboard', 'almirah', 'bed', 'mattress', 'chair', 'table',
        'study table', 'hinge', 'paint', 'wall', 'crack', 'ceiling', 'plaster', 'key',
        'furniture'
    ]
}

URGENCY_KEYWORDS = {
    'Urgent': [
        'emergency', 'urgent', 'fire', 'smoke', 'spark', 'electric shock', 'hazard',
        'immediate', 'flood', 'overflowing', 'burst', 'danger', 'broken lock', 'threat',
        'critical', 'severe', 'gas leak'
    ],
    'High': [
        'broken', 'not working', 'no water', 'no power', 'stuck', 'severe', 'pain',
        'spoiled', 'blackout', 'foul smell', 'cockroach', 'infestation', 'fallen'
    ],
    'Medium': [
        'slow', 'leak', 'drip', 'fluctuating', 'dim', 'delay', 'noise', 'loose',
        'cleaning needed', 'dusty', 'dirty'
    ],
    'Low': [
        'minor', 'request', 'inquiry', 'small', 'cosmetic', 'paint chip', 'suggestion'
    ]
}


def analyze_complaint(subject: str, description: str) -> Dict[str, Any]:
    """
    Analyzes subject and description to suggest the most probable Category
    and recommended Priority level with an explainable confidence score.
    """
    text = f"{subject or ''} {description or ''}".lower()

    # 1. Category scoring
    best_cat = 'Room Maintenance'
    max_cat_score = 0
    cat_scores = {}

    for cat, kws in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in kws:
            matches = len(re.findall(r'\b' + re.escape(kw) + r'\b', text))
            score += matches * 2
            if kw in (subject or '').lower():
                score += 3  # Subject words carry higher weight
        cat_scores[cat] = score
        if score > max_cat_score:
            max_cat_score = score
            best_cat = cat

    confidence = round(min(0.95, 0.40 + (max_cat_score * 0.1)), 2) if max_cat_score > 0 else 0.45

    # 2. Priority scoring
    suggested_priority = 'Medium'
    reason = "Standard maintenance review required."

    # Check for Urgent indicators
    urgent_matches = [kw for kw in URGENCY_KEYWORDS['Urgent'] if re.search(r'\b' + re.escape(kw) + r'\b', text)]
    if urgent_matches:
        suggested_priority = 'Urgent'
        reason = f"High safety or service risk detected ({', '.join(urgent_matches[:2])})."
    else:
        high_matches = [kw for kw in URGENCY_KEYWORDS['High'] if re.search(r'\b' + re.escape(kw) + r'\b', text)]
        if high_matches:
            suggested_priority = 'High'
            reason = f"Critical service disruption indicated ({', '.join(high_matches[:2])})."
        else:
            low_matches = [kw for kw in URGENCY_KEYWORDS['Low'] if re.search(r'\b' + re.escape(kw) + r'\b', text)]
            if low_matches and max_cat_score <= 2:
                suggested_priority = 'Low'
                reason = "Routine or non-critical item."
            else:
                suggested_priority = 'Medium'
                reason = "Normal processing priority assigned."

    return {
        'suggested_category': best_cat,
        'suggested_priority': suggested_priority,
        'confidence': confidence,
        'reasoning': reason
    }


def faq_bot_reply(message: str, user_name: str = "Student") -> Dict[str, Any]:
    """
    Intelligent hostel assistant chatbot engine answering queries on:
    - Outpasses, Curfews & Leaves
    - Mess Timings & Special Meals
    - Laundry & Dhobi Services
    - Emergency Help
    - Fee Payment & Receipts
    - Room Policies & Maintenance
    """
    query = (message or '').strip().lower()

    # Rule-based intents with detailed answers
    if not query:
        return {
            'reply': f"Hello {user_name}! I am **AIAC Assistant**, your 24/7 Hostel Virtual Concierge. You can ask me about outpass rules, mess menu & timings, laundry schedules, fee payments, emergency contacts, or complaint tracking.",
            'category': 'greeting'
        }

    # Greetings
    if re.search(r'\b(hi|hello|hey|greetings|good morning|good evening)\b', query):
        return {
            'reply': f"Hello {user_name}! How can I help you today? Ask me about: \n- **Outpass & Curfew rules**\n- **Today's Mess Menu** (including Sunday & Wednesday specials)\n- **Laundry pickup & delivery**\n- **Hostel & Dhobi Fees**\n- **Submitting a Maintenance Complaint**",
            'category': 'greeting'
        }

    # Outpass / Leave / Curfew
    if re.search(r'\b(outpass|leave|outing|vacation|curfew|permission|gate|timing|night out)\b', query):
        return {
            'reply': """**📋 Hostel Leave & Outpass Guidelines:**
1. **Curfew Time:** All campus residents must return by **09:30 PM**.
2. **Types of Leave:**
   - *One-day Outing*: For local errands returning before 09:30 PM.
   - *Overnight / Vacation Leave*: For visiting home or official excursions.
3. **Approval Window:** Please apply at least **6 hours** before departure.
4. **Outpass Verification:** Once approved by the warden, your dashboard generates a digital Outpass with a unique reference number. Show this at the main security checkpoint.""",
            'category': 'outpass'
        }

    # Mess / Food / Timings
    if re.search(r'\b(mess|food|breakfast|lunch|dinner|snack|menu|special|wednesday|sunday|timing)\b', query):
        return {
            'reply': """**🍽️ Mess Timings & Special Meals:**
* **Breakfast:** 07:30 AM – 09:00 AM (Sundays 08:00 AM – 10:00 AM)
* **Lunch:** 12:30 PM – 02:00 PM (Sundays extended to 02:30 PM)
* **Evening Snacks:** 05:00 PM – 06:00 PM
* **Dinner:** 07:30 PM – 09:30 PM

⭐ **Special Meals Highlight:**
* **Wednesday Dinner:** Chef's Midweek Feast featuring Special Biryani, Butter Naan & Hot Gulab Jamun!
* **Sunday Afternoon Lunch:** Grand Royal Dum Biryani, Paneer Tikka Masala, and Artisanal Kulfi!
*(View full weekly menu in the **Mess Menu** tab).*""",
            'category': 'mess'
        }

    # Laundry / Dhobi
    if re.search(r'\b(dhobi|laundry|clothes|cloth|wash|iron|schedule|pickup|delivery)\b', query):
        return {
            'reply': """**🧺 Dhobi & Laundry Service Information:**
1. **Collection Schedule:** Collections are held on scheduled weekday and weekend mornings.
2. **Limit:** Up to **15 garments** per collection batch for standard service.
3. **Turnaround Time:** Washed and ironed garments are typically delivered within **48 hours**.
4. **Tracking:** You can submit your laundry bundle directly in the **Dhobi & Laundry** section and monitor live statuses from *Request Submitted* to *Ready for Delivery*.""",
            'category': 'laundry'
        }

    # Fees & Payment
    if re.search(r'\b(fee|fees|payment|dues|hostel fee|dhobi fee|receipt|pay|cost|charge)\b', query):
        return {
            'reply': """**💳 Hostel & Dhobi Fees Guidelines:**
1. **Separate Accounts:** Hostel accommodation fees and Dhobi laundry fees are tracked separately.
2. **Hostel Fee:** Covers room accommodation, electricity, Wi-Fi, and amenities per semester.
3. **Dhobi Fee:** Monthly recurring service charge for personal clothing laundry.
4. **Online Demo Gateway:** You can make simulated payments safely and immediately download or print an official PDF receipt with verification references.""",
            'category': 'fees'
        }

    # Emergency
    if re.search(r'\b(emergency|urgent|ambulance|fire|doctor|hospital|police|guard|hazard|danger|medical)\b', query):
        return {
            'reply': """**🚨 EMERGENCY PROTOCOL & HELPLINES:**
- **Campus Medical Center & 24/7 Ambulance:** +91 98765 00108
- **Hostel Main Security Desk:** +91 98765 00100
- **Chief Warden Hotline:** +91 98765 00101
- **Emergency Electrician:** +91 98765 00102

🔴 *If you are experiencing an in-hostel emergency, use the red **Emergency Alert** button right now. The alert is instantly dispatched to the warden dashboard.*""",
            'category': 'emergency'
        }

    # Complaints / Repairs
    if re.search(r'\b(complaint|repair|fix|broken|plumbing|electric|wifi|internet|fan|light|water|room)\b', query):
        return {
            'reply': """**🛠️ Submitting & Tracking Complaints:**
1. Go to the **Complaints** tab.
2. Enter the subject and issue details. Our AI Assistant will automatically suggest the category and urgency priority!
3. Wardens review complaints, assign maintenance personnel, and post status updates.
4. You will receive an instant notification whenever your complaint is addressed.""",
            'category': 'complaints'
        }

    # Default fallback
    return {
        'reply': f"I understand you are asking about: *'{message}'*. \n\nFor specific assistance, you can navigate using the left sidebar to **Leave Management**, **Complaints**, **Mess Menu**, or **Emergency Support**. If you require immediate administrative action, you can also reach the Chief Warden's office at `+91 98765 00101` or visit the Warden Office during hours (09:00 AM – 06:00 PM).",
        'category': 'general'
    }


def generate_complaint_summary(complaints: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Summarizes complaints for Warden Reports & Analytics.
    Identifies common problem areas, resolution rates, and urgency distributions.
    """
    total = len(complaints)
    if total == 0:
        return {
            'total': 0,
            'summary_text': "No complaints recorded in the system yet. Hostel facilities are operating normally.",
            'top_categories': [],
            'hotspots': []
        }

    categories = {}
    priorities = {}
    statuses = {}
    locations = {}

    for c in complaints:
        cat = c.get('category', 'Other')
        prio = c.get('priority', 'Medium')
        st = c.get('status', 'Submitted')
        loc = c.get('location_or_room', 'Unknown')

        categories[cat] = categories.get(cat, 0) + 1
        priorities[prio] = priorities.get(prio, 0) + 1
        statuses[st] = statuses.get(st, 0) + 1
        locations[loc] = locations.get(loc, 0) + 1

    resolved_count = statuses.get('Resolved', 0)
    res_rate = round((resolved_count / total) * 100, 1)

    # Top category
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    top_cat_name, top_cat_count = sorted_cats[0]

    # Urgent count
    urgent_count = priorities.get('Urgent', 0) + priorities.get('Critical', 0)

    summary_text = (
        f"Analysis of {total} maintenance complaints shows a resolution rate of {res_rate}%. "
        f"The primary driver of complaints is '{top_cat_name}' with {top_cat_count} reports "
        f"({round((top_cat_count/total)*100)}% of total volume). "
        f"{urgent_count} items required urgent priority handling."
    )

    return {
        'total': total,
        'summary_text': summary_text,
        'resolution_rate': res_rate,
        'top_categories': sorted_cats[:4],
        'urgent_count': urgent_count
    }
