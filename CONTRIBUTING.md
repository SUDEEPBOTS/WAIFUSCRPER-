# Contributing to WAIFUSCRPER 🌸

Thank you for your interest in contributing to **WAIFUSCRPER**! We welcome community contributions, improvements, and bug reports.

---

## 🛠️ Getting Started

1. **Fork the Repository**
   - Click the **Fork** button on GitHub to fork into your own profile.
2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/WAIFUSCRPER-.git
   cd WAIFUSCRPER-
   ```
3. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. **Create a feature branch**
   ```bash
   git checkout -b feature/awesome-waifu-feature
   ```

---

## 📜 Coding Guidelines

- **Python Version**: Target Python 3.10+ (specifically Python 3.11).
- **Code Style**: Follow PEP 8 guidelines. Keep asynchronous code clean and properly awaited.
- **Copyright Header**: Maintain the standard short copyright header on all modified/new files:
  ```python
  # --------------------------------------------------------------------------
  # Copyright (c) 2026 TOXICXD43 / SUDEEPBOTS. All Rights Reserved.
  # Licensed under the MIT License. See LICENSE in the project root for details.
  # --------------------------------------------------------------------------
  ```
- **Error Handling**: Gracefully handle Telegram `FloodWait` and network timeouts.

---

## 🧪 Testing

Before submitting your PR, ensure syntax passes without any compilation errors:
```bash
python3 -m py_compile $(find . -name "*.py" -not -path "*/.*")
```

---

## 📬 Submitting a Pull Request

1. Push your branch:
   ```bash
   git push origin feature/awesome-waifu-feature
   ```
2. Open a Pull Request against the `main` branch.
3. Fill in the provided Pull Request template completely.
