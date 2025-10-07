# 🐍 Python Beginner Guide

> A complete step-by-step setup & learning roadmap for Python beginners using **VS Code**.

---

## 🎓 Learn Python

### 🎥 Recommended Tutorials

- **Bro Code Python Playlist:** [Watch on YouTube](https://www.youtube.com/playlist?list=PLZPZq0r_RZOOkUQbat8LyQii36cJf2SWT)  
  _(First 2 hours are enough to get started)_

### 📚 Documented Resources

1. [Official Python Tutorial](https://docs.python.org/3/tutorial/)
2. [W3Schools Python Tutorial](https://www.w3schools.com/python/)
3. [Real Python](https://realpython.com/) _(Covers Tkinter & Pygame)_

---

## 💻 Python GUI

### 🪟 Tkinter

- [Tkinter Full Course](https://www.youtube.com/watch?v=TuLxsvK4svQ)

### 🎮 Pygame (Animation)

- [Recommended Playlist](https://www.youtube.com/playlist?list=PLzMcBGfZo4-lp3jAExUCewBfMx3UZFkh5)
- [Full Course](https://www.youtube.com/watch?v=AY9MnQ4x3zk)

---

## 🧠 Advanced Tkinter Playlists

- [Video 1](https://www.youtube.com/watch?v=5UQZNHlaUVc&list=PLZPZq0r_RZOOeQBaP5SeMjl2nwDcJaV0T&index=28)
- [Video 2](https://www.youtube.com/watch?v=V9MbQ2Xl4CE&list=PLZPZq0r_RZOOeQBaP5SeMjl2nwDcJaV0T&index=29)
- [Video 3](https://www.youtube.com/watch?v=bfRwxS5d0SI&list=PLZPZq0r_RZOOeQBaP5SeMjl2nwDcJaV0T&index=30)

---

## 🧑‍🏫 Presentations

- Recommended tools: **[Gamma](https://gamma.app/)** or **[Prezi](https://prezi.com/)**
- Use any AI chatbot to craft good prompts (ChatGPT, DeepSeek, Claude, etc.)

---

## 💡 Vibe Coding Tools (AI-assisted)

- **VS Code GitHub Copilot**
- **[Phind.com](https://phind.com)**
- **AI Chatbots:** ChatGPT / DeepSeek / Claude _(Best choice)_

---

## ⚙️ Install Python 🐍

### Step 1: Download Python

1. Go to [python.org](https://python.org)
2. Hover over **Download**
3. Click the gray button under “Download for Windows”
4. Download starts automatically (e.g., `python-3.13.7-amd64.exe`)

### Step 2: Install Python

⚠️ **Important:**

- During installation, **check the box** “Add Python to PATH” ✅
- Click **Install Now** and wait for completion

### Step 3: Verify Installation

Open CMD and run:

```bash
python --version
```

If you see something like `Python 3.13.7` → ✅ **Success!**

---

## 🧩 Setup Python in VS Code

### Step 1: Install Python Extension

1. Open VS Code
2. Go to Extensions (Ctrl + Shift + X)
3. Search “Python” (by Microsoft)
4. Click **Install**

### Step 2: Install Pylance

Usually auto-installs. If not, install manually from the Extensions tab.

---

## 📝 Create Your First Python File

### Step 1: Create a Folder

Create a folder (e.g. `MyPythonProject`).

### Step 2: Open Folder in VS Code

`File → Open Folder → Select "MyPythonProject"`

### Step 3: Create a New File

Name it `test.py`.

### Step 4: Write Code

```python
print("Hello, World!")
print("Python is working!")
```

### Step 5: Run Code 🚀

**Method 1:** Click ▶️ (top-right in VS Code)  
**Method 2:** Right-click → _Run Python File in Terminal_

---

## 📦 Install Libraries (Tkinter & Pygame)

### 🪟 Tkinter

Already comes with Python! Test it:

```python
import tkinter as tk

root = tk.Tk()
root.title("It Works!")
root.geometry("300x200")
tk.Label(root, text="Tkinter is working!").pack()
root.mainloop()
```

### 🎮 Pygame

#### Step 1: Open Terminal in VS Code

`Terminal → New Terminal`

#### Step 2: Install Pygame

```bash
pip install pygame
```

#### Step 3: Test Pygame

```python
import pygame
pygame.init()

screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("Pygame Test")

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
```

A small window should appear briefly! ✅

---

## 🧰 Common Problems & Fixes

### ❌ Problem 1: “python is not recognized”

**Fix:**

- [Watch this Fix](https://www.youtube.com/watch?v=91SGaK7_eeY)
- Or reinstall Python and ensure “Add to PATH” is checked.

---

### ❌ Problem 2: “No module named pygame”

**Fix:**  
Run in terminal:

```bash
pip install pygame
```

---

### ❌ Problem 3: Code doesn’t run with ▶️

**Fix:**

- Save file (`Ctrl + S`)
- Ensure it ends with `.py`
- Try right-click → _Run Python File in Terminal_

---

### ❌ Problem 4: VS Code doesn’t recognize Python

**Fix:**

1. Press `Ctrl + Shift + P`
2. Search: **Python: Select Interpreter**
3. Choose the Python version
4. Restart VS Code

---
