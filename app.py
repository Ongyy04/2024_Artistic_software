import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from pymongo import MongoClient
import os
from werkzeug.security import generate_password_hash, check_password_hash
from random import randint
from werkzeug.utils import secure_filename
from bson import ObjectId
from twilio.rest import Client
import os
import uuid
import base64
from twilio.base.exceptions import TwilioRestException
import random
from pymongo import DESCENDING
from dotenv import load_dotenv


# .env 파일 로드
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB connection setup
client = MongoClient('localhost', 27017)
db_user = client['userdata']
users_collection = db_user['users']
db_rec = client['travel_records']
posts_collection = db_rec['posts']

# Naver Client credentials

NAVER_REDIRECT_URI = "http://localhost:5000/naver/callback"

# Google Client credentials

GOOGLE_REDIRECT_URI = "http://localhost:5000/google/callback"

NAVER_AUTH_URL = "https://nid.naver.com/oauth2.0/authorize?response_type=code"
NAVER_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
NAVER_USER_INFO_URL = "https://openapi.naver.com/v1/nid/me"

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
@app.route('/')
@app.route('/ready')
def ready():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated
    return render_template('ready.html')  # Render ready.html after successful login
# Login route
import hashlib
def hash_password(password):
    # 새로운 salt 값 생성
    salt = os.urandom(16).hex()  # 16바이트의 임의의 salt 값 생성
    # n 값을 16384로 줄여서 해시 생성
    hashed_password = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return f"scrypt:16384:8:1${salt}${hashed_password}"
def verify_scrypt_password(stored_password, input_password):
    try:
        # 저장된 비밀번호 해시를 구성 요소로 분리
        components = stored_password.split('$')
        scrypt_params = components[0]  # 'scrypt:16384:8:1'
        salt = components[1]  # salt 값
        stored_hash = components[2]  # 실제 저장된 해시 값

        # scrypt 파라미터에서 n, r, p 값 추출
        n, r, p = map(int, scrypt_params.split(':')[1:])

        # 입력된 비밀번호를 동일한 파라미터로 해시
        scrypt_hash = hashlib.scrypt(input_password.encode(), salt=salt.encode(), n=n, r=r, p=p).hex()

        # 해시된 입력 비밀번호와 저장된 해시를 비교
        return scrypt_hash == stored_hash
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')

        if not user_id or not password:
            print('아이디와 비밀번호를 모두 입력해주세요.', 'error')
            return render_template('login.html', error=True)

        # MongoDB에서 user_id로 사용자 찾기
        user = users_collection.find_one({'user_id': user_id})
        if user:
            hashed_password = user.get('password')
    
            print(hashed_password)
            print(password)
            
            if verify_scrypt_password(hashed_password, password):
                session['user_id'] = user['user_id']
                return redirect(url_for('check'))
            else:
                 print('아이디 또는 비밀번호가 잘못되었습니다q.', 'error')
        else:
             print('아이디 또는 비밀번호가 잘못되었습니다w.', 'error')

    return render_template('login.html', error=True)


@app.route('/kakao', methods=["GET"])
def kakao():
    kakao_user_id = session.get('kakao_user_id')

    if not kakao_user_id:
        return redirect(url_for('login'))  # 세션에 사용자 ID가 없으면 로그인 페이지로 리디렉션

    user = users_collection.find_one({"user_id": kakao_user_id})
    print(f"User fetched from DB: {user}")  # 디버깅을 위해 사용자 정보 출력

    if user and 'phone_number' in user and user['phone_number'].strip():
        return redirect(url_for('ready'))
    else:
        return render_template('make_name.html')

@app.route('/kakao/register', methods=['POST'])
def kakao_register():
    data = request.json
    kakao_user_id = data.get('kakao_id')
    nickname = data.get('nickname')

    if not kakao_user_id:
        return jsonify({"success": False, "message": "Kakao ID is missing"}), 400

    # Set Kakao user ID as 'user_id' in session
    session['user_id'] = kakao_user_id

    # Insert or update the user's kakao_id, nickname, and type in the database
    users_collection.update_one(
        {"user_id": kakao_user_id},
        {"$set": {"nickname": nickname, "type": "kakao"}},  # Set the type as 'kakao'
        upsert=True
    )

    # Redirect to the next step (make_name) after Kakao login
    return jsonify({"success": True, "redirect_url": url_for('make_name')}), 200


# Route for Naver login
@app.route('/naver/login')
def naver_login():
    return redirect(f"{NAVER_AUTH_URL}&client_id={NAVER_CLIENT_ID}&redirect_uri={NAVER_REDIRECT_URI}&state=naver_login")

@app.route('/naver/callback')
def naver_callback():
    code = request.args.get('code')
    state = request.args.get('state')

    token_request = requests.post(
        NAVER_TOKEN_URL,
        params={
            "grant_type": "authorization_code",
            "client_id": NAVER_CLIENT_ID,
            "client_secret": NAVER_CLIENT_SECRET,
            "code": code,
            "state": state,
        }
    )
    
    token_response_data = token_request.json()
    access_token = token_response_data.get('access_token')

    if not access_token:
        return jsonify({"success": False, "message": "Failed to retrieve access token"}), 400

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    user_info_request = requests.get(NAVER_USER_INFO_URL, headers=headers)
    user_info = user_info_request.json()

    if user_info['resultcode'] == "00":
        naver_user_data = user_info['response']
        naver_user_id = naver_user_data['id']

        # Set Naver user ID as 'user_id' in session
        session['user_id'] = naver_user_id

        users_collection.update_one(
            {"user_id": naver_user_id},
            {"$set": {"user_id": naver_user_id, "type": "naver"}},  # Set the type as 'naver'
            upsert=True
        )

        return redirect(url_for('make_name'))
    else:
        return jsonify({"success": False, "message": "Failed to retrieve user information from Naver"}), 400



# Route for Google login
@app.route('/google/login')
def google_login():
    return redirect(f"{GOOGLE_AUTH_URL}?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=email%20profile")

# Route for Google login
@app.route('/google/callback')
def google_callback():
    code = request.args.get('code')

    token_request = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    )

    token_response_data = token_request.json()
    access_token = token_response_data.get('access_token')

    if not access_token:
        return jsonify({"success": False, "message": "Failed to retrieve access token"}), 400

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    user_info_request = requests.get(GOOGLE_USER_INFO_URL, headers=headers)
    user_info = user_info_request.json()

    google_user_id = user_info['sub']

    # Set Google user ID as 'user_id' in session
    session['user_id'] = google_user_id

    users_collection.update_one(
        {"user_id": google_user_id},
        {"$set": {"user_id": google_user_id,  "type": "google"}},  # Set the type as 'google'
        upsert=True
    )

    return redirect(url_for('make_name'))

@app.route('/make_id', methods=['GET', 'POST'])
def make_id():
    session.clear()  # Clear session to prevent duplication
    if request.method == 'POST':
        user_id = request.form['user_id']
        
        # Check if the user ID already exists
        if users_collection.find_one({"user_id": user_id}):
            flash('아이디가 이미 존재합니다.', 'error')
            return redirect(url_for('make_id'))
        else:
            # Save the user ID and type in MongoDB
            try:
                users_collection.insert_one({"user_id": user_id, "type": "general"})  # Set the type as 'general'
                session['user_id'] = user_id  # Save the user ID in the session for the next steps
                
                return redirect(url_for('make_pw'))  # Redirect to the password setup page
            except Exception as e:
                flash('데이터 저장 중 오류가 발생했습니다.', 'error')
                return redirect(url_for('make_id'))
    
    # If it's a GET request, render the make_id page
    return render_template('make_id.html')


@app.route('/check_id', methods=['POST'])
def check_id():
    user_id = request.json.get('user_id')  # 클라이언트로부터 전달된 아이디 값

    if not user_id:
        return jsonify({"success": False, "message": "아이디를 입력해 주세요."}), 400

    # MongoDB에서 아이디 중복 확인
    user = users_collection.find_one({"user_id": user_id})

    if user:
        return jsonify({"success": False, "message": "이미 사용 중인 아이디입니다."}), 409
    else:
        return jsonify({"success": True, "message": "사용 가능한 아이디입니다."}), 200
from werkzeug.security import generate_password_hash

