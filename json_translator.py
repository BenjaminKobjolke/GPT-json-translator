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

languagesAll = ["it-IT", 
                "fr-FR", "es-ES", "de-DE", "pt-PT", "pt-BR", "nl-NL", "ru-RU", "pl-PL", "tr-TR", "zh-CN", "ja-JP",
                "ko-KR",
                "ar-AR", "hi-IN", "sv-SE", "no-NO", "fi-FI", "da-DK", "cs-CZ",
                "sk-SK", "hu-HU", "ro-RO", "uk-UA", "bg-BG", "hr-HR", "sr-SP", "sl-SI", "et-EE", "lv-LV", "lt-LT",
                "he-IL",
                "fa-IR", "ur-PK", "bn-IN", "ta-IN", "te-IN", "mr-IN", "ml-IN", "th-TH", "vi-VN"]


languages = ["it-IT", 
                "fr-FR", "es-ES", "de-DE", "pt-PT", "pt-BR", "nl-NL", "ru-RU", "pl-PL", "tr-TR", "zh-CN", "ja-JP",
                "ko-KR",
                "ar-AR", "hi-IN", "sv-SE", "no-NO", "fi-FI", "da-DK", "cs-CZ",
                "sk-SK", "hu-HU", "ro-RO", "uk-UA", "bg-BG", "hr-HR", "sr-SP", "sl-SI", "et-EE", "lv-LV", "lt-LT",
                "he-IL",
                "fa-IR", "ur-PK", "bn-IN", "ta-IN", "te-IN", "mr-IN", "ml-IN", "th-TH", "vi-VN"]



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
    with open(input_path, "r", encoding="utf-8") as f:
        source_json = json.load(f)
except PermissionError:
    print(f"Permission denied: Unable to read the file {input_path}")
    exit()
except json.JSONDecodeError as e:
    print(f"Error parsing source JSON file {input_path}:")
    print(f"Error details: {str(e)}")
    exit()
except IOError as e:
    print(f"Error reading source file {input_path}:")
    print(f"Error details: {str(e)}")
    exit()


# Function to load overrides for a target language
def load_overrides(language_code):
    # get path from argument_file_path
    path_without_file = os.path.dirname(argument_file_path)
    overrides_path = os.path.join(path_without_file, "_overrides", f"{language_code}.json")
    if os.path.exists(overrides_path):
        try:
            with open(overrides_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading overrides for {language_code}:")
            print(f"Error details: {str(e)}")
            return {}
    return {}


# Define function to translate text for a given target language
def translate(target_lang, rows_to_translate):
    print(f"Translating to {target_lang}...")
    try:
        # Call OpenAI API to translate text
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
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
    except Exception as e:
        print(f"Error calling OpenAI API for {target_lang}:")
        print(f"Error details: {str(e)}")
        return {}
    # only double quotes are allowed in JSON, so replace single quotes with double quotes
    # translated_json_str = translated_json_str.replace("'", '"')
    print(f"Translation to {target_lang} complete.")
    # print(f"Translated JSON:\n{translated_json}\n")
    # convert the string into a json object
    try:
        translated_json = json.loads(translated_json_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response for {target_lang}:")
        print(f"Error details: {str(e)}")
        print("Problematic JSON string:")
        print(translated_json_str)
        # Return empty dict to allow process to continue for other languages
        return {}
    return translated_json


def filter_overrides(overrides, keys_for_translation):
    # Create a copy of keys_for_translation to work on
    filtered_keys = keys_for_translation.copy()
    # Iterate through the overrides
    for key in overrides.keys():
        # If the key from overrides exists in keys_for_translation, remove it
        filtered_keys.pop(key, None)
    return filtered_keys


# Main translation logic including loading overrides
with concurrent.futures.ThreadPoolExecutor() as executor:
    future_to_language = {}
    for target_language in languages:
        lang_code = target_language.split('-')[0]
        print(f"Processing language: {lang_code}")
        overrides = load_overrides(lang_code)

        # Determine which keys need translation
        existing_json_path = os.path.join(os.path.dirname(argument_file_path), f"{lang_code}.json")
        existing_json = {}
        if os.path.exists(existing_json_path):
            try:
                with open(existing_json_path, "r", encoding="utf-8") as f:
                    existing_json = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading existing translations for {lang_code}:")
                print(f"Error details: {str(e)}")
                existing_json = {}

        keys_for_translation = {key: value for key, value in source_json.items() if
                                key not in existing_json}

        keys_for_translation = filter_overrides(overrides, keys_for_translation)

        '''
        print(overrides)
        print(keys_for_translation)
        exit()
        '''
        if keys_for_translation:
            future_to_language[executor.submit(translate, target_language, keys_for_translation)] = (
                target_language, existing_json, overrides)
        else:
            # save at least the overrides
            lang_code = target_language.split('-')[0]
            output_path = os.path.join(os.path.dirname(argument_file_path), f"{lang_code}.json")
            updated_json = {**overrides, **existing_json}
            # print(updated_json)

            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(updated_json, f, indent=2, ensure_ascii=False)
                print(f"Output file saved as {output_path}")
            except IOError as e:
                print(f"Error saving file for {target_language}:")
                print(f"Error details: {str(e)}")

    # Process completed translation tasks
for future in concurrent.futures.as_completed(future_to_language):
    target_language, existing_json, overrides = future_to_language[future]
    try:
        translated_json = future.result()

        # Merge translations with existing JSON and overrides, giving precedence to overrides
        updated_json = {**existing_json, **translated_json, **overrides}
        lang_code = target_language.split('-')[0]
        output_path = os.path.join(os.path.dirname(argument_file_path), f"{lang_code}.json")

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(updated_json, f, indent=2, ensure_ascii=False)
            print(f"Output file saved as {output_path}")
        except IOError as e:
            print(f"Error saving translation file for {target_language}:")
            print(f"Error details: {str(e)}")
    except Exception as e:
        print(f"Error processing translation for {target_language}:")
        print(f"Error details: {str(e)}")

print("Translation process complete.")
