import argparse
import yaml
import csv
import re

def load_config(path: str):
    parser = argparse.ArgumentParser()
    parser.add_argument('--conf', default=path)
    args = parser.parse_args()
    config_path = args.conf
    param = yaml.safe_load(open(config_path, 'r', encoding="utf8"))
    return param


def combine_csv(file1_path, file2_path, output_path='combined.csv'):
    with open(file1_path, 'r', encoding="utf8") as f1, \
            open(file2_path, 'r', encoding="utf8") as f2:

        file1 = csv.DictReader(f1)
        file2 = csv.DictReader(f2)

        # Use the headers from the first file
        headers = file1.fieldnames

        with open(output_path, 'w', newline='', encoding="utf8") as out_file:
            writer = csv.DictWriter(out_file, fieldnames=headers)
            writer.writeheader()

            for row in file1:
                writer.writerow(row)

            for row in file2:
                writer.writerow(row)

    print(f"Files combined successfully into {output_path}")

def preprocess_csv(path):
    def clean_text(text):
        # Lowercase and remove punctuation using regex
        return re.sub(r'[^\w\s]', '', text.lower()).strip()

    with open(path, 'r', encoding='utf8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames

        cleaned_rows = []
        for row in reader:
            if 'transcript' in row and row['transcript'].strip():
                row['transcript'] = clean_text(row['transcript'])
            cleaned_rows.append(row)

    with open(path, 'w', newline='', encoding='utf8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    print(f"Preprocessed 'col1' and saved: {path}")
if __name__ == "__main__":
    preprocess_csv("../scripts.csv")