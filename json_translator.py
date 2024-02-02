# Credits: Leonardo Rignanese (twitter.com/leorigna)
import sys

import openai
import json
import os
import concurrent.futures
from config import API_KEY, SOURCE_PATH

# Set up OpenAI API credentials (https://beta.openai.com/docs/developer-quickstart/your-api-keys)
openai.api_key = API_KEY

# Set up target languages for translation

languagesAll = ["it-IT", "en-US",
             "fr-FR", "es-ES", "de-DE", "pt-PT", "pt-BR", "nl-NL", "ru-RU", "pl-PL", "tr-TR", "zh-CN", "ja-JP", "ko-KR",
             "ar-AR", "hi-IN", "sv-SE", "no-NO", "fi-FI", "da-DK", "cs-CZ",
             "sk-SK", "hu-HU", "ro-RO", "uk-UA", "bg-BG", "hr-HR", "sr-SP", "sl-SI", "et-EE", "lv-LV", "lt-LT", "he-IL",
             "fa-IR", "ur-PK", "bn-IN", "ta-IN", "te-IN", "mr-IN", "ml-IN", "th-TH", "vi-VN"]
languages = ["de-DE"]
'''
languages = ["it-IT", "en-US",
             "fr-FR", "es-ES", "de-DE"]
'''

argument_file_path = None

# for debug
# get the current working directory
print(os.getcwd())

argument_file_path = os.getcwd() + "\\locales\\en.json"
if len(sys.argv) > 1:
    # Argument is provided
    argument_file_path = sys.argv[1
    ]

# PromptAll user to enter the path to the input JSON file
if argument_file_path:
    input_path = argument_file_path
elif (SOURCE_PATH):
    input_path = SOURCE_PATH
else:
    input_path = input("Enter the path to the source JSON file: ")
print(f"Reading input file from {input_path}")

# check if path exists
if not os.path.exists(input_path):
    print(f"Error: Path not found at {input_path}")
    exit()

# Load JSON file with language translations as a single string
try:
    with open(input_path, "r") as f:
        source_json = json.load(f)
    # Do E_something with source_json
except PermissionError:
    print(f"Permission denied: Unable to read the file {input_path}")
    exit()


# Define function to translate text for a given target language
def translate(target_lang, rows_to_translate):
    print(f"Translating to {target_lang}...")
    # Call OpenAI API to translate text
    completion = openai.chat.completions.create(
        model="gpt-4-1106-preview",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are TranslatorGpt, a powerful language model designed for seamless translation of text across multiple languages. You have been trained on a vast corpus of linguistic data and possess a deep understanding of grammar, syntax, and vocabulary of every language in the world. You only translate json values, not json keys.",
            },
            {
                "role": "user",
                "content": f"Translate the following JSON to {target_lang}:\n\n{rows_to_translate}\n",
            },
        ],
    )
    print(completion.choices[0].message.content)
    translated_json_str = completion.choices[0].message.content
    # only double quotes are allowed in JSON, so replace single quotes with double quotes
    # translated_json_str = translated_json_str.replace("'", '"')
    print(f"Translation to {target_lang} complete.")
    # print(f"Translated JSON:\n{translated_json}\n")
    # convert the string into a json object
    translated_json = json.loads(translated_json_str)
    return translated_json


# Translate the JSON string into target languages
with concurrent.futures.ThreadPoolExecutor() as executor:
    # Submit translation tasks to the executor
    future_to_language = {}
    for target_language in languages:
        filename = target_language.split('-')[0]
        filename = f"{filename}.json"
        output_path = os.path.join(os.path.dirname(input_path), filename)

        existing_json = {}
        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                try:
                    existing_json = json.load(f)
                except json.decoder.JSONDecodeError:
                    existing_json = {}

        # Filter out keys from existing_json that are not in source_json (en.json)
        filtered_existing_json = {key: value for key, value in existing_json.items() if key in source_json}

        # Determine keys that need translation
        missing_keys = set(source_json.keys()) - set(filtered_existing_json.keys())
        if missing_keys:
            print(f"Found {len(missing_keys)} missing keys for {target_language}")
            filtered_json = {key: value for key, value in source_json.items() if key in missing_keys}
            future_to_language[
                executor.submit(translate, target_language, filtered_json)] = target_language, filtered_existing_json
        else:
            # If no new translations are needed, write the filtered existing translations back to the file
            with open(output_path, "w") as f:
                json.dump(filtered_existing_json, f, indent=2)
            print(f"No new translations needed for {target_language}. Updated file saved.")

# Process completed translation tasks and write output files
for future in concurrent.futures.as_completed(future_to_language):
    target_language, filtered_existing_json = future_to_language[future]
    filename = target_language.split('-')[0]
    filename = f"{filename}.json"
    try:
        translated_json = future.result()
        # Combine filtered existing translations with new translations
        output_json = {**filtered_existing_json, **translated_json}

        output_path = os.path.join(os.path.dirname(input_path), filename)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_json, f, indent=2, ensure_ascii=False)
        print(f"Output file saved as {output_path}")
    except Exception as e:
        print(f"Error occurred while translating to {target_language}: {e}")

print("Translation complete.")

# Credits: Leonardo Rignanese (twitter.com/leorigna)
