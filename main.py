import os, glob
import re
import json
import webbrowser
from pathlib import Path
import dearpygui.dearpygui as dpg
# from dearpygui.demo import show_demo
from apnggif import apnggif
import zipfile
import httpx
from utils import logger, _hsv_to_rgb
from download import DownloadManager

logger = logger('Line Sticker Downloader', to_file=False)


# Main Logic
class Config:
    MODE_LIST = {
        "sticker": 0,
        "theme": 1,
        "emoji": 2
    }
    PLATFORM_LIST = {
        "android": 0,
        "iphone": 1,
        "pc": 2
    }
    TYPES_STICKER = {
        0: "stickers@2x.zip",
        1: "stickerpack@2x.zip",
        2: "sticker_custom_plus_base@2x.zip",
        3: "sticker_name_base@2x.zip",
    }
    TYPES_EMOJI = {
        "package.zip?v=1": 0,
        "package_animation.zip": 1
    }
    TYPES_THEME = {
        "/4/WEBSTORE/icon_198x278.png?__=20161019": 0,
        "/4/ANDROID/ja/preview_001_720x1232.png": 1
    }

    # URL TO GET OVERLAY "/sticker/{STICKER_ID@2.png}/iPhone/overlay/plus/default/sticker@2x.png"

    def __init__(self):
        self.mode = 0
        self.platform = 1

    def get_current_mode(self):
        return list(self.MODE_LIST.keys())[list(self.MODE_LIST.values()).index(self.mode)]

    def get_current_platform(self):
        return list(self.PLATFORM_LIST.keys())[list(self.PLATFORM_LIST.values()).index(self.platform)]

    def get_current_sticker_types(self, parsed_type: str):
        match parsed_type:
            case "STATIC":
                return self.TYPES_STICKER.get(0)
            case "NAME_TEXT":
                return self.TYPES_STICKER.get(3)
            case "PER_STICKER_TEXT":
                return self.TYPES_STICKER.get(2)
            case _:
                return self.TYPES_STICKER.get(1)


CONFIG_VAR = Config()

# DearPyGUI Main Program #

dpg.create_context()
dpg.create_viewport(title="Line Sticker Downloader", resizable=False,
                    width=600, height=485, min_width=600, min_height=485, max_width=600, max_height=485)

dpg.set_viewport_small_icon("./icon.ico")
dpg.set_viewport_large_icon("./icon.ico")


def download_sticker(url: str):
    logger.info(f"Using Input URL: {url}")

    regex_match = re.search(r"\d+", url)
    if not regex_match:
        logger.error("No Sticker ID Found")
        return

    parsed_sticker_id = regex_match.group()
    logger.info(f"Number Found : {parsed_sticker_id}")

    logger.info(f"Trying to Download Sticker with ID: {parsed_sticker_id}")

    current_platform = CONFIG_VAR.get_current_platform()

    fallback_urls = [
        f"https://stickershop.line-scdn.net/stickershop/v1/product/{parsed_sticker_id}/{current_platform}/",
        f"http://dl.stickershop.line.naver.jp/products/0/0/1/{parsed_sticker_id}/{current_platform}/",
    ]

    def _get_metadata(_dm: httpx.Client):
        try:
            for uri in fallback_urls:
                logger.info(f"Trying to get metadata from: {uri}")
                req = _dm.get(uri + "productInfo.meta",
                              headers={
                                  "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/103.0 Mobile/15E148 Safari/605.1.15",
                                  "accept": "application/json",
                                  "Content-Type": "application/json",
                                  "charset": "UTF-8", })
                if req.status_code == 200:
                    req.encoding = 'utf-8'
                    return req.json()
        except httpx.HTTPError as err:
            logger.error(f"HTTP Error: {err}")
            return {}

    def _download_sticker(_dm: httpx.Client, _ext: str):
        Path(f"output").mkdir(parents=True, exist_ok=True)
        try:
            for uri in fallback_urls:
                with httpx.stream("GET", uri + _ext) as stream_resp:
                    logger.info(f"STATUS CODE STREAM {stream_resp.status_code}")
                    progress_download = 0
                    total = int(stream_resp.headers["Content-Length"])
                    logger.info(f"Total Size: {total}")
                    with open(f"output/{parsed_sticker_id}_{current_platform}_{_ext}", "wb") as f:
                        for chunk in stream_resp.iter_bytes(1024):
                            progress_download += len(chunk)
                            dpg.configure_item("Progress",
                                               overlay=f"Downloading... {str(progress_download)}/{str(total)}",
                                               default_value=progress_download / total)
                            if chunk:
                                f.write(chunk)
                    return True
        except httpx.StreamError as err:
            logger.error(f"Stream Error: {err}")
            return True

    with DownloadManager() as dm:
        raw_data_json = _get_metadata(dm)
        logger.info(f"Raw Data JSON: {json.dumps(raw_data_json, ensure_ascii=False)}")
        sticker_parsed_name = raw_data_json["title"]["en"]
        sticker_parsed_author = raw_data_json["author"]["en"]
        sticker_parsed_type = raw_data_json["stickerResourceType"]
        dpg.configure_item("log_items",
                           default_value=
                           f"Sticker Name: {sticker_parsed_name}\n"
                           f"Sticker Author: {sticker_parsed_author}\n"
                           f"Sticker Type: {sticker_parsed_type}")

        sticker_uri = CONFIG_VAR.get_current_sticker_types(sticker_parsed_type)
        logger.info(f"Sticker URI: {sticker_uri}")

        if _download_sticker(dm, sticker_uri):
            logger.info("Successfully Downloaded Sticker")
        else:
            logger.error("Error Downloading Sticker")
        dpg.configure_item("Progress", overlay="Waiting...", default_value=0)