@app.route('/make_pw', methods=['GET', 'POST'])
def make_pw():
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # 비밀번호 일치 확인
        if password != confirm_password:
            flash('비밀번호가 일치하지 않습니다.', 'error')
            return redirect(url_for('make_pw'))

        # 로그인 유형 확인 및 소셜 로그인 계정에서 비밀번호 설정 방지
        login_type = session.get('login_type')
        user_id = session.get('user_id')

        if login_type in ['google', 'naver', 'kakao']:
            flash('소셜 로그인 계정에 비밀번호를 설정할 수 없습니다.', 'error')
            return redirect(url_for('login'))

        if user_id:
            # scrypt를 이용하여 비밀번호 해시 생성
            hashed_password = hash_password(password)
            try:
                # 일반 회원가입 사용자에 한해 비밀번호 업데이트
                users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"password": hashed_password}}
                )
                
                return redirect(url_for('make_name'))
            except Exception as e:
                flash('데이터 저장 중 문제가 발생했습니다. 다시 시도해주세요.', 'error')
                return redirect(url_for('make_pw'))

    return render_template('make_pw.html')

  

# Route for name creation
@app.route('/verify_code', methods=['POST'])
def verify_code():
    data = request.get_json()
    entered_code = data['verification_code']
    saved_code = session.get('verification_code')

    if entered_code == saved_code:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

@app.route('/make_name', methods=['GET', 'POST'])
def make_name():
    user_id = session.get('user_id')
    print(f"Session user_id: {user_id}")  # Debug: Check if user_id is correctly stored in session
    
    if not user_id:
        return redirect(url_for('login'))

    # Fetch the user's name directly from the MongoDB database
    user = users_collection.find_one({"user_id": user_id})
    name = user.get('name') if user else None
    print(f"User name from DB before POST: {name}")  # Debug: Check if the name is already stored in the database
    
    # If the name is already in the database, redirect to the ready page
    if name:
        return redirect(url_for('ready'))

    if request.method == 'POST':
        # Retrieve the name from the form POST data
        name = request.form.get('name')
        print(f"Form name from POST: {name}")  # Debug: Check if name is coming from the form

        if not name:
            # Handle error if no name is provided
            flash('이름을 입력해 주세요.', 'error')
            print("Error: No name provided in POST request")  # Debug message for missing name
            return redirect(url_for('make_name'))

        # Update the user's name in MongoDB
        try:
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"name": name}}
            )
            print(f"User name updated in MongoDB for user_id: {user_id}, name: {name}")
        except Exception as e:
            # Handle any errors that occur during the database update
            flash('이름 업데이트 중 오류가 발생했습니다.', 'error')
            print(f"Error updating name in MongoDB: {e}")  # Debug message for DB update error
            return redirect(url_for('make_name'))

        # After successfully setting the name, redirect to the next step (make_nickname)
        return redirect(url_for('make_nickname'))

    return render_template('make_name.html')
@app.route('/make_nickname', methods=['GET', 'POST'])
def make_nickname():
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('login'))

    user_data = users_collection.find_one({"user_id": user_id})

    if user_data:
        user_type = user_data.get('type')
        if user_type in ['naver', 'kakao', 'google']:
            # Update password field to "NULL"
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"password": "NULL"}}
            )

    if request.method == 'POST':
        nickname = request.form['user_nickname']  # Changed key here
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"nickname": nickname}}
        )
        session['nickname'] = nickname
        return redirect(url_for('make_phone'))

    return render_template('make_nickname.html')

@app.route('/change-nickname', methods=['GET', 'POST'])
def change_nickname():
    if request.method == 'POST':
        # 선택된 닉네임과 사용자 ID를 세션에서 가져옴
        selected_nickname = request.form.get('user_nickname')
        user_id = session.get('user_id')

        if user_id and selected_nickname:
            # 데이터베이스에서 사용자의 닉네임을 업데이트
            users_collection.update_one({'user_id': user_id}, {'$set': {'nickname': selected_nickname}})
        
        # 업데이트 성공 후 설정 페이지로 리디렉션
        return redirect(url_for('setting'))

    # GET 요청 시 폼 렌더링
    return render_template('change_NickName.html')

@app.route('/check_nickname', methods=['POST'])
def check_nickname():
    data = request.get_json()
    user_nickname = data.get('user_nickname')

    # 데이터베이스에서 닉네임 중복 확인
    existing_user = users_collection.find_one({"nickname": user_nickname})

    if existing_user:
        # 닉네임이 이미 존재함
        return jsonify({"status": "duplicate", "message": "이미 사용 중인 닉네임입니다."})
    else:
        # 닉네임 사용 가능
        return jsonify({"status": "available", "message": "사용 가능한 닉네임입니다."})



# Twilio API credentials

client = Client(account_sid, auth_token)


# Helper function to format the phone number
def ver_phone_num(phone_number):
    """Formats the phone number for Korea."""
    if phone_number.startswith('010'):
        return '+82' + phone_number[1:]  # Remove the leading 0 and add '+82'
    else:
        raise ValueError('Invalid phone number format')

# Function to send a verification code
def send_verification_code(phone_number):
    """Sends a verification code to the given phone number."""
    formatted_number = ver_phone_num(phone_number)  # Format the phone number
    verification_code = randint(100000, 999999)  # Generate random 6-digit code
    
    try:
        message = client.messages.create(
            from_='+12674045433',  # Twilio phone number
            body=f'인증번호: {verification_code}',  # Send the code in the message body
            to=formatted_number  # Use formatted phone number
        )
        print(f"Message sent, SID: {message.sid}")
        return verification_code
    except Exception as e:
        print(f"Error sending message: {e}")
        return None
@app.route('/send_verification', methods=['POST'])
def send_verification():
    data = request.get_json()
    phone_number = data['phone_number']

    try:
        # Send the verification code here
        sent_code = send_verification_code(phone_number)
        session['verification_code'] = str(sent_code)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/make_phone', methods=['GET', 'POST'])
def make_phone():
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('login'))

    # Fetch user from the database
    user = users_collection.find_one({"user_id": user_id})

    # If user doesn't have 'credits', 'stack_credit', or 'nocheck' fields, set them to 0
    if 'credits' not in user or 'stack_credit' not in user or 'nocheck' not in user:
        update_fields = {}
        if 'credits' not in user:
            update_fields['credits'] = 0
            user['credits'] = 0  # Update the in-memory user object
        if 'stack_credit' not in user:
            update_fields['stack_credit'] = 0
            user['stack_credit'] = 0  # Update the in-memory user object
        if 'nocheck' not in user:
            update_fields['nocheck'] = 0
            user['nocheck'] = 0  # Update the in-memory user object

        if update_fields:
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": update_fields}
            )

    if request.method == 'POST':
        phone_number = request.form['phone_number']

        # Check if the verification code was submitted
        verification_code = request.form.get('verification_code')
        saved_code = session.get('verification_code')

        # Allow "test-user" to bypass verification
        if verification_code == "test-user" or (verification_code and saved_code):
            # Verify the code
            if verification_code == "test-user" or verification_code == saved_code:
                # Code matches, save the phone number to the database
                users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"phone_number": phone_number}}
                )
                session.pop('verification_code', None)  # Remove the code from session after use
                return redirect(url_for('make_profile'))
            else:
                # Code doesn't match, show an error message
                flash('인증번호가 일치하지 않습니다. 다시 시도해주세요.')
        else:
            # No verification code submitted yet, so send one
            sent_code = send_verification_code(phone_number)
            if sent_code:
                session['verification_code'] = str(sent_code)  # Save the code in session
                flash('인증번호가 전송되었습니다. 확인 후 입력해주세요.')
            else:
                flash('메시지 전송에 실패했습니다. 나중에 다시 시도해주세요.')

    return render_template('make_phone.html', credits=user['credits'], stack_credit=user['stack_credit'], nocheck=user['nocheck'])

# Route for profile creation (file upload)
@app.route('/make_profile', methods=['GET', 'POST'])
def make_profile():
    user_id = session.get('user_id') 

    if not user_id:
        return redirect(url_for('login'))

    if request.method == 'POST':
        profile_image = request.files['profile_image']
        upload_folder = 'static/image/uploads_profile'  # Updated folder path

        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        if profile_image:
            profile_image.save(os.path.join(upload_folder, profile_image.filename))
            profile_image_path = f'/static/image/uploads_profile/{profile_image.filename}'  # Updated path
        else:
            profile_image_path = '/static/image/profile.png'

        # 소셜 로그인 여부 확인 (소셜 로그인일 경우 비밀번호를 건드리지 않음)
        if session.get('kakao_user_id') or session.get('naver_user_id') or session.get('google_user_id'):
            # 소셜 로그인 사용자는 비밀번호 없이 프로필 이미지 업데이트
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "profile_image": profile_image_path,
                    "password": None
                }}
            )
        else:
            # 일반 회원가입 사용자의 경우 비밀번호를 건드리지 않고 프로필 이미지만 업데이트
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "profile_image": profile_image_path
                }}
            )

        
        return redirect(url_for('choose'))

    return render_template('make_profile.html')

