import os
import re
import tkinter as tk
from tkinter import filedialog, ttk


class MovieFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.filesize = self.get_file_size(filepath)
        self.title = None
        # self.imdb_id = None
        self.edition = None
        self.quality = None
        self.video_dynamic_range = None
        self.audio_codec = None
        self.video_codec = None
        # self.media_info = []
        self.release_group = None
        self.parse_filename()

    def parse_filename(self):
        # bracket_pattern = r"\[([^\]]+?)\]"
        # media_info_match = re.findall(bracket_pattern, self.filename)
        # stripped_items = [
        #     item.replace("{", "").replace("}", "") for item in media_info_match
        # ]
        # self.media_info = "-".join(stripped_items)

        quality_match = re.search(r"\[(WEBDL|Bluray|Remux)[^\]]*\]", self.filename)
        self.quality = (
            quality_match.group(0)[1:-1] if quality_match else "Unknown Quality"
        )

        video_dynamic_range_match = re.search(r"\[(DV|HDR)[^\]]*\]", self.filename)
        self.video_dynamic_range = (
            video_dynamic_range_match.group(0)[1:-1]
            if video_dynamic_range_match
            else "SDR"
        )

        audio_codec_match = re.search(
            r"\[[^\]]*(2\.0|5\.1|7\.1)[^\]]*\]", self.filename
        )
        self.audio_codec = (
            audio_codec_match.group(0)[1:-1] if audio_codec_match else "Unknown Codec"
        )

        video_codec_match = re.search(
            r"\[(h265|h264|x265|x264|HEVC|VC1|AVC|MPEG2)[^\]]*\]", self.filename
        )
        self.video_codec = (
            video_codec_match.group(0)[1:-1] if video_codec_match else "Unknown Codec"
        )

        title_match = re.search(r"(.*?\))", self.filename)
        self.title = title_match.group(1) if title_match else "Unknown Title"

        imdb_match = re.search(r"(imdb-[^\}]+)", self.filename)
        self.imdb_id = imdb_match.group(1) if imdb_match else "No IMDB ID"

        edition_match = re.search(r"edition-([^\}]+)", self.filename)
        self.edition = edition_match.group(1) if edition_match else " "

        release_group_match = re.search(r"-(\w+)(?=\.)", self.filename)
        self.release_group = (
            release_group_match.group(1) if release_group_match else "No Group"
        )
        
    def get_file_size(self, filepath):
        size_bytes = os.path.getsize(filepath)
        size_gigabytes = size_bytes / (1024 * 1024 * 1024)
        self.filesize_gb = size_gigabytes
        return f"{size_gigabytes:.2f} GB"



class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie Library")
        self.sort_order = None

        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.root, textvariable=self.search_var)
        self.search_entry.pack(fill=tk.X)
        self.search_entry.bind("<KeyRelease>", self.update_treeview)

        self.entry_count_label = ttk.Label(self.root, text="Total Movies: 0")
        self.entry_count_label.pack(fill=tk.X)

        self.total_size_label = ttk.Label(self.root, text="Total Size: 0")
        self.total_size_label.pack(fill=tk.X)

        self.tree = ttk.Treeview(
            self.frame,
            columns=(
                "Title",
                # "IMDB ID",
                "Edition",
                "Quality",
                "Video Dynamic Range",
                "Audio Codec",
                "Video Codec",
                # "Media Info",
                "Release Group",
                "File Size",
            ),
            show="headings",
        )
        self.tree.heading("Title", text="Title", command=self.sort_by_title)
        # self.tree.heading("IMDB ID", text="IMDB ID")
        self.tree.heading("Edition", text="Edition")
        self.tree.heading("Quality", text="Quality")
        self.tree.heading("Video Dynamic Range", text="Video Dynamic Range")
        self.tree.heading("Audio Codec", text="Audio Codec")
        self.tree.heading("Video Codec", text="Video Codec")
        # self.tree.heading("Media Info", text="Media Info")
        self.tree.heading("Release Group", text="Release Group")
        self.tree.heading("File Size", text="File Size")

        self.scrollbar = ttk.Scrollbar(
            self.frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.config(yscrollcommand=self.scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.load_button = ttk.Button(
            self.root, text="Load Directory", command=self.load_directory
        )
        self.load_button.pack(fill=tk.X)

        self.all_movies = []

    def load_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.load_movies(directory)

    def update_total_size(self, total_size_gb):
        if total_size_gb >= 1000:
            total_size_tb = total_size_gb / 1024
            display_text = f"Total Size: {total_size_tb:.2f} TB"
        else:
            display_text = f"Total Size: {total_size_gb:.2f} GB"
            # Ensure the label is being updated
        # print("Updating label to:", display_text)  # Debug print to check what we're setting the label to
        self.total_size_label.config(text=display_text)

    def sort_by_title(self, toggle_sort=True):
        if self.sort_order is None:
            self.sort_order = "ascending"
        reverse = self.sort_order == "descending"

        l = [(self.tree.set(k, "Title"), k) for k in self.tree.get_children('')]
        l.sort(reverse=reverse, key=lambda x: x[0].lower())

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        order_indicator = "↑" if self.sort_order == "ascending" else "↓"
        self.tree.heading("Title", text=f"Title {order_indicator}", command=self.sort_by_title)

        if toggle_sort:
            self.sort_order = "descending" if self.sort_order == "ascending" else "ascending"

    def load_movies(self, directory):
        self.tree.delete(*self.tree.get_children())
        self.all_movies = []
        total_size_gb = 0

        for root, dirs, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                if os.path.isfile(filepath) and filepath.lower().endswith(
                    (".mkv", ".mp4")
                ):
                    movie = MovieFile(filepath)
                    self.all_movies.append(movie)

                    if movie.title:
                        self.tree.insert(
                            "",
                            "end",
                            values=(
                                movie.title,
                                # movie.imdb_id,
                                movie.edition,
                                movie.quality,
                                movie.video_dynamic_range,
                                movie.audio_codec,
                                movie.video_codec,
                                # movie.media_info,
                                movie.release_group,
                                movie.filesize,
                            ),
                        )
                    total_size_gb += movie.filesize_gb
            self.entry_count_label.config(text=f"Total Movies: {len(self.all_movies)}")
            self.update_total_size(total_size_gb)

    def update_treeview(self, event=None):
        search_text = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        displayed_count = 0
        total_size_gb = 0 
        for movie in self.all_movies:
            if self.matches_search(movie, search_text):
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        movie.title,
                        movie.edition,
                        movie.quality,
                        movie.video_dynamic_range,
                        movie.audio_codec,
                        movie.video_codec,
                        movie.release_group,
                        movie.filesize,
                    ),
                )
                displayed_count += 1
                total_size_gb += movie.filesize_gb
                # print(f"Adding size {movie.filesize_gb} GB for movie {movie.title}")
        self.sort_by_title(toggle_sort=False)
        self.entry_count_label.config(text=f"Total Movies: {displayed_count}")
        self.update_total_size(total_size_gb)
        

    def matches_search(self, movie, text):
        attributes_to_check = [
            "title",
            "edition",
            "quality",
            "video_dynamic_range",
            "audio_codec",
            "video_codec",
            "release_group",
        ]
        for attr in attributes_to_check:
            attribute_value = getattr(movie, attr, None)
            if attribute_value and text in attribute_value.lower():
                return True
        return False


def main():
    root = tk.Tk()

    style = ttk.Style()
    style.theme_use('default')

    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
