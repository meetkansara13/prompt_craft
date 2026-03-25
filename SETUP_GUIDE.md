# PromptCraft Pro v3 — Setup Guide
### Windows · Anaconda Prompt · Step by Step

---

## STEP 1 — Extract the zip

Extract `promptcraft_pro_v3.zip` to your D: drive.

After extraction your folder should look like:

```
D:\promptcraft_v3\
    app\
    config\
    static\
    templates\
    tests\
    run.py
    requirements.txt
    environment.yml
    .env.example
    ...
```

---

## STEP 2 — Open Anaconda Prompt

Search **Anaconda Prompt** in Windows Start menu and open it.

You will see something like:

```
(base) C:\Users\YourName>
```

---

## STEP 3 — Switch to D: drive

```bat
D:
```

You will see:

```
(base) D:\>
```

---

## STEP 4 — Go into the project folder

```bat
cd promptcraft_v3
```

You will see:

```
(base) D:\promptcraft_v3>
```

---

## STEP 5 — Create the conda environment

```bat
conda env create -f environment.yml
```

This reads `environment.yml` and creates a new conda environment called **promptcraft** with Python 3.11 and all required packages.

Wait for it to finish. You will see:

```
Collecting package metadata: done
Solving environment: done
...
done
#
# To activate this environment, use:
#     conda activate promptcraft
```

> **This step is only needed ONCE.**
> Next time you just activate (Step 6).

---

## STEP 6 — Activate the environment

```bat
conda activate promptcraft
```

Your prompt changes from `(base)` to `(promptcraft)`:

```
(promptcraft) D:\promptcraft_v3>
```

---

## STEP 7 — Set up your API key

Copy the example config file:

```bat
copy .env.example .env
```

Open `.env` in Notepad:

```bat
notepad .env
```

You will see:

```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
FLASK_SECRET_KEY=change-this-to-a-random-string
FLASK_ENV=development
FLASK_DEBUG=true
```

Replace `sk-ant-api03-your-key-here` with your real key.
Replace `change-this-to-a-random-string` with any random text.

Save and close Notepad.

> **Get a free API key at:** https://console.anthropic.com

---

## STEP 8 — Run the app

```bat
python run.py
```

You will see:

```
  ✦  PromptCraft Pro v3
  ─────────────────────────────────────────
  http://localhost:5000
  ENV=development  DEBUG=True
  Press Ctrl+C to stop
```

Open your browser and go to: **http://localhost:5000**

---

## Every time after the first setup

Open Anaconda Prompt, then:

```bat
D:
cd promptcraft_v3
conda activate promptcraft
python run.py
```

---

## Run the tests

With the environment active:

```bat
pytest
```

Or run specific test groups:

```bat
REM Unit tests only (pure Python, zero external dependencies)
pytest tests\unit\ -v

REM Integration tests only (Flask + mocked Anthropic, no real API call)
pytest tests\integration\ -v
```

---

## Common errors and fixes

| Error | Fix |
|---|---|
| `conda: command not found` | Open **Anaconda Prompt**, not regular Command Prompt |
| `conda env create` fails with "already exists" | Run `conda env remove -n promptcraft` then try again |
| `ModuleNotFoundError: No module named 'flask'` | You forgot to activate: `conda activate promptcraft` |
| `No API key — please set your key first` | Open `.env` and check `ANTHROPIC_API_KEY` is set correctly |
| `API key rejected` | Make sure your key starts with `sk-ant-` and is copy-pasted correctly |
| Port 5000 already in use | Change port in `run.py`: `app.run(port=5001)` |

---

## Deactivate / remove environment

```bat
REM Deactivate (go back to base)
conda deactivate

REM Remove environment completely
conda env remove -n promptcraft
```
