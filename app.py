# app.py
from flask import Flask, render_template, request, jsonify
import firebase_admin
import requests
from newsapi import NewsApiClient
from firebase_admin import credentials, firestore
from datetime import date, datetime


app = Flask(__name__)

#Initialize Firebase app
cred = credentials.Certificate("avis-version-1-firebase-adminsdk-f8gqq-d3e9484930.json
") 
firebase_admin.initialize_app(cred)
db = firestore.client()

# weather
api_key = '158daff2807cd485622b18ad3693b507'
lat = 13.0015
lon = 80.1182

# news
api_key2 = '9d9ee06becc74255a6b081f9ecca7b1f' 

@app.route('/')
def home():

    # weather
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        weather_data = response.json()
        
        weather_description = weather_data['weather'][0]['description']
        temperature = weather_data['main']['temp']
        city = weather_data['name']
        
        print(f"Current weather in {city}: {weather_description}")
        print(f"Temperature: {temperature}°C")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")


    # news
    title = "Not found"
    description  = "Not found"
    newsapi = NewsApiClient(api_key=api_key2)
    try:
        top_headline = newsapi.get_top_headlines(q='Business', language='en', page_size=1)
        article = top_headline['articles'][0] if top_headline['totalResults'] > 0 else None
        if article:
            title = article['title']
            description = article['description']
        else:
            print('No articles found.')
    except Exception as e:
         print(f'An error occurred: {e}')
    
    # random facts
    url = "https://useless-facts.sameerkumar.website/api"
    try:
        response = requests.get(url)
        data = response.json()
        fact = data["data"]
    except Exception as e:
        print("Error fetching random fact:", e)
        
    # motivation 
    url = "https://zenquotes.io/api/random"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            quote = data[0]
            if 'q' in quote and 'a' in quote:
                motivation = f'"{quote["q"]}" - {quote["a"]}'
            else:
                print("Failed to retrieve a quote. Response structure is unexpected.")
        else:
            print("Failed to retrieve a quote. No data found.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    # wallet
    wallet_ref = db.collection('details').document('wallet')
    wallet_data = wallet_ref.get()
    if wallet_data.exists:
        amount = wallet_data.to_dict().get('amount')
    else:
        amount = "N/A"  # Default value if amount is not found

    print(amount)

    # time
    current_date = date.today()
    day_of_week = current_date.strftime('%A')
    time = f"{day_of_week} : {current_date}"
    return render_template('index.html',time = time, current_amount=amount, quote = motivation, city = city, weather_data = temperature, weather_description = weather_description ,news_heading = title , news_des = description ,fact = fact)

@app.route('/get_tasks', methods=['GET'])
def get_tasks():
    today = date.today().isoformat()
    tasks_ref = db.collection('tasks').where('date', '==', today)
    tasks = tasks_ref.stream()
    
    task_list = []
    for task in tasks:
        task_dict = task.to_dict()
        task_list.append({
            'name': task_dict.get('name'),
            'time': task_dict.get('time'),
            'date': task_dict.get('date')
        })
    for task in task_list:
        task['parsed_time'] = datetime.strptime(task['time'], "%H:%M").time()

    task_list.sort(key=lambda x: x['parsed_time'])
    for task in task_list:
        task.pop('parsed_time', None)

    return jsonify(task_list)


@app.route('/add_task', methods=['POST'])
def add_task():
    task_data = request.json
    task_name = task_data.get('name')
    task_time = task_data.get('time')
    task_date = task_data.get('date')

    db.collection('tasks').add({
        'name': task_name,
        'time': task_time,
        'date': task_date
    })

    return jsonify({'success': True}), 200

@app.route('/update_wallet_amount', methods=['POST'])
def update_wallet_amount():
    request_data = request.json
    new_amount = request_data.get('amount')

    # Update amount in Firebase
    wallet_ref = db.collection('details').document('wallet')
    wallet_ref.set({
        'amount': new_amount
    })

    return jsonify({'success': True}), 200

if __name__ == '__main__':
    app.run(debug=True , port=9297 , host='0.0.0.0')
