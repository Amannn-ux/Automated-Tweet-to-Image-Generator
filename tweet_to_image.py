from flask import Flask, request, jsonify, send_file, render_template
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os

app = Flask(__name__)

# Twitter API credentials (set your own keys here or use environment variables)
BEARER_TOKEN = os.getenv("BEARER_TOKEN", "Replace with your actual Bearer Token")  

# Function to fetch tweet data from Twitter API
def fetch_tweet(tweet_url):
    tweet_id = tweet_url.split("/")[-1].split("?")[0]
    url = f"https://api.twitter.com/2/tweets/{tweet_id}?expansions=author_id&user.fields=name,username,profile_image_url"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    
    # Debugging the response for more details
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching tweet: {response.status_code}")
        print(response.text)  # Print the full error response for debugging
        return None

# Function to create an image of the tweet
def create_tweet_image(tweet_data):
    tweet = tweet_data['data']
    user = tweet_data['includes']['users'][0]

    # Set up the canvas
    width, height = 800, 400
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Load fonts - use a default font if the path is invalid
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Update with a valid font path
        font_large = ImageFont.truetype(font_path, 24)
        font_small = ImageFont.truetype(font_path, 18)
    except IOError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw profile image
    profile_image_url = user['profile_image_url'].replace('_normal', '')
    print(f"Profile Image URL: {profile_image_url}")  # Debugging the profile image URL
    profile_image_response = requests.get(profile_image_url)
    
    if profile_image_response.status_code == 200:
        profile_image = Image.open(BytesIO(profile_image_response.content)).resize((80, 80))
        image.paste(profile_image, (20, 20))

    # Draw username and tweet text
    draw.text((120, 20), user['name'], font=font_large, fill="black")
    draw.text((120, 60), f"@{user['username']}", font=font_small, fill="gray")
    draw.text((20, 120), tweet['text'], font=font_small, fill="black")

    # Save the image to a BytesIO object
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_image():
    data = request.json
    tweet_url = data.get("tweet_url")

    if not tweet_url:
        return jsonify({"error": "Tweet URL is required"}), 400

    tweet_data = fetch_tweet(tweet_url)
    if not tweet_data:
        return jsonify({"error": "Failed to fetch tweet data. Check the URL or API credentials."}), 400

    image = create_tweet_image(tweet_data)
    return send_file(image, mimetype="image/png", as_attachment=True, download_name="tweet.png")

if __name__ == "__main__":
    app.run(debug=True)  # Set debug=False in production
