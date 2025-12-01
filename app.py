from flask import Flask, render_template, redirect, session, request
from functools import wraps
import pymongo
import os
import ssl
import random

app = Flask(__name__)
app.secret_key=b'\xf3\xc0\xcd\x1c\x147\x96C\xecf\xdf\x02H\x1c\xa6\xa6'



CONNECTION_STRING = os.getenv("STRING")
client = pymongo.MongoClient(CONNECTION_STRING)
db = client.thirukkural_pazhagu

#Decorators
def login_required(f):
    @wraps(f)
    def wrap(*arg, **kwargs):
        if'logged_in' in session:
            return f(*arg, **kwargs)
        else:
            return redirect('/')
    return wrap

#Routes
from user import routes

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register/')
def register():
    return render_template('register.html')


@app.route('/index/')
@login_required
def index():
    # Fetch current user data from DB to ensure fresh stats
    user_email = session['user']['email']
    current_user = db.user_details.find_one({"email": user_email})
    
    # Calculate learnt kural count from DB data
    learnt_kural_count = 0
    if current_user and 'points' in current_user:
        for adhigaram in current_user['points']['stars']['kurals_completed']:
            for kural_stars in adhigaram:
                if kural_stars > 0:
                    learnt_kural_count += 1
    
    # Fetch Leaderboard (Top 5 by diamond points)
    leaderboard = []
    try:
        pipeline = [
            {"$addFields": {"total_diamonds": "$points.diamonds.total"}},
            {"$sort": {"total_diamonds": -1}},
            {"$limit": 5}
        ]
        top_users = list(db.user_details.aggregate(pipeline))
        for idx, user in enumerate(top_users, 1):
            leaderboard.append({
                "rank": idx,
                "name": user.get('name', 'Unknown'),
                "points": user.get('points', {}).get('diamonds', {}).get('total', 0)
            })
    except Exception as e:
        print(f"Error fetching leaderboard: {e}")

    # Get other stats from DB data
    streak = current_user.get('current_streak', 0) if current_user else 0
    last_adhigaram = current_user.get('last_accessed_adhigaram', 'கடவுள் வாழ்த்து') if current_user else 'கடவுள் வாழ்த்து'

    return render_template('index.html', 
                           learnt_kural_count=learnt_kural_count,
                           leaderboard=leaderboard,
                           streak=streak,
                           last_adhigaram=last_adhigaram)

@app.route('/select_adhigaram')
@login_required
def select_adhigaram():
    return render_template('select_adhigaram.html')


@app.route('/select_game')
@login_required
def select_game():
    return render_template('select_game.html')


@app.route('/test_dashboard')
@login_required
def test_dashboard():
    # Fetch all adhigarams
    adhigarams = list(db.adhigaram_data.find({}, {"_id": 0, "adhigaram_id": 1, "adhigaram": 1}).sort("adhigaram_id", 1))
    
    # Fetch user progress
    user_email = session['user']['email']
    current_user = db.user_details.find_one({"email": user_email})
    
    adhigaram_progress = {}
    if current_user and 'points' in current_user:
        kurals_completed = current_user['points']['stars']['kurals_completed']
        for i, adhigaram_stars in enumerate(kurals_completed):
            # adhigaram_id is i + 1
            learned_count = sum(1 for stars in adhigaram_stars if stars > 0)
            adhigaram_progress[i + 1] = learned_count
            
    return render_template('test_dashboard.html', adhigarams=adhigarams, progress=adhigaram_progress)

