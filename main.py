import os
import time
import requests
import json
import re
import unicodedata
import zipfile
import threading
from apnggif import apnggif
import dearpygui.dearpygui as dpg

class StickerDownloader:
    current_sticker = None
    output_dir = "output"
    mode = "sticker"  # default value
    store_type = "iphone"  # default value
    store_id = 0

    meta_url = "FIND IT YOURSELF ITS PUBLICLY AVALIABLE"

    sticker_url_list = [
        "FIND IT YOURSELF ITS PUBLICLY AVALIABLE",
        "FIND IT YOURSELF ITS PUBLICLY AVALIABLE",
        "FIND IT YOURSELF ITS PUBLICLY AVALIABLE",
        "FIND IT YOURSELF ITS PUBLICLY AVALIABLE"
        "FIND IT YOURSELF ITS PUBLICLY AVALIABLE"
        "FIND IT YOURSELF ITS PUBLICLY AVALIABLE"
    ]

    emoji_url_list = [
        "FIND IT YOURSELF ITS PUBLICLY AVALIABLE",
        "FIND IT YOURSELF ITS PUBLICLY AVALIABLE",
    ]

    theme_url_list = [
        "FIND IT YOURSELF ITS PUBLICLY AVALIABLE",
        "FIND IT YOURSELF ITS PUBLICLY AVALIABLE"
    ]

    def __init__(self):
        self.__render_pre_init__()
        self.__render_main_window__()
        self.__render_post_init__()

    def __render_pre_init__(self):
        dpg.create_context()
        dpg.create_viewport(
            title="Sticker Downloader",
            width=300,
            max_width=300,
            height=320,
            max_height=320,
            resizable=False,
        )
        dpg.setup_dearpygui()

    def __render_post_init__(self):
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    def __render_main_window__(self):
        dpg.add_file_dialog(directory_selector=True, show=False, callback=self.__internal_file_dialog__,
                            tag="file_dialog")

        with dpg.window(label="Sticker Downloader", tag="main_window"):
            with dpg.menu_bar():
                with dpg.menu(label="Mode"):
                    dpg.add_combo(("Sticker", "Emoji", "Theme"),
                                  tag="combo_mode",
                                  default_value="Sticker",
                                  user_data="mode",
                                  callback=self.__internal_menu_callback__)

                    dpg.add_combo(("android", "iphone", "PC"),
                                  tag="combo_type",
                                  default_value="iphone",
                                  user_data="type",
                                  callback=self.__internal_menu_callback__)

                with dpg.menu(label="Convert"):
                    dpg.add_menu_item(label="Convert to gif", callback=self.__internal_convert_button__)

            dpg.add_text("Store URL:")
            dpg.add_input_text(
                label="##Store URL",
                hint="Insert Store URL Here",
                width=268,
                tag="sticker_url"
            )
            dpg.add_button(label="Download",
                           tag="download_button",
                           callback=self.download_button_callback)

            dpg.add_text(show=False, tag="store_status")

            dpg.add_spacer(height=70)
            with dpg.group():
                dpg.add_text("Download Progress...")
                dpg.add_progress_bar(
                    label="Progress",
                    tag="progress_bar",
                    width=268,
                )
                # assuming we're on windows
                dpg.add_button(label="Open Folder",
                               tag="open_folder_button",
                               callback=lambda: os.system("explorer ."))

    def __internal_file_dialog__(self, sender, item_data):
        pass

    def __internal_menu_callback__(self, sender, item_data, user_data):
        if user_data == "mode":
            self.mode = item_data
        if user_data == "type":
            self.store_type = item_data
        # print(f"sender: {sender}, \t app_data: {item_data}, \t user_data: {user_data}")
        print(f"mode: {self.mode}, \t type: {self.store_type}")

    def __internal_convert_button__(self):
        self.convert_to_gif(recursive=True)

    def download_button_callback(self, item):
        value = dpg.get_value("sticker_url")
        if value is not None:
            regstr = re.search("\d{2,}", value)
            if regstr is not None:
                self.store_id = regstr.group(0)
                self.download()
            else:
                # regex for emoji
                regstr = re.search("([0-9]+([a-zA-Z]+[0-9]+)+)", value)
                if regstr is not None:
                    self.store_id = regstr.group(0)
                    self.download()

                # Todo : add check for theme download

    # Ripped from https://github.com/django/django/blob/main/django/utils/text.py
    def slugify(self, value, allow_unicode=False):
        """
        Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
        dashes to single dashes. Remove characters that aren't alphanumerics,
        underscores, or hyphens. Convert to lowercase. Also strip leading and
        trailing whitespace, dashes, and underscores.
        """
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize('NFKC', value)
        else:
            value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower())
        return re.sub(r'[-\s]+', '-', value).strip('-_')

    def download(self):
        # grab the meta data from request url
        meta_response = requests.get(self.meta_url.replace("STORE_ID", self.store_id))
        if meta_response.status_code == 200:
            meta_data = json.loads(meta_response.text)
            # bytes(meta_data["title"]["en"], 'utf-8').decode('utf-8', 'ignore')
            self.output_dir = self.slugify(meta_data["title"]["en"])
            if not os.path.exists(self.output_dir):
                try:
                    os.makedirs(self.output_dir)
                    with open(f"{self.output_dir}/meta.json", "w") as f:
                        f.write(json.dumps(meta_data, indent=4))
                except Exception as e:
                    return
            else:
                pass
        else:
            dpg.set_value("store_status", "Invalid Store ID, Check Log for Details")
            dpg.show_item("store_status")
            return

        dpg.set_value("store_status", f"Found Store Status:\n {meta_data['title']['en']}")
        dpg.show_item("store_status")
        # download the actual file into output directory
        match self.mode:
            case "sticker":
                dthread = threading.Thread(target=self.download_sticker)
                dthread.start()
                # self.download_sticker()
            case "emoji":
                self.download_emoji()
            case "theme":
                self.download_theme()
            case _:
                return

    def download_sticker(self, url=None):
        if url is None:
            url = self.sticker_url_list[0].replace("STORE_ID", self.store_id).replace("STORE_TYPE", self.store_type)

        sticker_data = requests.get(url, stream=True)
        downloaded = 0
        if sticker_data.status_code == 200:
            sticker_size = int(sticker_data.headers.get('content-length'))
            self.filename = f"{self.store_id}.zip"
            with open(self.filename, "wb") as f:
                for chunk in sticker_data.iter_content(chunk_size=2 * 1024):
                    if chunk:
                        downloaded += len(chunk)
                        self.update_progressbar(downloaded / sticker_size)
                        f.write(chunk)
                    time.sleep(0.01)

            if os.path.isfile(self.filename):
                try:
                    with zipfile.ZipFile(self.filename, 'r') as zip_ref:
                        zip_ref.extractall(self.output_dir)
                    os.remove(self.filename)
                except Exception as e:
                    print(e)

    def convert_to_gif(self, directory=".", recursive=False):
        # get all file inside directory and convert to gif
        for file in os.listdir(directory):
            if os.path.isdir(file):
                folder_path = os.path.join(directory, file)
                for file2 in os.listdir(folder_path):
                    if file2 in ["animation", "sound", "popup", "animation@2x"]:
                        folder_path2 = os.path.join(folder_path, file2)
                        for file3 in os.listdir(folder_path2):
                            if file3.endswith(".png" or ".m4a"):
                                file_path = os.path.join(folder_path2, file3)
                                apnggif(file_path)

    def update_progressbar(self, value=1.0):
        dpg.set_value('progress_bar', value)

    def download_emoji(self, url=None):
        pass

    def download_theme(self, url=None):
        pass


if __name__ == '__main__':
    # log.basicConfig(filename='logger.log', level=log.DEBUG, format='%(asctime)s %(message)s')
    sticker = StickerDownloader()
