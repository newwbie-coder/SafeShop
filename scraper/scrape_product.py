import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

# ---------- PRODUCT ID ----------
product_id = "40307753"

url = f"https://www.bigbasket.com/pd/{product_id}/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# ---------- Extract hidden Next.js JSON ----------
script = soup.find("script", {"id": "__NEXT_DATA__"})
data = json.loads(script.string)

# ---------- Storage ----------
product_data = {
    "product_id": product_id,
    "ingredients": "",
    "nutrition": ""
}

# ---------- Clean text ----------
def clean_text(text):
    lines = text.splitlines()
    lines = [l.strip() for l in lines if l.strip()]
    return "\n".join(lines)

# ---------- Recursive search ----------
def search_sections(obj):

    if isinstance(obj, dict):

        if "title" in obj and "content" in obj:

            title = obj["title"]
            content = obj["content"]

            clean = BeautifulSoup(content, "html.parser").get_text()
            clean = clean_text(clean)

            # Extract only first occurrence
            if "Ingredient" in title and product_data["ingredients"] == "":
                product_data["ingredients"] = clean
                print("\n==== Ingredients ====")
                print(clean)

            if "Nutrition" in title and product_data["nutrition"] == "":
                product_data["nutrition"] = clean
                print("\n==== Nutritional Facts ====")
                print(clean)

        for key in obj:
            search_sections(obj[key])

    elif isinstance(obj, list):
        for item in obj:
            search_sections(item)


# ---------- Run scraper ----------
search_sections(data)

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "generated"
dataset_file = DATA_DIR / "safeshop_dataset.jsonl"

existing_ids = set()

DATA_DIR.mkdir(parents=True, exist_ok=True)

if dataset_file.exists():

    with dataset_file.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
                existing_ids.add(record["product_id"])
            except Exception:
                pass

# ---------- Save if new ----------
if product_id not in existing_ids:

    with dataset_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(product_data) + "\n")

    print(f"\nSaved to {dataset_file}")

else:
    print("\nProduct already exists in dataset — skipping save")

print("\nSaved Record:")
print(product_data)