from flask import Flask, json, jsonify, request, redirect, render_template, session
from app import db
import random
import time
import uuid
from datetime import datetime
from ngram_model import get_model


class kural:
    def fetchKural(self):
        if request.method == "POST":
            select_adhigaram = request.form.get('select_adhigaram')
            adhigaram_data = db['adhigaram_data']
            query = {"adhigaram": select_adhigaram}
            adhigaram = adhigaram_data.find(
                query, {"_id": 0, "adhigaram_id": 1})
            adhigaram_list = list(adhigaram)
            
            # Update last accessed adhigaram
            session['user']['last_accessed_adhigaram'] = select_adhigaram
            db.user_details.update_one(
                {"email": session['user']['email']},
                {"$set": {"last_accessed_adhigaram": select_adhigaram}}
            )
            session.modified = True
            
            return jsonify({"adhigaram_id": adhigaram_list[0]["adhigaram_id"]}), 200

    def learn_thirukkural(self):
        if request.method == "GET":
            kuralId = request.args.get("kuralId")
            kural_data = db['kural_data']
            query = {"kural_id": int(kuralId)}
            return render_template('learn_thirukkural.html', kural=kural_data.find_one(query))

    def selected_game(self):
        if request.method == "POST":
            select_adhigaram = request.form.get('select_adhigaram')
            random_kural = request.form.get('random_kural')
            game_type = request.form.get('game_type')
            error = ''
            if((select_adhigaram == '' and random_kural == None) or game_type == None):

                if(game_type == None):
                    error = '*விளையாட்டை தேர்வுசெய்க '
                else:
                    error = '*அதிகாரம் தேர்வுசெய்க'
                return jsonify({"error": error}), 401
            
            adhigaramNumber = 0
            if(random_kural != None):
                adhigaramNumber = random.randint(1, 133)

            elif(select_adhigaram != ''):
                adhigaram_data = db['adhigaram_data']
                #select_adhigaram = select_adhigaram.strip()
                query = {"adhigaram": select_adhigaram}
                print(select_adhigaram)

                adhigaram = adhigaram_data.find(
                    query, {"_id": 0, "adhigaram_id": 1})
                adhigaram_list = list(adhigaram)
                print(adhigaram_list)
                #kuralStarList = session['user']['points']['stars']['kurals_completed'][int(adhigaram_list[0]["adhigaram_id"]-1)]
                adhigaramNumber = adhigaram_list[0]['adhigaram_id']
                # for star in kuralStarList:
                #     if star == 0:
                #         error = '*'+select_adhigaram + \
                #             ' அதிகாரத்திலுள்ள அணைத்து குறள்களையும் கற்ற பின் விளையாடலாம்'
                #         return jsonify({"error": error}), 401
            

            """adhigaram_data = db['adhigaram_data']
            query = {"adhigaram": select_adhigaram}
            adhigaram = adhigaram_data.find(
                query, {"_id": 0, "adhigaram_id": 1})
            adhigaram_list = list(adhigaram)
            print(adhigaram_list)
            adhigaramNumber = adhigaram_list[0]['adhigaram_id'] """
             #Calculate the correct Kural ID
            kural_start = (adhigaramNumber - 1) * 10 + 1
            kural_end = adhigaramNumber * 10
            kuralNumber = random.randint(kural_start, kural_end)


            query = {"kural_id": int(kuralNumber)}
            return jsonify({"kuralId": str(kuralNumber), "site": game_type}), 200

    def drag_drop_game(self):
        if request.method == "GET":
            kuralId = request.args.get("kuralId")
            kural_data = db['kural_data']
            query = {"kural_id": int(kuralId)}
            kuralData = kural_data.find_one(query)
            kuralWordsList = kuralData['kural'][0][0].split(
            ) + kuralData['kural'][1][0].split()
            random.shuffle(kuralWordsList)
            return render_template('drag_drop_game.html', kuralWord=kuralWordsList, porul=kuralData['porul'], kuralId=kuralId)

    def evaluate_drag_game(self):
        if request.method == "POST":
            userAssignedKural = []
            userAssignedKural.append(request.form.get("word1"))
            userAssignedKural.append(request.form.get("word2"))
            userAssignedKural.append(request.form.get("word3"))
            userAssignedKural.append(request.form.get("word4"))
            userAssignedKural.append(request.form.get("word5"))
            userAssignedKural.append(request.form.get("word6"))
            userAssignedKural.append(request.form.get("word7"))
            kuralId = request.form.get("kuralId")
            kural_data = db['kural_data']
            query = {"kural_id": int(kuralId)}
            kuralData = kural_data.find_one(query)
            kuralWordsList = kuralData['kural'][0][0].split(
            ) + kuralData['kural'][1][0].split()
            diamonds = 0
            correctOrder = 0
            if(userAssignedKural == kuralWordsList):
                diamonds = 3
            else:
                for i in range(0, 7):
                    if(userAssignedKural[i] == kuralWordsList[i]):
                        correctOrder += 1

                if(correctOrder > 0 and correctOrder <= 3):
                    diamonds = 1
                elif(correctOrder > 3 and correctOrder <= 6):
                    diamonds = 2
                else:
                    diamonds = 0

            if (diamonds > 0):
                adhigaram_number = str((int(kuralId) - 1) // 10)
                total = 0
                if (int(session['user']['points']['diamonds']['drag_drop'][int(adhigaram_number)]) < int(session['user']['points']['diamonds']['total']) + diamonds):
                    total = (int(session['user']['points']['diamonds']['total']) + diamonds) - int(
                        session['user']['points']['diamonds']['drag_drop'][int(adhigaram_number)])
                else:
                    total = int(session['user']['points']['diamonds']
                                ['drag_drop'][int(adhigaram_number)])
                condition = {'email': session['user']['email']}
                dataToBeUpdated = {
                    "points.diamonds.drag_drop."+adhigaram_number: diamonds, "points.diamonds.total": total}

                db.user_details.update_one(
                    condition, {"$set": dataToBeUpdated})

                session['user']['points']['diamonds']['total'] = total
                session['user']['points']['diamonds']['drag_drop'][int(
                    adhigaram_number)] = diamonds

                session.modified = True

            return render_template('drag_drop_game_1.html', kuralWord=(kuralWordsList), porul=kuralData['porul'], diamonds=diamonds)

    def fillups_game(self):
        if request.method == "GET":
            kuralId = request.args.get("kuralId")
            kural_data = db['kural_data']
            query = {"kural_id": int(kuralId)}
            kuralData = kural_data.find_one(query)
            kuralWordsList = kuralData['kural'][0][0].split(
            ) + kuralData['kural'][1][0].split()
            missingWordIndex = random.randint(0, 6)
            missingWord = kuralWordsList[missingWordIndex]
            kuralWordsList[missingWordIndex] = "__________"

            #adding more options
            options = ["நீடுவாழ்", "யாண்டும்", "தாள்சேர்ந்தார்க்", "இனிய", "பயன்என்று",
    "உளரென்று", "அன்போடு", "மணியினும்", "செல்வத்துள்", "சான்றோர்",
    "மிகுத்து", "பெருக்கல்", "கேடில்லை", "இல்லாள்தன்", "நாடொறும்",
    "மறந்தும்", "காதன்மை", "வாய்மை", "பொருட்டால்", "கேள்வி",
    "மாண்ட", "படிபொறை", "தம்மைப்", "உளராக", "இடும்பை",
    "சால்பின்", "துறந்தார்", "கொடியன", "நாணுடைமை", "விரும்பி",
    "குழவி", "அம்மா", "நுகர்வார்", "அறத்தான்", "மாண்பு",
    "தொடர்ந்து", "விளக்கம்", "முன்னேறல்", "நிலைமை", "ஒழுக்கம்",
    "பிறப்பொடு", "துன்பம்", "தோன்றும்", "உணர்ச்சி", "உயர்ச்சி",
    "அடக்கம்", "செல்வம்", "பெருமை", "நன்றி"]
            random.shuffle(options)
            options = options[:3]
            if missingWord not in options:
                options.append(missingWord)
            random.shuffle(options)
            return render_template('fillups_game.html', kuralWord=kuralWordsList, porul=kuralData['porul'], kuralId=kuralId, options=options, index=missingWordIndex)

    def evaluate_fillups_game(self):
        if request.method == "POST":
            kuralId = request.form.get("kuralId")
            answer = request.form.get("answer")
            answerIndex = request.form.get("index")

            kural_data = db['kural_data']
            query = {"kural_id": int(kuralId)}
            kuralData = kural_data.find_one(query)
            kuralWordsList = kuralData['kural'][0][0].split(
            ) + kuralData['kural'][1][0].split()
            diamonds = 0
            if(kuralWordsList[int(answerIndex)] == answer):
                diamonds = 2
                adhigaram_number = str((int(kuralId) - 1) // 10)

                if (int(session['user']['points']['diamonds']['fillups'][int(adhigaram_number)]) < int(session['user']['points']['diamonds']['total']) + diamonds):
                    total = (int(session['user']['points']['diamonds']['total']) + diamonds) - int(
                        session['user']['points']['diamonds']['fillups'][int(adhigaram_number)])
                else:
                    total = int(session['user']['points']['diamonds']
                                ['fillups'][int(adhigaram_number)])
                condition = {'email': session['user']['email']}

                dataToBeUpdated = {
                    "points.diamonds.fillups."+adhigaram_number: diamonds, "points.diamonds.total": total}

                db.user_details.update_one(
                    condition, {"$set": dataToBeUpdated})

                session['user']['points']['diamonds']['total'] = total
                session['user']['points']['diamonds']['fillups'][int(
                    adhigaram_number)] = diamonds

                session.modified = True

            return render_template('fillups_game_1.html', diamonds=diamonds)

    def ngram_game(self):
        """Render the N-gram prediction game page."""
        if request.method == "GET":
            return render_template('ngram_game.html')

    def get_ngram_kural(self):
        """Get a random kural with one word masked for the N-gram game."""
        if request.method == "GET":
            kural_data = db['kural_data']
            
            # Get random kural ID (1-1330)
            random_kural_id = random.randint(1, 1330)
            
            query = {"kural_id": int(random_kural_id)}
            kuralData = kural_data.find_one(query)
            
            if not kuralData:
                return jsonify({"error": "Kural not found"}), 404
            
            # Validate kural structure
            if 'kural' not in kuralData or len(kuralData['kural']) < 2:
                return jsonify({"error": "Invalid kural structure"}), 400
            
            # Randomly choose line1 or line2
            line_choice = random.randint(0, 1)
            chosen_line = kuralData['kural'][line_choice][0] if len(kuralData['kural'][line_choice]) > 0 else ""
            
            # Split line into words
            words = [w.strip() for w in chosen_line.split() if w.strip()] if chosen_line else []
            
            # If line has less than 2 words, try the other line
            if len(words) < 2:
                line_choice = 1 - line_choice
                chosen_line = kuralData['kural'][line_choice][0] if len(kuralData['kural'][line_choice]) > 0 else ""
                words = [w.strip() for w in chosen_line.split() if w.strip()] if chosen_line else []
            
            # If still no valid words, return error
            if len(words) < 1:
                return jsonify({"error": "Kural has no valid words"}), 400
            
            # Randomly select a word to mask (avoid first and last for better context)
            if len(words) > 2:
                masked_index = random.randint(1, len(words) - 2)
            else:
                masked_index = random.randint(0, len(words) - 1)
            
            correct_word = words[masked_index]
            
            # Create masked line
            masked_words = words.copy()
            masked_words[masked_index] = "_____"
            masked_line = " ".join(masked_words)
            
            return jsonify({
                "kural_id": random_kural_id,
                "line_number": line_choice + 1,
                "masked_line": masked_line,
                "masked_index": masked_index,
                "correct_word": correct_word,
                "porul": kuralData.get('porul', {})
            }), 200

    def ngram_predict(self):
        """Get machine prediction for the masked word using N-gram model."""
        if request.method == "POST":
            data = request.get_json()
            masked_line = data.get('masked_line', '')
            masked_index = data.get('masked_index', -1)
            
            if not masked_line or masked_index < 0:
                return jsonify({"error": "Invalid request"}), 400
            
            start_time = time.time()
            
            # Get the N-gram model and make prediction
            model = get_model()
            predicted_word = model.predict_from_line(masked_line, masked_index)
            
            elapsed_time_ms = int((time.time() - start_time) * 1000)
            
            return jsonify({
                "prediction": predicted_word or "",
                "machine_time_ms": elapsed_time_ms
            }), 200

    def submit_ngram_score(self):
        """Submit user score and save to MongoDB."""
        if request.method == "POST":
            data = request.get_json()
            
            # Get score data
            kural_id = data.get('kural_id')
            correct_word = data.get('correct_word', '')
            user_answer = data.get('user_answer', '')
            machine_prediction = data.get('machine_prediction', '')
            user_correct = (user_answer.strip() == correct_word.strip())
            machine_correct = (machine_prediction.strip() == correct_word.strip())
            user_time_ms = data.get('user_time_ms', 0)
            machine_time_ms = data.get('machine_time_ms', 0)
            
            # Get user info from session
            user_email = session.get('user', {}).get('email', '')
            user_name = session.get('user', {}).get('name', '')
            
            # Create score document
            score_doc = {
                "_id": uuid.uuid4().hex,
                "user_email": user_email,
                "user_name": user_name,
                "kural_id": int(kural_id),
                "correct_word": correct_word,
                "user_answer": user_answer,
                "machine_prediction": machine_prediction,
                "user_correct": user_correct,
                "machine_correct": machine_correct,
                "user_time_ms": int(user_time_ms),
                "machine_time_ms": int(machine_time_ms),
                "timestamp": datetime.now()
            }
            
            # Save to MongoDB
            ngram_scores = db['ngram_game_scores']
            ngram_scores.insert_one(score_doc)
            
            return jsonify({
                "success": True,
                "user_correct": user_correct,
                "machine_correct": machine_correct
            }), 200

    def ngram_leaderboard(self):
        """Get leaderboard for N-gram game."""
        if request.method == "GET":
            ngram_scores = db['ngram_game_scores']
            
            # Get top 10 players by accuracy (user_correct count)
            pipeline = [
                {
                    "$match": {"user_correct": True}
                },
                {
                    "$group": {
                        "_id": "$user_email",
                        "user_name": {"$first": "$user_name"},
                        "total_correct": {"$sum": 1},
                        "avg_time_ms": {"$avg": "$user_time_ms"}
                    }
                },
                {
                    "$sort": {"total_correct": -1, "avg_time_ms": 1}
                },
                {
                    "$limit": 10
                }
            ]
            
            leaderboard = list(ngram_scores.aggregate(pipeline))
            
            # Format leaderboard
            formatted_leaderboard = []
            for idx, entry in enumerate(leaderboard, 1):
                formatted_leaderboard.append({
                    "rank": idx,
                    "user_name": entry.get('user_name', ''),
                    "total_correct": entry.get('total_correct', 0),
                    "avg_time_ms": int(entry.get('avg_time_ms', 0))
                })
            
            return jsonify({"leaderboard": formatted_leaderboard}), 200
