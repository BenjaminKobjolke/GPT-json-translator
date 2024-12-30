import os
import json
import sys

def remove_attributes_from_json_files(directory, attributes_file):
    
    if not os.path.isfile(attributes_file):
        print(f"Attributes file {attributes_file} does not exist.")
        sys.exit(1)
        
    try:
        with open(attributes_file, 'r', encoding='utf-8') as file:
            file_content = file.read()
            print("File content:", file_content)  # Debugging line
            attributes_to_remove = json.loads(file_content)
    except Exception as e:
        print(f"Failed to load attributes to remove: {e}")
        sys.exit(1)
    
    # Iterate over all .json files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".json") and filename != "en.json":
            file_path = os.path.join(directory, filename)
            print("open file path: " + file_path)
            # Load the JSON content
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
               
            for attribute in attributes_to_remove:
                 if attribute in data:
                    print(f"Removing attribute {attribute} from {filename}")  # Debugging line
                    del data[attribute]              
            
            # Save the modified JSON content back to the file
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)

if __name__ == "__main__":    
    directory_path = sys.argv[1]
    attributes_to_remove_file = sys.argv[2]
    
    print(directory_path)
    print(attributes_to_remove_file)
    
    
    remove_attributes_from_json_files(directory_path, attributes_to_remove_file)
