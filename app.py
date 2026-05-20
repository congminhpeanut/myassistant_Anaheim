import os
import json
import requests
from flask import Flask, jsonify, send_from_directory, request, Response
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
env_file = os.path.join(basedir, ".env")
if os.path.isfile(env_file):
    load_dotenv(env_file, override=False)

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/api")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "kimi-k2.6:cloud")

app = Flask(__name__, static_folder='static')

def b(en, vi):
    return {"en": en, "vi": vi}

TRIP_OVERVIEW = {
    "event": b("ADLM 2026 Annual Meeting & Clinical Lab Expo",
               "Hội nghị Thường niên ADLM 2026 & Triển lãm Phòng thí nghiệm"),
    "venue": b("Anaheim Convention Center", "Trung tâm Hội nghị Anaheim"),
    "address": "800 W Katella Ave, Anaheim, CA 92802, USA",
    "dates": b("July 26 – 30, 2026", "26 – 30 tháng 7, 2026"),
    "expo_dates": b("July 28 – 30, 2026", "28 – 30 tháng 7, 2026"),
    "your_arrival": b("July 24 or 25, 2026", "24 hoặc 25 tháng 7, 2026"),
    "poster_location": b("Expo Show Floor, Poster Hall",
                         "Sàn Triển lãm, Phòng Poster"),
    "travelers": 2,
    "budget_per_day": b("~$50 per person per day", "~$50 / người / ngày"),
    "contact": b("ADLM Registration", "Đăng ký ADLM"),
    "contact_email": "meeting@myadlm.org"
}

AIRPORT_DATA = {
    "recommended_airport": {
        "code": "SNA",
        "name": b("John Wayne Airport (Orange County)", "Sân bay John Wayne (Hạt Cam)"),
        "distance_to_venue": b("14 miles (22 km)", "22 km"),
        "drive_time": b("15–20 minutes", "15–20 phút"),
        "why": b(
            "Closest to Anaheim. Smaller and easier to navigate. Shorter immigration queues. Less connection hassle.",
            "Gần Anaheim nhất. Nhỏ hơn, dễ dàng di chuyển. Ít xếp hàng nhập cư. Ít rắc rối chuyển sân bay.")
    },
    "alternative_airport": {
        "code": "LAX",
        "name": b("Los Angeles International Airport", "Sân bay Quốc tế Los Angeles"),
        "distance_to_venue": b("36 miles (58 km)", "58 km"),
        "drive_time": b("45–90 minutes (traffic dependent)", "45–90 phút (phụ thuộc giao thông)"),
        "why": b(
            "More international flights from Asia. Often cheaper tickets but much longer transfer.",
            "Nhiều chuyến bay quốc tế từ châu Á hơn. Vé thường rẻ hơn nhưng di chuyển xa hơn nhiều.")
    },
    "arrival_tips": [
        b("Fill out the Customs Declaration Form (given on plane or via Mobile Passport Control app).",
          "Điền tờ khai Hải quan (cấp trên máy bay hoặc qua app Mobile Passport Control)."),
        b("Vietnam passport holders need ESTA under the Visa Waiver Program. Apply at least 72 hours before departure.",
          "Người mang hộ chiếu Việt Nam cần ESTA theo Chương trình Miễn thị thực. Đăng ký ít nhất 72 giờ trước khi bay."),
        b("Keep passport, boarding pass, hotel confirmation, and return ticket ready.",
          "Chuẩn bị sẵn hộ chiếu, vé máy bay, xác nhận khách sạn, vé về."),
        b("At customs, state purpose clearly: 'attending a medical conference.' Show ADLM confirmation if asked.",
          "Tại hải quan, nói rõ mục đích: 'tham dự hội nghị y khoa.' Đưa xác nhận ADLM nếu được yêu cầu."),
        b("Allow 1.5–2 hours for immigration at LAX; ~1 hour at SNA.",
          "Dự tính 1.5–2 giờ nhập cư tại LAX; ~1 giờ tại SNA."),
        b("After customs, collect luggage then follow Ground Transportation signs.",
          "Sau hải quan, lấy hành lý rồi theo biển chỉ Ground Transportation."),
        b("Exchange $200–300 in cash at the airport. Credit cards accepted almost everywhere.",
          "Đổi $200–300 tiền mặt tại sân bay. Thẻ tín dụng dùng được ở hầu hết mọi nơi.")
    ],
    "ground_transport": {
        "sna": b("Ground Transportation Center (GTC) — follow signs to Ride App Zone or taxi stand.",
                 "Trung tâm Vận chuyển (GTC) — theo biển chỉ Ride App hoặc taxi."),
        "lax": b("LAX-it shuttle to designated pickup zone. Follow purple signs for Uber/Lyft/Taxi.",
                 "Xe đưa LAX-it đến khu vực đón khách. Theo biển tím cho Uber/Lyft/Taxi.")
    }
}

