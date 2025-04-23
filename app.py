from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from selectolax.parser import HTMLParser
from urllib.parse import urlparse, urljoin
import re
import time
import json
import random
from bs4 import BeautifulSoup
from collections import Counter
from nltk.util import ngrams
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options



# Flask app setup
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Dummy user store (now stores any username dynamically)
users = {}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if user_id in users else None












#best----------------------------------------------------------------
# LOGIN


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Simplified login to accept any username/password
        if username and password:
            # Add user to the session
            if username not in users:
                users[username] = generate_password_hash(password)
                
            user = User(username)
            login_user(user)

            # Set default session values to 0 for a fresh session
            session['lead_count'] = 0
            session['email_count'] = 0
            session['phone_count'] = 0
            session['address_count'] = 0
            session['social_media_count'] = 0
            session['company_name_count'] = 0
            
            # Redirect to the index or dashboard after login
            return redirect(url_for('dashboard'))
        
        return 'Invalid credentials', 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Logs out the user
    session.clear()  # Clears all session data
    return redirect(url_for('login'))  # Redirects to the login page (or any other page)


#NEW ROUTES-----------–--------------------------------------------

@app.route('/')
def index():
    return render_template('dashboard.html')  # Assuming you have an 'index.html' template


@app.route('/dashboard')
@login_required
def dashboard():
    # Retrieve the qualified_leads_count from the session, defaulting to 0 if not found
    qualified_leads_count = session.get('qualified_leads_count', 0)
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # For AJAX requests, render just the content part
        return render_template('dashboard_content.html', 
                              title="Smart Overview", 
                              qualified_leads_count=qualified_leads_count)
    else:
        # For regular requests, render the full page with layout
        return render_template('dashboard.html', 
                              title="Smart Overview", 
                              qualified_leads_count=qualified_leads_count)
                              
@app.route('/leads-generator', endpoint='unique_leads_generator')
@login_required
def leads_generator():
    # Your function logic here
    return render_template('leads_generator.html', title="Leads Generator")



# SALES SECTION------------------


# sales-trends-----------
@app.route('/sales_trends')
def sales_trends():
    return render_template('sales_trends.html')




# sales-analyzer--------------

@app.route('/sales-analyze')
def sales_analyzer():
    return render_template('sales_analyze.html')






# email-accelerator---------------------

@app.route('/email-growth-engine')
def email_growth_engine():
    return render_template('email_growth_engine.html')




# help-support----------------

@app.route('/help-support')
def help_support():
    return render_template('help_support.html')




#PEOPLE SEARCH--------------------------------------------------------------------------------------------------------
from flask import Flask, render_template, request, url_for
import requests
from bs4 import BeautifulSoup
import re


