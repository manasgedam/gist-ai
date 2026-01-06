import os
from supabase import create_client, Client, ClientOptions
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Increase the timeout to 300 seconds (5 mins) for large video uploads
opts = ClientOptions(postgrest_client_timeout=60, storage_client_timeout=300)
supabase: Client = create_client(url, key, options=opts)

def start_db_job(video_id, url):
    # Delete child ideas first (Foreign Key constraint safety)
    supabase.table("viral_ideas").delete().eq("video_id", video_id).execute()
    # Delete the parent job
    supabase.table("processing_jobs").delete().eq("video_id", video_id).execute()
    
    # 2. Create a fresh record
    new_job = {"video_id": video_id, "url": url, "status": "pending"}
    result = supabase.table("processing_jobs").insert(new_job).execute()
    
    return result.data[0], False

def update_db_status(job_id, status):
    # If job_id was accidentally passed as a dictionary, extract the string
    if isinstance(job_id, dict):
        job_id = job_id.get("id")
        
    supabase.table("processing_jobs")\
        .update({"status": status})\
        .eq("id", job_id)\
        .execute()
# Fixed the order of arguments: total_duration moved before output_path
def save_viral_idea(job_id, video_id, idea, total_duration, output_path=None):
    # 1. Clean the job_id
    clean_job_id = job_id.get("id") if isinstance(job_id, dict) else job_id
    
    # Extract timestamps safely
    ts = idea.get("timestamps", [[0, 0]])
    start_time = ts[0][0] if ts else 0
    end_time = ts[0][1] if ts else 0

    # 2. Match the dictionary keys EXACTLY to your Supabase Column Names
    data_to_save = {
        "job_id": clean_job_id,
        "video_id": video_id,
        "title": idea.get("title", "Untitled"),
        "explanation": idea.get("explanation", ""),
        "timestamps": ts,
        "salience_score": idea.get("salience_score", 0),
        "total_duration": total_duration,
        "video_url": output_path, # Mapping output_path (the URL) to video_url
        "start_time": start_time, # Highly recommended for the timeline logic
        "end_time": end_time      # Highly recommended for the timeline logic
    }
    
    print(f"DEBUG: Attempting to save idea: {data_to_save['title']}")
    
    try:
        return supabase.table("viral_ideas").insert(data_to_save).execute()
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")
        return None
 
def upload_video_to_supabase(local_path: str, video_id: str, filename: str):
    storage_path = f"{video_id}/{filename}"
    try:
        with open(local_path, 'rb') as f:
            supabase.storage.from_("reels").upload(
                path=storage_path,
                file=f,
                file_options={"content-type": "video/mp4", "x-upsert": "true"}
            )
        
        # FIX: Extract the actual string URL from the response
        response = supabase.storage.from_("reels").get_public_url(storage_path)
        return response # If this is a string, great. If it's an object, use response.public_url
    except Exception as e:
        print(f"Cloud Upload Error: {e}")
        return None
def link_video_url_to_idea(video_id: str, title: str, video_url: str):
    """Updates the viral_ideas table with the final cloud link."""
    supabase.table("viral_ideas") \
        .update({"video_url": video_url}) \
        .eq("video_id", video_id) \
        .eq("title", title) \
        .execute()




import shutil

def save_local_video(local_path, video_id, filename):
    # This points to your Next.js project's public folder
    # Adjust the path to match your actual Next.js folder location
    nextjs_public_base = "../meaning-engine-ui/public/reels" 
    
    target_dir = os.path.join(nextjs_public_base, video_id)
    os.makedirs(target_dir, exist_ok=True)
    
    target_path = os.path.join(target_dir, filename)
    
    # Copy the file from your backend exports to Next.js public folder
    shutil.copy(local_path, target_path)
    
    # Return the path that the browser understands
    return f"/reels/{video_id}/{filename}"