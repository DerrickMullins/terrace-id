import requests
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load the variables from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE_URL = "https://www.fanchants.com"
LEAGUE_URL = "https://www.fanchants.com/football-league/premiership/"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

def scrape_fanchants():
    # STEP 1: Get the list of Teams from the Premiership page
    print("Fetching teams from Premiership...")
    res = requests.get(LEAGUE_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Look for links that point to football-team pages
    team_links = soup.select('a[href*="/football-team/"]')
    
    # Use a set to avoid visiting the same team twice
    unique_team_urls = set(BASE_URL + link['href'] for link in team_links)

    for team_url in unique_team_urls:
        # Extract team name from URL (e.g., .../chelsea/ -> Chelsea)
        team_name = team_url.rstrip('/').split('/')[-1].replace('-', ' ').replace('_', ' ').title()
        print(f"\n--- Scraping Team: {team_name} ---")
        
        # STEP 2: Navigate to the Team's page
        team_res = requests.get(team_url, headers=HEADERS)
        team_soup = BeautifulSoup(team_res.text, 'html.parser')
        
        # STEP 3: Find all audio links using the class you provided
        # Specifically looking for the play-button class and href ending in .mp3/.mp4
        audio_elements = team_soup.find_all('a', class_='play-button')
        
        for audio in audio_elements:
            audio_path = audio.get('href')
            
            # Ensure it's a valid audio link
            if audio_path and (audio_path.endswith('.mp3') or audio_path.endswith('.mp4')):
                full_audio_url = BASE_URL + audio_path
                
                # Attempt to find the chant name (usually in an alt tag or nearby text)
                img_tag = audio.find('img')
                chant_name = img_tag.get('alt', 'Unknown Chant') if img_tag else "Unknown Chant"
                
                print(f"Found: {chant_name} -> {full_audio_url}")

                # STEP 4: Insert into Supabase
                payload = {
                    "team": team_name,
                    "chant_name": chant_name,
                    "audio_url": full_audio_url,
                }

                try:
                    # Using upsert to prevent duplicates if the script runs again
                    supabase.table("chants").upsert(payload, on_conflict="audio_url").execute()
                except Exception as e:
                    print(f"Error saving to Supabase: {e}")

        # Be kind to the server
        time.sleep(2)

if __name__ == "__main__":
    scrape_fanchants()