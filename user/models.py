from flask import Flask, jsonify, request, session, redirect
from passlib.hash import pbkdf2_sha256
from app import db
import uuid


from datetime import datetime, timedelta

class User:
    def start_session(self, user):
        if 'password' in user:
            del user['password']
        session['logged_in'] = True
        session['user'] = user
        # Ensure session has the new fields even if DB doesn't (for old users)
        if 'current_streak' not in session['user']:
            session['user']['current_streak'] = 0
        if 'last_accessed_adhigaram' not in session['user']:
            session['user']['last_accessed_adhigaram'] = "கடவுள் வாழ்த்து" # Default
            
        print(user)
        return jsonify(user), 200

    def signup(self):
        print(request.form)

        # creating user object
        kuralList = [[0]*10 for _ in range(133)]
        adhigaramList = [0]*133
        
        user = {
            "_id": uuid.uuid4().hex,
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "password": request.form.get('password'),
            "cpassword": request.form.get('cpassword'),
            "points":{
                "stars":{
                    "total" : 0,
                    "kurals_completed": list(kuralList)
                },
                "diamonds":{
                    "total" : 0,
                    "drag_drop":list(adhigaramList),
                    "fillups":list(adhigaramList)
                }
            },
            "last_login_date": datetime.now().strftime("%Y-%m-%d"),
            "current_streak": 1,
            "last_accessed_adhigaram": "கடவுள் வாழ்த்து"
        }

        # Password Encryption
        user['password'] = pbkdf2_sha256.encrypt(user['password'])
        # user['cpassword'] = user['password']

        # check for existing email id
        if db.user_details.find_one({"email": user['email']}):
            return jsonify({"error": "Email already exists"}), 400

        if db.user_details.insert_one(user):
            return self.start_session(user)

        return jsonify({"error": "Signup failed"}), 400

    def signout(self):
        session.clear()
        return redirect('/')

    def login(self):
        user = db.user_details.find_one({"email": request.form.get('email')})

        if user and pbkdf2_sha256.verify(request.form.get('password'), user['password']):
            # Update Streak Logic
            today = datetime.now().strftime("%Y-%m-%d")
            last_login = user.get('last_login_date')
            current_streak = user.get('current_streak', 0)
            
            if last_login != today:
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                if last_login == yesterday:
                    current_streak += 1
                else:
                    current_streak = 1 # Reset streak if missed a day (or first time with new logic)
                
                # Update DB
                db.user_details.update_one(
                    {"_id": user["_id"]},
                    {"$set": {
                        "last_login_date": today,
                        "current_streak": current_streak
                    }}
                )
                user['last_login_date'] = today
                user['current_streak'] = current_streak
            
            return self.start_session(user)

        return jsonify({"error": "மின்னஞ்சல் அல்லது கடவுச்சொல் தவறு"}), 401
