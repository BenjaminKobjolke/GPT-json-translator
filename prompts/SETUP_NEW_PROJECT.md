# Setup GPT-json-translator for a New Project

You are helping me set up the GPT-json-translator tool for my project. Follow these steps:

## Step 1: Gather Project Information

Ask me for:
1. **Project folder path** - The root folder of my project (e.g., `D:\wamp64\www\dashboard`)
2. **Source language file path** - The path to my primary language JSON file (e.g., `D:\wamp64\www\dashboard\lang\en.json`)

## Step 2: Check for Second Input Language

Look at the folder containing my source language file. If there are multiple JSON files present (e.g., `en.json`, `de.json`, `fr.json`):

Ask me: "I found multiple JSON files in your language folder: [list files]. Would you like to use a second input language for better translation quality? If yes, which file should be used as the second input?"

**Note:** The second input language provides additional context to the AI translator, resulting in more accurate translations. The second input file will NOT be overwritten during translation.

## Step 3: Create the Batch File

Create a `tools` subfolder in my project if it doesn't exist, then create a file named `translator_app_texts.bat` with the following content:

### If using second input language:
```bat
d:
cd "d:\GIT\BenjaminKobjolke\GPT-json-translator"

call activate_environment.bat

call .\.venv\Scripts\python.exe json_translator.py "<SOURCE_LANGUAGE_FILE_PATH>" --second-input "<SECOND_INPUT_FILE_PATH>"

cd %~dp0
```

### If NOT using second input language:
```bat
d:
cd "d:\GIT\BenjaminKobjolke\GPT-json-translator"

call activate_environment.bat

call .\.venv\Scripts\python.exe json_translator.py "<SOURCE_LANGUAGE_FILE_PATH>"

cd %~dp0
```

Replace `<SOURCE_LANGUAGE_FILE_PATH>` and `<SECOND_INPUT_FILE_PATH>` with the actual paths I provided.

## Step 4: Confirm Setup

After creating the batch file, tell me:
- The full path to the created batch file
- How to run it (double-click or run from command line)
- Remind me that I need to have the GPT-json-translator configured with a valid OpenAI API key in `settings.ini`

---

## Example

**User provides:**
- Project folder: `D:\wamp64\www\dashboard`
- Source file: `D:\wamp64\www\dashboard\lang\en.json`
- Second input: `D:\wamp64\www\dashboard\lang\de.json`

**Result batch file at** `D:\wamp64\www\dashboard\tools\translator_app_texts.bat`:
```bat
d:
cd "d:\GIT\BenjaminKobjolke\GPT-json-translator"

call activate_environment.bat

call .\.venv\Scripts\python.exe json_translator.py "D:\wamp64\www\dashboard\lang\en.json" --second-input "D:\wamp64\www\dashboard\lang\de.json"

cd %~dp0
```
