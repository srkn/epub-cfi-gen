from epubcfi_utils import *
import csv
from pathlib import PosixPath
import json
import sys
import os
import argparse


class Controller:
    current_path = os.path.dirname(os.path.realpath(sys.argv[0]))

    def __init__(self, epub_file, text_node_format, output_format):
        self.epub_name = PosixPath(epub_file).stem
        self.spine_data = get_epub_spine_content(epub_file)
        self.epubcfi_list = []
        self.text_node_format = text_node_format
        self.output_file_path = Controller.current_path + "/" + self.epub_name + "." + output_format
        self.generate_and_save_epubcfi()

        if output_format == "json":
            self.write_epub_cfi_to_json()
        if output_format == "csv":
            self.write_epub_cfi_to_csv()

    def write_epub_cfi_to_json(self):
        with open(self.output_file_path, "+w") as outfile:
            json.dump(self.epubcfi_list, outfile, indent=4)

    def write_epub_cfi_to_csv(self):
        with open(self.output_file_path, "+w", newline="") as csvfile:
            fieldnames = ["word", "idref",  "cfi"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for data in self.epubcfi_list:
                word = data.get("word")
                idref = data.get("idref")
                cfi = data.get("cfi")
                writer.writerow({"word": word, "idref": idref, "cfi": cfi})

    def generate_and_save_epubcfi(self):
        for spine in self.spine_data:
            spine_body = get_body_content_and_cfi_step(spine["content"])
            epucfi_list = generate_epucfi(body_cfi_step=spine_body["cfi_step"], spine_idref=spine["idref"],
                                          data=enumarete_all_child(
                                              spine_body["content"], text_node_type=self.text_node_format))
            for epucfi in epucfi_list:
                self.epubcfi_list.append(epucfi)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate EPUB Canonical Fragment Identifiers")
    parser.add_argument("-i", "--input", help="Epub file path")
    parser.add_argument(
        "-n", "--node_type",
        help="Word node format, split or flat",
        choices=["split", "flat"])
    parser.add_argument("-o", "--output_format", choices=["json", "csv"], help="Output file format, json or csv")
    args = parser.parse_args()

    controller = Controller(
        epub_file=args.input,
        text_node_format=args.node_type,
        output_format=args.output_format)
