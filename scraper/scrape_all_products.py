import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path

headers = {
    "User-Agent": "Mozilla/5.0"
}

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "generated"
dataset_file = DATA_DIR / "safeshop_dataset.jsonl"
product_ids_file = DATA_DIR / "product_ids.txt"


def clean_text(text):
    lines = text.splitlines()
    lines = [l.strip() for l in lines if l.strip()]
    return "\n".join(lines)


def extract_product(product_id, category):

    url = f"https://www.bigbasket.com/pd/{product_id}/"

    try:
        response = requests.get(url, headers=headers)
    except:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script:
        return None

    data = json.loads(script.string)

    product_data = {
        "product_id": product_id,
        "name": "",
        "brand": "",
        "category": category,
        "image": "",
        "ingredients": "",
        "nutrition": ""
    }

    def search(obj):

        if isinstance(obj, dict):

            # product name
            if "desc" in obj and product_data["name"] == "":
                product_data["name"] = obj["desc"]

            # brand
            if "brand" in obj and product_data["brand"] == "":
                brand = obj["brand"]

                if isinstance(brand, dict) and "name" in brand:
                    product_data["brand"] = brand["name"]
                else:
                    product_data["brand"] = brand

            # image
            if "images" in obj and product_data["image"] == "":
                images = obj["images"]

                if isinstance(images, list) and len(images) > 0:

                    img = images[0]

                    if isinstance(img, dict) and "s" in img:
                        product_data["image"] = img["s"]
                    else:
                        product_data["image"] = img

            # ingredients / nutrition
            if "title" in obj and "content" in obj:

                title = obj["title"]
                content = obj["content"]

                clean = BeautifulSoup(content, "html.parser").get_text()
                clean = clean_text(clean)

                if "Ingredient" in title and product_data["ingredients"] == "":
                    product_data["ingredients"] = clean

                if "Nutrition" in title and product_data["nutrition"] == "":
                    product_data["nutrition"] = clean

            for key in obj:
                search(obj[key])

        elif isinstance(obj, list):
            for item in obj:
                search(item)

    search(data)

    return product_data


def load_existing_ids():
    existing = set()

    if dataset_file.exists():
        with dataset_file.open("r", encoding="utf-8") as f:

            for line in f:
                try:
                    record = json.loads(line)
                    existing.add(record["product_id"])
                except Exception:
                    pass

    return existing


existing_ids = load_existing_ids()

products = []

DATA_DIR.mkdir(parents=True, exist_ok=True)

with product_ids_file.open() as f:
    for line in f:
        pid, category = line.strip().split(",")
        products.append((pid, category))


for pid, category in products:

    if pid in existing_ids:
        print(f"Skipping {pid} (already scraped)")
        continue

    print(f"\nScraping product {pid} ({category})")

    product = extract_product(pid, category)

    if product and (product["ingredients"] or product["nutrition"]):
        with dataset_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(product) + "\n")

        print("Saved:", pid)

    else:
        print("Skipping", pid, "(no ingredients or nutrition)")

    time.sleep(2)