@app.route('/take_adhigaram_test/<int:adhigaram_id>')
@login_required
def take_adhigaram_test(adhigaram_id):
    # Verify if unlocked
    user_email = session['user']['email']
    current_user = db.user_details.find_one({"email": user_email})
    
    if current_user and 'points' in current_user:
        kurals_completed = current_user['points']['stars']['kurals_completed']
        # adhigaram_id is 1-based, list is 0-based
        if adhigaram_id < 1 or adhigaram_id > 133:
             return redirect('/test_dashboard')
             
        adhigaram_stars = kurals_completed[adhigaram_id - 1]
        learned_count = sum(1 for stars in adhigaram_stars if stars > 0)
        
        if learned_count < 10:
            return redirect('/test_dashboard') # Locked
            
        # Generate Test (3 Questions)
        # We will use a helper method in kural.py or inline here. Inline for simplicity first.
        # Fetch 3 random kurals from this adhigaram
        kural_start = (adhigaram_id - 1) * 10 + 1
        kural_end = adhigaram_id * 10
        
        # Select 3 distinct random kural IDs
        test_kural_ids = random.sample(range(kural_start, kural_end + 1), 3)
        
        questions = []
        kural_data_coll = db['kural_data']
        
        for k_id in test_kural_ids:
            kural_data = kural_data_coll.find_one({"kural_id": k_id})
            if kural_data:
                # Create a Fillups question (simplest for now)
                # Split kural into words
                lines = kural_data['kural']
                words = lines[0][0].split() + lines[1][0].split()
                
                # Remove empty strings
                words = [w for w in words if w.strip()]
                
                if len(words) > 2:
                    missing_idx = random.randint(0, len(words) - 1)
                    missing_word = words[missing_idx]
                    words[missing_idx] = "__________"
                    
                    # Generate options (1 correct + 3 wrong)
                    # For wrong options, pick random words from same adhigaram or generic list
                    # For simplicity, using a generic list + shuffle
                    wrong_options = ["அறம்", "பொருள்", "இன்பம்", "வீடு", "உலகம்", "மக்கள்", "அன்பு", "பண்பு"]
                    options = random.sample(wrong_options, 3)
                    options.append(missing_word)
                    random.shuffle(options)
                    
                    questions.append({
                        "id": k_id,
                        "type": "fillups",
                        "question_text": " ".join(words),
                        "options": options,
                        "correct_answer": missing_word,
                        "porul": kural_data.get('porul', '')
                    })
        
        # Store questions in session to verify answers later
        session['current_test'] = {
            "adhigaram_id": adhigaram_id,
            "questions": questions
        }
        
        return render_template('take_adhigaram_test.html', adhigaram_id=adhigaram_id, questions=questions)
            
    return redirect('/test_dashboard')

@app.route('/submit_adhigaram_test', methods=['POST'])
@login_required
def submit_adhigaram_test():
    if 'current_test' not in session:
        return redirect('/test_dashboard')
        
    test_data = session['current_test']
    questions = test_data['questions']
    score = 0
    total = len(questions)
    
    results = []
    
    for i, q in enumerate(questions):
        user_answer = request.form.get(f'answer_{i}')
        is_correct = user_answer == q['correct_answer']
        if is_correct:
            score += 1
        results.append({
            "question": q['question_text'],
            "user_answer": user_answer,
            "correct_answer": q['correct_answer'],
            "is_correct": is_correct,
            "porul": q['porul']
        })
        
    # Generate Report
    percentage = (score / total) * 100
    recommendation = ""
    if percentage == 100:
        recommendation = "மிகச்சிறப்பு! நீங்கள் இந்த அதிகாரத்தை முழுமையாகக் கற்றுவிட்டீர்கள். (Excellent! You have mastered this Adhigaram.)"
    elif percentage >= 60:
        recommendation = "நன்று! இன்னும் சிறிது பயிற்சி தேவை. (Good! A little more practice is needed.)"
    else:
        recommendation = "மேலும் பயிற்சி தேவை. குறள்களை மீண்டும் படிக்கவும். (More practice needed. Please review the Kurals.)"
        
    return render_template('test_report.html', 
                           score=score, 
                           total=total, 
                           results=results, 
                           recommendation=recommendation,
                           adhigaram_id=test_data['adhigaram_id'])
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host="0.0.0.0", port=port)
