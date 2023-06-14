import spacy
import rasa
import sqlite3
import requests
import geocoder

model_path = "./path_to_trained_nlu_model"
database_path = "./user_data.db"


class User:
    def __init__(self, name=None, email=None, blood_type=None, location=None):
        self.name = name
        self.email = email
        self.blood_type = blood_type
        self.location = location

    def update_profile(self, name=None, email=None, blood_type=None, location=None):
        if name:
            self.name = name
        if email:
            self.email = email
        if blood_type:
            self.blood_type = blood_type
        if location:
            self.location = location


def extract_entities(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    entities = []
    for entity in doc.ents:
        if entity.label_ == "PERSON" or entity.label_ == "ORG":
            entities.append(entity.text)
    return entities


def process_user_input(text):
    user_intent = None
    entities = extract_entities(text)

    if entities:
        interpreter = rasa.nlu.Interpreter.load(model_path)
        result = interpreter.parse(entities[0])
        user_intent = result['intent']['name']

    return user_intent


def create_user_table():
    conn = sqlite3.connect(database_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                (name text, email text PRIMARY KEY, blood_type text, location text)''')
    conn.commit()
    conn.close()


def check_existing_user(email):
    conn = sqlite3.connect(database_path)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user_data = c.fetchone()
    conn.close()
    return user_data


def register_user():
    print("Welcome to the blood donation registration!")
    name = input("Please enter your name: ")
    email = input("Please enter your email address: ")
    blood_type = input("Please enter your blood type: ")

    existing_user = check_existing_user(email)
    if existing_user:
        print("User already exists with this email. Skipping registration.")
        return None

    user_location = get_user_location()
    user = User(name, email, blood_type, user_location)

    conn = sqlite3.connect(database_path)
    c = conn.cursor()
    c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (user.name, user.email, user.blood_type, user.location))
    conn.commit()
    conn.close()

    return user


def update_user_profile(user):
    print("Let's update your profile.")
    name = input("Enter your new name (or press Enter to keep the current name): ")
    email = input("Enter your new email (or press Enter to keep the current email): ")
    blood_type = input("Enter your new blood type (or press Enter to keep the current blood type): ")
    location = input("Enter your new location (or press Enter to keep the current location): ")
    user.update_profile(name, email, blood_type, location)

    conn = sqlite3.connect(database_path)
    c = conn.cursor()
    c.execute("UPDATE users SET name=?, blood_type=?, location=? WHERE email=?",
              (user.name, user.blood_type, user.location, user.email))
    conn.commit()
    conn.close()


def get_user_location():
    try:
        # Use an IP geolocation service to get the user's IP address
        ip_response = requests.get("https://api.ipify.org?format=json")
        ip_data = ip_response.json()
        ip_address = ip_data["ip"]

        # Use geocoder library to retrieve the location information based on the IP address
        g = geocoder.ip(ip_address)
        if g.ok:
            location = g.geojson["features"][0]["properties"]["raw"]
            return location
        else:
            print("Unable to retrieve user location.")
    except requests.exceptions.RequestException as e:
        print("Error occurred while retrieving IP address:", str(e))

    return None


def main():
    create_user_table()

    while True:
        print("\nBlood Donation System")
        print("1. Register")
        print("2. Update Profile")
        print("3. Exit")
        choice = input("Select an option: ")

        if choice == "1":
            user = register_user()
            if user:
                print("Registration Successful!")
                print(f"Name: {user.name}")
                print(f"Email: {user.email}")
                print(f"Blood Type: {user.blood_type}")
                print(f"Location: {user.location}")
        elif choice == "2":
            email = input("Enter your email: ")
            existing_user = check_existing_user(email)
            if existing_user:
                user = User(existing_user[0], existing_user[1], existing_user[2], existing_user[3])
                update_user_profile(user)
                print(
                    f"Updated Profile - Name: {user.name}, Email: {user.email}, Blood Type: {user.blood_type}, Location: {user.location}")
            else:
                print("User not found. Please register first.")
        elif choice == "3":
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
