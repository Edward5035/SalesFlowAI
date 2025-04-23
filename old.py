from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time
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

# Function to clean and standardize addresses with additional filtering for irrelevant content
def clean_address(address):
    if not address:
        return "N/A"
    
    # Normalize spaces and remove unwanted text patterns
    address = re.sub(r'\s+', ' ', address).strip()  # Normalize spaces
    
    # Exclude addresses that are actually phrases like "years of experience", or incomplete addresses
    # Pattern to exclude unwanted non-address content
    unwanted_patterns = [
        r'\d{1,4}\s*(years? of experience|exp|experience)',  # Matches "20 years exp", "10 years of experience"
        r'\d{4}\s*(I won|CareGuide|ServicesFind|Inc|LLC)',   # Exclude business names or unwanted phrases
        r'\d{1,4}\s*(Bay Street|Toronto|Canada)',            # Exclude partial or incomplete address (like "Bay Street")
        r'\d{1,4}\s*(way|st|ave|road|blvd|dr|ln|terr|pl|court|circle|drive|square|crescent)',  # Ensure valid street types like "Way", "Road", etc.
        r'\d+\s*(unit|apartment|suite|floor)',  # Exclude non-residential info (e.g., suite, unit)
        r'\d+\s*(po box|p\.o\. box)',            # Exclude P.O. Box style addresses
        r'\b(usa|united states|canada|uk|united kingdom|australia|aus|new zealand|nz|europe|european)\b',  # Remove references to countries/regions in the address
        r'\d{1,4}\s*(days ago|days and|week|month|year|ago|on)',  # Exclude time-based references like "52 days ago"
        r'\d{2,4}\s*(Thu|Fri|Sat|Sun)\s*\d{2}',  # Exclude time-based references like "00 Thu 08"
    ]
    
    # Apply each unwanted pattern and remove matches
    for pattern in unwanted_patterns:
        address = re.sub(pattern, '', address, flags=re.IGNORECASE).strip()
    
    # Ensure valid length (at least 5 characters), and not just a street number or incomplete info
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

        # Further cleaning of addresses to remove unwanted text blocks
        addresses = [addr for addr in addresses if len(addr.split()) > 2]  # Basic check for valid address length

        # Extract business name using multiple strategies
        business_name = "N/A"
        
        # 1. Check for Open Graph (og:title) tag for business name
        og_title_tag = soup.find("meta", property="og:title")
        if og_title_tag and og_title_tag.get("content"):
            business_name = clean_text(og_title_tag["content"])

        # 2. Check for <h1> or <h2> tags (common for business name or page title)
        if business_name == "N/A":  # Only use this if no Open Graph title was found
            h1_tag = soup.find("h1")
            if h1_tag:
                business_name = clean_text(h1_tag.get_text())

        # 3. Fallback: Use the <title> tag if no other options are available
        if business_name == "N/A":
            title_tag = soup.find("title")
            if title_tag:
                business_name = clean_text(title_tag.get_text())

        # Limit results to top 2 entries for each type
        contact_info = {
            "business_name": business_name,
            "emails": emails[:2],
            "phone_numbers": [p for p in phones[:2] if p],  # Ensure phone numbers are not None
            "addresses": addresses[:2]
        }

        return contact_info

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return {"emails": [], "phone_numbers": [], "addresses": [], "business_name": "N/A"}

# Function to scrape results from Mojeek search engine
def scrape_mojeek(query, num_results=30):
    base_url = "https://www.mojeek.com/search"
    results = []
    page = 1

    # List of terms that typically indicate list-based articles
    exclude_keywords = [
        "top", "best", "most popular", "must-see", "ultimate", "must-have", "recommended",
        "10 best", "top 10", "list", "ranking", "rank", "guide", "how to", "you won’t believe",
        "this will change your life", "shocking", "surprising", "unbelievable", "must-read",
        "facts", "things you didn’t know", "reasons to", "ways to", "discover", "amazing", 
        "reviews", "top rated", "highly rated", "latest", "explore", "uncover"
    ]
    
    # Excluded domains (add known list-based domains)
    excluded_domains = ["buzzfeed.com", "ranker.com", "top10.com", "listverse.com", "thetop10s.com"]

    while len(results) < num_results:
        url = f"{base_url}?q={query.replace(' ', '+')}&page={page}"
        headers = {"User-Agent": ua.random} # use fake user agent

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract the results from the search page
            search_results = soup.select("ul.results-standard li")
            # Filter based on URL or description before extracting full content
            
            for result in search_results:
                title_tag = result.select_one("a.title")
                link_tag = result.select_one("a.ob")
                description_tag = result.select_one("p.s")

                title = clean_text(title_tag.text if title_tag else "No title available")
                link = link_tag["href"] if link_tag else "No link available"
                description = clean_text(description_tag.text if description_tag else "No description available")

                # Filter results based on URL and description to avoid list content
                if (
                    any(domain in link.lower() for domain in excluded_domains) or
                    any(phrase in title.lower() or phrase in description.lower() for phrase in exclude_keywords) or
                    any(char.isdigit() for char in title)  # Exclude pages with numbers in the title (like "10 best")
                ):
                    continue

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
def hot_leads():
    query = request.form.get('query', '')
    results = []

    if query:
        raw_results = scrape_mojeek(query, num_results=30)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(extract_contact_info, result['link']): result for result in raw_results}
            
            # Process results as they complete to preserve order
            results = []
            for future in as_completed(futures):
                result = futures[future]
                try:
                    contact_info = future.result()
                    results.append({
                        **result,
                        **contact_info  # Merge contact info into the result data
                    })
                except Exception as e:
                    print(f"Error getting contact info for {result['link']}: {e}")

    return render_template("hot_leads.html", results=results, query=query, datetime=datetime)

