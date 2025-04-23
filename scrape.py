from flask import Flask, render_template_string, request, session, redirect, url_for
import requests
from bs4 import BeautifulSoup
import re
import smtplib
from email.mime.text import MIMEText
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Mojeek scraper
def scrape_mojeek(keyword, location):
    query = f"{keyword} {location}"
    url = f"https://www.mojeek.com/search?q={requests.utils.quote(query)}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    results = []
    for result in soup.select(".result"):
        title_tag = result.find("h2")
        link_tag = result.find("a", href=True)
        snippet = result.find("p")
        link = link_tag['href'] if link_tag else ''
        
        # Try to extract email from the snippet or the result div
        snippet_text = snippet.get_text() if snippet else ''
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', snippet_text)
        email = email_match.group(0) if email_match else None

        if email and link and title_tag:
            results.append({
                "id": str(uuid.uuid4()),
                "title": title_tag.get_text(strip=True),
                "link": link,
                "snippet": snippet_text,
                "email": email
            })
    return results

# Call to your Colab-hosted AI generator
def generate_ai_message(business_description, lead_title, message_type):
    prompt = f"Write a {message_type} outreach email for this business: '{business_description}' to a lead titled '{lead_title}'"
    try:
        response = requests.post("https://your-colab-url.com/generate", json={"prompt": prompt}, timeout=10)
        return response.json().get("message", "No message returned")
    except Exception as e:
        return f"[Error: {str(e)}]"

# Send email
def send_email(to_email, subject, message, from_email="your@email.com", smtp_server="smtp.example.com"):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    try:
        with smtplib.SMTP(smtp_server, 587) as server:
            server.starttls()
            server.login(from_email, "your-password")
            server.send_message(msg)
        return True
    except Exception as e:
        return False

@app.route('/ai_agent', methods=["GET", "POST"])
def ai_agent():
    if request.method == "POST":
        keyword = request.form.get("keyword")
        location = request.form.get("location")
        business = request.form.get("business")
        tone = request.form.get("tone")

        leads = scrape_mojeek(keyword, location)
        sent_leads = []

        for lead in leads:
            ai_msg = generate_ai_message(business, lead['title'], tone)
            success = send_email(lead["email"], "A Quick Hello", ai_msg)
            sent_leads.append({
                **lead,
                "ai_message": ai_msg,
                "status": "✅ Sent" if success else "❌ Failed"
            })

        session['results'] = sent_leads
        return redirect(url_for("ai_agent"))

    results = session.pop('results', [])
    return render_template_string(TEMPLATE, results=results)


if __name__ == "__main__":
    app.run(debug=True)