# gui.py

from typing import List

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from feedhandler import FeedHandler, FeedConfig, Article


class FeedManagerGUI:
    """
    A graphical user interface for managing RSS feeds using Tkinter.

    Attributes:
        root (tk.Tk): The main window of the application.
        feed_handler (FeedHandler): An instance of FeedHandler to manage feeds.
        frame (tk.Frame): The main frame containing the listbox and scrollbar.
        listbox (tk.Listbox): A listbox to display the list of feeds.
        scrollbar (tk.Scrollbar): A scrollbar for the listbox.
        articles_frame (tk.Frame): A frame to display articles.
        articles_tree (ttk.Treeview): A treeview to display article titles and links.
    """

    def __init__(self, root: tk.Tk, feed_handler: FeedHandler):
        """
        Initialize the FeedManagerGUI.

        Args:
            root (tk.Tk): The main window of the application.
            feed_handler (FeedHandler): An instance of FeedHandler to manage feeds.
        """
        self.root = root
        self.root.title("RSS Gazette")
        self.feed_handler = feed_handler

        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=10)

        self.listbox = tk.Listbox(self.frame, width=80, height=15)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.display_articles)

        scrollbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL)
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox.config(yscrollcommand=scrollbar.set)

        self.update_feed_list()

        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Add Feed", command=self.add_feed).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Remove Feed", command=self.remove_feed).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Update Feed", command=self.update_feed).pack(side=tk.LEFT, padx=5)

        self.articles_frame = tk.Frame(root)
        self.articles_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.articles_tree = ttk.Treeview(self.articles_frame, columns=("Title", "Link"), show="headings")
        self.articles_tree.heading("Title", text="Title")
        self.articles_tree.heading("Link", text="Link")
        self.articles_tree.column("Title", width=400)
        self.articles_tree.column("Link", width=400)
        self.articles_tree.pack(fill=tk.BOTH, expand=True)

        scrollbar_articles = tk.Scrollbar(self.articles_frame, orient=tk.VERTICAL, command=self.articles_tree.yview)
        scrollbar_articles.pack(side=tk.RIGHT, fill=tk.Y)
        self.articles_tree.configure(yscrollcommand=scrollbar_articles.set)

    def update_feed_list(self) -> None:
        """
        Update the listbox with the current list of feeds.
        """
        self.listbox.delete(0, tk.END)
        for feed in self.feed_handler.feeds_data:
            self.listbox.insert(tk.END, f"{feed.name} ({feed.url})")

    def add_feed(self) -> None:
        """
        Add a new feed by prompting the user for input.
        """
        url = simpledialog.askstring("Input", "Enter the feed URL:")
        if url:
            num_articles = simpledialog.askinteger(
                "Input", "Enter the number of articles to fetch (default is 5):", initialvalue=5)
            category = simpledialog.askstring("Input", "Enter the category (optional):")
            name = simpledialog.askstring("Input", "Enter the name (optional):")
            if num_articles is not None:
                feed_config = FeedConfig(url=url, num_articles=num_articles, category=category, name=name)
                self.feed_handler.add_feed(feed_config)
                self.update_feed_list()
            else:
                messagebox.showerror("Error", "Number of articles must be an integer.")

    def remove_feed(self) -> None:
        """
        Remove a selected feed from the list.
        """
        selected_index = self.listbox.curselection()
        if selected_index:
            feed_url = self.feed_handler.feeds_data[selected_index[0]].url
            self.feed_handler.remove_feed(feed_url)
            self.update_feed_list()
        else:
            messagebox.showerror("Error", "Please select a feed to remove.")

    def update_feed(self) -> None:
        """
        Update a selected feed by prompting the user for new input.
        """
        selected_index = self.listbox.curselection()
        if selected_index:
            feed = self.feed_handler.feeds_data[selected_index[0]]
            url = simpledialog.askstring("Input", "Enter the new feed URL:", initialvalue=feed.url)
            if url:
                num_articles = simpledialog.askinteger(
                    "Input", "Enter the new number of articles to fetch:", initialvalue=feed.num_articles)
                category = simpledialog.askstring("Input", "Enter the new category (optional):", initialvalue=feed.category)
                name = simpledialog.askstring("Input", "Enter the new name (optional):", initialvalue=feed.name)
                if num_articles is not None:
                    feed_config = FeedConfig(url=url, num_articles=num_articles, category=category, name=name)
                    self.feed_handler.update_feed(feed.url, feed_config)
                    self.update_feed_list()
                else:
                    messagebox.showerror("Error", "Number of articles must be an integer.")
        else:
            messagebox.showerror("Error", "Please select a feed to update.")

    def display_articles(self, event) -> None:
        """
        Display articles for the selected feed.

        Args:
            event: The event triggered by selecting a feed in the listbox.
        """
        selected_index = self.listbox.curselection()
        if selected_index:
            feed_config = self.feed_handler.feeds_data[selected_index[0]]
            articles = self.feed_handler.parse_feed(feed_config)
            self.update_articles_display(articles)
        else:
            self.update_articles_display([])

    def update_articles_display(self, articles: List[Article]) -> None:
        """
        Update the treeview with the list of articles.

        Args:
            articles: List of articles to display.
        """
        self.articles_tree.delete(*self.articles_tree.get_children())
        for article in articles:
            self.articles_tree.insert("", "end", values=(article.title, article.link))


if __name__ == "__main__":
    root = tk.Tk()
    feed_manager = FeedHandler("feeds.json")  # Renamed to avoid conflict
    app = FeedManagerGUI(root, feed_manager)
    root.mainloop()