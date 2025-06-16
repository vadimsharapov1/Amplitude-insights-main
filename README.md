# 📊 Amplitude User Data Extractor

**Simple tool to download user data from Amplitude** - Perfect for beginners! 

## 🎯 What This Does

This tool helps you download user behavior data from Amplitude Analytics:
- Download events for specific users
- Analyze what users do in your app
- Export data for further analysis
- Works with any Amplitude account

## 🚀 How to Use (Beginner Guide)

### Step 1: Download This Project

**Download ZIP**
1. Click the green "Code" button at the top of this page
2. Click "Download ZIP"
3. Extract the ZIP file to your Desktop

### Step 2: Open in VS Code

1. **Download VS Code** (if you don't have it): https://code.visualstudio.com/
2. **Open VS Code**
3. **Open the project folder:**
   - Click `File` → `Open Folder`
   - Navigate to where you extracted/downloaded this project
   - Click "Select Folder"

### Step 3: Install Python Requirements

1. **Open Terminal in VS Code:**
   - Press `Ctrl+`` (backtick) or go to `Terminal` → `New Terminal`
2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```
   (If `pip` doesn't work, try `pip3` or `python -m pip`)

### Step 4: Add Your Amplitude API Keys

**🔑 Where to Find Your API Keys:**
1. **Login to Amplitude:** Go to https://amplitude.com and login
2. **Go to Settings:** Click your profile picture → Settings
3. **Find Projects:** Click "Projects" in the left menu
4. **Select Your Project:** Click on your app/project name
5. **Copy the Keys:** You'll see "API Key" and "Secret Key" - copy both

**📝 Where to Add Your API Keys:**
1. **In VS Code:** Look for the file `.env.template`
2. **Copy the template:** Right-click `.env.template` → Copy, then Paste → rename to `.env`
3. **Edit the .env file:** Double-click to open it
4. **Replace the placeholders:**
   ```
   AMPLITUDE_API_KEY=paste_your_api_key_here
   AMPLITUDE_SECRET_KEY=paste_your_secret_key_here
   ```
5. **Save the file:** Press `Ctrl+S` (Windows) or `Cmd+S` (Mac)

### Step 5: Add Your User IDs

**👥 Where to Find User IDs in Amplitude:**

**Method 1: From Cohorts (Recommended)**
1. **Go to Amplitude:** Login to your Amplitude dashboard
2. **Navigate to Cohorts:** Click "Cohorts" in the left menu
3. **Select a Cohort:** Choose any cohort with users you want to analyze
4. **View Users:** Click "View Users" or the user count number
5. **Copy User IDs:** You'll see a list of User IDs - copy the ones you want

**Method 2: From Live View**
1. **Go to Live View:** Click "Live" in Amplitude
2. **Find Recent Events:** Look at recent user activity
3. **Copy User IDs:** Click on events to see User IDs

**Method 3: From User Lookup**
1. **Go to User Lookup:** Click "Users" → "User Lookup"
2. **Search for Users:** Find specific users
3. **Copy their User IDs:** From the user profile

**📝 Where to Add User IDs:**
1. **In VS Code:** Look for folder `user_ids/`
2. **Copy the template:** Right-click `user_ids.txt.template` → Copy → Paste → rename to `my_users.txt`
3. **Edit the file:** Double-click `my_users.txt` to open
4. **Add your user IDs:** Replace the example with your real user IDs:
   ```
   your_user_id_1|January 1, 2024|January 31, 2024
   your_user_id_2|February 1, 2024|February 28, 2024
   ```
   Format: `UserID|StartDate|EndDate`
5. **Save the file:** Press `Ctrl+S`

### Step 6: Run the Program

1. **Open Terminal in VS Code** (if not already open):
   - Press `Ctrl+`` (backtick)
2. **Run the main program:**
   ```bash
   python main.py
   ```
3. **Follow the prompts** - the program will guide you through the process
4. **Wait for completion** - it will download all your user data

### Step 7: Check Your Results

- **Your data will be saved in:** `private/userData/` folder
- **You'll see files like:** `user_[userid]_events_[dates].json`
- **Open these files** to see the user behavior data!