@app.route('/choose')
def choose():
    return render_template('choose.html')
@app.route('/choose2')
def choose2():
    return render_template('choose2.html')

@app.route('/choose3')
def choose3():
    return render_template('choose3.html')


@app.route('/make_profile')
def make_profile_view():
    return render_template('make_profile.html')

@app.route('/ready')
def ready_view():
    return render_template('ready.html')

@app.route('/save_gender', methods=['POST'])
def save_gender():
    user_id = session.get('user_id') 
    
    if not user_id:
        return redirect(url_for('login'))  # 세션에 사용자 정보가 없으면 로그인 페이지로 리디렉션
    
    gender = request.form.get('gender')

    if not gender:
        flash('성별을 선택해 주세요.', 'error')
        return redirect(url_for('choose'))
    
    # MongoDB에 gender 값 업데이트
    users_collection.update_one(
        {"user_id": user_id},  # 소셜 로그인 사용자와 일반 로그인 사용자 모두 동일하게 처리
        {"$set": {"gender": gender}}
    )

    # choose2.html로 이동
    return redirect(url_for('choose2'))

@app.route('/save_age', methods=['POST'])
def save_age():
    user_id = session.get('user_id') 
    
    if not user_id:
        return redirect(url_for('login'))  # 세션에 사용자 정보가 없으면 로그인 페이지로 리디렉션

    # 폼에서 선택된 나이대 값 받기
    age = request.form.get('age')

    if not age:
        flash('나이대를 선택해 주세요.', 'error')
        return redirect(url_for('choose'))

    # MongoDB에 age 값 업데이트
    users_collection.update_one(
        {"user_id": user_id},  # 소셜 로그인 사용자와 일반 로그인 사용자 모두 동일하게 처리
        {"$set": {"age": age}}
    )

    # choose3.html로 이동
    return redirect(url_for('choose3'))

@app.route('/save_prefer', methods=['POST'])
def save_prefer():
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('login'))  # 세션에 사용자 정보가 없으면 로그인 페이지로 리디렉션
    
    # 사용자가 선택한 여행 스타일 값을 가져옵니다.
    prefer = request.form.get('prefer')

    if not prefer:
        flash('여행 스타일을 선택해 주세요.', 'error')
        return redirect(url_for('choose'))

    # MongoDB에 prefer 항목 업데이트
    users_collection.update_one(
        {"user_id": user_id},  # 소셜 로그인 사용자와 일반 로그인 사용자 모두 동일하게 처리
        {"$set": {"prefer": prefer}}
    )

    # 저장이 완료되면 ready.html로 이동
    return redirect(url_for('ready_view'))



@app.route('/find')
def find():
    return render_template('find.html')
@app.route('/find_id', methods=['GET', 'POST'])
def find_id():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        verification_code = request.form.get('verification_code')
        saved_code = session.get('verification_code')

        # Allow "test-user" to bypass verification
        if verification_code == "test-user" or (verification_code and saved_code):
            if verification_code == "test-user" or verification_code == saved_code:
                # Find the user by phone number
                user = users_collection.find_one({"phone_number": phone_number})
                if user:
                    session.pop('verification_code', None)  # Remove the code from session
                    # Pass the user_id to the template
                    return render_template('id.html', user_id=user['user_id'])  # Redirect to id.html with user_id
                else:
                    flash('해당 전화번호로 등록된 사용자를 찾을 수 없습니다.')
            else:
                flash('인증번호가 일치하지 않습니다. 다시 시도해주세요.')
        else:
            # Send the verification code if no code has been submitted yet
            sent_code = send_verification_code(phone_number)
            if sent_code:
                session['verification_code'] = str(sent_code)
                flash('인증번호가 전송되었습니다. 확인 후 입력해주세요.')
            else:
                flash('메시지 전송에 실패했습니다. 나중에 다시 시도해주세요.')

    return render_template('find_id.html')



@app.route('/id')
def id():
    return render_template('id.html')

@app.route('/find_pw', methods=['GET', 'POST'])
def find_pw():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')

        # Validate the phone number in the users collection
        user = users_collection.find_one({"phone_number": phone_number})

        if not user:
            flash('전화번호가 일치하지 않습니다.', 'error')
            return redirect(url_for('find_pw'))

        # Store the phone number in the session for future use
        session['phone_number'] = phone_number
        flash('전화번호 인증에 성공했습니다.', 'success')
        return redirect(url_for('update_password'))  # Redirect to the pw.html for password update

    return render_template('find_pw.html')

@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if the passwords match
        if new_password != confirm_password:
            flash('비밀번호가 일치하지 않습니다.', 'error')
            return redirect(url_for('update_password'))

        # Retrieve the phone number from the session
        phone_number = session.get('phone_number')

        if not phone_number:
            flash('전화번호 인증이 필요합니다.', 'error')
            return redirect(url_for('find_pw'))

        # Hash the new password using the same hash_password function
        hashed_password = hash_password(new_password)
        try:
            users_collection.update_one(
                {"phone_number": phone_number},
                {"$set": {"password": hashed_password}}
            )
            flash('비밀번호가 성공적으로 변경되었습니다.', 'success')
            return redirect(url_for('login'))  # Redirect to login page after successful update
        except Exception as e:
            flash('비밀번호 변경 중 문제가 발생했습니다. 다시 시도해주세요.', 'error')
            return redirect(url_for('update_password'))
    
    return render_template('pw.html')  # This is your pw.html where password inputs are taken


from datetime import datetime

from datetime import datetime, timedelta

@app.route('/check', endpoint='check')
def check_view():
    user_id = session.get('user_id')
    # MongoDB에서 해당 사용자 데이터를 가져옴
    user_data = users_collection.find_one({'user_id': user_id})

    if user_data:
        # 현재 nocheck 값을 가져옴
        nocheck = user_data.get('nocheck', 0)

        # nocheck가 0보다 크면 -1 감소시키고, 그렇지 않으면 변경하지 않음
        if nocheck > 0:
            a=nocheck%10
            new_nocheck = nocheck - a
            users_collection.update_one({'user_id': user_id}, {'$set': {'nocheck': new_nocheck}})
        else:
            new_nocheck = 0

    if not user_id:
        return redirect(url_for('login'))  # Redirect to login if no user is logged in
    
    # Fetch user data from the database based on user_id
    user_data = users_collection.find_one({'user_id': user_id})
    
    if not user_data:
        return "User not found", 404
    
    # Get user's credits or set to 0 if not found
    credits = user_data.get('credits', 0)
    stack_credit = user_data.get('stack_credit', 0)  # Fetch stack_credit value
    
    # Get user's last check-in date
    last_check_in_date = user_data.get('last_check_in_date')
    
    # Get the current date
    today = datetime.today().date()
    
    # Initialize nocheck and check_in_count if not present
    check_in_count = user_data.get('check_in_count', 0)
    nocheck = user_data.get('nocheck', 0)

    # Check if the user has already checked in today
    already_checked_in = False
    if last_check_in_date:
        last_check_in_date = datetime.strptime(last_check_in_date, '%Y-%m-%d').date()
        if last_check_in_date == today:
            already_checked_in = True

    # If the user hasn't checked in today, perform check-in logic
    if not already_checked_in:
        # Check if there is a gap between today and the last check-in date
        if last_check_in_date:
            days_missed = (today - last_check_in_date).days
            # If days were missed (more than 1 day), increment nocheck by the number of missed days
            if days_missed > 1:
                nocheck += days_missed - 1

        # If the user hasn't reached the limit of 28 days
        if check_in_count < 28:
            check_in_count += 1
        else:
            check_in_count = 1  # Restart check-in count after 28 days
            
    

        # Update the user's data in MongoDB
        users_collection.update_one(
            {'user_id': user_id},
            {'$set': {
                'check_in_count': check_in_count,
                'last_check_in_date': today.strftime('%Y-%m-%d'),
                'nocheck': nocheck,
                'credits': credits,
                'stack_credit': stack_credit
            }}
        )
    else:
        print("Already checked in today. No credits or check-in updates.")

    # Render the template with the credits, check_in_count, nocheck, and stack_credit values
    return render_template('check.html', credits=credits, check_in_count=check_in_count, nocheck=nocheck, stack_credit=stack_credit, already_checked_in=already_checked_in)
