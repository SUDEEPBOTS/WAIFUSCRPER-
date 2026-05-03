<h1 align="center">
    ─˹ 𝐖ᴀɪꜰᴜ ꭙ sᴄʀᴘᴇʀ ˼─
</h1>

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com/?lines=WELCOME+TO+WAIFUSCRPER+REPO;ADVANCED+WAIFU+SCRAPER+BOT;SCRAPE+%7C+APPROVE+%7C+SAVE+%7C+AUTO;POWERED+BY+PYROGRAM+%2B+MONGODB" alt="Typing SVG">
</p>

<p align="center">
  <img src="https://files.catbox.moe/sjm5sv.jpg" width="350" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
</p>

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com/?lines=FORK+THIS+REPO+BEFORE+DEPLOY;STAR+THIS+REPO+IF+YOU+LIKE+IT;🌸+HAPPY+SCRAPING~" alt="Typing SVG">
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/YOURNAME/WAIFUSCRPER?style=for-the-badge&logo=github&color=f783ac&labelColor=1a1a2e"/>
  <img src="https://img.shields.io/github/forks/YOURNAME/WAIFUSCRPER?style=for-the-badge&logo=github&color=c084fc&labelColor=1a1a2e"/>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=1a1a2e"/>
  <img src="https://img.shields.io/badge/Pyrogram-2.0.106-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white&labelColor=1a1a2e"/>
  <img src="https://img.shields.io/badge/MongoDB-Motor-47A248?style=for-the-badge&logo=mongodb&logoColor=white&labelColor=1a1a2e"/>
</p>

---

## ⚠️ 𝗗𝗜𝗦𝗖𝗟𝗔𝗜𝗠𝗘𝗥

«Note: Do not use your main Telegram account as a userbot or string session.
The account may get restricted or lose access to channels.
Always use a spare/dedicated account as the scraper userbot.»

---

## 🌸 What is WAIFUSCRPER?

A **Telegram bot** that scrapes waifu images from any Telegram channel using a userbot string session, parses their captions, uploads images to **Catbox / ImgBB**, and saves them directly to **MongoDB** — ready to be used by YUKIWAFUS or any waifu bot.

**Features:**
- Scrape any public/private channel via userbot
- Manual approve mode — review each waifu before saving
- Auto mode — save all automatically
- Catbox + ImgBB image hosting
- Caption parsing — name, rarity, series, ID auto-detected
- FloodWait protection with smart delays
- Live progress updates while scraping
- Stop anytime with `/wstop`

---

## 🖇 Generating Pyrogram String Session

Before deploying, generate a Pyrogram V2 String Session for your userbot:

<p align="center">
<a href="https://t.me/SessionStringZbot">
<img src="https://img.shields.io/badge/Generate%20String%20Session-blueviolet?style=for-the-badge&logo=appveyor" width="250"/>
</a>
</p>

---

<h2 align="center">─「 ᴅᴇᴘʟᴏʏᴍᴇɴᴛ ᴍᴇᴛʜᴏᴅs 」─</h2>

## 🚀 DEPLOY ON HEROKU

<p align="center">
<a href="https://dashboard.heroku.com/new?template=https://github.com/YOURNAME/WAIFUSCRPER">
<img src="https://img.shields.io/badge/Deploy%20On%20Heroku-430098?style=for-the-badge&logo=heroku" width="220">
</a>
</p>

---

## 💻 DEPLOY ON VPS / LOCALHOST (Python 3.11 + VENV)

**1️⃣ Update System**
```bash
sudo apt update && sudo apt upgrade -y
```

**2️⃣ Install Python 3.11**
```bash
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y
```

**3️⃣ Install Required Packages**
```bash
sudo apt install git curl nano nodejs npm -y
```

**4️⃣ Install PM2**
```bash
sudo npm install -g pm2
```