TRANSPORT_OPTIONS = [
    {
        "mode": b("Rideshare (Uber / Lyft)", "Xe tiện chuyển (Uber / Lyft)"),
        "from_sna": b("$35–45, 20–25 min", "$35–45, 20–25 phút"),
        "from_lax": b("$70–90, 50–70 min", "$70–90, 50–70 phút"),
        "pros": b("Door-to-door — No waiting — Two people share cost",
                  "Tận nơi — Không đợi — 2 người chia tiền"),
        "cons": b("Surge pricing possible — Need app + payment card",
                  "Có thể tăng giá — Cần app + thẻ thanh toán"),
        "steps": [
            b("1. Download Uber or Lyft. Vietnam phone number works.",
              "1. Tải Uber hoặc Lyft. Số điện thoại Việt Nam dùng được."),
            b("2. Add credit card (Visa/MasterCard) or PayPal.",
              "2. Thêm thẻ tín dụng (Visa/MasterCard) hoặc PayPal."),
            b("3. Request ride from airport pickup zone.",
              "3. Đặt xe từ khu vực đón khách tại sân bay."),
            b("4. Input: '800 W Katella Ave, Anaheim, CA'",
              "4. Nhập: '800 W Katella Ave, Anaheim, CA'"),
            b("5. Choose UberX (cheapest) or UberXL (more luggage space).",
              "5. Chọn UberX (rẻ nhất) hoặc UberXL (nhiều chỗ đựng hành lý).")
        ],
        "recommended": b("Best for first-time travelers", "Tốt nhất cho người đi lần đầu")
    },
    {
        "mode": b("Airport Shuttle (Prime Time)", "Xe Đưa Đón (Prime Time)"),
        "from_sna": b("$20–25/person, 30–40 min", "$20–25/người, 30–40 phút"),
        "from_lax": b("$35–45/person, 60–80 min", "$35–45/người, 60–80 phút"),
        "pros": b("Pre-bookable online — Fixed price — Door-to-door",
                  "Đặt trước trên mạng — Giá cố định — Tận nơi"),
        "cons": b("May stop at multiple hotels — Fixed schedule",
                  "Có thể dừng nhiều khách sạn — Lịch trình cố định"),
        "steps": [
            b("1. Book online at primetimeshuttle.com",
              "1. Đặt trước tại primetimeshuttle.com"),
            b("2. Provide flight number and hotel address.",
              "2. Cung cấp số hiệu chuyến bay và địa chỉ khách sạn."),
            b("3. Show booking confirmation at Ground Transportation.",
              "3. Xuất trình xác nhận đặt tại Ground Transportation.")
        ],
        "recommended": b("Good for fixed budgets", "Tốt cho ngân sách cố định")
    },
    {
        "mode": b("Public Transit", "Phương tiện Công cộng"),
        "from_sna": b("OCTA Bus ~$2, 60–80 min", "Xe buýt OCTA ~$2, 60–80 phút"),
        "from_lax": b("FlyAway ($9.75) + Metrolink (~$14), total ~$24, 2.5 hours",
                  "FlyAway ($9.75) + Metrolink (~$14), tổng ~$24, 2.5 giờ"),
        "pros": b("Cheapest option — See local area",
                  "Rẻ nhất — Ngắm cảnh địa phương"),
        "cons": b("Complex for first-timers — Hard with luggage — Slow",
                  "Phức tạp cho người mới — Khó mang hành lý — Chậm"),
        "steps": [
            b("1. LAX: board FlyAway Bus to LA Union Station.",
              "1. Từ LAX: đi xe FlyAway đến LA Union Station."),
            b("2. Buy Metrolink ticket to Anaheim Station.",
              "2. Mua vé Metrolink đến ga Anaheim."),
            b("3. Walk 15 min or take ART bus ($4) to Convention Center.",
              "3. Đi bộ 15 phút hoặc xe ART ($4) đến Trung tâm Hội nghị.")
        ],
        "recommended": b("For tight budgets only", "Chỉ cho ngân sách rất hạn chế")
    }
]

HOTELS = [
    {
        "name": b("Hilton Anaheim", "Khách sạn Hilton Anaheim"),
        "address": "777 Convention Way, Anaheim, CA 92802",
        "distance": b("0.2 miles (3 min walk)", "300 m (đi bộ 3 phút)"),
        "price": b("$170–220/night", "$170–220/đêm"),
        "why": b("Next door to convention center. Walk to poster session in 3 minutes. Official conference hotel.",
                 "Sát bên trung tâm hội nghị. Đi bộ 3 phút đến poster. Khách sạn chính thức của hội nghị.")
    },
    {
        "name": b("Anaheim Marriott", "Khách sạn Anaheim Marriott"),
        "address": "700 W Convention Way, Anaheim, CA 92802",
        "distance": b("0.3 miles (5 min walk)", "500 m (đi bộ 5 phút)"),
        "price": b("$150–200/night", "$150–200/đêm"),
        "why": b("Connected to convention center via pedestrian bridge. Premium location.",
                 "Nối với trung tâm hội nghị bằng cầu đi bộ. Vị trí đẹp.")
    },
    {
        "name": b("Courtyard by Marriott", "Courtyard by Marriott Anaheim"),
        "address": "2045 S Harbor Blvd, Anaheim, CA 92802",
        "distance": b("0.8 miles (15 min walk / 5 min Uber)", "1.3 km (đi bộ 15 phút / Uber 5 phút)"),
        "price": b("$120–160/night", "$120–160/đêm"),
        "why": b("Best balance of price and proximity. Short Uber to venue.",
                 "Cân bằng tốt nhất giữa giá và khoảng cách. Uber ngắn đến hội nghị.")
    },
    {
        "name": b("Best Western Plus Anaheim Inn", "Best Western Plus Anaheim Inn"),
        "address": "1630 S Harbor Blvd, Anaheim, CA 92802",
        "distance": b("1.0 mile (20 min walk / 7 min Uber)", "1.6 km (đi bộ 20 phút / Uber 7 phút)"),
        "price": b("$100–140/night", "$100–140/đêm"),
        "why": b("Budget option. Includes breakfast. Short ART bus ride.",
                 "Tùy chọn tiết kiệm. Có bữa sáng. Gần trạm xe bus ART.")
    }
]