@app.route('/update_credits', methods=['POST'])
def update_credits():
    try:
        data = request.get_json()
        print("Received data:", data)  # Debugging statement
        user_id = session.get('user_id')
        credits_to_add = data.get('credits_to_add', 0)
        
        # Fetch user data from the database
        user_data = users_collection.find_one({'user_id': user_id})
        print("User data found:", user_data)  # Debugging statement
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Get current credits and stack_credit, or default to 0
        current_credits = user_data.get('credits', 0)
        stack_credit = user_data.get('stack_credit', 0)
        
        # Add the credits to both fields
        new_credits = current_credits + credits_to_add
        new_stack_credit = stack_credit + credits_to_add
        
        # Update the user's credits and stack_credit in the database
        result = users_collection.update_one(
            {'user_id': user_id},
            {'$set': {
                'credits': new_credits,
                'stack_credit': new_stack_credit
            }}
        )
        
        print("Update result:", result)  # Debugging statement
        
        return jsonify({'message': 'Credits updated successfully'}), 200
    except Exception as e:
        print("Error during credits update:", str(e))  # Print error to logs
        return jsonify({'error': 'An error occurred during credits update'}), 500


@app.route('/get_credits', methods=['GET'])
def get_credits():
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401
    
    # Fetch the user data
    user_data = users_collection.find_one({'user_id': user_id})

    if not user_data:
        return jsonify({'error': 'User not found'}), 404

    # Return the current credits
    current_credits = user_data.get('credits', 0)
    return jsonify({'credits': current_credits}), 200


import random
from bson import ObjectId

import os
from flask import send_file


@app.route('/home', methods=['GET'])
def home_view():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # Fetch user data from the database
    user_data = users_collection.find_one({'user_id': user_id})
    if not user_data:
        
        return "User not found", 404

    user_prefer = user_data.get('prefer', 'Unknown')

    # Get the profile image and nickname from the user data
    profile_image_user = user_data.get('profile_image', 'image/uploads_profile/default_profile.png')  # User's profile image
    nickname = user_data.get('nickname', 'Unknown User')

    # Get the selected region filter from the query parameters (default is '전체')
    selected_region = request.args.get('region', '전체')

    # Build the region filter based on the selected region
    if selected_region == '전체':
        region_filter = {}
    elif selected_region == '한국':
        region_filter = {'tags.region': {'$regex': r'한국'}}  # Updated regex to match '한국' anywhere in the region tag

    elif selected_region == '아메리카':
        region_filter = {'$or': [{'tags.region': {'$regex': r'^북미 - '}}, {'tags.region': {'$regex': r'^남미 - '}}]}
    elif selected_region == '아시아':
        region_filter = {'tags.region': {'$regex': r'^아시아 - ', '$not': {'$regex': '한국'}}}  # Matches '아시아' but excludes '한국'

    else:
        region_filter = {'tags.region': {'$regex': f'^{selected_region} - '}}  # Regex to match the continent

    # Prepare the filter for recommended posts, including user's preference
    recommended_filter = region_filter.copy()
    recommended_filter.update({"tags.travel_type": user_prefer})

    # Fetch the top 2 posts with the most likes without considering user's preference (hot posts)
    top_posts = list(posts_collection.find(
        region_filter, 
        {
            'tags.age': 1, 'tags.gender': 1, 'tags.travel_type': 1, 
            'tags.region': 1, 'tags.cost': 1, 'tags.relationship': 1, 'tags.during': 1, 
            'image_path': 1, 'user_id': 1, 'likes': 1
        }
    ).sort('likes', -1).limit(2))

    search_clicked = request.args.get('search_clicked')
    if search_clicked:
        return redirect(url_for('search_get'))

    # Add user nicknames and profile images to the hot posts and save their IDs to avoid duplicates in recommended posts
    hot_post_ids = []
    for post in top_posts:
        post_user = users_collection.find_one({'user_id': post['user_id']})
        post['nickname'] = post_user.get('nickname', 'Unknown User') if post_user else 'Unknown User'
        post['profile_image'] = post_user.get('profile_image', 'image/uploads_profile/default_profile.png') if post_user else 'image/uploads_profile/default_profile.png'
        full_region = post.get('tags', {}).get('region', 'Unknown Region')
        post['region'] = full_region.split(' - ')[1] if ' - ' in full_region else full_region
        hot_post_ids.append(post['_id'])

        # Ensure the image path is correct and read the image file
        if post.get('image_path'):
            image_path = os.path.join('static', post['image_path'])
            try:
                with open(image_path, "rb") as image_file:
                    post['image_data'] = image_file.read()  # Read image file content
            except FileNotFoundError:
               
                post['image_data'] = None

    # Fetch all recommended posts except the hot posts, and select 5 random posts for the recommended section
    all_posts = list(posts_collection.find(
        {'_id': {'$nin': hot_post_ids}, **recommended_filter},
        {
            'tags.age': 1, 'tags.gender': 1, 'tags.travel_type': 1, 
            'tags.region': 1, 'tags.cost': 1, 'tags.relationship': 1, 'tags.during': 1, 
            'image_path': 1, 'user_id': 1, 'likes': 1
        }
    ))
    recommended_posts = random.sample(all_posts, 5) if len(all_posts) >= 5 else all_posts

    # Add user nicknames and tags_list to the recommended posts
    for post in recommended_posts:
        post_user = users_collection.find_one({'user_id': post['user_id']})
        post['nickname'] = post_user.get('nickname', 'Unknown User') if post_user else 'Unknown User'
        post['profile_image'] = post_user.get('profile_image', 'image/uploads_profile/default_profile.png') if post_user else 'image/uploads_profile/default_profile.png'
        post['region'] = post.get('tags', {}).get('region', 'Unknown Region')

        # Extract tags as a list of strings
        tags = post.get('tags', {})
        tags_list = []
        for key, value in tags.items():
            if isinstance(value, list):
                tags_list.extend(value)
            else:
                tags_list.append(value)
        post['tags_list'] = tags_list

        # Ensure the image path is correct and read the image file
        if post.get('image_path'):
            image_path = os.path.join('static', post['image_path'])
            try:
                with open(image_path, "rb") as image_file:
                    post['image_data'] = image_file.read()  # Read image file content
                post['image_path'] = post['image_path'].replace('\\', '/')  # Ensure path consistency
            except FileNotFoundError:
                
                post['image_data'] = None

    # Pass the data to the template
    return render_template(
        'home.html', 
        profile_image_user=profile_image_user,  # User의 프로필 이미지
        nickname=nickname, 
        top_posts=top_posts, 
        recommended_posts=recommended_posts, 
        selected_region=selected_region
    )



# 파일 업로드 설정
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    if '.' in filename:
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in ALLOWED_EXTENSIONS
    return False

def generate_unique_filename(filename):
    if '.' in filename:
        ext = filename.rsplit('.', 1)[1].lower()
    else:
        flash('파일 이름에 확장자가 없습니다.')
        return None
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    return unique_filename

@app.route('/write', methods=['GET', 'POST'])
def write():
    user_id = session.get('user_id')  # 세션에서 user_id 가져오기
    if not user_id:
        return redirect(url_for('login'))  # 로그인하지 않은 경우 로그인 페이지로 리디렉션

    popular_tags = {
        'age': get_most_common_tag_value('age'),
        'gender': get_most_common_tag_value('gender'),
        'travel_type': get_most_common_tag_value('travel_type'),
        'region': get_most_common_tag_value('region'),
        'cost': get_most_common_tag_value('cost'),
        'relationship': get_most_common_tag_value('relationship'),
        'during': get_most_common_tag_value('during'),
    }

    if request.method == 'POST':
        # 폼 데이터 가져오기
        content = request.form.get('content', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        travel_type = request.form.get('travel_type', '').strip()
        region = request.form.get('region', '').strip()
        cost = request.form.get('cost', '').strip()
        relationship = request.form.get('relationship', '').strip()
        during = request.form.get('during', '').strip()

        tags = {
            'age': age,
            'gender': gender,
            'travel_type': travel_type,
            'region': region,
            'cost': cost,
            'relationship': relationship,
            'during': during
        }

        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = generate_unique_filename(filename)
            if unique_filename:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)

                # 게시물 데이터 생성
                post_data = {
                    'user_id': user_id,
                    'content': content,
                    'image_path': f"uploads/{unique_filename}",
                    'tags': tags,
                    'likes': 0,
                    'comments': []
                }

                posts_collection.insert_one(post_data)

                # 사용자의 credits 값을 20 증가
                users_collection.update_one(
                    {'user_id': user_id},
                    {'$inc': {'credits': 20}}
                )

                flash('글이 업로드되었습니다.')
                return redirect(url_for('write'))
            else:
                return redirect(url_for('write'))
        else:
            flash('허용되지 않는 파일 형식입니다.')
            return redirect(url_for('write'))

    return render_template('write.html', popular_tags=popular_tags)


