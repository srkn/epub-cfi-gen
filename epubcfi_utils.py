from bs4 import BeautifulSoup as beso, Comment
from bs4.element import NavigableString, Tag
from yael import SimpleEPUB


def get_epub_spine_content(epub_path):

    epub = SimpleEPUB(path=epub_path)
    data = []
    for index, epub_spine in enumerate(epub.resolved_spine):
        idref = epub.ebook.container.default_rendition.pac_document.spine.itemrefs[index].v_idref
        content = epub.asset_contents(epub_spine)
        data.append({"idref": idref, "content": content})
    return data


def apply_black_list(list_elem):
    escape = "\n"
    blank = " "
    if escape != list_elem and list_elem != blank:
        return True


def get_text_data(content_list):
    text_data = []
    last_index = 1
    for index, content in enumerate(content_list):
        if isinstance(content, NavigableString) and not isinstance(content, Comment):
            text_cfi_step = str(last_index) + ":0"
            text_data.append({"node": content, "index": text_cfi_step})
            last_index += 2
    return text_data


def get_splitted_text_data(content_list):
    text_data = []
    last_index = 1
    for content in content_list:
        if isinstance(content, NavigableString) and not isinstance(content, Comment):
            c = 0
            for text in content.split():
                length = len(text) + 1
                c += length
                index = c - length
                chr_offset = ":" + str(index)
                text_cfi_step = str(last_index) + chr_offset
                text_data.append({"node": text, "index": text_cfi_step})
            last_index += 2
    return text_data


def get_body_content_and_cfi_step(html):
    soup = beso(html, "html.parser")
    cfi_step = (len([tag for tag in soup.body.previous_siblings if tag.name is not None]) + 1) * 2
    return {"content": soup.body, "cfi_step": cfi_step}


def enumarete_all_child(body, text_node_type, child_list=None):

    if child_list is None:
        child_list = []
    for index, child in enumerate(list(filter(apply_black_list, body.childGenerator()))):
        if isinstance(child, Tag):
            index = (index + 1) * 2
            tag = child.name
            child_id = child.attrs.get("id")
            if text_node_type == "split":
                text = get_splitted_text_data(list(filter(apply_black_list, child.contents)))
            elif text_node_type == "flat":
                text = get_text_data(list(filter(apply_black_list, child.contents)))
            data = {"tag": tag, "id": child_id, "index": index, "text": text, "children": []}
            child_list.append(data)
            if child.childGenerator():
                enumarete_all_child(child, text_node_type=text_node_type, child_list=data["children"])
    return child_list


def generate_epucfi(body_cfi_step, spine_idref, data: list, cfi_list=None, previous_step=None):

    if cfi_list is None:
        cfi_list = []
    prefix_cfi = "/" + str(body_cfi_step) + "/"
    for node in data:
        node_index = str(node["index"]) + "[{}]".format(node["id"]) + "/" if node["id"] else str(node["index"]) + "/"
        parent_index = previous_step + node_index if previous_step else node_index
        for text in node["text"]:
            cfi_step = prefix_cfi + parent_index + text["index"]
            final_epub_cfi = "epubcfi(" + cfi_step + ")"
            new_node = {"word": text["node"].strip(), "idref": spine_idref, "cfi": final_epub_cfi}
            cfi_list.append(new_node)
        if node["children"]:
            generate_epucfi(body_cfi_step, spine_idref, node["children"], cfi_list, previous_step=parent_index)

    return cfi_list