SCHEDULE = {
    "opening_mixer": {
        "date": b("Sunday, July 26, 2026", "Chủ nhật, 26 tháng 7, 2026"),
        "time": "6:30 PM – 8:00 PM",
        "location": b("Arena Plaza, Anaheim Convention Center",
                     "Arena Plaza, Trung tâm Hội nghị Anaheim"),
        "what": b("Welcome reception with free food and drinks. Network before the conference.",
                  "Tiệc chào đón miễn phí ăn uống. Gặp gỡ trước hội nghị."),
        "tip": b("Arrive early (6:15). Lines form fast.", "Đến sớm (6:15 giờ). Có đông người nhanh.")
    },
    "expo_days": {
        "dates": b("Tuesday July 28 – Thursday July 30, 2026",
                   "Thứ Ba 28 – Thứ Năm 30 tháng 7, 2026"),
        "hours": "9:30 AM – 5:00 PM (Thu ends noon)",
        "location": b("Expo Show Floor, Anaheim Convention Center",
                     "Sàn Triển lãm, Trung tâm Hội nghị Anaheim"),
        "what": b("800+ exhibitors. Poster sessions during expo hours.",
                 "800+ gian hàng. Buổi poster trong giờ triển lãm."),
        "tip": b("Poster sessions usually Tuesday–Wednesday afternoon.",
                "Buổi poster thường chiều Thứ Ba–Thứ Tư.")
    },
    "days": [
        {"day": b("Sat Jul 25", "Thứ 7, 25/7"), "events": b("Arrive, check in, rest", "Đến, nhận phòng, nghỉ ngơi"), "priority": "low"},
        {"day": b("Sun Jul 26", "Chủ nhật, 26/7"), "events": b("Registration. Opening Mixer 6:30–8:00 PM.", "Đăng ký. Tiệc chào đón 6:30–8:00 tối."), "priority": "high"},
        {"day": b("Mon Jul 27", "Thứ Hai, 27/7"), "events": b("Educational sessions, workshops.", "Các buổi học, hội thảo."), "priority": "medium"},
        {"day": b("Tue Jul 28", "Thứ Ba, 28/7"), "events": b("Expo Day 1. YOUR POSTER DAY likely afternoon.", "Ngày Triển lãm 1. NGÀY POSTER CỦA BẠN có thể chiều."), "priority": "high"},
        {"day": b("Wed Jul 29", "Thứ Tư, 29/7"), "events": b("Expo Day 2. More posters.", "Ngày Triển lãm 2. Thêm poster."), "priority": "high"},
        {"day": b("Thu Jul 30", "Thứ Năm, 30/7"), "events": b("Expo Day 3 (ends noon). Morning only.", "Ngày Triển lãm 3 (kết thúc trưa). Chỉ buổi sáng."), "priority": "medium"},
        {"day": b("Fri Jul 31", "Thứ Sáu, 31/7"), "events": b("Departure or extend stay.", "Về nước hoặc kéo dài lưu trú."), "priority": "low"},
    ]
}

FOOD = [
    {
        "name": b("The Anaheim Packing District", "Khu Ẩm thực Anaheim Packing District"),
        "address": "440 S Anaheim Blvd, Anaheim, CA 92805",
        "distance": b("1.5 miles from venue", "2.4 km từ hội nghị"),
        "price": b("$12–18/meal", "$12–18/bữa ăn"),
        "what": b("Food hall with 20+ vendors. Vietnamese banh mi, ramen, tacos, pizza, craft beer.",
                 "Khu ăn uống 20+ gian hàng. Bánh mì Việt, ramen, tacos, pizza, bia thủ công."),
        "tip": b("Great for dinner. Uber $8–12. Open until 10 PM.",
                "Tuyệt vời cho bữa tối. Uber $8–12. Mở đến 10 giờ tối.")
    },
    {
        "name": b("In-N-Out Burger", "In-N-Out Burger"),
        "address": "1168 State College Blvd, Anaheim, CA 92806",
        "distance": b("1.2 miles from venue", "1.9 km từ hội nghị"),
        "price": b("$8–12/meal", "$8–12/bữa ăn"),
        "what": b("California's iconic fast burger. Fresh, cheap, fast. Must-try for first-time US visitors.",
                 "Burger nổi tiếng California. Tươi ngon, rẻ, nhanh. Nên thử cho người mới đến Mỹ."),
        "tip": b("Order 'Animal Style' for secret menu. Cash or card accepted.",
                "Đặt 'Animal Style' cho menu bí mật. Tiền mặt hoặc thẻ đều được.")
    },
    {
        "name": b("Pho 79 (Vietnamese)", "Phở 79 (Việt Nam)"),
        "address": "9941 Hazard Ave, Garden Grove, CA 92844",
        "distance": b("3 miles (10 min Uber)", "4.8 km (Uber 10 phút)"),
        "price": b("$12–16/meal", "$12–16/bữa ăn"),
        "what": b("Authentic Vietnamese pho and banh cuon. Orange County's large Vietnamese community (Little Saigon). Tastes like home.",
                 "Phở và bánh cuốn chính gốc. Cộng đồng người Việt lớn tại Orange County (Little Saigon). Vị như nhà."),
        "tip": b("Open until 9 PM. Uber $12–15. Comfort food after long flight.",
                "Mở đến 9 giờ tối. Uber $12–15. Món ăn quen thuộc sau chuyến bay dài.")
    },
    {
        "name": b("Chipotle / McDonald's / Subway", "Chipotle / McDonald's / Subway"),
        "address": b("Multiple locations near venue", "Nhiều chi nhánh gần hội nghị"),
        "distance": b("Walking distance", "Đi bộ được"),
        "price": b("$8–12/meal", "$8–12/bữa ăn"),
        "what": b("Reliable, fast, cheap. Chipotle bowls are filling. McDonald's has $1–5 value menu.",
                 "Đáng tin cậy, nhanh, rẻ. Chipotle no lắng. McDonald's có menu $1–5."),
        "tip": b("Chipotle app for mobile order and skip line.",
                "App Chipotle đặt trước và nhảy hàng.")
    },
    {
        "name": b("Convention Center Food Court", "Khu Ăn uống Trung tâm Hội nghị"),
        "address": b("Inside Anaheim Convention Center", "Bên trong Trung tâm Hội nghị Anaheim"),
        "distance": b("Inside venue", "Bên trong hội nghị"),
        "price": b("$14–20/meal", "$14–20/bữa ăn"),
        "what": b("Coffee stands, sandwiches, pizza, salads during expo days.",
                 "Cà phê, bánh mì, pizza, salad trong ngày triển lãm."),
        "tip": b("Lines are long 12:00–1:00 PM. Eat early (11:30 AM) or late (1:30 PM).",
                "Đông từ 12–1 giờ trưa. Ăn sớm (11:30) hoặc muộn (1:30).")
    }
]

