import os
import json
import xml.etree.ElementTree as ET
from subprocess import call

def decode_apk(apk_path):
    output_dir = f"{apk_path}_decoded"
    # Check if output directory already exists to avoid re-decoding
    if not os.path.exists(output_dir):
        # Use apktool jar file to decode the APK file
        call(f"java -jar apktool_2.9.3.jar d {apk_path} -o {output_dir}", shell=True)
    else:
        print(f"Directory {output_dir} already exists. Skipping decoding.")
    return output_dir

def process_apks(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".apk"):
                apk_path = os.path.join(root, file)
                decoded_dir = decode_apk(apk_path)
def load_permissions_dict(json_file_path):
    """Load permissions and their descriptions from a JSON file."""
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        return json.load(json_file)

def parse_manifest(file_path, permissions_dict):
    """Parse the AndroidManifest.xml and extract package name and permissions."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        ns = {'android': '{http://schemas.android.com/apk/res/android}'}
        package_name = root.get('package', 'Unknown Package')
        permissions = root.findall(".//uses-permission", ns)
        extracted_permissions = []
        for perm in permissions:
            perm_name = perm.get(f"{ns['android']}name")
            if perm_name:
                simple_name = perm_name.split('.')[-1]
                description = permissions_dict.get(simple_name, "No description available")
                extracted_permissions.append({"permission": simple_name, "description": description})
            else:
                extracted_permissions.append({"permission": "Unknown", "description": "No description available"})
        return package_name, extracted_permissions, file_path
    except ET.ParseError as e:
        return 'Unknown Package', [], file_path

def find_manifest_files(directory):
    """Find AndroidManifest.xml files in the first-level subdirectories of the specified directory."""
    manifest_files = []
    subdirs = [os.path.join(directory, o) for o in os.listdir(directory) 
               if os.path.isdir(os.path.join(directory,o))]
    for subdir in subdirs:
        for root, dirs, files in os.walk(subdir, topdown=True):
            for file in files:
                if file.endswith('AndroidManifest.xml'):
                    manifest_files.append(os.path.join(root, file))
            break  # Ensure only the top level of each subdirectory is checked
    return manifest_files

def process_manifest_files(manifest_files, permissions_dict):
    """Process each manifest file found and compile results."""
    result_data = {}
    for file_path in manifest_files:
        package, permissions, _ = parse_manifest(file_path, permissions_dict)
        result_data[package] = {
            "file_path": file_path,
            "permissions": permissions
        }
    return result_data

def save_to_json(data, filename):
    """Save extracted data to a JSON file."""
    with open(filename, 'w', newline='', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)

# Example usage
directory_path = 'Result'
apk_info = process_apks(directory)

permissions_dict = load_permissions_dict('user_permission.dict')
output = 'permissions_output.json'

manifest_files = find_manifest_files(directory_path)

print(f"Found {len(manifest_files)} AndroidManifest.xml files.")

data = process_manifest_files(manifest_files, permissions_dict)
save_to_json(data, output)
