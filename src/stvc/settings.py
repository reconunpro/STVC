"""Settings window for STVC configuration."""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from . import __version__
from .audio import list_audio_devices
from .config import load_dictionary_raw, save_config, save_dictionary

log = logging.getLogger(__name__)


class SettingsWindow:
    """Tkinter-based settings window with tabbed interface.

    Provides UI for configuring:
    - Microphone selection
    - Hotkey remapping
    - Dictionary editing
    """

    def __init__(
        self,
        parent: tk.Tk,
        config: dict,
        on_hotkey_change: Callable[[str], None] | None = None,
        on_device_change: Callable[[str], None] | None = None,
        on_dictionary_change: Callable[[str], None] | None = None,
    ):
        """Initialize settings window.

        Args:
            parent: Parent tk.Tk root window
            config: Current configuration dict
            on_hotkey_change: Callback when hotkey changes
            on_device_change: Callback when audio device changes
            on_dictionary_change: Callback when dictionary changes
        """
        self.parent = parent
        self.config = config.copy()
        self.on_hotkey_change = on_hotkey_change
        self.on_device_change = on_device_change
        self.on_dictionary_change = on_dictionary_change

        self.window = None
        self.dictionary_data = None

        # UI state
        self.capturing_hotkey = False
        self.captured_keys = set()

    def show(self):
        """Create and show the settings window."""
        if self.window is not None:
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("STVC Settings")
        self.window.geometry("600x500")
        self.window.resizable(False, False)

        # Center on screen
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"600x500+{x}+{y}")

        # Load dictionary
        self.dictionary_data = load_dictionary_raw()

        # Create notebook with tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self._create_general_tab(notebook)
        self._create_hotkey_tab(notebook)
        self._create_dictionary_tab(notebook)
        self._create_about_tab(notebook)

        # Bottom buttons
        button_frame = tk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Save", command=self._on_save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT, padx=5)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Show and focus window (after all UI is built)
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

        # Make modal after window is visible (optional - removed transient since parent is hidden)
        # self.window.grab_set()

    def _create_general_tab(self, notebook: ttk.Notebook):
        """Create the General settings tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="General")

        # Microphone selection
        ttk.Label(frame, text="Microphone Device:", font=("", 10, "bold")).pack(anchor=tk.W, padx=20, pady=(20, 5))

        device_frame = tk.Frame(frame)
        device_frame.pack(fill=tk.X, padx=20, pady=5)

        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(device_frame, textvariable=self.device_var, state="readonly")
        self.device_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(device_frame, text="Refresh", command=self._refresh_devices).pack(side=tk.LEFT, padx=(5, 0))

        # Load devices
        self._refresh_devices()

        # Set current device
        current_device = self.config.get("audio", {}).get("device", "")
        if current_device:
            self.device_var.set(current_device)
        elif self.device_combo["values"]:
            self.device_var.set(self.device_combo["values"][0])

    def _refresh_devices(self):
        """Refresh the list of audio devices."""
        devices = list_audio_devices()
        if not devices:
            self.device_combo["values"] = ["No input devices found"]
            self.device_var.set("No input devices found")
            log.warning("No audio input devices found")
            return

        device_names = [f"{d['index']}: {d['name']}" for d in devices]
        self.device_combo["values"] = device_names

        # Keep current selection if still valid
        if self.device_var.get() not in device_names and device_names:
            self.device_var.set(device_names[0])

    def _create_hotkey_tab(self, notebook: ttk.Notebook):
        """Create the Hotkey settings tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Hotkey")

        ttk.Label(frame, text="Push-to-Talk Hotkey:", font=("", 10, "bold")).pack(anchor=tk.W, padx=20, pady=(20, 5))

        # Current hotkey display
        current_hotkey = self.config.get("hotkey", {}).get("push_to_talk", "ctrl+f13")

        hotkey_frame = tk.Frame(frame)
        hotkey_frame.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(hotkey_frame, text="Current:").pack(side=tk.LEFT)
        self.hotkey_label = ttk.Label(hotkey_frame, text=current_hotkey, font=("", 10, "bold"))
        self.hotkey_label.pack(side=tk.LEFT, padx=(5, 0))

        # Capture button
        self.capture_button = ttk.Button(frame, text="Record New Hotkey", command=self._start_hotkey_capture)
        self.capture_button.pack(padx=20, pady=10)

        # Instructions
        self.hotkey_instructions = ttk.Label(
            frame,
            text="Click 'Record New Hotkey' and press your desired key combination.\nExample: Ctrl+F13, Alt+Space, Shift+F5",
            justify=tk.LEFT
        )
        self.hotkey_instructions.pack(padx=20, pady=10)

    def _start_hotkey_capture(self):
        """Start capturing a new hotkey."""
        self.capturing_hotkey = True
        self.captured_keys.clear()
        self.capture_button.config(text="Press key combination...", state=tk.DISABLED)
        self.hotkey_instructions.config(text="Press your desired key combination now...", foreground="blue")

        # Bind key events
        self.window.bind("<KeyPress>", self._on_key_press)
        self.window.bind("<KeyRelease>", self._on_key_release)
        self.window.focus_set()

    def _on_key_press(self, event):
        """Handle key press during hotkey capture."""
        if not self.capturing_hotkey:
            return

        key_name = self._get_key_name(event)
        if key_name:
            self.captured_keys.add(key_name)

    def _on_key_release(self, event):
        """Handle key release during hotkey capture."""
        if not self.capturing_hotkey:
            return

        # When any key is released, finalize the capture
        if self.captured_keys:
            self._finalize_hotkey_capture()

    def _get_key_name(self, event) -> str:
        """Convert tkinter key event to hotkey string component."""
        keysym = event.keysym.lower()

        # Map special keys
        key_map = {
            "control_l": "ctrl", "control_r": "ctrl",
            "alt_l": "alt", "alt_r": "alt",
            "shift_l": "shift", "shift_r": "shift",
        }

        return key_map.get(keysym, keysym)

    def _finalize_hotkey_capture(self):
        """Finalize the hotkey capture."""
        self.capturing_hotkey = False
        self.window.unbind("<KeyPress>")
        self.window.unbind("<KeyRelease>")

        # Build hotkey string
        modifiers = []
        main_key = None

        for key in self.captured_keys:
            if key in ("ctrl", "alt", "shift"):
                modifiers.append(key)
            else:
                main_key = key

        if main_key:
            new_hotkey = "+".join(modifiers + [main_key])
            self.hotkey_label.config(text=new_hotkey)
            self.config.setdefault("hotkey", {})["push_to_talk"] = new_hotkey

            self.hotkey_instructions.config(
                text=f"New hotkey set: {new_hotkey}\nClick 'Save' to apply.",
                foreground="green"
            )
        else:
            self.hotkey_instructions.config(
                text="No valid key captured. Click 'Record New Hotkey' to try again.",
                foreground="red"
            )

        self.capture_button.config(text="Record New Hotkey", state=tk.NORMAL)

    def _create_dictionary_tab(self, notebook: ttk.Notebook):
        """Create the Dictionary editor tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Dictionary")

        ttk.Label(frame, text="Custom Vocabulary:", font=("", 10, "bold")).pack(anchor=tk.W, padx=20, pady=(20, 5))

        # Listbox with scrollbar
        list_frame = tk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.dict_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.dict_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.dict_listbox.yview)

        # Populate listbox
        self._refresh_dictionary_list()

        # Add/Remove buttons
        button_frame = tk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=20, pady=5)

        self.add_entry = ttk.Entry(button_frame)
        self.add_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(button_frame, text="Add Term", command=self._add_term).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Remove", command=self._remove_term).pack(side=tk.LEFT, padx=2)

        # Term count
        self.term_count_label = ttk.Label(frame, text="")
        self.term_count_label.pack(anchor=tk.W, padx=20, pady=5)
        self._update_term_count()

    def _refresh_dictionary_list(self):
        """Refresh the dictionary listbox."""
        self.dict_listbox.delete(0, tk.END)

        categories = self.dictionary_data.get("categories", {})
        for category, terms in categories.items():
            # Add category header
            self.dict_listbox.insert(tk.END, f"[{category.upper()}]")
            self.dict_listbox.itemconfig(tk.END, bg="lightgray")

            # Add terms
            for term in terms:
                self.dict_listbox.insert(tk.END, f"  {term}")

    def _add_term(self):
        """Add a new term to the custom category."""
        term = self.add_entry.get().strip()
        if not term:
            messagebox.showwarning("Empty Term", "Please enter a term to add.")
            return

        # Add to custom category
        if "custom" not in self.dictionary_data["categories"]:
            self.dictionary_data["categories"]["custom"] = []

        if term in self.dictionary_data["categories"]["custom"]:
            messagebox.showinfo("Duplicate", f"'{term}' is already in the custom dictionary.")
            return

        self.dictionary_data["categories"]["custom"].append(term)
        self._refresh_dictionary_list()
        self._update_term_count()
        self.add_entry.delete(0, tk.END)

    def _remove_term(self):
        """Remove selected term from custom category."""
        selection = self.dict_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a term to remove.")
            return

        item_text = self.dict_listbox.get(selection[0])

        # Check if it's a category header
        if item_text.startswith("["):
            messagebox.showwarning("Invalid Selection", "Cannot remove category headers.")
            return

        # Extract term (remove leading spaces)
        term = item_text.strip()

        # Only allow removing from custom category
        if "custom" in self.dictionary_data["categories"]:
            if term in self.dictionary_data["categories"]["custom"]:
                self.dictionary_data["categories"]["custom"].remove(term)
                self._refresh_dictionary_list()
                self._update_term_count()
            else:
                messagebox.showwarning("Cannot Remove", "Only terms from the 'custom' category can be removed.")
        else:
            messagebox.showwarning("Cannot Remove", "Only terms from the 'custom' category can be removed.")

    def _update_term_count(self):
        """Update the term count label."""
        total = sum(len(terms) for terms in self.dictionary_data.get("categories", {}).values())
        self.term_count_label.config(text=f"Total terms: {total}")

    def _create_about_tab(self, notebook: ttk.Notebook):
        """Create the About tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="About")

        ttk.Label(frame, text="STVC", font=("", 16, "bold")).pack(pady=(40, 5))
        ttk.Label(frame, text=f"Version {__version__}", font=("", 10)).pack(pady=5)
        ttk.Label(frame, text="Speech-to-Text for Vibe Coding", font=("", 10)).pack(pady=5)
        ttk.Label(frame, text="A Windows PTT tool with context-aware transcription", font=("", 9)).pack(pady=20)

    def _on_save(self):
        """Save all settings."""
        try:
            # Save audio device
            device_selection = self.device_var.get()
            if device_selection and not device_selection.startswith("No input"):
                # Extract device index from "index: name" format
                device_index = device_selection.split(":")[0].strip()
                self.config.setdefault("audio", {})["device"] = device_index

                if self.on_device_change:
                    self.on_device_change(device_index)

            # Save hotkey
            hotkey = self.config.get("hotkey", {}).get("push_to_talk")
            if hotkey and self.on_hotkey_change:
                self.on_hotkey_change(hotkey)

            # Save dictionary
            save_dictionary(self.dictionary_data)

            if self.on_dictionary_change:
                # Flatten dictionary for transcriber
                from .config import load_dictionary
                terms_str = load_dictionary()
                self.on_dictionary_change(terms_str)

            # Save config
            save_config(self.config)

            messagebox.showinfo("Settings Saved", "All settings have been saved successfully.")
            self._on_cancel()

        except Exception as e:
            log.error(f"Failed to save settings: {e}")
            messagebox.showerror("Save Failed", f"Failed to save settings: {e}")

    def _on_cancel(self):
        """Close the settings window without saving."""
        if self.window:
            self.window.grab_release()
            self.window.destroy()
            self.window = None