EMERGENCY = {
    "police_fire_ambulance": "911",
    "vietnam_consulate": {
        "location": b("San Francisco, CA", "San Francisco, CA"),
        "phone": "+1 (415) 922-1707",
        "address": "1700 California St, San Francisco, CA 94109"
    },
    "hospitals": [
        {
            "name": "St. Joseph Hospital",
            "phone": "+1 (714) 771-8000",
            "distance": b("4 miles from venue", "6.4 km từ hội nghị"),
            "note": b("Full ER. Accepts international insurance.",
                     "Khoa cấp cứu đầy đủ. Chấp nhận bảo hiểm quốc tế.")
        },
        {
            "name": "UC Irvine Medical Center",
            "phone": "+1 (714) 456-7000",
            "distance": b("5 miles from venue", "8 km từ hội nghị"),
            "note": b("Level 1 trauma center. Best for serious emergencies.",
                     "Trung tâm cấp cứu cấp 1. Tốt nhất cho trường hợp nguy hiểm.")
        }
    ],
    "pharmacy": {
        "name": "CVS Pharmacy",
        "note": b("1120 W Katella Ave, open 24h. Basic meds, first aid, snacks.",
                 "1120 W Katella Ave, mở 24 giờ. Thuốc cơ bản, sơ cứu, ăn nhẹ.")
    },
    "tips": [
        b("Always carry passport copy (physical + photo on phone).",
          "Luôn mang theo bản sao hộ chiếu (bản in + ảnh trên điện thoại)."),
        b("Keep hotel address written on paper in English.",
          "Viết sẵn địa chỉ khách sạn bằng tiếng Anh trên giấy."),
        b("Share live location with colleague via WhatsApp.",
          "Chia sẻ vị trí trực tiếp với đồng nghiệp qua WhatsApp."),
        b("US emergency services speak English only. Say 'I need ambulance.'",
          "Dịch vụ khẩn cấp Mỹ chỉ nói tiếng Anh. Nói 'I need ambulance.'")
    ]
}

ACTIVITIES = [
    {
        "name": b("Disneyland Park", "Công viên Disneyland"),
        "distance": b("0.5 miles from venue", "800 m từ hội nghị"),
        "cost": b("$104–219/day", "$104–219/ngày"),
        "what": b("World-famous theme park. Walking distance. Visit Thursday afternoon or Friday.",
                 "Công viên chủ đề nổi tiếng thế giới. Đi bộ được. Chiều Thứ Năm hoặc Thứ Sáu.")
    },
    {
        "name": b("Downtown Disney District", "Khu Downtown Disney"),
        "distance": b("0.6 miles from venue", "1 km từ hội nghị"),
        "cost": b("FREE to enter", "Vào cửa miễn phí"),
        "what": b("Shopping, dining, live music. No ticket needed. Free evening walk.",
                 "Mua sắm, ăn uống, nhạc sống. Không cần vé. Đi dạo buổi tối miễn phí.")
    },
    {
        "name": b("Little Saigon (Westminster)", "Little Saigon (Westminster)"),
        "distance": b("6 miles (15 min Uber)", "10 km (Uber 15 phút)"),
        "cost": b("FREE to walk, food ~$10–20", "Đi dạo miễn phí, ăn ~$10–20"),
        "what": b("Largest Vietnamese community outside Vietnam. Banh mi, ca phe sua da, Vietnamese supermarkets.",
                 "Cộng đồng người Việt lớn nhất ngoài Việt Nam. Bánh mì, cà phê sữa đá, siêu thị Việt.")
    },
    {
        "name": b("Newport Beach", "Bãi biển Newport"),
        "distance": b("12 miles (20 min Uber)", "19 km (Uber 20 phút)"),
        "cost": b("FREE beach. Parking $2–15", "Bãi biển miễn phí. Đỗ xe $2–15"),
        "what": b("Classic California beach. Pier, boardwalk, fish tacos. Friday relaxation.",
                 "Bãi biển California kinh điển. Cầu tàu, đi bộ dọc biển, fish tacos. Thư giãn Thứ Sáu.")
    }
]