def download_theme(url: str):
    pass


def download_emoji(url: str):
    pass


def begin_unzip_callback(source):
    logger.info(f"Unzipping all files in output folder")
    for file in os.listdir("output"):
        if file.endswith(".zip"):
            logger.info(f"found zip file in {os.path.join('output', file)}")
            with zipfile.ZipFile(os.path.join('output', file), 'r') as zip_ref:
                zip_ref.extractall(os.path.join('output', Path(os.path.join('output', file)).stem))
                logger.info(f"Unzipped {file}")


def convert_to_gif_callback(source, app_data):
    logger.info("Button Convert to GIF Pressed")
    logger.info(f"DATA : {app_data}")
    file_path_name = app_data["file_path_name"]
    logger.info(f"File Path Name: {file_path_name}")
    files = glob.glob(file_path_name + '/**/*.png', recursive=True)
    for file in files:
        logger.info(f"Found File: {file}")
        apnggif(file)
    logger.info(f"Files: {files}")


def download_callback(source):
    logger.info("Button Download Pressed")
    logger.info(f"Selected Mode: {CONFIG_VAR.get_current_mode()}")

    url_string = str(dpg.get_value("input_mode") or "None")
    logger.info(f"""Link String : {url_string}""")

    if CONFIG_VAR.mode == 0:
        download_sticker(url_string)


def change_mode_callback(source):
    logger.info(f"Changing Mode to: {str(dpg.get_item_label(source))}")
    dpg.configure_item("input_mode", default_value="")
    match dpg.get_item_label(source):
        case "Sticker Downloader":
            CONFIG_VAR.mode = 0
            dpg.configure_item("sticker_mode", default_value=True)
            dpg.configure_item("theme_mode", default_value=False)
            dpg.configure_item("emoji_mode", default_value=False)
            dpg.configure_item("input_mode", label="Sticker ID/Link", hint="Input Sticker ID/Link")

        case "Theme Downloader":
            CONFIG_VAR.mode = 1
            dpg.configure_item("sticker_mode", default_value=False)
            dpg.configure_item("theme_mode", default_value=True)
            dpg.configure_item("emoji_mode", default_value=False)
            dpg.configure_item("input_mode", label="Theme ID/Link", hint="Input Theme ID/Link")

        case "Emoji Downloader":
            CONFIG_VAR.mode = 2
            dpg.configure_item("sticker_mode", default_value=False)
            dpg.configure_item("theme_mode", default_value=False)
            dpg.configure_item("emoji_mode", default_value=True)
            dpg.configure_item("input_mode", label="Emoji ID/Link", hint="Input Emoji ID/Link")


with dpg.font_registry():
    default_font = dpg.add_font("./fonts/Poppins.ttf", 18)
    dpg.bind_font(default_font)

with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8, category=dpg.mvThemeCat_Core)
    with dpg.theme_component(dpg.mvInputInt):
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
    with dpg.theme_component(dpg.mvProgressBar):
        dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, (95, 192, 244, 255))
    dpg.bind_theme(global_theme)

with dpg.theme(tag="btn_cancel_theme"):
    with dpg.theme_component(dpg.mvButton):
        dpg.add_theme_color(dpg.mvThemeCol_Button, _hsv_to_rgb(0, 0.6, 0.6))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _hsv_to_rgb(0, 0.8, 0.8))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _hsv_to_rgb(0, 0.7, 0.7))

with dpg.theme(tag="btn_ok_theme"):
    with dpg.theme_component(dpg.mvButton):
        dpg.add_theme_color(dpg.mvThemeCol_Button, _hsv_to_rgb(0.287, 0.6, 0.6))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _hsv_to_rgb(0.287, 0.8, 0.8))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _hsv_to_rgb(0.287, 0.7, 0.7))

with dpg.theme(tag="btn_theme"):
    with dpg.theme_component(dpg.mvButton):
        dpg.add_theme_color(dpg.mvThemeCol_Button, _hsv_to_rgb(0.6, 0.6, 0.6))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _hsv_to_rgb(0.6, 0.8, 0.8))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _hsv_to_rgb(0.6, 0.7, 0.7))