@app.route('/upload', methods=['POST'])
def upload():
    user_id = session.get('user_id')  # 세션에서 user_id 가져오기
    if not user_id:
        return redirect(url_for('login'))  # 로그인하지 않은 경우 로그인 페이지로 리디렉션

    content = request.form.get('content', '')

    age = request.form.get('age', '나이대')
    gender = request.form.get('gender', '성별')
    travel_type = request.form.get('travel_type', '여행 유형')
    region = request.form.get('region', '지역')
    cost = request.form.get('cost', '비용')
    relationship = request.form.get('relationship', '관계')
    during = request.form.get('during', '여행 기간')

    tags = {
        'age': age,
        'gender': gender,
        'travel_type': travel_type,
        'region': region,
        'cost': cost,
        'relationship': relationship,
        'during': during
    }

    # 필수 필드 체크
    missing_fields = []
    if age == '미선택':
        missing_fields.append('나이대')
    if gender == '미선택':
        missing_fields.append('성별')
    if travel_type == '미선택':
        missing_fields.append('여행 유형')
    if region == '미선택':
        missing_fields.append('지역')
    if cost == '미선택':
        missing_fields.append('비용')
    if relationship == '미선택':
        missing_fields.append('관계')
    if during == '미선택':
        missing_fields.append('여행 기간')

    if missing_fields:
        if 'file' not in request.files or request.files['file'].filename == '':
            flash(f"다음 항목들을 채워주세요: 사진, 관심사({', '.join(missing_fields)})")
        else:
            flash(f"다음 항목들을 채워주세요: 관심사({', '.join(missing_fields)})")
        return redirect(url_for('write'))
    else:
        if 'file' not in request.files or request.files['file'].filename == '':
            flash("다음 항목을 채워주세요: 사진")
            return redirect(url_for('write'))

    file = request.files['file']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(filename)

        if unique_filename is None:
            return redirect(url_for('write'))

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        try:
            file.save(file_path)
        except Exception as e:
            flash(f"파일 저장 중 오류 발생: {str(e)}")
            return redirect(url_for('write'))

        # 게시물 데이터 생성
        post_data = {
            'user_id': user_id,
            'content': content,
            'image_path': f"uploads/{unique_filename}",
            'tags': tags,
            'likes': 0,
            'comments': []
        }

        try:
            posts_collection.insert_one(post_data)

            # 사용자의 credits 값을 20 증가
            users_collection.update_one(
                {'user_id': user_id},
                {'$inc': {'credits': 50}}
            )

            flash('글이 업로드되었습니다.')
        except Exception as e:
            flash(f"MongoDB 저장 중 오류 발생: {str(e)}")
            return redirect(url_for('write'))

        return redirect(url_for('write'))

    flash('허용되지 않는 파일 형식입니다.')
    return redirect(url_for('write'))
@app.route('/search', methods=['GET'])
def search_get():
    query = request.args.get('query', '').strip()

    if query:
        # 1. Find users whose nickname matches the query
        users = list(users_collection.find({"nickname": {"$regex": query, "$options": "i"}}))
        user_ids = [user['user_id'] for user in users]

        # 2. Find posts that match the query
        posts = list(posts_collection.find({
            "$or": [
                {"tags.age": {"$regex": query, "$options": "i"}},
                {"tags.gender": {"$regex": query, "$options": "i"}},
                {"tags.travel_type": {"$regex": query, "$options": "i"}},
                {"tags.region": {"$regex": query, "$options": "i"}},
                {"tags.cost": {"$regex": query, "$options": "i"}},
                {"tags.relationship": {"$regex": query, "$options": "i"}},
                {"tags.during": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}},
                {"user_id": {"$in": user_ids}}
            ]
        }))

        for post in posts:
            post['_id'] = str(post['_id'])
            post_user = users_collection.find_one({'user_id': post['user_id']})
            post['nickname'] = post_user.get('nickname', 'Unknown User') if post_user else 'Unknown User'
            post['profile_image'] = post_user.get('profile_image', 'image/uploads_profile/default_profile.png') if post_user else 'image/uploads_profile/default_profile.png'
            post['region'] = post.get('tags', {}).get('region', 'Unknown Region')

            tags = post.get('tags', {})
            tags_list = []
            for key, value in tags.items():
                if isinstance(value, list):
                    tags_list.extend(value)
                else:
                    tags_list.append(value)
            post['tags_list'] = tags_list
        
        # Debug: print posts to check data
        print(posts)

        return jsonify({'posts': posts})

    # No query provided: render search.html
    return render_template('search.html')






@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    selected_region = request.json.get('region')

    if selected_region:
        pipeline = [
            {"$match": {"tags.region": selected_region}},  # 지역 필터링
            {"$sample": {"size": 2}}  # 무작위로 2개 선택
        ]
        posts = list(posts_collection.aggregate(pipeline))

        for post in posts:
            post['_id'] = str(post['_id'])  # ObjectId를 문자열로 변환
            post['image_path'] = url_for('static', filename=post['image_path'])  # 이미지 경로 처리

        return jsonify({"posts": posts})

    return jsonify({"posts": []}), 404

