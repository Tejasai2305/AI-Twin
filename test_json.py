import json

with open("data/notes.json", "r") as file:
    notes = json.load(file)

for note in notes:
    print(f"Title   : {note['title']}")
    print(f"Content : {note['content']}")
    print("-" * 30)