
# Script to strip specific onclick attributes
file_path = r'c:\JESSE.01\jesse_saas\app\templates\menu\public.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content.replace('onclick="flipPrev()"', '')
    new_content = new_content.replace('onclick="flipNext()"', '')

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Success: Removed onclick handlers.")
    else:
        print("Info: No onclick handlers found (already removed?).")

except Exception as e:
    print(f"Error: {e}")