def get_most_common_tag_value(tag_name):
    pipeline = [
        {"$group": {"_id": f"$tags.{tag_name}", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    result = list(posts_collection.aggregate(pipeline))
    if result:
        return result[0]['_id']
    else:
        return "미선택"

@app.route('/add', methods=['POST'])
def add_document():
    data = request.json
    posts_collection.insert_one(data)
    return jsonify({"message": "Document added!"}), 201

@app.route('/documents', methods=['GET'])
def get_documents():
    documents = list(posts_collection.find({}, {"_id": 0}))  # MongoDB에서 문서를 가져오고, _id 필드 제외
    return jsonify(documents), 200





@app.route('/save')
def save():
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('login'))

    user_data = users_collection.find_one({'user_id': user_id})

    if not user_data:
        return redirect(url_for('login'))

    saved_posts_ids = user_data.get('saved_posts', [])

    # posts_collection의 '_id' 필드 타입 확인
    sample_post = posts_collection.find_one()
    if sample_post and isinstance(sample_post['_id'], ObjectId):
        # 'saved_posts_ids'를 ObjectId로 변환
        try:
            saved_posts_object_ids = [ObjectId(post_id) for post_id in saved_posts_ids]
        except Exception as e:
            print(f"Invalid ObjectId: {e}")
            saved_posts_object_ids = []
        query = {'_id': {'$in': saved_posts_object_ids}}
    else:
        # '_id'가 문자열인 경우 변환 없이 사용
        query = {'_id': {'$in': saved_posts_ids}}

    # 저장된 게시물 가져오기
    saved_posts = list(posts_collection.find(query))

    # 이미지 처리
    for post in saved_posts:
        image_path = os.path.join('static', post['image_path'])
        if os.path.exists(image_path):
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                post['image_data'] = base64.b64encode(image_data).decode('utf-8')
        else:
            post['image_data'] = None  # 기본 이미지 설정 가능

    return render_template('save.html', posts=saved_posts)



@app.route('/remove_accessory', methods=['POST'])
def remove_accessory():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': 'User ID not provided'})

    # 사용자 데이터에서 accessory_suffix를 제거
    users_collection.update_one(
        {'user_id': user_id},
        {'$set': {'accessory_suffix': ''}}
    )

    return jsonify({'success': True})

def calculate_character_image(stack_credit, nocheck, accessory_suffix=''):
    # 기본 캐릭터 이미지 결정
    if stack_credit < 100:
        character_image = 'character_1.png'
    elif stack_credit < 300:
        character_image = 'character_2.png'
    elif stack_credit < 500:
        character_image = 'character_3.png'
    elif stack_credit < 800:
        character_image = 'character_4.png'
    else:
        character_image = 'character_5.png'

    # nocheck 값에 따라 캐릭터 이미지 수정
    if nocheck < 10:
        character_image = character_image.replace('.png', '_default.png')
        # nocheck가 10 미만일 때만 액세서리 적용
        if accessory_suffix:
            character_image = character_image.replace('.png', accessory_suffix)
    elif 10 <= nocheck < 20:
        character_image = character_image.replace('.png', '_dust.png')
    elif 20 <= nocheck < 30:
        character_image = character_image.replace('.png', '_band.png')
    elif 30 <= nocheck < 40:
        character_image = character_image.replace('.png', '_poop.png')
    elif 40 <= nocheck < 50:
        character_image = character_image.replace('.png', '_fly.png')
    elif nocheck >= 50:
        character_image = character_image.replace('.png', '_ghost.png')

    return character_image

@app.route('/my')
def my():
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('login'))

    # MongoDB에서 사용자 데이터 가져오기
    user_data = users_collection.find_one(
        {'user_id': user_id},
        {
            'stack_credit': 1,
            'nocheck': 1,
            'profile_image': 1,
            'accessory_suffix': 1,
            'purchased_accessories': 1,
            'nickname': 1  # Fetch the nickname
        }
    )

    if user_data:
        stack_credit = user_data.get('stack_credit', 0)
        nocheck = user_data.get('nocheck', 0)
        profile_image = user_data.get('profile_image', '/static/image/default_profile.png')
        accessory_suffix = user_data.get('accessory_suffix', '')
        purchased_accessories = user_data.get('purchased_accessories', [])
        nickname = user_data.get('nickname', '사용자')  # Default nickname if not found
    else:
        stack_credit = 0
        nocheck = 0
        profile_image = '/static/image/default_profile.png'
        accessory_suffix = ''
        purchased_accessories = []
        nickname = '사용자'  # Default nickname

    # 캐릭터 이미지 계산
    character_image = calculate_character_image(stack_credit, nocheck, accessory_suffix)

    # 사용자 게시물 가져오기
    posts = list(posts_collection.find({'user_id': user_id}).sort('_id', -1).limit(2))
    for post in posts:
        post['_id'] = str(post['_id'])

    # 액세서리 목록에 구매 여부 추가
    accessories = []
    for accessory in ACCESSORIES:
        accessory_copy = accessory.copy()
        accessory_copy['purchased'] = accessory['name'] in purchased_accessories
        accessories.append(accessory_copy)

    # 템플릿 렌더링
    return render_template(
        'my.html',
        posts=posts,
        character_image=character_image,
        profile_image=profile_image,
        nocheck=nocheck,
        user_id=user_id,
        nickname=nickname,  # Pass the nickname to the template
        accessories=accessories
    )


@app.route('/get_updated_character_image', methods=['POST'])
def get_updated_character_image():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': 'User ID not provided'})

    # 업데이트된 사용자 데이터 가져오기
    user_data = users_collection.find_one(
        {'user_id': user_id},
        {'stack_credit': 1, 'nocheck': 1, 'accessory_suffix': 1}
    )

    if not user_data:
        return jsonify({'success': False, 'message': 'User not found'})

    stack_credit = user_data.get('stack_credit', 0)
    nocheck = user_data.get('nocheck', 0)
    accessory_suffix = user_data.get('accessory_suffix', '')

    # 캐릭터 이미지 다시 계산
    character_image = calculate_character_image(stack_credit, nocheck, accessory_suffix)

    return jsonify({'success': True, 'character_image': character_image})

# 로그인 함수와 기타 필요한 라우트 및 함수들 추가
ACCESSORIES = [
    {'name': 'straw_hat', 'display_name': '밀짚모자', 'price': 15},
    {'name': 'carrot_hat', 'display_name': '당근모자', 'price': 45},
    {'name': 'apple_hat', 'display_name': '사과모자', 'price': 45},
    {'name': 'orange_hat', 'display_name': '귤모자', 'price': 45},
    {'name': 'crown_hat', 'display_name': '왕관모자', 'price': 100},
    {'name': 'egg', 'display_name': '계란', 'price': 25},
    {'name': 'orange_half','display_name': '반쪽 귤', 'price': 25},
    {'name': 'donut', 'display_name': '도넛', 'price': 50},
    {'name': 'sticker', 'display_name': '스티커', 'price': 40},
    {'name': 'sunglass', 'display_name': '선글라스', 'price': 45},
    {'name': 'mustache', 'display_name': '수염', 'price': 45},
    {'name': 'ribbon', 'display_name': '리본', 'price': 50} 
]


@app.route('/reduce_nocheck', methods=['POST'])
def reduce_nocheck():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': 'User ID not provided'})

    users_collection.update_one({'user_id': user_id}, {'$inc': {'nocheck': -10}})

    return jsonify({'success': True})
@app.route('/buy_accessory', methods=['POST'])
def buy_accessory():
    data = request.get_json()
    user_id = data.get('user_id')
    accessory_name = data.get('accessory_name')

    if not user_id or not accessory_name:
        return jsonify({'success': False, 'message': '잘못된 요청입니다.'})

    # 사용자 데이터 가져오기
    user_data = users_collection.find_one({'user_id': user_id})

    if not user_data:
        return jsonify({'success': False, 'message': '사용자를 찾을 수 없습니다.'})

    credits = user_data.get('credits', 0)
    purchased_accessories = user_data.get('purchased_accessories', [])

    # 이미 구매한 액세서리인지 확인
    if accessory_name in purchased_accessories:
        return jsonify({'success': False, 'message': '이미 구매한 액세서리입니다.'})

    # 액세서리 가격 가져오기
    accessory = next((a for a in ACCESSORIES if a['name'] == accessory_name), None)

    if not accessory:
        return jsonify({'success': False, 'message': '액세서리를 찾을 수 없습니다.'})

    price = accessory['price']

    # 크레딧이 충분한지 확인
    if credits < price:
        return jsonify({'success': False, 'message': '크레딧이 부족합니다.'})

    # 크레딧 차감 및 액세서리 구매 처리
    users_collection.update_one(
        {'user_id': user_id},
        {
            '$inc': {'credits': -price},
            '$push': {'purchased_accessories': accessory_name}
        }
    )

    return jsonify({'success': True})
@app.route('/select_accessory', methods=['POST'])
def select_accessory():
    data = request.get_json()
    user_id = data.get('user_id')
    accessory_name = data.get('accessory_name')

    if not user_id or not accessory_name:
        return jsonify({'success': False, 'message': '잘못된 요청입니다.'})

    # 사용자 데이터 가져오기
    user_data = users_collection.find_one({'user_id': user_id})

    if not user_data:
        return jsonify({'success': False, 'message': '사용자를 찾을 수 없습니다.'})

    purchased_accessories = user_data.get('purchased_accessories', [])

    # 구매한 액세서리인지 확인
    if accessory_name not in purchased_accessories:
        return jsonify({'success': False, 'message': '구매하지 않은 액세서리입니다.'})

    # 액세서리 접미사 업데이트
    accessory_suffix = '_' + accessory_name + '.png'

    users_collection.update_one(
        {'user_id': user_id},
        {'$set': {'accessory_suffix': accessory_suffix}}
    )

    return jsonify({'success': True})

@app.route('/deco')
def deco():
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('login'))

    # 사용자 데이터 가져오기
    user_data = users_collection.find_one(
        {'user_id': user_id},
        {'credits': 1, 'purchased_accessories': 1, 'accessory_suffix': 1, 'stack_credit': 1, 'nocheck': 1}
    )

    if user_data:
        credits = user_data.get('credits', 0)
        purchased_accessories = user_data.get('purchased_accessories', [])
        accessory_suffix = user_data.get('accessory_suffix', '')
        stack_credit = user_data.get('stack_credit', 0)
        nocheck = user_data.get('nocheck', 0)
    else:
        credits = 0
        purchased_accessories = []
        accessory_suffix = ''
        stack_credit = 0
        nocheck = 0

    # 액세서리 목록에 구매 여부 추가
    accessories = []
    for accessory in ACCESSORIES:
        accessory_copy = accessory.copy()
        accessory_copy['purchased'] = accessory['name'] in purchased_accessories
        accessories.append(accessory_copy)

    # 캐릭터 이미지 계산 (이미 구현된 함수 사용)
    character_image = calculate_character_image(stack_credit, nocheck, accessory_suffix)
    original_character_image = calculate_character_image(stack_credit, nocheck)

    return render_template(
        'deco.html',
        accessories=accessories,
        credits=credits,
        user_id=user_id,
        character_image=character_image,
        original_character_image=original_character_image,
        nocheck=nocheck
    )

