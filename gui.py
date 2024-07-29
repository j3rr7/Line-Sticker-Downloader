import os
import asyncio
from dearpygui import dearpygui as dpg
from scraper import scrape_line_store_stickers_test


class LineStickerDownloader:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.sticker_data = []
        self._loading_stickers = False
        self._setup()

    def _setup(self):
        self._setup_dpg()
        self._create_windows()
        # self._create_ui()

    def _setup_dpg(self):
        dpg.create_context()
        dpg.create_viewport(title="Line Sticker Downloader", width=750, height=450)
        dpg.set_viewport_small_icon("icon.ico")
        dpg.set_viewport_large_icon("icon.ico")
        self._set_font()

    def _set_font(self):
        with dpg.font_registry():
            default_font = dpg.add_font("fonts/Poppins.ttf", 18)
            dpg.bind_font(default_font)

    def _create_windows(self):
        self._create_about_window()
        self._create_main_window()

    def _create_about_window(self):
        with dpg.window(
            tag="about_window",
            show=False,
            menubar=False,
            no_collapse=True,
            no_resize=True,
            no_title_bar=True,
            pos=(150, 70),
        ):
            dpg.add_text("Line Sticker Downloader", color=(23, 255, 23))
            dpg.add_text(
                "Version: 1.0.0\nLicense: MIT\nAuthor: @Jere", color=(198, 123, 123)
            )
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Github", callback=self._open_github)
                dpg.add_button(
                    label="Close", callback=lambda: dpg.hide_item("about_window")
                )

    def _create_main_window(self):
        with dpg.window(label="Showcase Window", tag="main_window"):
            self._create_menu_bar()
            self._create_mode_groups()

    def _create_menu_bar(self):
        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Quit", callback=self._quit_callback)
            with dpg.menu(label="View"):
                with dpg.menu(label="Mode"):
                    for mode in ["Sticker Mode", "Theme Mode", "Emoji Mode"]:
                        tag = mode.lower().replace(" ", "_")
                        dpg.add_menu_item(
                            label=mode,
                            tag=tag,
                            default_value=tag == "sticker_mode",
                            check=True,
                            callback=self._toggle_mode_callback,
                        )
            dpg.add_menu_item(
                label="About", callback=lambda: dpg.show_item("about_window")
            )

    def _create_mode_groups(self):
        self._create_sticker_mode_group()
        self._create_theme_mode_group()
        self._create_emoji_mode_group()

    def _create_sticker_mode_group(self):
        with dpg.group(tag="sticker_mode_group", show=True):
            with dpg.tab_bar(label="Sticker Mode"):
                self._create_store_tab()
                self._create_manual_tab()

    def _create_store_tab(self):
        with dpg.tab(label="Store", tag="store_tab"):
            with dpg.group(horizontal=True):
                dpg.add_button(label="<<", callback=self._previous_page_callback)
                dpg.add_button(label=">>", callback=self._next_page_callback)
                dpg.add_spacer(width=15)
                dpg.add_button(
                    label="Reload Stickers", callback=self._reload_stickers_callback
                )
            self._create_sticker_table()

    def _create_sticker_table(self):
        with dpg.table(
            header_row=True, resizable=True, tag="sticker_table", parent="store_tab"
        ):
            dpg.add_table_column(label="Sticker Name & Link", width_stretch=True)
            dpg.add_table_column(label="Image", width_stretch=True)
            dpg.add_table_column(label="Action")

    def _create_manual_tab(self):
        with dpg.tab(label="Manual"):
            with dpg.group(horizontal=True):
                with dpg.child_window(width=400):
                    dpg.add_text("Input Sticker ID/Link")
                with dpg.child_window():
                    dpg.add_input_text(
                        label="Sticker ID/Link", hint="Input Sticker ID/Link"
                    )
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Grab Info")
                        dpg.add_button(label="Download")
                    dpg.add_spacer(height=10)
                    with dpg.collapsing_header(label="Bulk Download"):
                        dpg.add_input_text(
                            label="Bulk ID/Link",
                            tag="bulk_input",
                            hint="Bulk ID/Link",
                            multiline=True,
                        )
                        dpg.add_button(label="Download")

    def _create_theme_mode_group(self):
        with dpg.group(tag="theme_mode_group", show=False):
            dpg.add_text("Theme Mode")

    def _create_emoji_mode_group(self):
        with dpg.group(tag="emoji_mode_group", show=False):
            dpg.add_text("Emoji Mode")

    def _toggle_mode_callback(self, sender, app_data, user_data):
        modes = {
            "sticker_mode": "sticker_mode_group",
            "theme_mode": "theme_mode_group",
            "emoji_mode": "emoji_mode_group",
        }
        for mode, group in modes.items():
            dpg.configure_item(group, show=(sender == mode))
            dpg.set_value(mode, sender == mode)

    def _open_github(self):
        os.system("start https://github.com/j3rr7/Line-Sticker-Downloader/")

    async def _collect_stickers(self):
        return await scrape_line_store_stickers_test()

    def _callback_stickers_data_collected(self, task):
        self._loading_stickers = False
        stickers = task.result()
        print("Stickers collected", stickers)
        self._update_sticker_table(stickers)

    def _add_and_load_image(self, image_path, parent=None):
        width, height, channels, data = dpg.load_image(image_path)

        with dpg.texture_registry() as reg_id:
            texture_id = dpg.add_static_texture(width, height, data, parent=reg_id)

        if parent is None:
            return dpg.add_image(texture_id)
        else:
            return dpg.add_image(texture_id, parent=parent)

    def _update_sticker_table(self, stickers):
        if dpg.does_item_exist("sticker_table"):
            dpg.delete_item("sticker_table")

        self._create_sticker_table()
        # Add stickers to the table here
        for index, sticker in enumerate(stickers):
            with dpg.table_row(parent="sticker_table", tag=f"sticker_row_{index}"):
                with dpg.group():
                    dpg.add_text(f"{sticker['name']}\n{sticker['link']}")
                    dpg.add_button(label="copy link", callback=lambda: print("copy link"))
                    dpg.add_button(label="open link", callback=lambda: print("open link"))
                    
                self._add_and_load_image(
                    image_path=sticker["cached_image"], parent=f"sticker_row_{index}"
                )
                dpg.add_button(label="Download", callback=lambda: print("Download"))

    def _reload_stickers_callback(self):
        if self._loading_stickers:
            return
        self._loading_stickers = True

        if dpg.does_item_exist("sticker_table"):
            dpg.delete_item("sticker_table")

        self._create_sticker_table()

        with dpg.table_row(parent="sticker_table", tag="loading_sticker_indicator"):
            dpg.add_loading_indicator(parent="loading_sticker_indicator")
            dpg.add_loading_indicator(parent="loading_sticker_indicator")
            dpg.add_loading_indicator(parent="loading_sticker_indicator")

        task = self.loop.create_task(self._collect_stickers())
        task.add_done_callback(self._callback_stickers_data_collected)

    def _previous_page_callback(self, sender, app_data, user_data):
        pass

    def _next_page_callback(self, sender, app_data, user_data):
        pass

    def _quit_callback(self):
        self.loop.stop()
        dpg.stop_dearpygui()

    async def _run_dpg(self):
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()
            await asyncio.sleep(0.01)

    def run(self):
        dpg.set_primary_window("main_window", True)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        self.loop.run_until_complete(self._run_dpg())
        dpg.destroy_context()


if __name__ == "__main__":
    app = LineStickerDownloader()
    app.run()
