import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)


def sign_up(email: str, password: str):
    client = get_supabase_client()
    return client.auth.sign_up({"email": email, "password": password})


def sign_in(email: str, password: str):
    client = get_supabase_client()
    return client.auth.sign_in_with_password({"email": email, "password": password})


def sign_out():
    client = get_supabase_client()
    client.auth.sign_out()


def save_report(user_id: str, file_name: str, age, gender, parameters, pattern_findings, context_notes, summary, recommendations):
    client = get_supabase_client()
    data = {
        "user_id": user_id,
        "file_name": file_name,
        "age": age,
        "gender": gender,
        "parameters": [p.model_dump() for p in parameters],
        "pattern_findings": pattern_findings,
        "context_notes": context_notes,
        "summary": summary,
        "recommendations": recommendations,
    }
    return client.table("reports").insert(data).execute()


def get_user_reports(user_id: str):
    client = get_supabase_client()
    result = client.table("reports").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return result.data


if __name__ == "__main__":
    # Quick connection test - just checks the client initializes correctly
    client = get_supabase_client()
    print("Supabase client created successfully.")
    print(f"URL configured: {os.getenv('SUPABASE_URL') is not None}")
    print(f"Key configured: {os.getenv('SUPABASE_KEY') is not None}")