with dpg.window(tag="Help Window", modal=True, show=False, no_title_bar=True, pos=(30, 30), width=450, height=300):
    dpg.add_text("Help Window")
    dpg.add_separator()
    dpg.add_spacer(height=10)
    with dpg.collapsing_header(label="Sticker Downloader"):
        dpg.add_text("LINE has several sticker types\n"
                     "\tNo icons\t: Regular sticker\n"
                     "\tSpeaker icon\t: Regular sticker with sound\n"
                     "\tArrow icon\t: Animated sticker\n"
                     "\tArrow and speaker icon\t: Animated sticker with sound\n"
                     "\tLightning icon\t: Pop up sticker\n"
                     "\tLightning and speaker icon\t: Pop up sticker with sound\n")
    dpg.add_spacer(height=10)
    with dpg.collapsing_header(label="Theme Downloader"):
        dpg.add_text("Coming Soon...")
    dpg.add_spacer(height=10)
    with dpg.collapsing_header(label="Emoji Downloader"):
        dpg.add_text("Coming Soon...")
    dpg.add_spacer(height=10)
    dpg.add_button(label="Close", width=75,
                   callback=lambda: dpg.configure_item("Help Window", show=False))
    dpg.bind_item_theme(dpg.last_item(), "btn_cancel_theme")

with dpg.window(tag="About Window", modal=True, show=False, no_title_bar=True, pos=(30, 30), width=450, height=300,
                no_resize=True):
    dpg.add_text("This program brought to you by Jeremy")
    dpg.add_text("If you have any issues please use github issues")
    dpg.add_text("Any feedback is appreciated")
    dpg.add_button(label="Click Here to go to Github Issues",
                   callback=lambda: webbrowser.open("https://github.com/j3rr7/Line-Sticker-Downloader/issues"))
    dpg.bind_item_theme(dpg.last_item(), "btn_theme")
    dpg.add_spacer(height=50)
    dpg.add_button(label="OK", width=75,
                   callback=lambda: dpg.configure_item("About Window", show=False))
    dpg.bind_item_theme(dpg.last_item(), "btn_ok_theme")

with dpg.window(tag="Unzip Window", modal=True, show=False, no_title_bar=True, pos=(150, 90), width=300, height=200,
                no_resize=True):
    dpg.add_text("WARNING!!!")
    dpg.add_text("This will unzip all files inside output folder \nand create new folders")
    dpg.add_text("Make sure all zip file is inside output folder")

    dpg.add_button(label="Click Here to begin unzip", tag="btn_unzip", callback=begin_unzip_callback)
    dpg.bind_item_theme(dpg.last_item(), "btn_theme")
    dpg.add_button(label="Cancel", width=75,
                   callback=lambda: dpg.configure_item("Unzip Window", show=False))
    dpg.bind_item_theme(dpg.last_item(), "btn_cancel_theme")

with dpg.file_dialog(directory_selector=True, show=False, file_count=0,
                     width=530, height=350,
                     callback=convert_to_gif_callback, tag="folder_gif_dialog"):
    dpg.add_text("WARNING!!!\nAll .png in this folder\nwill be converted to GIF\nClick Ok to continue")

with dpg.window(tag="Main Window"):
    with dpg.menu_bar():
        with dpg.menu(label="Options"):
            dpg.add_menu_item(label="Sticker Downloader", check=True,
                              tag="sticker_mode", default_value=True,
                              callback=change_mode_callback)
            dpg.add_menu_item(label="Theme Downloader", check=True,
                              tag="theme_mode",
                              callback=change_mode_callback)
            dpg.add_menu_item(label="Emoji Downloader", check=True,
                              tag="emoji_mode",
                              callback=change_mode_callback)
        with dpg.menu(label="Convert"):
            dpg.add_menu_item(label="Unzip Stickers", callback=lambda: dpg.configure_item("Unzip Window", show=True))
            dpg.add_menu_item(label="APNG to gif", callback=lambda: dpg.show_item("folder_gif_dialog"))
        with dpg.menu(label="Misc"):
            dpg.add_menu_item(label="Help", tag="help_btn",
                              callback=lambda: dpg.configure_item("Help Window", show=True))
            dpg.add_menu_item(label="About", tag="about_btn",
                              callback=lambda: dpg.configure_item("About Window", show=True))

    dpg.add_text("Line Sticker Downloader")

    dpg.add_input_text(label="Sticker ID/Link", hint="Input Sticker ID/Link", tag="input_mode")
    dpg.add_button(label="Download", callback=download_callback)
    dpg.bind_item_theme(dpg.last_item(), "btn_theme")
    dpg.add_spacer(height=10)
    dpg.add_text("Progress")
    dpg.add_progress_bar(tag="Progress", default_value=0.0, overlay="Waiting...")
    dpg.add_spacer(height=10)
    dpg.add_text("LOG ITEMS", tag="log_items")

# show_demo()

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window(window="Main Window", value=True)
dpg.start_dearpygui()
dpg.destroy_context()