# Function to extract people-related info from a LinkedIn profile
def extract_linkedin_info(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the name and job title from LinkedIn
        name = None
        title = None

        name_tag = soup.find('h1', class_='top-card-layout__title')
        if name_tag:
            name = name_tag.get_text(strip=True)

        title_tag = soup.find('h2', class_='top-card-layout__headline')
        if title_tag:
            title = title_tag.get_text(strip=True)

        return name, title

    except requests.exceptions.RequestException as e:
        print(f"Error fetching LinkedIn profile: {e}")
        return None, None

# Function to search Mojeek for LinkedIn profiles related to a company
def search_linkedin_profiles(query):
    search_url = f"https://www.mojeek.com/search?q={query} employees site:linkedin.com"

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        linkedin_profiles = []
        results = soup.select('li a')
        
        for link in results:
            href = link.get('href')
            if href and 'linkedin.com' in href:
                if not href.startswith('http'):
                    href = 'https://www.mojeek.com' + href
                linkedin_profiles.append(href)

        return linkedin_profiles

    except requests.exceptions.RequestException as e:
        print(f"Error fetching results from Mojeek: {e}")
        return []

# Function to extract people-related info from a company's About Us page
def extract_about_us_info(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract names from the About Us page
        names = []
        for paragraph in soup.find_all('p'):
            text = paragraph.get_text()
            matches = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)
            names.extend(matches)

        return names

    except requests.exceptions.RequestException as e:
        print(f"Error fetching About Us page: {e}")
        return []

# Combined route for people search (LinkedIn and About Us)
@app.route('/people_search', methods=['GET', 'POST'])
@login_required
def people_search():
    query = request.form.get('query', '')
    results = []
    people_count = 0  # Initialize people_count

    if query:
        # LinkedIn Search
        linkedin_urls = search_linkedin_profiles(query)
        for url in linkedin_urls:
            name, title = extract_linkedin_info(url)
            if name and title:
                results.append({
                    'title': title,
                    'people_links': [url]  # Store the LinkedIn URL as a "people link"
                })
                people_count += 1

        # About Us Search (example URL - replace with actual logic if needed)
        about_us_url = f"https://www.google.com/search?q={query}+about+us"  # Example: Google search for "company + about us"
        about_us_names = extract_about_us_info(about_us_url)
        for name in about_us_names:
            results.append({
                'title': name,
                'people_links': []  # No direct link, just a name
            })
            people_count += 1

    return render_template("people_search.html", results=results, query=query, people_count=people_count)





# Hot LEADS
from flask import Flask, render_template, request, session
import requests
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import random
from fake_useragent import UserAgent

# Initialize UserAgent
ua = UserAgent()


# Function to clean and standardize text
def clean_text(text):
    if not text:
        return "N/A"
    text = BeautifulSoup(text, 'html.parser').get_text()  # Remove HTML tags
    text = text.strip()
    text = ' '.join(text.split())  # Normalize spaces
    return text

# Function to clean and format phone numbers
def clean_phone(phone):
    if not phone:
        return None

    # Remove unwanted words like "Phone", "Call", "Tel", or any non-digit characters (except for parentheses, dashes, and spaces)
    phone = re.sub(r'(\bPhone\b|\bCall\b|\bTel\b|[^\d\(\)\-\s])', '', phone)

    # Remove extra spaces and line breaks
    phone = re.sub(r'\s+', ' ', phone).strip()

    # Now clean the phone number format (only digits should remain)
    digits = re.sub(r'\D', '', phone)  # Keep only digits

    # Filter out numbers with only 1 or 2 digits, which are not valid phone numbers
    if len(digits) <= 2:
        return None

    # Validate and format phone numbers
    if len(digits) == 10:  # Standard 10-digit number
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':  # US phone number starting with 1 (country code)
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    
    return None

# Function to clean and standardize addresses
def clean_address(address):
    if not address:
        return "N/A"
    
    address = re.sub(r'\s+', ' ', address).strip()  # Normalize spaces
    if len(address) < 5 or not any(word in address.lower() for word in [
        "street", "road", "avenue", "drive", "lane", "boulevard", "court", "plaza", "terrace", "crescent"
    ]):
        return "N/A"
    
    return address

# Function to extract contact information from a webpage
def extract_contact_info(url):
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract emails, phones, and addresses using regex
        email_pattern = r"([\w\.-]+@[\w\.-]+\.\w+)"
        phone_pattern = r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        address_pattern = r"\d+\s[\w\s]+(?:St|Ave|Rd|Blvd|Ln|Terr|Pl)\.?"

        emails = list(set(re.findall(email_pattern, soup.get_text())))
        phones = list(set(re.findall(phone_pattern, soup.get_text())))
        addresses = list(set(re.findall(address_pattern, soup.get_text())))

        # Clean extracted data
        emails = [clean_text(email) for email in emails]
        phones = [clean_phone(phone) for phone in phones]
        addresses = [clean_address(address) for address in addresses]

        # Limit results to top 2 entries for each type
        contact_info = {
            "emails": emails[:2],
            "phone_numbers": [p for p in phones[:2] if p],  # Ensure phone numbers are not None
            "addresses": addresses[:2]
        }

        return contact_info

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return {"emails": [], "phone_numbers": [], "addresses": []}

# Function to scrape results from Mojeek search engine
def scrape_mojeek(query, num_results=30):
    base_url = "https://www.mojeek.com/search"
    results = []
    page = 1

    while len(results) < num_results:
        url = f"{base_url}?q={query.replace(' ', '+')}&page={page}"
        headers = {"User-Agent": ua.random}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            search_results = soup.select("ul.results-standard li")
            for result in search_results:
                title_tag = result.select_one("a.title")
                link_tag = result.select_one("a.ob")
                description_tag = result.select_one("p.s")

                title = clean_text(title_tag.text if title_tag else "No title available")
                link = link_tag["href"] if link_tag else "No link available"
                description = clean_text(description_tag.text if description_tag else "No description available")

                results.append({
                    "title": title,
                    "link": link,
                    "description": description
                })

            if len(results) >= num_results:
                break

            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching results: {e}")
            break

    return results[:num_results]


@app.route('/hot_leads', methods=['GET', 'POST'])
@login_required
def hot_leads():
    query = request.form.get('query', '')
    results = []
    email_count = 0
    phone_count = 0
    address_count = 0

    if query:
        raw_results = scrape_mojeek(query, num_results=30)

        # Use ThreadPoolExecutor for concurrent extraction of contact info
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(extract_contact_info, result['link']): result for result in raw_results}
            
            # Process results as they complete
            for future in as_completed(futures):
                result = futures[future]
                try:
                    contact_info = future.result()
                    # Merge contact info with the result and append
                    results.append({
                        **result,
                        **contact_info
                    })
                    # Count the emails, phone numbers, and addresses
                    email_count += len(contact_info['emails'])
                    phone_count += len(contact_info['phone_numbers'])
                    address_count += len(contact_info['addresses'])
                except Exception as e:
                    print(f"Error getting contact info for {result['link']}: {e}")

        # Store the counts and results in the session for future use
        session['results'] = results
        session['query'] = query
        session['email_count'] = email_count
        session['phone_count'] = phone_count
        session['address_count'] = address_count

    return render_template("hot_leads.html", results=results, query=query, datetime=datetime)