PLACES = [
    {"id": "convention_center", "name": b("Anaheim Convention Center", "Trung tâm Hội nghị Anaheim"),
     "address": "800 W Katella Ave, Anaheim, CA 92802",
     "category": "venue", "transit_note": b("Walk if within 0.5 mi; ART bus line 15, 16.", "Đi bộ nếu <800 m; xe bus ART 15, 16.")},
    {"id": "sna", "name": b("John Wayne Airport (SNA)", "Sân bay John Wayne (SNA)"),
     "address": "18601 Airport Way, Santa Ana, CA 92707",
     "category": "airport", "transit_note": b("Uber/Lyft $35–45 (20 min). OCTA bus 76+change ~1.5h.", "Uber/Lyft $35–45 (20 phút). Xe bus OCTA 76+chuyển ~1.5 giờ.")},
    {"id": "lax", "name": b("Los Angeles International Airport (LAX)", "Sân bay Quốc tế Los Angeles (LAX)"),
     "address": "1 World Way, Los Angeles, CA 90045",
     "category": "airport", "transit_note": b("FlyAway + Metrolink ~2.5h total. Uber/Lyft $70–90 (50–70 min).", "FlyAway + Metrolink ~2.5 giờ. Uber/Lyft $70–90 (50–70 phút).")},
    {"id": "disneyland", "name": b("Disneyland Park", "Công viên Disneyland"),
     "address": "1313 Disneyland Dr, Anaheim, CA 92802",
     "category": "activity", "transit_note": b("ART bus line 15 (10 min). Walk 0.5–1.0 mi from nearby hotels.", "Xe bus ART 15 (10 phút). Đi bộ 0.8–1.6 km từ khách sạn gần.")},
    {"id": "downtown_disney", "name": b("Downtown Disney District", "Khu Downtown Disney"),
     "address": "1585 Disneyland Dr, Anaheim, CA 92802",
     "category": "activity", "transit_note": b("ART bus or walk 0.6 mi from Hilton/Marriott.", "Xe ART hoặc đi bộ 1 km từ Hilton/Marriott.")},
    {"id": "packing_district", "name": b("Anaheim Packing District", "Khu Ẩm thực Anaheim Packing District"),
     "address": "440 S Anaheim Blvd, Anaheim, CA 92805",
     "category": "food", "transit_note": b("ART bus or Uber $8–12 (5–7 min).", "Xe ART hoặc Uber $8–12 (5–7 phút).")},
    {"id": "pho79", "name": b("Pho 79", "Phở 79"),
     "address": "9941 Hazard Ave, Garden Grove, CA 92844",
     "category": "food", "transit_note": b("Uber $12–15 (10–12 min). OCTA bus 25 + walk.", "Uber $12–15 (10–12 phút). Xe bus OCTA 25 + đi bộ.")},
    {"id": "newport_beach", "name": b("Newport Beach", "Bãi biển Newport"),
     "address": "Newport Beach, CA 92663",
     "category": "activity", "transit_note": b("OCTA bus 1 or 47 (~45 min). Uber $25–35 (20 min).", "Xe bus OCTA 1 hoặc 47 (~45 phút). Uber $25–35 (20 phút).")},
    {"id": "little_saigon", "name": b("Little Saigon (Westminster)", "Little Saigon (Westminster)"),
     "address": "Bolsa Ave, Westminster, CA 92683",
     "category": "food", "transit_note": b("OCTA bus 25 or 54 (~30 min). Uber $15–20 (15 min).", "Xe bus OCTA 25 hoặc 54 (~30 phút). Uber $15–20 (15 phút).")},
    {"id": "st_joseph", "name": b("St. Joseph Hospital", "Bệnh viện St. Joseph"),
     "address": "1100 W Stewart Dr, Orange, CA 92868",
     "category": "emergency", "transit_note": b("Uber $12–18 (10–15 min). OCTA bus 57.", "Uber $12–18 (10–15 phút). Xe bus OCTA 57.")},
    {"id": "uc_irvine", "name": b("UC Irvine Medical Center", "Trung tâm Y tế UC Irvine"),
     "address": "101 The City Dr S, Orange, CA 92868",
     "category": "emergency", "transit_note": b("Uber $14–20 (12–18 min). OCTA bus 57 + 79.", "Uber $14–20 (12–18 phút). Xe bus OCTA 57 + 79.")},
    {"id": "cvs", "name": b("CVS Pharmacy (24h)", "Nhà thuốc CVS (24 giờ)"),
     "address": "1120 W Katella Ave, Orange, CA 92867",
     "category": "pharmacy", "transit_note": b("Walk if near Katella Ave; otherwise ART bus.", "Đi bộ nếu gần Katella Ave; không thì xe ART.")},
    {"id": "hilton", "name": b("Hilton Anaheim", "Khách sạn Hilton Anaheim"),
     "address": "777 Convention Way, Anaheim, CA 92802",
     "category": "hotel", "transit_note": b("Next to convention center.", "Sát bên trung tâm hội nghị.")},
    {"id": "marriott", "name": b("Anaheim Marriott", "Khách sạn Anaheim Marriott"),
     "address": "700 W Convention Way, Anaheim, CA 92802",
     "category": "hotel", "transit_note": b("Connected via pedestrian bridge.", "Nối bằng cầu đi bộ.")},
    {"id": "courtyard", "name": b("Courtyard by Marriott", "Courtyard by Marriott"),
     "address": "2045 S Harbor Blvd, Anaheim, CA 92802",
     "category": "hotel", "transit_note": b("ART bus or Uber $6–8 to venue.", "Xe ART hoặc Uber $6–8 đến hội nghị.")},
    {"id": "bestwestern", "name": b("Best Western Plus Anaheim Inn", "Best Western Plus Anaheim Inn"),
     "address": "1630 S Harbor Blvd, Anaheim, CA 92802",
     "category": "hotel", "transit_note": b("ART bus line 15 or walk 20 min.", "Xe bus ART 15 hoặc đi bộ 20 phút.")},
]

# Map hotel ID to the corresponding place ID
HOTEL_PLACE_MAP = {
    "hilton anaheim": "hilton",
    "anaheim marriott": "marriott",
    "courtyard by marriott": "courtyard",
    "best western plus anaheim inn": "bestwestern",
}

def hotel_connections(hotel_name):
    hotel_key = hotel_name.lower().strip()
    place_id = HOTEL_PLACE_MAP.get(hotel_key)
    if not place_id:
        return []
    hotel_addr = next((p for p in PLACES if p["id"] == place_id), None)
    if not hotel_addr:
        return []
    results = []
    for place in PLACES:
        if place["id"] == place_id:
            continue
        # Build Google Maps transit directions link
        gmaps = f"https://www.google.com/maps/dir/?api=1&origin={hotel_addr['address']}&destination={place['address']}&travelmode=transit"
        results.append({
            "place_id": place["id"],
            "place_name": place["name"],
            "category": place["category"],
            "address": place["address"],
            "transit_note": place["transit_note"],
            "google_maps_transit_url": gmaps,
        })
    return results

