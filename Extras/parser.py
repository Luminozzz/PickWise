import csv
from extractors.parent_extractor import extractor

def extract_feature(feature: str, value):
    feature = feature.lower()

    if feature == "form factor":
        return extractor.ergonomy(value)

def load_csv(file_path: str) -> dict[str,dict[str,str]]:
    data = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file) # {product_name: str, feature: str, value: str}
        for row in reader:
            product_name = row['product_name']
            feature = row['feature']
            value = row['value']
            if product_name not in data:
                brand_name = product_name.split(None, 1)[0]
                data[product_name] = {
                    'brand_name': brand_name,
                }
            data[product_name][feature] = value
    return data


         