@app.route('/dashboard23')
def dashboard23():
    # Retrieve the counts stored in session
    email_count = session.get('email_count', 0)
    phone_count = session.get('phone_count', 0)
    address_count = session.get('address_count', 0)

    return render_template("dashboard.html", email_count=email_count, phone_count=phone_count, address_count=address_count)






# LEAD MANAGER --------------------------------------------
@app.route('/lead_manager')
@login_required
def lead_manager():
    # Retrieve all data from the session
    results = session.get('results', [])
    query = session.get('query', '')
    email_count = session.get('email_count', 0)
    phone_count = session.get('phone_count', 0)
    address_count = session.get('address_count', 0)

    # Pass the same variables as hot_leads.html
    return render_template(
        "lead_manager.html",
        results=results,
        query=query,
        datetime=datetime,
        email_count=email_count,
        phone_count=phone_count,
        address_count=address_count
    )





# SOCIAL MEDIA LEADS-----------------
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# Define a pattern for social media links
SOCIAL_MEDIA_PATTERNS = [
    'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'youtube.com', 'pinterest.com'
]

# Function to extract the real title and social media links from a webpage
def extract_social_links(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the title of the page (either from <title> or <h1>)
        title = soup.title.string if soup.title else 'No Title Found'
        heading = soup.find('h1')
        page_title = title if not heading else heading.get_text()

        # Find <a> tags that contain social media links
        social_links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if any(social in href for social in SOCIAL_MEDIA_PATTERNS):
                social_links.append(href)

        # If no social media links found, check footer or contact pages
        if not social_links:
            social_links = find_social_media_in_footer_or_contact(url)

        return list(set(social_links)), page_title  # Return social links and page title

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return [], 'No Title Found'  # Return an empty list and a default title

# Function to scrape footer or contact page specifically for social media links
def find_social_media_in_footer_or_contact(url):
    possible_pages = [url + '/contact', url + '/about', url + '/footer']
    social_links = []
    
    for page in possible_pages:
        try:
            response = requests.get(page, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if any(social in href for social in SOCIAL_MEDIA_PATTERNS):
                    social_links.append(href)
            if social_links:
                break  # Stop once we find social media links
        except requests.exceptions.RequestException:
            continue  # Skip if page doesn't exist or fails

    return social_links

# Function to handle concurrent social media scraping for multiple URLs
def gather_social_media_links(urls):
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(extract_social_links, url): url for url in urls}
        social_media_results = []

        for future in as_completed(futures):
            url = futures[future]
            try:
                links, title = future.result()  # Get both social links and title
                # Only add results that have social media links
                if links:
                    social_media_results.append({
                        'url': url,
                        'social_media_links': links,
                        'title': title  # Include the extracted title
                    })
            except Exception as e:
                print(f"Error processing {url}: {e}")

    return social_media_results

# Flask route for the email leads page (now for social media links)
@app.route('/social_leads', methods=['GET', 'POST'])
@login_required
def social_media_leads():
    query = request.form.get('query', '')
    results = []
    social_media_count = 0

    if query:
        # Replace spaces with '+' to form query string
        search_query = query.replace(" ", "+")
        search_url = f"https://www.mojeek.com/search?q={search_query}"

        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract search results
            search_results = soup.select("ul.results-standard li")
            urls_to_scrape = []

            for result in search_results:
                link_tag = result.select_one("a.ob")
                if link_tag:
                    urls_to_scrape.append(link_tag['href'])

            # Now, gather social media links from the URLs found
            social_media_results = gather_social_media_links(urls_to_scrape)

            # Count the total number of social media links found
            for result in social_media_results:
                social_media_count += len(result['social_media_links'])
                results.append(result)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching results from search engine: {e}")

    return render_template("social_media_leads.html", results=results, query=query, social_media_count=social_media_count)



#Email LEADS----------------------
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from fake_useragent import UserAgent

# Initialize UserAgent
ua = UserAgent()

# Function to clean and standardize text
def sanitize_text(text):
    if not text:
        return "N/A"
    text = BeautifulSoup(text, 'html.parser').get_text()  # Remove HTML tags
    text = text.strip()
    text = ' '.join(text.split())  # Normalize spaces
    return text

# Function to extract emails from a webpage
def gather_emails(url):
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract emails using regex
        email_pattern = r"([\w\.-]+@[\w\.-]+\.\w+)"
        emails = list(set(re.findall(email_pattern, soup.get_text())))

        # Clean extracted emails
        emails = [sanitize_text(email) for email in emails]

        return {"emails": emails}

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return {"emails": []}

# Function to scrape results from Mojeek search engine
def search_mojeek(query, num_results=30):
    base_url = "https://www.mojeek.com/search"
    results = []
    page = 1

    while len(results) < num_results:
        url = f"{base_url}?q={query.replace(' ', '+')}&page={page}"
        headers = {"User-Agent": ua.random}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            search_results = soup.select("ul.results-standard li")
            for result in search_results:
                title_tag = result.select_one("a.title")
                link_tag = result.select_one("a.ob")

                title = sanitize_text(title_tag.text if title_tag else "No title available")
                link = link_tag["href"] if link_tag else "No link available"

                results.append({
                    "title": title,
                    "link": link,
                })

            if len(results) >= num_results:
                break

            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching results: {e}")
            break

    return results[:num_results]

# Flask route for the email leads page
@app.route('/email_leads', methods=['GET', 'POST'])
@login_required
def email_leads():
    query = request.form.get('query', '')
    results = []
    email_count = 0

    if query:
        raw_results = search_mojeek(query, num_results=30)

        # Use ThreadPoolExecutor for concurrent extraction of emails
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(gather_emails, result['link']): result for result in raw_results}
            
            # Process results as they complete
            for future in as_completed(futures):
                result = futures[future]
                try:
                    contact_info = future.result()
                    # Merge email info with the result and append
                    if contact_info['emails']:  # Only append if there are emails
                        results.append({
                            **result,
                            **contact_info
                        })
                        # Count the emails
                        email_count += len(contact_info['emails'])
                except Exception as e:
                    print(f"Error getting email info for {result['link']}: {e}")

    return render_template("email_leads.html", results=results, query=query, email_count=email_count, datetime=datetime)


