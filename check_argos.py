import argostranslate.package

argostranslate.package.update_package_index()

packages = argostranslate.package.get_available_packages()

matches = [
    p for p in packages
    if p.from_code == "en" and p.to_code == "ne"
]

if matches:
    print("English to Nepali model available!")
    for p in matches:
        print(p)
else:
    print("English to Nepali model not found.")