@app.route('/badge')
def badge_collection():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # 사용자가 방문한 지역을 추출
    user_posts = posts_collection.find({'user_id': user_id})
    visited_regions = set()
    for post in user_posts:
        region = post.get('tags', {}).get('region')
        if region:
            visited_regions.add(region)

    # 지역별 도시 목록 정의
    regions = {
        '한국': ['서울', '부산', '대구', '여수', '인천'],
        '유럽': ['프랑스', '영국', '스위스', '이탈리아','스페인'],
        '아시아': ['일본', '중국', '싱가포르','태국'],
        '북미': ['미국', '캐나다'],
        '남미': [ '멕시코', '브라질', '자메이카', '아르헨티나'],
        '오세아니아': ['호주', '뉴질랜드' ],
        '아프리카': ['남아공', '우간다', '콩고', '가나', '말리']
    }

    # 각 지역별로 뱃지 정보 생성
    badge_locations = {}
    for region_name, cities in regions.items():
        badges = []
        for city in cities:
            if region_name == '한국':
                # 한국은 '아시아 - 한국 - 도시' 형식으로 저장되어 있으므로 예외 처리
                full_region_name = f'아시아 - 한국 - {city}'
            else:
                # 다른 지역은 '지역명 - 도시' 형식으로 처리
                full_region_name = f'{region_name} - {city}'

            if full_region_name in visited_regions:
                # 사용자가 해당 지역을 방문했을 경우
                badges.append({
                    'name': city,
                    'image': url_for('static', filename=f'image/{city}.png'),  # 획득한 뱃지 이미지 경로
                    'locked': False
                })
            else:
                # 방문하지 않았을 경우 잠금 처리
                badges.append({
                    'name': city,
                    'image': url_for('static', filename='image/잠금.png'),  # 잠금 이미지 경로
                    'locked': True
                })
        badge_locations[region_name] = badges

    return render_template('badge_collection.html', badge_locations=badge_locations)


@app.route('/save_accessory', methods=['POST'])
def save_accessory():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    accessory_suffix = data.get('accessory_suffix')

    # Update the user's accessory in the database
    users_collection.update_one({'user_id': user_id}, {'$set': {'accessory_suffix': accessory_suffix}})

    return jsonify({'success': True}), 200


@app.route('/view_mypost/<post_id>')
def view_mypost(post_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # 게시물 가져오기
    post = posts_collection.find_one({'_id': ObjectId(post_id)})
    if not post:
        return "Post not found", 404

    # 사용자 정보 가져오기
    user = users_collection.find_one({"user_id": post.get('user_id')})
    if not user:
        return "User not found", 404

    post['_id'] = str(post['_id'])

    # 사용자 프로필 이미지와 닉네임 추가
    post['profile_image'] = user.get('profile_image', 'default_profile.png')
    post['nickname'] = user.get('nickname', '익명')

    # 이미지 처리
    image_path = os.path.join('static', post.get('image_path', ''))
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            encoded_image_data = base64.b64encode(image_file.read()).decode('utf-8')
        post['image_data'] = encoded_image_data
    else:
        post['image_data'] = ''

    # 현재 사용자가 게시물을 저장했는지 확인
    user_data = users_collection.find_one({'user_id': user_id})
    saved_posts = user_data.get('saved_posts', [])
    saved_by_user = post['_id'] in saved_posts

    # 필요하면 user_id를 템플릿에 전달
    return render_template('myPostDetail.html', post=post, saved_by_user=saved_by_user, user_id=user_id)





@app.route('/image/<post_id>')
def serve_image(post_id):
    post = posts_collection.find_one({'_id': ObjectId(post_id)})
    if not post or 'image_data' not in post:
        return '', 404
    image_data_binary = post['image_data']
    return Response(image_data_binary, mimetype='image/jpeg')


@app.route('/mypost')
def mypost():
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('login'))

    # Fetch posts for the logged-in user
    posts = list(posts_collection.find({'user_id': user_id}))

    # Convert MongoDB's ObjectId to a string for use in the template
    for post in posts:
        post['_id'] = str(post['_id'])

    # Pass the posts data to the 'mypost.html' template
    return render_template('mypost.html', posts=posts)

@app.route('/post/<post_id>')
def post(post_id):
    post_data = posts_collection.find_one({'_id': ObjectId(post_id)})

    if not post_data:
        return "No posts found", 404

    # 게시물을 작성한 사용자의 ID 가져오기
    user_id = post_data.get('user_id')

    # 작성자 정보 가져오기
    user = users_collection.find_one({"user_id": user_id})

    if not user:
        return "User not found", 404

    # 게시물 데이터에 작성자의 프로필 이미지와 닉네임 추가
    post_data['profile_image'] = user.get('profile_image', 'default_profile.png')
    post_data['nickname'] = user.get('nickname', '익명')

    post_data['username'] = post_data.get('username', 'Anonymous')
    post_data['post_content'] = post_data.get('content', '')
    post_data['tags'] = post_data.get('tags', {})
    post_data['comments'] = post_data.get('comments', [])
    post_data['likes'] = post_data.get('likes', 0)

    # 이미지 데이터 처리
    image_path = os.path.join('static', post_data['image_path'])

    if not os.path.exists(image_path):
        return "Image not found", 404

    with open(image_path, "rb") as image_file:
        image_data_base64 = base64.b64encode(image_file.read()).decode('utf-8')

    post_data['image_data'] = image_data_base64
    post_data['image_filename'] = os.path.basename(post_data['image_path'])

    # 현재 사용자 ID 가져오기
    current_user_id = session.get('user_id')

    # 현재 사용자가 해당 게시물을 좋아요했는지 확인
    post_data['liked_by_user'] = False
    if current_user_id:
        post_data['liked_by_user'] = current_user_id in post_data.get('liked_by', [])

    # 현재 사용자가 해당 게시물을 저장했는지 확인
    saved_by_user = False
    if current_user_id:
        current_user_data = users_collection.find_one({"user_id": current_user_id})
        if current_user_data:
            saved_posts = current_user_data.get('saved_posts', [])
            saved_by_user = str(post_id) in saved_posts

    return render_template('post.html', post=post_data, user_id=current_user_id, saved_by_user=saved_by_user)

@app.route('/add_comment/<post_id>', methods=['POST'])
def add_comment(post_id):
    comment_text = request.form.get('comment', '').strip()
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"success": False, "error": "로그인이 필요합니다."}), 401

    user_data = users_collection.find_one({'user_id': user_id})
    if not user_data or 'nickname' not in user_data:
        return jsonify({"success": False, "error": "사용자의 닉네임을 찾을 수 없습니다."}), 400

    nickname = user_data['nickname']

    if not comment_text:
        return jsonify({"success": False, "error": "댓글을 입력해주세요."}), 400

    post = posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        return jsonify({"success": False, "error": "게시물을 찾을 수 없습니다."}), 404

    comment = {'nickname': nickname, 'text': comment_text}

    posts_collection.update_one({'_id': ObjectId(post_id)}, {'$push': {'comments': comment}})

    return jsonify({"success": True, "comment": comment}), 200

@app.route('/like/<post_id>', methods=['POST'])
def like(post_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401

    post_data = posts_collection.find_one({'_id': ObjectId(post_id)})

    if not post_data:
        return jsonify({'error': 'Post not found'}), 404

    if 'liked_by' not in post_data:
        post_data['liked_by'] = []

    if user_id in post_data['liked_by']:
        # 좋아요 취소
        posts_collection.update_one(
            {'_id': ObjectId(post_id)},
            {'$inc': {'likes': -1}, '$pull': {'liked_by': user_id}}
        )
        new_like_status = False
    else:
        # 좋아요 추가
        posts_collection.update_one(
            {'_id': ObjectId(post_id)},
            {'$inc': {'likes': 1}, '$push': {'liked_by': user_id}}
        )
        new_like_status = True

    updated_post = posts_collection.find_one({'_id': ObjectId(post_id)})

    return jsonify({
        'likes': updated_post.get('likes', 0),
        'liked_by_user': new_like_status
    })

@app.route('/save_post/<post_id>', methods=['POST'])
def save_post(post_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401

    post_data = posts_collection.find_one({'_id': ObjectId(post_id)})
    if not post_data:
        return jsonify({'error': 'Post not found'}), 404

    user_data = users_collection.find_one({'user_id': user_id})
    if not user_data:
        return jsonify({'error': 'User not found'}), 404

    saved_posts = user_data.get('saved_posts', [])

    if str(post_id) in saved_posts:
        # 저장 취소
        users_collection.update_one(
            {'user_id': user_id},
            {'$pull': {'saved_posts': str(post_id)}}
        )
        saved = False
    else:
        # 저장
        users_collection.update_one(
            {'user_id': user_id},
            {'$push': {'saved_posts': str(post_id)}}
        )
        saved = True

    return jsonify({'saved': saved})









@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    try:
        # MongoDB에서 해당 게시물 삭제
        result = posts_collection.delete_one({'_id': ObjectId(post_id)})
        if result.deleted_count > 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': '삭제할 게시물을 찾을 수 없습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'게시물 삭제 중 오류 발생: {str(e)}'})
    