# PHONE LEADS---------------------------
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import random
from fake_useragent import UserAgent

# Initialize UserAgent
ua = UserAgent()

# Function to clean and standardize text
def sanitize_text(text):
    if not text:
        return "N/A"
    text = BeautifulSoup(text, 'html.parser').get_text()  # Remove HTML tags
    text = text.strip()
    text = ' '.join(text.split())  # Normalize spaces
    return text

# Function to extract phone numbers from text
def extract_phone_numbers(text):
    # Regular expression pattern for phone numbers
    phone_pattern = r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})'
    phone_numbers = list(set(re.findall(phone_pattern, text)))
    return [sanitize_text(phone_number) for phone_number in phone_numbers]

# Function to gather contact information (phone numbers)
def gather_contact_information(url):
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        phone_numbers = extract_phone_numbers(soup.get_text())  # Extract phone numbers from the page

        return {"phone_numbers": phone_numbers[:2]}

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return {"phone_numbers": []}

# Function to scrape results from Mojeek search engine
def search_mojeek(company_name, num_results=30):
    base_url = "https://www.mojeek.com/search"
    results = []

    # Search for "Contact Us" pages
    contact_query = f"{company_name} contact us"
    contact_results = []
    page = 1
    while len(contact_results) < num_results / 2:  # Limit to half the results
        url = f"{base_url}?q={contact_query.replace(' ', '+')}&page={page}"
        headers = {"User-Agent": ua.random}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            search_results = soup.select("ul.results-standard li")
            for result in search_results:
                title_tag = result.select_one("a.title")
                link_tag = result.select_one("a.ob")
                description_tag = result.select_one("p.s")

                title = sanitize_text(title_tag.text if title_tag else "No title available")
                link = link_tag["href"] if link_tag else "No link available"
                description = sanitize_text(description_tag.text if description_tag else "No description available")

                contact_results.append({
                    "title": title,
                    "link": link,
                    "description": description
                })

            if len(contact_results) >= num_results / 2:
                break
            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching results: {e}")
            break

    # Search for company name + "phone"
    phone_query = f"{company_name} phone"
    phone_results = []
    page = 1
    while len(phone_results) < num_results / 2:  # Limit to half the results
        url = f"{base_url}?q={phone_query.replace(' ', '+')}&page={page}"
        headers = {"User-Agent": ua.random}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            search_results = soup.select("ul.results-standard li")
            for result in search_results:
                title_tag = result.select_one("a.title")
                link_tag = result.select_one("a.ob")
                description_tag = result.select_one("p.s")

                title = sanitize_text(title_tag.text if title_tag else "No title available")
                link = link_tag["href"] if link_tag else "No link available"
                description = sanitize_text(description_tag.text if description_tag else "No description available")

                # Extract phone numbers from description
                phone_numbers_from_description = extract_phone_numbers(description)
                result_data = {
                    "title": title,
                    "link": link,
                    "description": description,
                    "phone_numbers": phone_numbers_from_description
                }
                phone_results.append(result_data)

            if len(phone_results) >= num_results / 2:
                break
            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching results: {e}")
            break

    # Combine results
    results = contact_results + phone_results
    return results[:num_results]

