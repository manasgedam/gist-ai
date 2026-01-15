import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_user_simulation(youtube_url):
    print(f"🎬 Submitting video to Gist AI: {youtube_url}")
    
    # 1. Start the process
    response = requests.post(f"{BASE_URL}/process/", params={"youtube_url": youtube_url})
    if response.status_code != 202:
        print("❌ Failed to start process")
        return

    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✅ Job Created! ID: {job_id}")

    # 2. Poll the status until completed
    print("\n--- Progress Monitor ---")
    while True:
        status_resp = requests.get(f"{BASE_URL}/status/{job_id}")
        data = status_resp.json()
        status = data["status"]
        
        # Simple CLI progress bar
        sys.stdout.write(f"\rCurrent Status: [{status:15}] | Clips Found: {data['clips_found']}")
        sys.stdout.flush()

        if status == "COMPLETED":
            print("\n\n🎉 SUCCESS! Your Gist is ready.")
            print(f"Total Clips: {len(data['clips'])}")
            for clip in data['clips']:
                print(f" - {clip['title']} ({clip['start_time']}s - {clip['end_time']}s)")
            break
        
        if "FAILED" in status:
            print(f"\n\n❌ Pipeline Error: {status}")
            break

        time.sleep(2) # Wait 2 seconds before checking again

if __name__ == "__main__":
    test_url = "https://youtu.be/NsyI9LIXbFM?si=Bs7-Cck1Rt_oZ-7e" # Example
    run_user_simulation(test_url)