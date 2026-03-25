# Check if student is already registered
if email in activity["participants"]:
    raise HTTPException(status_code=400, detail="Already registered for this activity")

# Check if activity is full
if len(activity["participants"]) >= activity["max_participants"]:
    raise HTTPException(status_code=400, detail="Activity is full")

# Add student
activity["participants"].append(email)