# Flask route for the hot leads page
@app.route('/phone_leads', methods=['GET', 'POST'])
@login_required
def phone_leads():
    query = request.form.get('query', '')
    results = []
    phone_count = 0

    if query:
        raw_results = search_mojeek(query, num_results=30)

        # Use ThreadPoolExecutor for concurrent extraction of phone info
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(gather_contact_information, result['link']): result for result in raw_results if 'link' in result}

            # Process results as they complete
            for future in as_completed(futures):
                result = futures[future]
                try:
                    phone_info = future.result()
                    # If phone numbers were found in the search result description, merge those in
                    if 'phone_numbers' in result and result['phone_numbers']:
                        phone_info['phone_numbers'] = list(set(phone_info['phone_numbers'] + result['phone_numbers']))

                    # Merge phone info with the result and append
                    results.append({
                        **result,
                        **phone_info
                    })
                    # Count the phone numbers
                    phone_count += len(phone_info['phone_numbers'])
                except Exception as e:
                    print(f"Error getting phone info for {result.get('link', 'no link')}: {e}")

    return render_template("phone_leads.html", results=results, query=query, phone_count=phone_count, datetime=datetime)





# ADDRESS LEADS----------------------------------------------
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from fake_useragent import UserAgent
from urllib.parse import urljoin



# Initialize UserAgent
ua = UserAgent()

# Function to clean and standardize text
def format_text(text):
    if not text:
        return "N/A"
    text = BeautifulSoup(text, 'html.parser').get_text()  # Remove HTML tags
    text = text.strip()
    text = ' '.join(text.split())  # Normalize spaces
    return text

# Function to clean and standardize addresses
def format_address(address):
    if not address:
        return "N/A"

    address = re.sub(r'\s+', ' ', address).strip()  # Normalize spaces
    if not re.search(r'\d+', address) or not any(word in address.lower() for word in [
        "street", "road", "avenue", "drive", "lane", "boulevard", "court", "plaza", "terrace", "crescent", "sq", "way"
    ]):
        return "N/A"

    return address

# Function to extract company name
def extract_company_name(soup, url):
    # Look for common indicators of company names in meta tags, titles, or headings
    company_name = None

    # Try meta description
    meta_description = soup.find("meta", attrs={"name": "description"})
    if meta_description:
        company_name = meta_description.get("content")

    # Try title tag
    if not company_name:
        title_tag = soup.find("title")
        if title_tag:
            company_name = title_tag.get_text()

    # Try OG title
    if not company_name:
        og_title = soup.find("meta",  attrs={"property": "og:title"})
        if og_title:
            company_name = og_title.get("content")

    # Try H1 tag
    if not company_name:
        h1_tag = soup.find("h1")
        if h1_tag:
            company_name = h1_tag.get_text()

    if company_name:
        company_name = format_text(company_name)
        # Remove generic terms
        company_name = re.sub(r"(|official|website)$", "", company_name, flags=re.IGNORECASE)
        return company_name

    return "N/A"  # Return a default if company name not found

