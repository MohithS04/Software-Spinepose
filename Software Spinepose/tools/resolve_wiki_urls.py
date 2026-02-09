import hashlib

filenames = [
    "Squatting.jpg",
    "Romanian-deadlift-1.png",
    "H._J._Whigham,_golfer_(in_follow_through).PNG",
    "Summer_Streets_NYC_2023-08-19,_female_runner_on_Park_Av_and_66th,_Upper_East_Side,_Manhattan.jpg"
]

base_url = "https://upload.wikimedia.org/wikipedia/commons"

print("Resolving URLs...")
for fname in filenames:
    # Wikipedia spaces are usually underscores in filenames
    clean_name = fname.replace(" ", "_")
    # MD5 hash
    m = hashlib.md5(clean_name.encode('utf-8')).hexdigest()
    # Path: /a/ab/Filename
    path = f"{m[0]}/{m[0:2]}"
    full_url = f"{base_url}/{path}/{clean_name}"
    print(f"{fname}: {full_url}")
