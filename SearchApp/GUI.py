import csv
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from SearchApp.ConcurrentScraper import *


class App(tk.Frame):
    def __init__(self, parent):
        self.DARKGREEN = "#252D29"
        self.LIGHTGREEN = "#B6CDC4"

        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.time_lb = .21
        self.time_ub = .38
        self.links = []
        self.classes = {}
        self.first_url = ""

        # Info label at top
        self.top_info = tk.Label(self.parent,
                                 fg=self.DARKGREEN,
                                 text="Drop csv files from Google Patents here:")
        self.top_info.pack(pady=3)

        # Drag and drop listbox
        self.list_dnd = tk.Listbox(self.parent,
                                   selectmode=tk.SINGLE,
                                   bg=self.LIGHTGREEN,
                                   fg=self.DARKGREEN,
                                   selectbackground="white")
        self.list_dnd.pack(fill=tk.BOTH,
                           pady=3,
                           padx=10)
        self.list_dnd.drop_target_register(DND_FILES)
        self.list_dnd.dnd_bind("<<Drop>>", self.drop_inside_list_box)
        # TODO: this seems to bind for all lists?
        self.list_dnd.bind('<<ListboxSelect>>', self.on_link_select)

        # Label showing info on selected csv
        self.link_info = tk.Label(self.parent)
        self.link_info.pack(fill=tk.X,
                            pady=3)

        # Frame to hold parse settings and labels
        # Contains: entry label, entry box, check time button, check time label, parse button
        self.parse_frame = tk.Frame(self.parent)
        self.parse_frame.pack(pady=3)

        # Entry area
        self.entry_frame = tk.Frame(self.parse_frame)
        self.entry_frame.pack(pady=3)
        self.entry_label = tk.Label(self.entry_frame,
                                    text="Number of results to parse:",
                                    fg=self.DARKGREEN)
        self.entry_label.pack(side=tk.LEFT)
        self.entry_box = tk.Entry(self.entry_frame,
                                  fg=self.DARKGREEN)
        self.entry_box.pack(side=tk.RIGHT)

        # Button area
        self.button_frame = tk.Frame(self.parse_frame)
        self.button_frame.pack(pady=3)
        self.time_btn = tk.Button(self.button_frame,
                                  text="Check time",
                                  command=self.check_time,
                                  fg=self.DARKGREEN)
        self.time_btn.pack(side=tk.LEFT)
        self.parse_btn = tk.Button(self.button_frame,
                                   text="Parse",
                                   command=self.start_parse,
                                   fg=self.DARKGREEN)
        self.parse_btn.pack(side=tk.RIGHT,
                            pady=3)

        # Listbox to hold the results of the parse
        self.list_show_label = tk.Label(self.parent,
                                        text="Classes are shown in the form 'Name: Description: Frequency'",
                                        fg=self.DARKGREEN)
        self.list_show_label.pack()
        self.list_show = tk.Listbox(self.parent,
                                    selectmode=tk.SINGLE,
                                    background=self.LIGHTGREEN,
                                    fg=self.DARKGREEN,
                                    selectbackground="WHITE")
        self.list_show.pack(fill=tk.BOTH,
                            expand=True,
                            pady=3,
                            padx=10)

        # Button to do google search
        self.search_btn = tk.Button(self.parent,
                                    text="Refine Search",
                                    command=self.refine_search,
                                    fg=self.DARKGREEN)
        self.search_btn.pack(pady=3)

    def drop_inside_list_box(self, event):
        if event.data.endswith('.csv') and event.data not in self.list_dnd.get(0, "end"):
            self.list_dnd.insert("end", event.data)

    def on_link_select(self, event):
        self.get_links(self.list_dnd.get(self.list_dnd.curselection()[0]))
        self.link_info.config(text=f"File contains {len(self.links)} links",
                              fg=self.DARKGREEN)

    def get_links(self, name):
        self.links = []
        name_col = 0
        link_col = 0
        with open(name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    self.first_url = row[1]
                    line_count += 1
                elif line_count == 1:
                    for k, v in enumerate(row):
                        if v == "id":
                            name_col = k
                        elif v == "result link":
                            link_col = k
                    line_count += 1
                else:
                    if 'US-D' not in row[name_col]:
                        self.links.append(row[link_col])
                    line_count += 1

    def check_time(self):
        try:
            number = int(self.entry_box.get())
        except:
            messagebox.showerror("Error", "Please enter a number of links to parse.")
        else:
            if self.links:
                number = min(number, len(self.links))
                min_sec = number * self.time_lb
                max_sec = number * self.time_ub
                messagebox.showinfo("Info",f'Parsing should take between {min_sec} and {max_sec} seconds')
            else:
                messagebox.showerror("Error", "Please select a file to parse.")

    def start_parse(self):
        try:
            number = int(self.entry_box.get())
        except:
            messagebox.showerror("Error", "Please enter a number of links to parse.")
        else:
            if self.links:
                number = min(number, len(self.links))
                self.list_show.delete("0", "end")
                threading.Thread(target=self.parse, args=[number]).start()
            else:
                messagebox.showerror("Error", "Please select a file to parse")

    def parse(self, number):
        s = Scraper(self.links[0:number])
        self.classes = s.scrape()
        for key in self.classes:
            self.list_show.insert("end", f'{key}: {self.classes[key]}')

    def refine_search(self):
        if not len(self.list_show.get(0, "end")):
            messagebox.showerror("Error", "You must parse links to refine your search.")
        else:
            search_root = tk.Tk()
            SelectWindow(search_root, self.classes, self.first_url).pack(side="top", fill="both", expand=True)
            search_root.mainloop()


class SelectWindow(tk.Frame):
    # todo: don't show params as addable if they're included in the searched url
    def __init__(self, parent, classes, first_url):
        super().__init__()
        self.parent = parent

        self.DARKGREEN = "#252D29"
        self.LIGHTGREEN = "#B6CDC4"

        self.first_url = first_url
        self.adders_label = tk.Label(self.parent,
                                     text="Select classes to add to your search",
                                     fg=self.DARKGREEN)
        self.adders_label.pack(pady=3)
        self.adders_classes_label = tk.Label(self.parent,
                                             text="Classes are shown in the form 'Name: Description: Frequency'",
                                             fg=self.DARKGREEN)
        self.adders_classes_label.pack()
        self.adders = tk.Listbox(self.parent,
                                 selectmode=tk.MULTIPLE,
                                 exportselection=False,
                                 bg=self.LIGHTGREEN,
                                 fg=self.DARKGREEN,
                                 selectbackground="white")
        self.adders.pack(fill=tk.BOTH,
                         expand=True,
                         pady=3,
                         padx=10)
        for key in classes:
            self.adders.insert("end", f'{key}: {classes[key]}')

        self.removers_label = tk.Label(self.parent,
                                       text="Select classes to remove from your search",
                                       fg=self.DARKGREEN)
        self.removers_label.pack(pady=3)
        self.removers_classes_label = tk.Label(self.parent,
                                               text="Classes are shown in the form 'Name: Description: Frequency'",
                                               fg=self.DARKGREEN)
        self.removers_classes_label.pack()
        self.removers = tk.Listbox(self.parent,
                                   selectmode=tk.MULTIPLE,
                                   exportselection=False,
                                   fg=self.DARKGREEN,
                                   bg=self.LIGHTGREEN,
                                   selectbackground="white")
        self.removers.pack(fill=tk.BOTH,
                           expand=True,
                           pady=3,
                           padx=10)
        for key in classes:
            self.removers.insert("end", f'{key}: {classes[key]}')

        self.search_btn = tk.Button(self.parent,
                                    text="Refine Search",
                                    command=self.refine_search,
                                    fg=self.DARKGREEN)
        self.search_btn.pack(pady=3)

    def refine_search(self):
        add_ls = self.adders.curselection()
        remove_ls = self.removers.curselection()
        if not len(add_ls) and not len(remove_ls):
            messagebox.showerror("Error", "Please select at least one class to add or remove from your search results.")
        else:
            intersection = [value for value in add_ls if value in remove_ls]
            if len(intersection):
                messagebox.showerror("Error", "You cannot add and remove the same class. Please check your selection.")
            else:
                url = self.get_formatted_url(add_ls, remove_ls)
                webbrowser.open_new_tab(url)

    def get_formatted_url(self, add_ls, remove_ls):
        add_params = map(lambda s: self.adders.get(s).split(':')[0], add_ls)
        remove_params = map(lambda s: f'-{self.removers.get(s).split(":")[0]}', remove_ls)
        new_url = self.first_url.replace("%252f", "%2f")
        for param in add_params:
            new_url += f'&q={param.replace("/", "%2f")}'
        for param in remove_params:
            new_url += f'&q={param.replace("/", "%2f")}'
        return new_url


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    App(root).pack(side="top", fill="both", expand=True)
    root.mainloop()