DAILY_PLAN = [
    {
        "day": b("Day 0 — Sat Jul 25", "Ngày 0 — Thứ 7, 25/7"),
        "title": b("Arrival & Settle", "Đến nơi & Ổn định"),
        "morning": b("Land at SNA or LAX. Collect luggage. Clear customs.", "Đáp xuống SNA hoặc LAX. Nhận hành lý. Làm thủ tục hải quan."),
        "afternoon": b("Uber/Lyft to hotel. Check in. Rest after long flight.", "Uber/Lyft vào khách sạn. Nhận phòng. Nghỉ sau chuyến bay dài."),
        "evening": b("Walk to Downtown Disney (free). Dinner at Naples ($20). Early sleep.", "Đi bộ qua Downtown Disney (miễn phí). Ăn tối Naples ($20). Ngủ sớm."),
        "budget": "$60–75",
        "priority": "rest"
    },
    {
        "day": b("Day 1 — Sun Jul 26", "Ngày 1 — Chủ nhật, 26/7"),
        "title": b("Registration & Welcome Mixer", "Đăng ký & Tiệc chào đón"),
        "morning": b("Late breakfast at hotel. Explore Anaheim area.", "Bữa sáng muộn tại khách sạn. Khám phá khu vực Anaheim."),
        "afternoon": b("Convention Center registration. Pick up badge. Walk Expo floor preview.", "Đăng ký tại Trung tâm Hội nghị. Nhận thẻ. Ngắm sàn triển lãm."),
        "evening": b("Opening Mixer 6:30–8:00 PM at Arena Plaza. Free food + networking.", "Tiệc chào đón 6:30–8:00 tối tại Arena Plaza. Ăn miễn phí + gặp gỡ."),
        "budget": "$20–30",
        "priority": "high"
    },
    {
        "day": b("Day 2 — Mon Jul 27", "Ngày 2 — Thứ Hai, 27/7"),
        "title": b("Educational Sessions", "Các Buổi Học"),
        "morning": b("Breakfast. Attend morning educational sessions.", "Bữa sáng. Tham dự các buổi học buổi sáng."),
        "afternoon": b("Workshops and short courses. Visit expo floor between sessions.", "Hội thảo và khóa học ngắn. Ghé sàn triển lãm giữa buổi."),
        "evening": b("Dinner at Packing District ($15). Explore food hall with colleague.", "Ăn tối tại Packing District ($15). Khám phá khu ẩm thực với đồng nghiệp."),
        "budget": "$30–40",
        "priority": "medium"
    },
    {
        "day": b("Day 3 — Tue Jul 28", "Ngày 3 — Thứ Ba, 28/7"),
        "title": b("Expo Day 1 + YOUR POSTER", "Ngày Triển lãm 1 + POSTER CỦA BẠN"),
        "morning": b("Early breakfast. Review poster setup time. Morning expo sessions.", "Bữa sáng sớm. Xem giờ dựng poster. Các buổi triển lãm sáng."),
        "afternoon": b("YOUR POSTER PRESENTATION. Stand by poster. Speak with visitors. Take notes.", "TRÌNH BÀY POSTER CỦA BẠN. Đứng tại poster. Nói chuyện với khách. Ghi chú."),
        "evening": b("Celebrate! Dinner at In-N-Out ($10) or Vietnamese pho ($15).", "Ăn mừng! Ăn In-N-Out ($10) hoặc phở Việt ($15)."),
        "budget": "$30–40",
        "priority": "high"
    },
    {
        "day": b("Day 4 — Wed Jul 29", "Ngày 4 — Thứ Tư, 29/7"),
        "title": b("Expo Day 2", "Ngày Triển lãm 2"),
        "morning": b("Breakfast. Visit other posters. Morning expo.", "Bữa sáng. Xem poster người khác. Triển lãm buổi sáng."),
        "afternoon": b("Industry presentations. Networking lunch.", "Các buổi trình bày của doanh nghiep. Bữa trưa gặp gỡ."),
        "evening": b("Dinner at hotel or Downtown Disney. Pack belongings.", "Ăn tối tại khách sạn hoặc Downtown Disney. Thu dọn hành lý."),
        "budget": "$30–40",
        "priority": "high"
    },
    {
        "day": b("Day 5 — Thu Jul 30", "Ngày 5 — Thứ Năm, 30/7"),
        "title": b("Final Expo Morning + Free Time", "Buổi Sáng Triển lãm Cuối + Tự Do"),
        "morning": b("Expo ends at noon. Final booth visits. Collect contacts.", "Triển lãm kết thúc trưa. Ghé thăm cuối. Thu thập danh bạ."),
        "afternoon": b("Checkout hotel (or extend). Afternoon free.", "Trả phòng (hoặc kéo dài). Buổi chiều tự do."),
        "evening": b("Optional: Disneyland evening (ticket ~$150) or rest.", "Tùy chọn: Tối Disneyland (vé ~$150) hoặc nghỉ."),
        "budget": "$10–50",
        "priority": "medium"
    },
    {
        "day": b("Day 6 — Fri Jul 31", "Ngày 6 — Thứ Sáu, 31/7"),
        "title": b("Departure", "Về Nước"),
        "morning": b("Hotel checkout. Uber/shuttle to SNA (~$35).", "Trả phòng. Uber/shuttle ra SNA (~$35)."),
        "afternoon": b("Fly home to Vietnam.", "Bay về Việt Nam."),
        "evening": b("In transit.", "Trên đường bay."),
        "budget": "$40–60",
        "priority": "low"
    }
]

LINKS = {
    "adlm": "https://myadlm.org",
    "venue": "https://www.anaheimconventioncenter.com",
    "flyaway": "https://www.flylax.com/flyaway-bus",
    "flyaway_app": "https://apps.apple.com/us/app/lax-flyaway/id6443780499",
    "primetime": "https://primetimeshuttle.com",
    "uber": "https://www.uber.com",
    "lyft": "https://www.lyft.com",
    "disneyland": "https://disneyland.disney.go.com",
    "esta": "https://esta.cbp.dhs.gov",
    "metrolink": "https://www.metrolinktrains.com"
}

# ---------- OLLAMA CHATBOT ----------

