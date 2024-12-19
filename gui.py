"""
GUI Module.
"""
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import json
import os

import ttkbootstrap as tb

from feedhandler import FeedHandler, FeedConfig
from generator import EpubGenerator

# Import the logger setup function
from logger import _setup_logger


class EpistleGUI:
    """The main class, here the magic gets drawn"""

    def __init__(self, root):
        self.root = root
        self.root.title("Epistle")
        self.root.geometry("800x540")
        self.handler = FeedHandler("configs/feeds.json")
        self.generator = EpubGenerator()
        self.settings_file = "configs/settings.json"

        # Create a logger for this class
        self.logger = _setup_logger("EpistleGUI")

        # Ensure the configs directory exists
        self.ensure_configs_directory_exists()

        # Load settings from JSON file
        self.settings = self.load_settings()

        # Apply theme from settings
        if "theme" in self.settings:
            self.root.style.theme_use(self.settings["theme"])
            self.logger.info("Applied theme: %s", self.settings['theme'])

        # Create Notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")

        # Feed Tab
        feed_tab = ttk.Frame(self.notebook)
        self.notebook.add(feed_tab, text="Feeds")

        # Configure grid weights for feed tab
        feed_tab.rowconfigure(0, weight=1)
        feed_tab.columnconfigure(0, weight=1)
        feed_tab.columnconfigure(1, weight=1)

        # Combined Input and Buttons Frame
        combined_frame = tb.Frame(feed_tab, padding=(10, 10))
        combined_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Configure grid weights for combined frame
        combined_frame.rowconfigure(0, weight=1)
        combined_frame.rowconfigure(1, weight=1)
        combined_frame.rowconfigure(2, weight=1)
        combined_frame.rowconfigure(3, weight=1)  # New row for buttons
        combined_frame.columnconfigure(0, weight=1)
        combined_frame.columnconfigure(1, weight=1)

        # Feed URL Input
        tb.Label(combined_frame, text="Feed URL:").grid(
            row=0, column=0, sticky="w", padx=10, pady=5)
        self.url_entry = tb.Entry(combined_frame, width=40)
        self.url_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # Feed Name Input
        tb.Label(combined_frame, text="Feed Name:").grid(
            row=1, column=0, sticky="w", padx=10, pady=5)
        self.name_entry = tb.Entry(combined_frame, width=40)
        self.name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Number of Articles Input
        tb.Label(combined_frame, text="Number of Articles:").grid(
            row=2, column=0, sticky="w", padx=10, pady=5)
        self.num_entry = tb.Entry(combined_frame, width=5)
        self.num_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Buttons Frame
        btn_frame = tb.Frame(combined_frame, padding=(10, 5))
        btn_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")

        # Configure grid weights for buttons frame
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)
        btn_frame.columnconfigure(3, weight=1)

        # Buttons
        self.add_btn = tb.Button(
            btn_frame, text="Add Feed", command=self.add_feed, width=15)
        self.add_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.edit_btn = tb.Button(
            btn_frame, text="Edit Feed", command=self.edit_feed, width=15)
        self.edit_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.del_btn = tb.Button(
            btn_frame, text="Delete Feed", command=self.delete_feed, width=15)
        self.del_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.gen_btn = tb.Button(
            btn_frame, text="Generate EPUB", command=self.generate_epub, width=15)
        self.gen_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Feed List
        self.tree = tb.Treeview(feed_tab, columns=(
            "Name", "URL", "Articles"), show="headings")
        self.tree.heading("Name", text="Feed Name")
        self.tree.heading("URL", text="Feed URL")
        # Center the "Articles" column header
        self.tree.heading("Articles", text="Articles", anchor="center")
        # Center the "Articles" column data
        self.tree.column("Articles", anchor="center")
        self.tree.grid(row=1, column=0, columnspan=2,
                       sticky="nsew", padx=10, pady=5)

        self.refresh_feed_list()

        # Settings Tab
        settings_tab = tb.Frame(self.notebook, padding=(10, 10))
        self.notebook.add(settings_tab, text="Settings")

        # Configure grid weights for settings tab
        settings_tab.rowconfigure(0, weight=1)
        settings_tab.rowconfigure(1, weight=1)
        settings_tab.rowconfigure(2, weight=1)
        settings_tab.rowconfigure(3, weight=1)
        settings_tab.rowconfigure(4, weight=1)
        settings_tab.rowconfigure(5, weight=1)
        settings_tab.rowconfigure(6, weight=1)
        settings_tab.rowconfigure(7, weight=1)
        settings_tab.rowconfigure(8, weight=1)
        settings_tab.columnconfigure(0, weight=1)
        settings_tab.columnconfigure(1, weight=1)

        # SMTP Username/Email
        tb.Label(settings_tab, text="SMTP Username/Email:").grid(
            row=0, column=0, sticky="w", padx=10, pady=5)
        self.smtp_username_entry = tb.Entry(settings_tab, width=40)
        self.smtp_username_entry.grid(
            row=0, column=1, padx=10, pady=5, sticky="ew")
        self.smtp_username_entry.insert(
            0, self.settings.get("smtp_username", ""))

        # SMTP Password
        tb.Label(settings_tab, text="SMTP Password:").grid(
            row=1, column=0, sticky="w", padx=10, pady=5)
        self.smtp_password_entry = tb.Entry(settings_tab, width=40, show="*")
        self.smtp_password_entry.grid(
            row=1, column=1, padx=10, pady=5, sticky="ew")
        self.smtp_password_entry.insert(
            0, self.settings.get("smtp_password", ""))

        # SMTP Server
        tb.Label(settings_tab, text="SMTP Server:").grid(
            row=2, column=0, sticky="w", padx=10, pady=5)
        self.smtp_server_entry = tb.Entry(settings_tab, width=40)
        self.smtp_server_entry.grid(
            row=2, column=1, padx=10, pady=5, sticky="ew")
        self.smtp_server_entry.insert(
            0, self.settings.get("smtp_server", ""))

        # SMTP Port
        tb.Label(settings_tab, text="SMTP Port:").grid(
            row=3, column=0, sticky="w", padx=10, pady=5)
        self.smtp_port_entry = tb.Entry(settings_tab, width=40)
        self.smtp_port_entry.grid(
            row=3, column=1, padx=10, pady=5, sticky="ew")
        self.smtp_port_entry.insert(
            0, self.settings.get("smtp_port", ""))

        # Target Email
        tb.Label(settings_tab, text="Target Email:").grid(
            row=4, column=0, sticky="w", padx=10, pady=5)
        self.target_email_entry = tb.Entry(settings_tab, width=40)
        self.target_email_entry.grid(
            row=4, column=1, padx=10, pady=5, sticky="ew")
        self.target_email_entry.insert(
            0, self.settings.get("target_email", ""))

        # Time to Send Emails
        tb.Label(settings_tab, text="Time to Send Emails (HH:MM):").grid(
            row=5, column=0, sticky="w", padx=10, pady=5)

        # Time Picker Frame
        time_picker_frame = tb.Frame(settings_tab)
        time_picker_frame.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        # Hour Spinbox
        self.hour_var = tk.StringVar(value=self.settings.get("hour", "00"))
        hour_spinbox = tb.Spinbox(time_picker_frame, from_=0, to=23,
                                  wrap=True, format="%02.0f", textvariable=self.hour_var, width=3)
        hour_spinbox.grid(row=0, column=0, padx=(0, 2), pady=0, sticky="e")

        # Colon Label
        colon_label = tb.Label(time_picker_frame, text=":")
        colon_label.grid(row=0, column=1, padx=2, pady=0)

        # Minute Spinbox
        self.minute_var = tk.StringVar(value=self.settings.get("minute", "00"))
        minute_spinbox = tb.Spinbox(time_picker_frame, from_=0, to=59,
                                    wrap=True, format="%02.0f",
                                    textvariable=self.minute_var, width=3)
        minute_spinbox.grid(row=0, column=2, padx=(2, 0), pady=0, sticky="w")

        # Days Between Emails
        tb.Label(settings_tab, text="Days Between Emails:").grid(
            row=6, column=0, sticky="w", padx=10, pady=5)
        self.days_entry = tb.Entry(settings_tab, width=40)
        self.days_entry.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        self.days_entry.insert(0, self.settings.get("days_between_emails", ""))

        # Article Type Dropdown
        tb.Label(settings_tab, text="Article Type:").grid(
            row=7, column=0, sticky="w", padx=10, pady=5)
        self.article_type_var = tk.StringVar(value=self.settings.get(
            "article_type", "Summary"))  # Default to Summary
        self.article_type_dropdown = tb.Combobox(settings_tab, textvariable=self.article_type_var,
                                                values=[
                                                    "Full", "Summary"], width=37, state="readonly")
        self.article_type_dropdown.grid(
            row=7, column=1, padx=10, pady=5, sticky="ew")

        # Theme Selection
        tb.Label(settings_tab, text="Select Theme:").grid(
            row=8, column=0, sticky="w", padx=10, pady=5)
        self.theme_var = tk.StringVar(
            value=self.settings.get("theme", "darkly"))  # Default theme
        self.theme_dropdown = tb.Combobox(
            settings_tab, textvariable=self.theme_var,
            values=self.get_available_themes(), width=37, state="readonly")
        self.theme_dropdown.grid(row=8, column=1, padx=10, pady=5, sticky="ew")
        self.theme_dropdown.bind("<<ComboboxSelected>>", self.change_theme)

        # Save Settings Button
        self.save_settings_btn = tb.Button(
            settings_tab, text="Save Settings", command=self.save_settings, width=15)
        self.save_settings_btn.grid(
            row=9, column=0, columnspan=2, pady=20, sticky="ew")

    def ensure_configs_directory_exists(self) -> None:
        """Ensure the configs directory exists."""
        config_dir = os.path.dirname(self.settings_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            self.logger.info("Created directory: %s", config_dir)

    def get_available_themes(self) -> list[str]:
        """Get a list of available ttkbootstrap themes."""
        return tb.Style().theme_names()

    # pylint: disable=unused-argument
    def change_theme(self, event) -> None:
        """Change the theme of the application based on the selected theme."""
        selected_theme = self.theme_var.get()
        self.root.style.theme_use(selected_theme)
        self.logger.info("Changed theme to: %s", selected_theme)

    def add_feed(self) -> None:
        """Add a new feed to the handler."""
        url = self.url_entry.get()
        name = self.name_entry.get() or "Unnamed Feed"
        num_articles = int(self.num_entry.get() or 5)
        if not url.startswith("http://") and not url.startswith("https://"):
            messagebox.showerror(
                "Input Error", "Please enter a valid URL starting with http:// or https://")
            self.logger.error("Invalid feed URL format: %s", url)
            return
        # Check for duplicates
        for feed in self.handler.feeds_data:
            if feed.url == url:
                messagebox.showerror(
                    "Duplicate Error", "Feed URL already exists!")
                self.logger.error(
                    "Attempted to add a duplicate feed with URL: %s", url)
                return
        new_feed = FeedConfig(url=url, name=name, num_articles=num_articles)
        self.handler.add_feed(new_feed)
        messagebox.showinfo("Success", "Feed added successfully!")
        self.logger.info("Added feed: %s (%s) with %d articles",
                         name, url, num_articles)
        self.clear_inputs()
        self.refresh_feed_list()

    def edit_feed(self) -> None:
        """Edit an existing feed."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning(
                "Selection Error", "No feed selected for editing!")
            self.logger.warning(
                "Attempted to edit a feed without selecting one.")
            return

        # Get selected feed
        feed_url = self.tree.item(selected_item, "values")[1]
        for feed in self.handler.feeds_data:
            if feed.url == feed_url:
                # Update feed with current input
                feed.name = self.name_entry.get() or feed.name
                feed.num_articles = int(
                    self.num_entry.get() or feed.num_articles)
                feed.url = self.url_entry.get() or feed.url
                self.handler.update_feed(feed_url, feed)
                messagebox.showinfo("Success", "Feed updated successfully!")
                self.logger.info("Updated feed: %s (%s) with %d articles",
                                 feed.name, feed.url, feed.num_articles)
                self.clear_inputs()
                self.refresh_feed_list()
                return

    def delete_feed(self) -> None:
        """Delete the selected feed."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "No feed selected!")
            self.logger.warning(
                "Attempted to delete a feed without selecting one.")
            return
        feed_url = self.tree.item(selected_item, "values")[1]
        self.handler.remove_feed(feed_url)
        messagebox.showinfo("Success", "Feed deleted successfully!")
        self.logger.info("Deleted feed with URL: %s", feed_url)
        self.refresh_feed_list()

    def generate_epub(self) -> None:
        """Generate the EPUB file."""
        output_file = filedialog.asksaveasfilename(
            defaultextension=".epub", filetypes=[("EPUB files", "*.epub")]
        )
        if not output_file:
            self.logger.warning("EPUB generation canceled by user.")
            return
        try:
            article_type = self.settings.get("article_type", "Summary")  # Default to Summary
            self.logger.info("Article type from settings: %s", article_type)
            if article_type not in ["Full", "Summary"]:
                self.logger.error("Unknown article type: %s", article_type)
                messagebox.showerror("Error", f"Unknown article type: {article_type}")
                return

            else:
                self.logger.info("Generating EPUB with type = %s.", article_type)
                self.generator.generate_epub(
                    self.handler.feeds_data,
                    self.handler, output_file,
                    article_type=article_type)
            messagebox.showinfo("Success", f"EPUB generated: {output_file}")
            self.logger.info("Generated EPUB: %s", output_file)

        # pylint: disable=broad-exception-caught
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate EPUB: {e}")
            self.logger.error("Failed to generate EPUB: %s", e)

    def refresh_feed_list(self) -> None:
        """Refresh the feed list display."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        for feed in self.handler.feeds_data:
            self.tree.insert("", tk.END, values=(
                feed.name, feed.url, feed.num_articles))
        self.tree.bind("<ButtonRelease-1>", self.load_selected_feed)
        self.logger.debug("Refreshed feed list.")

    # pylint: disable=unused-argument
    def load_selected_feed(self, event) -> None:
        """Load selected feed details into input fields."""
        selected_item = self.tree.selection()
        if selected_item:
            values = self.tree.item(selected_item, "values")
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, values[0])
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, values[1])
            self.num_entry.delete(0, tk.END)
            self.num_entry.insert(0, values[2])
            self.logger.debug(
                "Loaded feed: %s (%s) with %d articles", values[0], values[1], values[2])

    def clear_inputs(self) -> None:
        """Clear input fields."""
        self.url_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.num_entry.delete(0, tk.END)
        self.logger.debug("Cleared input fields.")

    def load_settings(self) -> dict:
        """Load settings from a JSON file."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as file:
                    settings = json.load(file)
                self.logger.info("Loaded settings: %s", settings)
                return settings
            except (FileNotFoundError, json.JSONDecodeError) as e:
                self.logger.error("Error loading settings: %s", e)
        self.logger.info("Settings file does not exist.")
        return {}

    def save_settings(self) -> None:
        """Save the settings to a JSON file."""
        smtp_username = self.smtp_username_entry.get()
        smtp_password = self.smtp_password_entry.get()
        smtp_server = self.smtp_server_entry.get()
        smtp_port = self.smtp_port_entry.get()
        target_email = self.target_email_entry.get()
        hour = self.hour_var.get()
        minute = self.minute_var.get()
        time_to_send = f"{hour}:{minute}"
        days_between_emails = self.days_entry.get()
        article_type = self.article_type_var.get()
        theme = self.theme_var.get()

        # Validate inputs
        if (not smtp_username or not smtp_password or not smtp_server or not smtp_port
            or not target_email or not time_to_send or not days_between_emails):
            messagebox.showerror("Input Error", "All fields must be filled!")
            self.logger.error(
                "Attempted to save settings with missing fields.")
            return

        try:
            # Convert days to integer
            days_between_emails = int(days_between_emails)
        except ValueError:
            messagebox.showerror(
                "Input Error", "Days between emails must be an integer!")
            self.logger.error(
                "Attempted to save settings with non-integer days between emails.")
            return

        try:
            # Convert port to integer
            smtp_port = int(smtp_port)
        except ValueError:
            messagebox.showerror(
                "Input Error", "SMTP port must be an integer!")
            self.logger.error(
                "Attempted to save settings with non-integer SMTP port.")
            return

        # Create settings dictionary
        settings = {
            "smtp_username": smtp_username,
            "smtp_password": smtp_password,
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "target_email": target_email,
            "hour": hour,
            "minute": minute,
            "days_between_emails": days_between_emails,
            "article_type": article_type,
            "theme": theme
        }

        # Save settings to JSON file
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as file:
                json.dump(settings, file, indent=4)
            self.logger.info("Saved settings: %s", settings)
            self.settings = self.load_settings()
            self.logger.info("Loaded newly saved settings.")
            messagebox.showinfo("Success", "Settings saved successfully!")
        # pylint: disable=broad-exception-caught
        except Exception as e:
            self.logger.error("Error saving settings: %s", e)
            messagebox.showerror("Error", f"Failed to save settings: {e}")


if __name__ == "__main__":
    start = tb.Window(themename="darkly")  # Default theme
    app = EpistleGUI(start)
    start.mainloop()