@app.route('/hotpost')
def hotpost():
    # 세션에서 유저 아이디 가져오기
    user_id = session.get('user_id')
    
    # 로그인되어 있지 않으면 로그인 페이지로 리다이렉트
    if not user_id:
        return redirect(url_for('login'))

    # 모든 포스트 중에서 'likes' 기준으로 상위 6개 가져오기
    top_posts = list(posts_collection.find()
                     .sort('likes', DESCENDING)
                     .limit(6))

    hot_post_ids = []
    for post in top_posts:
        # 유저 컬렉션에서 닉네임 가져오기
        post_user = users_collection.find_one({'user_id': post['user_id']})
        post['nickname'] = post_user.get('nickname', 'Unknown User') if post_user else 'Unknown User'
        post['tags'] = post.get('tags', {})
        post['post_content'] = post.get('content', "")
        hot_post_ids.append(post['_id'])

        # 이미지 경로가 있으면 파일을 읽어옴
        if post.get('image_path'):
            image_path = os.path.join('static', post['image_path'])
            try:
                with open(image_path, "rb") as image_file:
                    post['image_data'] = image_file.read()  # 이미지 파일 내용 읽기
            except FileNotFoundError:
                post['image_data'] = None

    # 'hotpost.html' 템플릿에 top_posts 데이터를 넘겨서 렌더링
    return render_template('hotpost.html', top_posts=top_posts)






@app.route('/change_profile', methods=['GET', 'POST'])
def change_profile():
    user_id = session.get('user_id')  # Get user_id from session

    if not user_id:
        return redirect(url_for('login'))  # Redirect to login if no user is logged in

    if request.method == 'POST':
        # Access the uploaded file from the form
        profile_image = request.files.get('profile_image')
        upload_folder = 'static/image/uploads_profile'  # Folder to store uploaded profile images

        # Ensure the upload folder exists
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        if profile_image:
            # Save the uploaded image to the specified folder
            file_path = os.path.join(upload_folder, profile_image.filename)
            profile_image.save(file_path)

            # Prepare the path to store in the database
            profile_image_path = f'/static/image/uploads_profile/{profile_image.filename}'

            # Update the user's profile image in the database
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "profile_image": profile_image_path
                }}
            )
        else:
            # If no image is uploaded, set the default profile image
            profile_image_path = '/static/image/profile.png'
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "profile_image": profile_image_path
                }}
            )

        # Redirect to the settings page after uploading
        return redirect(url_for('setting'))

    return render_template('setting.html')





@app.route('/setting')
def setting():
    user_id = session.get('user_id')

    if not user_id:
        return redirect(url_for('login'))

    #Fetch user data from MongoDB based on user_id
    user_data = users_collection.find_one({'user_id': user_id}, 
                                          {'_id': 0, 'nickname': 1, 'name': 1, 'phone_number': 1, 'profile_image': 1, 
                                           'gender': 1, 'age': 1, 'prefer': 1, 'user_id': 1, 'password': 1, 'type': 1})

    if not user_data:
        flash("User data not found.")
        return redirect(url_for('home'))

    # Extract values from the user_data
    nickname = user_data.get('nickname', 'Unknown')
    name = user_data.get('name', 'Unknown')
    phone_number = user_data.get('phone_number', 'Unknown')
    profile_image = user_data.get('profile_image', '/static/image/default_profile.png')
    gender = user_data.get('gender', 'Unknown')
    age = user_data.get('age', 'Unknown')
    prefer = user_data.get('prefer', 'Unknown')
    user_id_value = user_data.get('user_id', 'Unknown')
    password = user_data.get('password', '********')
    user_type = user_data.get('type', 'general')

    # Determine login_id based on type
    if user_type == 'naver':
        login_id = 'naver-login'
    elif user_type == 'kakao':
        login_id = 'kakao-login'
    elif user_type == 'google':
        login_id = 'google-login'
    else:
        login_id = user_id_value  # Use the user_id for general type

    # Render the settings page with the user data
    return render_template('setting.html', 
                           nickname=nickname, 
                           name=name, 
                           phone_number=phone_number, 
                           profile_image=profile_image,
                           gender=gender, 
                           age=age, 
                           prefer=prefer, 
                           login_id=login_id, 
                           password=password,
                           user_type=user_type)  # Pass user_type to the template





@app.route('/change_phone', methods=['GET', 'POST'])
def change_phone():
    user_id = session.get('user_id')  # Get the logged-in user_id from the session
    if request.method == 'POST':
        phone_number = request.form['phone_number']

        # Check if the verification code was submitted
        verification_code = request.form.get('verification_code')
        saved_code = session.get('verification_code')

        # Allow "test-user" to bypass verification
        if verification_code == "test-user" or (verification_code and saved_code):
            # Verify the code
            if verification_code == "test-user" or verification_code == saved_code:
                # Code matches, save the phone number to the database
                users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"phone_number": phone_number}}
                )
                session.pop('verification_code', None)  # Remove the code from session after use
                return redirect(url_for('setting'))  # Ensure the redirection is to 'setting'
            else:
                # Code doesn't match, show an error message
                flash('인증번호가 일치하지 않습니다. 다시 시도해주세요.')
        else:
            # No verification code submitted yet, so send one
            sent_code = send_verification_code(phone_number)
            if sent_code:
                session['verification_code'] = str(sent_code)  # Save the code in session
                flash('인증번호가 전송되었습니다. 확인 후 입력해주세요.')
            else:
                flash('메시지 전송에 실패했습니다. 나중에 다시 시도해주세요.')

    return render_template('change-phone.html')




@app.route('/change-password', methods=['GET', 'POST'])
def change_password_handler():
    if request.method == 'POST':
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))  # 로그인하지 않았을 경우, 로그인 페이지로 리디렉션

        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # 비밀번호와 확인 비밀번호가 일치하는지 확인
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('change_password_handler'))

        # scrypt로 비밀번호 해시 생성
        hashed_password = hash_password(password)

        # 데이터베이스에 해시된 비밀번호 업데이트
        users_collection.update_one({'user_id': user_id}, {'$set': {'password': hashed_password}})

        flash('Password updated successfully')
        return redirect(url_for('setting'))

    # GET 요청인 경우, 비밀번호 변경 폼 렌더링
    return render_template('change-password.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # 세션에서 'user_id' 제거
    return redirect(url_for('login'))  # 로그아웃 후 로그인 페이지로 리다이렉트




@app.route('/change-age', methods=['GET', 'POST'])
def change_age():
    if request.method == 'POST':
        # Retrieve selected age and user_id from session
        selected_age = request.form.get('age')
        user_id = session.get('user_id')

        if user_id and selected_age:
            # Update the user's age in the database
            users_collection.update_one({'user_id': user_id}, {'$set': {'age': selected_age}})
        
        # Redirect to setting.html after successful update
        return redirect(url_for('setting'))

    # Render the form if the request method is GET
    return render_template('change_age.html')

@app.route('/change-prefer', methods=['GET', 'POST'])
def change_prefer():
    if request.method == 'POST':
        # Retrieve selected preference and user_id from session
        selected_prefer = request.form.get('prefer')
        user_id = session.get('user_id')

        if user_id and selected_prefer:
            # Update the user's preference in the database
            users_collection.update_one({'user_id': user_id}, {'$set': {'prefer': selected_prefer}})
        
        # Redirect to setting.html after successful update
        return redirect(url_for('setting'))

    # Render the form if the request method is GET
    return render_template('change_prefer.html')

@app.route('/change-gender', methods=['GET', 'POST'])
def change_gender():
    if request.method == 'POST':
        # Retrieve selected gender and user_id from session
        selected_gender = request.form.get('gender')
        user_id = session.get('user_id')

        if user_id and selected_gender:
            # Update the user's gender in the database
            users_collection.update_one({'user_id': user_id}, {'$set': {'gender': selected_gender}})
        
        # Redirect to setting.html after successful update
        return redirect(url_for('setting'))

    # Render the form if the request method is GET
    return render_template('change_gender.html')



if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)



