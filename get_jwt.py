import os
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
import getpass

# --- ADDED: Hardcoded credentials for automation ---
HARDCODED_EMAIL = "boubaker.wa@hotmail.de"
HARDCODED_PASSWORD = "123123123"

def main():
    """
    Connects to Supabase and retrieves a JWT for a user.
    """
    # Load environment variables from .env file
    load_dotenv()

    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in your .env file.")
        return

    # Create a Supabase client
    supabase: Client = create_client(url, key)

    # --- Use hardcoded credentials ---
    email = HARDCODED_EMAIL
    password = HARDCODED_PASSWORD

    try:
        # Sign in the user
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})

        # Print the access token (JWT)
        jwt = response.session.access_token
        print("\n" + "="*50)
        print("Successfully authenticated!")
        print("Your JWT is printed below.")
        print("="*50 + "\n")
        print(jwt)
        print("\n" + "="*50)
        print("You can now paste this token into the Swagger UI.")
        print("="*50)

        # --- Write JWT to tmp_jwt.txt ---
        with open("tmp_jwt.txt", "w") as f:
            f.write(jwt)
        print("\nJWT token saved to tmp_jwt.txt\n")

        # --- Test the API endpoint ---
        # test_api_endpoint(jwt)  # Optionally comment out to avoid test call

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check your credentials and Supabase project settings.")

def test_api_endpoint(token: str):
    """
    Uses the provided JWT to make a test request to the analysis endpoint.
    """
    print("\n--- Testing API Endpoint ---")
    url = "https://critiquewire-backend.onrender.com/v1/analysis/article"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
      "url": "http://example.com/article",
      "title": "Test Article",
      "options": {
        "includeBiasAnalysis": True,
        "includeFactCheck": False,
        "includeContextAnalysis": False,
        "includeSummary": True,
        "includeExpertOpinion": False,
        "includeImpactAssessment": False
      }
    }

    print(f"Making POST request to: {url}")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        print(f"Response Status Code: {response.status_code}")
        print("Response Body:")
        print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while making the request: {e}")
    finally:
        print("--------------------------")

if __name__ == "__main__":
    main() 