# Function to find the contact page
def find_contact_page(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Search for links that may contain "contact" in their href
        contact_keywords = ["contact", "contact-us", "get-in-touch", "reach-us", "about"]
        contact_page_links = []

        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if any(keyword in href for keyword in contact_keywords):
                full_url = urljoin(url, href)  # Resolve relative URLs
                contact_page_links.append(full_url)

        # Return the first valid contact page found (if any)
        return contact_page_links[0] if contact_page_links else None

    except Exception as e:
        print(f"Error finding contact page for {url}: {e}")
        return None

# Function to extract contact info from a soup object
def extract_contact_from_soup(soup):
    address_pattern = r"\d+\s[\w\s]+(?:St|Ave|Rd|Blvd|Ln|Terr|Pl|Ct|Dr|Pkwy|Sq|Crescent|Suite|Apt)?\.?"
    addresses = list(set(re.findall(address_pattern, soup.get_text())))
    addresses = [format_address(address) for address in addresses]

    contact_info = {
        "addresses": addresses[:2]
    }

    return contact_info

# Function to extract contact information from a webpage
def get_contact_info(url):
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return {"company_name": "N/A", "addresses": []}

    # Extract company name
    company_name = extract_company_name(soup, url)

    # First, try to find the contact page
    contact_page_url = find_contact_page(url, headers)
    if contact_page_url:
        try:
            print(f"Found contact page: {contact_page_url}")
            response = requests.get(contact_page_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extract the address, phone, email from the contact page
            contact_info = extract_contact_from_soup(soup)
            return {"company_name": company_name, **contact_info}
        except requests.exceptions.RequestException as e:
            print(f"Error fetching contact page {contact_page_url}: {e}")
            contact_info = {"addresses": []}  # Handle contact page fetch failure gracefully

    else:
        # If no specific contact page, fall back to the original page
        contact_info = extract_contact_from_soup(soup)

    return {"company_name": company_name, **contact_info}

# Function to scrape results from Mojeek search engine
def fetch_mojeek_results(query, num_results=30):
    base_url = "https://www.mojeek.com/search"
    results = []
    page = 1

    while len(results) < num_results:
        url = f"{base_url}?q={query.replace(' ', '+')}&page={page}"
        headers = {"User-Agent": ua.random}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            search_results = soup.select("ul.results-standard li")
            for result in search_results:
                title_tag = result.select_one("a.title")
                link_tag = result.select_one("a.ob")
                description_tag = result.select_one("p.s")

                title = format_text(title_tag.text if title_tag else "No title available")
                link = link_tag["href"] if link_tag else "No link available"
                description = format_text(description_tag.text if description_tag else "No description available")

                results.append({
                    "title": title,
                    "link": link,
                    "description": description
                })

            if len(results) >= num_results:
                break

            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching results: {e}")
            break

    return results[:num_results]

@app.route('/address_leads', methods=['GET', 'POST'])
@login_required
def address_leads():
    query = request.form.get('query', '')
    results = []
    address_count = 0

    if query:
        raw_results = fetch_mojeek_results(query, num_results=30)

        # Use ThreadPoolExecutor for concurrent extraction of contact info
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(get_contact_info, result['link']): result for result in raw_results}

            # Process results as they complete
            for future in as_completed(futures):
                result = futures[future]
                try:
                    contact_info = future.result()
                    # Merge contact info with the result and append
                    processed_result = {
                        'company_name': contact_info.get('company_name', 'N/A'),
                        'addresses': contact_info.get('addresses', [])
                    }
                    results.append(processed_result)
                    # Count the addresses
                    address_count += len(contact_info['addresses'])
                except Exception as e:
                    print(f"Error getting contact info for {result['link']}: {e}")

        # After processing, show a success message
        return render_template("address_leads.html", results=results, query=query, datetime=datetime, show_results=True)
    else:
        # If no query, render the page without results
        return render_template("address_leads.html", results=[], query='', datetime=datetime, show_results=False, no_query=True)

if __name__ == '__main__':
    app.run(threaded=True)
