# 🎓 Canvas Student Dashboard

A real-time student dashboard for VinUni Canvas LMS. View your courses, grades, upcoming assignments, and missing submissions — all in one place.

Built with **Streamlit** and deployed for free on **Streamlit Community Cloud**.

## ✨ Features

- 📚 Active courses for the current term
- 📊 Live grades and scores
- ⚠️ Missing submissions tracker
- 📅 Upcoming assignments with urgency indicators
- 🏆 Full grade history across all terms

## 🚀 Deploy (Free)

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/canvas-dashboard.git
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to [streamlit.io/cloud](https://streamlit.io/cloud) and sign in with GitHub
2. Click **"New app"** → pick your repo → branch `main` → file `dashboard.py`
3. **Set secrets:**
   - `CANVAS_URL` → `https://vinuni.instructure.com`
   - `CANVAS_TOKEN` → your Canvas API token
4. Click **Deploy** ✅

Your dashboard will be live at `https://YOUR_APP.streamlit.app` — no credit card needed.

### 3. Run Locally (optional)

```bash
cd canvas-dashboard
pip install -r requirements.txt
mkdir -p .streamlit
echo "CANVAS_TOKEN='your-token'" > .streamlit/secrets.toml
echo "CANVAS_URL='https://vinuni.instructure.com'" >> .streamlit/secrets.toml
streamlit run dashboard.py
```

## 🔑 Getting Your Canvas Token

1. Log into Canvas → **Account** (sidebar) → **Settings**
2. Scroll to **Approved Integrations**
3. Click **+ New Access Token**
4. Give it a name (e.g., "Dashboard") and generate
5. Copy the token immediately — it won't show again

## 📁 Project Structure

```
canvas-dashboard/
├── dashboard.py        # Main Streamlit app
├── requirements.txt    # Python dependencies
└── .streamlit/
    └── secrets.toml    # Your Canvas credentials (gitignored)
```

---

Built with ❤️ by Forge