APP_CONTEXT = """
You are the Anaheim Travel Guide Assistant for ADLM 2026. You help a Vietnamese traveler attending the ADLM 2026 Annual Meeting & Clinical Lab Expo in Anaheim, California (July 26-30, 2026).

EVENT:
- Venue: Anaheim Convention Center, 800 W Katella Ave, Anaheim, CA 92802
- Expo: July 28-30, 2026 (9:30 AM – 5:00 PM, Thursday ends at noon)
- Opening Mixer: Sunday July 26, 6:30-8:00 PM at Arena Plaza
- Poster sessions: likely Tuesday-Wednesday afternoon
- Budget: ~$50 per person per day for 2 people

AIRPORTS:
- Recommended: SNA (John Wayne Airport) — 15-20 min, $35-45 Uber
- Alternative: LAX — 45-90 min, $70-90 Uber

TRANSPORT:
1. Uber/Lyft: door-to-door, Vietnam phone works, add Visa/MasterCard
2. Prime Time Shuttle: primetimeshuttle.com, pre-book, fixed price
3. Public transit: OCTA bus ~$2 (slow), or FlyAway + Metrolink ~$24 (2.5h from LAX)

HOTELS (nearest to farthest):
1. Hilton Anaheim — 777 Convention Way, $170-220/night, 3 min walk, official hotel
2. Anaheim Marriott — 700 W Convention Way, $150-200/night, 5 min walk, pedestrian bridge
3. Courtyard by Marriott — 2045 S Harbor Blvd, $120-160/night, 15 min walk / 5 min Uber
4. Best Western Plus Anaheim Inn — 1630 S Harbor Blvd, $100-140/night, 20 min walk / 7 min Uber

FOOD:
- Anaheim Packing District: 440 S Anaheim Blvd, food hall, $12-18, open until 10 PM
- In-N-Out Burger: 1168 State College Blvd, $8-12, order "Animal Style"
- Pho 79 (Vietnamese): 9941 Hazard Ave, Garden Grove, $12-16, open until 9 PM
- Chipotle/McDonald's/Subway: walkable, $8-12
- Convention Center Food Court: inside venue, $14-20, busy 12-1 PM

ACTIVITIES:
- Disneyland Park: 0.5 miles, $104-219/day
- Downtown Disney: 0.6 miles, FREE entry
- Little Saigon (Westminster): 6 miles, Vietnamese community
- Newport Beach: 12 miles, FREE beach

EMERGENCY:
- 911 for police/fire/ambulance
- Vietnam Consulate: +1 (415) 922-1707, San Francisco
- St. Joseph Hospital: +1 (714) 771-8000, 4 miles, full ER
- UC Irvine Medical Center: +1 (714) 456-7000, 5 miles, Level 1 trauma
- CVS Pharmacy 24h: 1120 W Katella Ave

CRITICAL RULES:
- ALWAYS reply in VIETNAMESE only, regardless of the user's language.
- Use markdown formatting: **bold** for emphasis, bullet points (- ) for lists.
- Keep responses structured: start with a brief summary paragraph, then bullet points if needed.
- Be SHORT and PRECISE. Maximum 3-4 sentences for simple questions. Only expand if the user asks for detail.
- If the user mentions they are lost, ask for their destination and use navigation data to give precise turn-by-turn directions.
- Always offer to open Google Maps for the final leg.
"""

def ollama_chat(user_message, conversation_history=None):
    if not OLLAMA_API_KEY:
        return {"reply": "Chatbot is offline (no API key configured).", "lang": "en"}
    messages = [{"role": "system", "content": APP_CONTEXT}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})
    url = f"{OLLAMA_BASE_URL}/chat"
    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        reply = data.get("message", {}).get("content", "")
        if not reply:
            reply = data.get("response", "")
        return {"reply": reply.strip(), "lang": "auto"}
    except Exception as e:
        return {"reply": f"Sorry, I could not reach the AI server. Error: {str(e)}", "lang": "en"}

# ---------- OSRM NAVIGATION ----------

KNOWN_DESTINATIONS = {
    "convention center": (33.8003, -117.9216),
    "anaheim convention center": (33.8003, -117.9216),
    "hilton anaheim": (33.8020, -117.9180),
    "anaheim marriott": (33.8010, -117.9190),
    "courtyard by marriott": (33.7920, -117.9140),
    "best western plus anaheim inn": (33.7880, -117.9150),
    "sna": (33.6757, -117.8682),
    "john wayne airport": (33.6757, -117.8682),
    "lax": (33.9416, -118.4085),
    "los angeles international airport": (33.9416, -118.4085),
    "disneyland": (33.8121, -117.9190),
    "downtown disney": (33.8090, -117.9190),
    "packing district": (33.8310, -117.9120),
    "anaheim packing district": (33.8310, -117.9120),
    "in-n-out": (33.8440, -117.9250),
    "pho 79": (33.7740, -117.9360),
    "little saigon": (33.7390, -117.9600),
    "newport beach": (33.6189, -117.9298),
    "st joseph hospital": (33.7780, -117.8600),
    "uc irvine medical center": (33.7750, -117.8460),
    "cvs pharmacy": (33.8030, -117.9210),
}