**5️⃣ Clone Repository**
```bash
git clone https://github.com/YOURNAME/WAIFUSCRPER.git
cd WAIFUSCRPER
```

**6️⃣ Create Virtual Environment**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

**7️⃣ Install Requirements**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**8️⃣ Setup Environment Variables**
```bash
cp .env.example .env
nano .env
```

| Variable | Required | Description |
|---|---|---|
| `API_ID` | ✅ | From [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | ✅ | From [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | ✅ | From [@BotFather](https://t.me/BotFather) |
| `MONGO_URI` | ✅ | MongoDB connection string |
| `OWNER_ID` | ✅ | Your Telegram user ID |
| `LOGGER_ID` | ✅ | Group/channel ID for approve logs |
| `STRING_SESSION` | ✅ | Pyrogram V2 string session |
| `TARGET_CHANNEL` | ✅ | Channel username or ID to scrape |
| `CATBOX_HASH` | ❌ | Catbox user hash for image hosting |
| `IMGBB_KEY` | ❌ | ImgBB API key (fallback host) |
| `APPROVE_MODE` | ❌ | `true` = manual review, `false` = auto |
| `DB_NAME` | ❌ | MongoDB DB name (default: waifuscrper) |
| `COLLECTION_NAME` | ❌ | Collection name (default: waifus) |

**9️⃣ Start Bot (PM2 — 24/7)**
```bash
pm2 start "venv/bin/python -m WAIFUSCRPER" --name WaifuScrper
pm2 save
pm2 startup
```

**🔍 Check Logs**
```bash
pm2 logs WaifuScrper
```

---

<h2 align="center">─「 ᴄᴏᴍᴍᴀɴᴅs 」─</h2>

### 🤖 Bot Commands

| Command | Description |
|---|---|
| `/start` | Start the bot & see main menu |
| `/help` | Show help menu |
| `/ping` | Check bot ping & health |

### 🌸 Scraper Commands *(Owner/Sudo only)*

| Command | Description |
|---|---|
| `/wstart` | Start scraping the target channel |
| `/wstop` | Stop the current scraping session |

### ⚙️ Config Commands *(Owner/Sudo only)*

| Command | Description |
|---|---|
| `/config` | View & edit all bot settings |
| `/setcap` | Set caption parsing keyword |
| `/setlog` | Set logger group/channel ID |
| `/setchannel` | Set target channel to scrape |
| `/setstring` | Set userbot string session |
| `/approve` | Toggle approve mode on/off |

### 🛡 Sudo Commands *(Owner only)*

| Command | Description |
|---|---|
| `/addsudo` | Add a sudo user |
| `/delsudo` | Remove a sudo user |
| `/sudolist` | List all sudo users |
| `/stats` | Bot & database stats |
| `/broadcast` | Broadcast message to all users |

---

## 🔄 How It Works

```
Target Channel
     ↓
  Userbot reads messages
     ↓
  Photo found?
     ↓
  Parse caption (name, rarity, series, ID)
     ↓
  Approve mode ON?  ──YES──→  Send to logger → Admin approves/skips
       ↓ NO                                         ↓
  Upload to Catbox/ImgBB ←───────────────── Approved
     ↓
  Save to MongoDB
     ↓
  Progress update every 10 waifus
```

---

<h2 align="center">─「 ᴄᴏɴᴛᴀᴄᴛ & sᴜᴘᴘᴏʀᴛ 」─</h2>

<p align="center">
<a href="https://t.me/Zcziiy">
<img src="https://img.shields.io/badge/Owner-Telegram-2CA5E0?style=for-the-badge&logo=telegram">
</a>
</p>

<p align="center">
<b>Owner Telegram:</b> <a href="https://t.me/Zcziiy">@Zcziiy</a>
</p>

---

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com/?lines=Thanks+for+using+WAIFUSCRPER+🌸;Star+the+repo+if+you+like+it!;Happy+scraping+waifus~" alt="Typing SVG">
</p>

