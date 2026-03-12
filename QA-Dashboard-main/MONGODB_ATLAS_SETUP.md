# Setting Up MongoDB Atlas (Cloud Database)

## Step 1: Create MongoDB Atlas Account (FREE)

1. Go to https://www.mongodb.com/cloud/atlas/register
2. Sign up with your email or Google account
3. Choose the **FREE M0 tier** (512MB storage, perfect for your needs)

## Step 2: Create a Cluster

1. After logging in, click **"Build a Database"**
2. Select **"M0 FREE"** tier
3. Choose your cloud provider (AWS recommended) and region (choose closest to you)
4. Click **"Create Cluster"** (takes 3-5 minutes)

## Step 3: Set Up Database Access

1. Click **"Database Access"** in left sidebar
2. Click **"Add New Database User"**
3. Choose **"Password"** authentication
4. Username: `qa_dashboard_user` (or your choice)
5. Password: Click **"Autogenerate Secure Password"** and **SAVE IT**
6. Database User Privileges: Select **"Read and write to any database"**
7. Click **"Add User"**

## Step 4: Set Up Network Access

1. Click **"Network Access"** in left sidebar
2. Click **"Add IP Address"**
3. Click **"Allow Access from Anywhere"** (for now - you can restrict later)
4. Click **"Confirm"**

## Step 5: Get Your Connection String

1. Go back to **"Database"** (Overview)
2. Click **"Connect"** on your cluster
3. Select **"Connect your application"**
4. Driver: **Python**, Version: **3.12 or later**
5. Copy the connection string - it looks like:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

## Step 6: Update Your Backend .env File

Replace `<username>` and `<password>` in the connection string with your actual credentials.

**IMPORTANT:** I'll update your backend/.env file now. You need to provide me with:
- Your MongoDB Atlas connection string
- Your preferred database name (e.g., "qa_dashboard_production")

Example connection string format:
```
mongodb+srv://qa_dashboard_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/qa_dashboard_production?retryWrites=true&w=majority
```

## Benefits of MongoDB Atlas:

✅ **Free forever** (512MB - enough for thousands of test cases)
✅ **Automatic backups**
✅ **99.95% uptime SLA**
✅ **Global deployment**
✅ **Easy to scale** when you grow
✅ **Built-in monitoring and alerts**

## After Setup:

Once you provide the connection string, I'll:
1. Update your backend/.env file
2. Restart the backend
3. Your data will automatically migrate to the cloud!

**Would you like me to wait for your MongoDB Atlas connection string, or would you prefer to set it up yourself later?**