def geocode_destination(query):
    q = query.lower().strip().rstrip(".?")
    if q in KNOWN_DESTINATIONS:
        return KNOWN_DESTINATIONS[q]
    # Fallback to Nominatim geocoding
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": query + ", Anaheim, CA, USA", "format": "json", "limit": 1}
        headers = {"User-Agent": "AnaheimGuideBot/1.0"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data:
            return (float(data[0]["lat"]), float(data[0]["lon"]))
    except Exception:
        pass
    return None

def osrm_route(start_lat, start_lon, end_lat, end_lon):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
        params = {"overview": "false", "steps": "true", "geometries": "geojson"}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        if data.get("code") != "Ok":
            return None
        route = data["routes"][0]
        legs = route["legs"][0]
        steps = []
        for step in legs.get("steps", []):
            dist_m = step.get("distance", 0)
            duration_s = step.get("duration", 0)
            instruction = step.get("name", "")
            maneuver = step.get("maneuver", {})
            maneuver_type = maneuver.get("type", "")
            modifier = maneuver.get("modifier", "")
            # Build human instruction
            instr = ""
            if maneuver_type == "depart":
                instr = f"Head {modifier or 'straight'} on {instruction}"
            elif maneuver_type == "turn":
                instr = f"Turn {modifier} onto {instruction}"
            elif maneuver_type == "continue":
                instr = f"Continue on {instruction}"
            elif maneuver_type == " roundabout":
                instr = f"Enter roundabout and take exit onto {instruction}"
            elif "roundabout" in maneuver_type:
                instr = f"At roundabout, take exit onto {instruction}"
            elif maneuver_type == "arrive":
                instr = f"Arrive at destination"
            else:
                instr = f"{maneuver_type.replace('_',' ').title()} {modifier} onto {instruction}"
            steps.append({
                "instruction": instr,
                "distance_m": round(dist_m, 1),
                "distance_text": f"{dist_m:.0f} m" if dist_m < 1000 else f"{dist_m/1000:.1f} km",
                "duration_s": round(duration_s, 1),
                "duration_text": f"{duration_s/60:.0f} min" if duration_s < 3600 else f"{duration_s/3600:.1f} h",
            })
        return {
            "total_distance_m": route["distance"],
            "total_distance_text": f"{route['distance']/1000:.1f} km",
            "total_duration_s": route["duration"],
            "total_duration_text": f"{route['duration']/60:.0f} min" if route["duration"] < 3600 else f"{route['duration']/3600:.1f} h",
            "steps": steps,
        }
    except Exception as e:
        return {"error": str(e)}


import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Anaheim Convention Center approximate center
ANAHEIM_LAT, ANAHEIM_LON = 33.8003, -117.9216
MAX_ROUTE_KM = 300  # reject if start is >300 km from Anaheim (prevents cross-continent routing)

# ---------- ROUTES ----------

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/overview')
def api_overview():
    return jsonify(TRIP_OVERVIEW)

@app.route('/api/airport')
def api_airport():
    return jsonify(AIRPORT_DATA)

@app.route('/api/transport')
def api_transport():
    return jsonify(TRANSPORT_OPTIONS)

@app.route('/api/hotels')
def api_hotels():
    return jsonify(HOTELS)

@app.route('/api/schedule')
def api_schedule():
    return jsonify(SCHEDULE)

@app.route('/api/food')
def api_food():
    return jsonify(FOOD)

@app.route('/api/emergency')
def api_emergency():
    return jsonify(EMERGENCY)

@app.route('/api/activities')
def api_activities():
    return jsonify(ACTIVITIES)

@app.route('/api/daily-plan')
def api_daily_plan():
    return jsonify(DAILY_PLAN)

@app.route('/api/links')
def api_links():
    return jsonify(LINKS)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json(force=True, silent=True) or {}
    user_msg = data.get("message", "")
    history = data.get("history", [])
    result = ollama_chat(user_msg, history)
    return jsonify(result)

@app.route('/api/navigate', methods=['POST'])
def api_navigate():
    data = request.get_json(force=True, silent=True) or {}
    start_lat = data.get("lat")
    start_lon = data.get("lon")
    destination = data.get("destination", "")
    lang = data.get("lang", "en")

    if start_lat is None or start_lon is None:
        return jsonify({"error": "Missing GPS coordinates. Please enable location services."}), 400
    if not destination:
        return jsonify({"error": "Missing destination."}), 400

    # Distance guard: do not route if user is nowhere near Anaheim (e.g. overseas)
    try:
        dist_km = haversine(float(start_lat), float(start_lon), ANAHEIM_LAT, ANAHEIM_LON)
        if dist_km > MAX_ROUTE_KM:
            return jsonify({"error": f"GPS position is too far from Anaheim ({dist_km:.0f} km). Turn-by-turn navigation only works when you are in the Anaheim area."}), 400
    except Exception:
        pass

    end = geocode_destination(destination)
    if not end:
        return jsonify({"error": f"Could not find destination: {destination}"}), 400

    route = osrm_route(float(start_lat), float(start_lon), end[0], end[1])
    if not route or "error" in route:
        return jsonify({"error": route.get("error", "Routing failed.")}), 500

    # Build directions prompt for Ollama to format nicely
    steps_summary = "\n".join(
        f"{i+1}. {s['instruction']} — {s['distance_text']} ({s['duration_text']})"
        for i, s in enumerate(route["steps"])
    )
    prompt = (
        f"The user is currently at GPS coordinates ({start_lat}, {start_lon}) and wants to go to '{destination}'.\n"
        f"OSRM routing data:\n"
        f"Total: {route['total_distance_text']} — {route['total_duration_text']}\n"
        f"Steps:\n{steps_summary}\n\n"
        f"Please provide a friendly, precise, step-by-step navigation guide in {'Vietnamese' if lang=='vi' else 'English'}. "
        f"Start with the total distance and estimated time. Then list each turn with exact street names and distances. "
        f"End with an encouragement message. Mention that the user can tap 'Open in Maps' for live GPS tracking."
    )

    ai_result = ollama_chat(prompt)
    return jsonify({
        "directions": route,
        "formatted": ai_result.get("reply", ""),
        "destination_coords": end,
        "google_maps_url": f"https://www.google.com/maps/dir/?api=1&origin={start_lat},{start_lon}&destination={end[0]},{end[1]}"
    })

@app.route('/api/chat/stream', methods=['POST'])
def api_chat_stream():
    data = request.get_json(force=True, silent=True) or {}
    user_msg = data.get("message", "")
    history = data.get("history", [])
    
    def generate():
        if not OLLAMA_API_KEY:
            yield json.dumps({"error": "Chatbot is offline (no API key configured)."}) + "\n"
            return
        
        messages = [{"role": "system", "content": APP_CONTEXT}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_msg})
        
        url = f"{OLLAMA_BASE_URL}/chat"
        headers = {
            "Authorization": f"Bearer {OLLAMA_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": True,
        }
        
        try:
            with requests.post(url, headers=headers, json=payload, stream=True, timeout=120) as resp:
                resp.raise_for_status()
                for raw_line in resp.iter_lines():
                    if raw_line:
                        try:
                            chunk = json.loads(raw_line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield json.dumps({"token": content}) + "\n"
                        except Exception:
                            pass
                yield json.dumps({"done": True}) + "\n"
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"
    
    return Response(generate(), mimetype='application/x-ndjson')

@app.route('/api/connections')
def api_connections():
    hotel = request.args.get("hotel", "").lower().strip()
    data = hotel_connections(hotel)
    return jsonify({"hotel": hotel, "connections": data})

@app.route('/health')
def health():
    return jsonify({"status": "ok", "chatbot": bool(OLLAMA_API_KEY)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)