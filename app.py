from flask import Flask, request, render_template, redirect, url_for
import os
import sqlite3
import datetime
import requests
from google import genai
import markdown, markdown2

telegram_token = os.getenv("TELEGRAM_TOKEN_2")
gemini_api_key = os.getenv("GEMINI_KEY")
gemini_client = genai.Client(api_key=gemini_api_key )
gemini_model = "gemini-2.0-flash"

app = Flask(__name__)


@app.route("/",methods=["GET", "POST"])
def index():
    return(render_template("index.html"))

@app.route("/main",methods=["GET", "POST"])
def main():
    return(render_template("main.html"))

@app.route("/fantasy", methods=["GET", "POST"])
def fantasy():
    # Eventually I will ask for other things like whether the user wants to create their own character or pick an existing one
    # for now, it'll just go straight to gemini just to make sure that it works
    q = "You are a game master that specializes in role-playing games. Generate a roleplaying game scenario that is set in a fantasy world like dungeons and dragons."
    r = gemini_client.models.generate_content(
        model=gemini_model,
        contents=q
    )
    r_html = markdown.markdown(
            r.text if r.text is not None else "",
            extensions=["fenced_code", "codehilite"]  
    )
    return(render_template("fantasy.html",r=r_html))

@app.route("/sci-fi", methods=["GET", "POST"])
def sci-fi():
    # Eventually I will ask for other things like whether the user wants to create their own character or pick an existing one
    # for now, it'll just go straight to gemini just to make sure that it works
    q = "You are a game master that specializes in role-playing games. Generate a roleplaying game scenario that is set in a sci-fi world."
    r = gemini_client.models.generate_content(
        model=gemini_model,
        contents=q
    )
    r_html = markdown.markdown(
            r.text if r.text is not None else "",
            extensions=["fenced_code", "codehilite"]  
    )
    return(render_template("fantasy.html",r=r_html))    

@app.route("/genres", methods=["GET", "POST"])
def genres():
    return(render_template("genres.html"))

@app.route("/gemini",methods=["GET", "POST"])
def gemini():
    return(render_template("gemini.html"))

@app.route("/gemini_reply",methods=["GET", "POST"])
def gemini_reply():
    q = request.form.get("q")
    #gemini
    r = gemini_client.models.generate_content(
        model=gemini_model,
        contents=q
    )
    r_html = markdown.markdown(
            r.text if r.text is not None else "",
            extensions=["fenced_code", "codehilite"]  
    )
    return(render_template("gemini_reply.html",r=r_html))


@app.route("/user_log",methods=["GET", "POST"])
def user_log():
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute("select * from users")
    r=""
    for row in c:
        print(row)
        r=r+str(row) + '\n'
    c.close()
    conn.close()
    return(render_template("user_log.html", r=r))

@app.route("/delete_log",methods=["GET", "POST"])
def delete_log():
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute("delete from users")
    conn.commit()
    c.close()
    conn.close()
    return(render_template("delete_log.html"))

@app.route("/logout", methods=["GET", "POST"])
def logout():
    return(render_template("index.html"))

@app.route('/sql', methods=["POST"])
def sql():
    name = request.form.get("q")
    if name:
        t = datetime.datetime.now()
        conn = sqlite3.connect('user.db')
        c = conn.cursor()
        c.execute("insert into  users(name,timestamp) values(?,?)",(name.lstrip(), t))
        conn.commit()
        c.close()
        conn.close()
    return redirect(url_for('main'))

@app.route("/paynow", methods=["GET", "POST"])
def paynow():
    return(render_template("paynow.html"))

@app.route("/prediction", methods=["GET","POST"])
def prediction():
    return(render_template("prediction.html"))

@app.route("/prediction_reply", methods=["GET","POST"])
def prediction_reply():
    try:
        q = float(request.form.get("q"))
    except ValueError:
        return render_template("prediction.html", r="Invalid input: Please enter a valid number.")
    return(render_template("prediction_reply.html", r=90.2 + (-50.6*q)))

@app.route("/start_telegram", methods=["GET", "POST"])
def start_telegram():
    domain_url = os.getenv('WEBHOOK_URL')
    
    delete_webhook_url = f"https://api.telegram.org/bot{telegram_token}/deleteWebhook"
    requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})

    set_webhook_url = f"https://api.telegram.org/bot{telegram_token}/setWebhook?url={domain_url}/telegram"
    # set webhook url for telegram bot
    webhook_response = requests.post(set_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    print('webhook:', webhook_response)
    if webhook_response.status_code == 200:
        # set status message
        status = "The telegram bot is running. Please check with the telegram bot. @dsai_tll_finance_bot"
    else:
        status = "Failed to start the telegram bot. Please check the logs."
    return(render_template("telegram.html", status=status))

@app.route("/telegram", methods=["GET", "POST"])
def telegram():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        # Extract the chat ID and message from the update
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        if text == "/start":
            r_text = "Welcome! You can ask me any finance-related questions."
        else:
            system_prompt = "You are a financial expert.  Answer ONLY questions related to finance, economics, investing, and financial markets. If the question is not related to finance, state that you cannot answer it."
            prompt = f"{system_prompt}\n\nUser Query: {text}"
            r = gemini_client.models.generate_content(
                model=gemini_model,
                contents=prompt
            )
            r_text = r.text if r.text is not None else ""
            r_text = r_text.replace('**','')

        # Send the response to the user
        send_message_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        requests.post(send_message_url, data={"chat_id": chat_id, "text": r_text})

    # Return a 200 OK response to Telegram to acknowledge that message was received
    return('ok', 200)


if __name__ == "__main__":
    app.run()