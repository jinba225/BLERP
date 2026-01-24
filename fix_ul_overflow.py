import os

def fix_overflow_issues(root_dir):
    target_string = 'class="bg-white rounded-lg shadow overflow-hidden"'
    replacement_string = 'class="bg-white rounded-lg shadow overflow-x-auto"'
    
    count = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('_list.html'):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if target_string in content:
                        new_content = content.replace(target_string, replacement_string)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Fixed: {filepath}")
                        count += 1
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

    print(f"\nTotal files fixed: {count}")

if __name__ == "__main__":
    templates_dir = os.path.join(os.getcwd(), 'templates')
    print(f"Scanning directory: {templates_dir}")
    fix_overflow_issues(templates_dir)
