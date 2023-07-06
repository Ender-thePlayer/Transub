import gi
import pysubs2
import time
import queue
import re
import os

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib, GdkPixbuf
from threading import Thread
from deep_translator import GoogleTranslator

languages = {
    'ro': 'Română (Romanian)',
    'en': 'English',
    'fr': 'Français (French)',
    'de': 'Deutsch (German)',
    'es': 'Español (Spanish)',
    'ja': '日本語 (Japanese)',
    'sq': 'Shqiptar (Albanian)',
}

def get_resource_path(rel_path):
    dir_of_py_file = os.path.dirname(__file__)
    rel_path_to_resource = os.path.join(dir_of_py_file, rel_path)
    abs_path_to_resource = os.path.abspath(rel_path_to_resource)
    return abs_path_to_resource


##The main window
class EntryWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Subtitler2000")
        self.set_size_request(600, 200)
        self.set_border_width(10)
        self.timeout_id = None

        headerbar = Gtk.HeaderBar()
        headerbar.set_title("Subtitler2000")
        headerbar.set_subtitle("hehe")
        headerbar.set_show_close_button(True)
        self.set_titlebar(headerbar)

        button = Gtk.Button(label="About")
        button.connect("clicked", on_about_button_clicked)
        headerbar.pack_end(button)

        mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(mainbox)

    ##The text and the select language button
        outlangbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        mainbox.pack_start(outlangbox, True, True, 0)

        outlanglabel = Gtk.Label(label="Select Output Language")
        outlangbox.pack_start(outlanglabel, True, True, 0)

        global outlangbutton
        outlangbutton = Gtk.ComboBoxText()
        outlangbutton.append_text("Română (Romanian)")
        outlangbutton.append_text("English")
        outlangbutton.append_text("Français (French)")
        outlangbutton.append_text("Deutsch (German)")
        outlangbutton.append_text("Español (Spanish)")
        outlangbutton.append_text("日本語 (Japanese)")
        outlangbutton.append_text("Shqiptar (Albanian)")
        outlangbutton.set_active(0)

        outlangbox.pack_start(outlangbutton, True, True, 0)

    ##The separator between the select language button and select file button
        separator1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        mainbox.pack_start(separator1, True, True, 0)

    ##The select file button
        filechbutton = Gtk.Button(label="Choose File")
        filechbutton.connect("clicked", lambda _: GLib.idle_add(self.on_file_clicked))
        mainbox.pack_start(filechbutton, True, True, 0)

    ##The progress bar
        global progress_bar
        progress_bar = Gtk.ProgressBar()
        mainbox.pack_start(progress_bar, True, True, 0)

    ##The expander where the text is shown
        expanderbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        expanderbox.set_size_request(600, 200)
        mainbox.pack_start(expanderbox, True, True, 0)

        expander = Gtk.Expander(label="Log")
        expander.set_expanded(True)

    ##The part that allows the text to scroll
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)

    ##The part where the text is entered
        textview = Gtk.TextView()
        textview.set_editable(False)
        textview.set_cursor_visible(False)

    ##The buffer for what text to show
        global textbuffer
        textbuffer = textview.get_buffer()
        self.adjustment = scrolledwindow.get_vadjustment()
        scrolledwindow.connect("size-allocate", on_size_allocate)

        scrolledwindow.add(textview)
        expander.add(scrolledwindow)
        expanderbox.pack_start(expander, True, True, 0)

    ##The start button
        startbt = Gtk.Button(label="Start")
        startbt.connect("clicked", self.on_btn_start)
        mainbox.pack_start(startbt, True, True, 0)
        
    ##The credit text shown at startup
        textbuffer.delete(textbuffer.get_start_iter(), textbuffer.get_end_iter())
        textbuffer.insert(textbuffer.get_start_iter(), "======================================================\n=== Project made by SuperYang#7281 and forked by EnderDatsIt#0802 ===\n======================================================\n")

##The action that the select file button does
    def on_file_clicked(self):
    ##The dialog that says what file to choose
        dialog = Gtk.FileChooserDialog(
            title="Please choose a file",
            parent=self,
            action=Gtk.FileChooserAction.OPEN)

        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Select", Gtk.ResponseType.OK)
        dialog.set_default_size(800, 400)

        filter_file = Gtk.FileFilter()
        filter_file.add_pattern("*.ass")
        filter_file.add_pattern("*.srt")
        dialog.add_filter(filter_file)

    ##The part that gets the file path and name
        global file
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            file = dialog.get_filename()
        dialog.destroy()

    ##The part that logs what file you chose
        end_iter = textbuffer.get_end_iter()
        textbuffer.insert(end_iter, "\nSelected file: " + file + "\n")

##The action that the start button does
    def on_btn_start(self, widget):
    ##The credit text shown when ran
        textbuffer.delete(textbuffer.get_start_iter(), textbuffer.get_end_iter())
        textbuffer.insert(textbuffer.get_start_iter(), "======================================================\n=== Project made by SuperYang#7281 and forked by EnderDatsIt#0802 ===\n======================================================\n")

    ##The part that gets the select language to translate in
        global language_var
        language_var = outlangbutton.get_active_text()

        global target_language
        target_language = next(key for key, value in languages.items() if value == language_var)  # Obține cheia limbii în funcție de valoarea selectată din dropdown    
       
    ##The part that translates
        progress_queue = queue.Queue()

        try:
        ##Invokes the translate_subtitles function to translate
            translation_thread = Thread(target=translate_subtitles, args=(file, target_language, progress_queue))
            translation_thread.start()

        ##Makes the start button unresponsive while the translation job is in progress
            widget.set_sensitive(False)

        ##Updates the progress in the progress bar and logs what line it just translated
            def update_progress_bar_and_text_buffer():
                try:
                    data = progress_queue.get_nowait()
                    fraction, message = data
                    progress_bar.set_fraction(fraction)
                    
                ##Updates the text buffer with the message
                    end_iter = textbuffer.get_end_iter()
                    textbuffer.insert(end_iter, message + "\n")

                except queue.Empty:
                    pass

            ##Handles the termination of the translation thread
                if translation_thread.is_alive():
                    return True
                
                else:
                    progress_queue.put(None)
                    GLib.idle_add(update_progress_bar, progress_queue)
                    widget.set_sensitive(True)
                    return False
                
            GLib.timeout_add(100, update_progress_bar_and_text_buffer)

    ##If file is not specified it will give an error, this is lazy handling of the error :P
        except Exception as e:
            end_iter = textbuffer.get_end_iter()
            textbuffer.insert(end_iter, "\nCannot transalte: File is not specified.\n")

##The about dialog window 
def on_about_button_clicked(button):
    dialog = Gtk.Dialog(
        title="About Subtitler2000",
        transient_for=None,
        flags=0,
    )

    dialog_box = dialog.get_content_area()
    
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    dialog_box.pack_end(box, False, False, 0)

    label = Gtk.Label(label="This project is a subtitle translation tool developed by SuperYang#7281\nand forked by EnderDatsIt#0802. It uses Google Translate API to translate subtitles\nand pysubs2 library for parsing subtitle files.\n\nVersion: beta_1.2")
    label.set_justify(Gtk.Justification.CENTER)
    label.set_halign(Gtk.Align.CENTER)
    label.set_valign(Gtk.Align.CENTER)
    label.set_margin_top(10)
    label.set_margin_bottom(10)
    label.set_margin_start(20)
    label.set_margin_end(20)

    box.pack_start(label, True, True, 0)

    dialog.grab_focus()
    dialog.show_all()
    dialog.run()
    dialog.destroy()

##The function that translates the file
def translate_subtitles(input_file, target_language, queue):

##Checks for file format
    if file.lower().endswith('.srt'):
        subs_format = 'srt'
    elif file.lower().endswith('.ass'):
        subs_format = 'ass'
    else:
        dialog = Gtk.MessageDialog(
            flags=0,
            message_type=Gtk.MessageType.OTHER,
            buttons=Gtk.ButtonsType.OK,
            text="This file format is not supported" )
        
        dialog.format_secondary_text(
            "The file you chose is not in a supported file format (*.srt or *.ass)"
        )
        
        dialog.run()
        dialog.destroy()
        return

##Loads the file you chose
    subs = pysubs2.load(input_file, encoding='utf-8')
    output_file = input_file.replace('.' + subs_format, '_translated.' + subs_format)
    
##Translates the file line by line
    global message

    for i, sub in enumerate(subs):
        original_text = sub.text
        modified_text= replace_newlines_with_spaces(original_text)

    ##Tries to translate the line
        try:
            translation = GoogleTranslator(source='auto', target=target_language).translate(modified_text)
            sub.text = translation
            message = f"Subtitle {i + 1}: {modified_text} -> {translation}"
        
        except Exception as e:
            translation = modified_text
            message = f"Subtitle {i + 1}: {modified_text} -> (translation failed)"

    ##Sends queue for the update_progress_bar_and_text_buffer function to log it
        queue.put((i / len(subs), message))

##Saves the file when the translation process is done
    if len(subs) > 0:
        subs.save(output_file, format_name=subs_format, encoding='utf-8')
        time.sleep(1)

        end_iter = textbuffer.get_end_iter()
        textbuffer.insert(end_iter, f"File translated successfully. Translated file: {output_file}")

##Updates the progress bar when the translation process is done
    progress_bar.set_fraction(0)

##Eh?
def update_progress_bar(queue):
    while True:
        data = queue.get()
        if data is None:
            break

        fraction, message = data
        progress_bar.set_fraction(fraction)
        
        # Update the text buffer with the message
        end_iter = textbuffer.get_end_iter()
        textbuffer.insert(end_iter, message + "\n")

##The function that autoscrolls the text box
def on_size_allocate(widget, allocation):
    vadjustment = widget.get_vadjustment()
    vadjustment.set_value(vadjustment.get_upper() - vadjustment.get_page_size())

##The function that puts a space after each new line character (/N) in the translation so that can it be translated
def replace_newlines_with_spaces(text):
    return re.sub(r'\\N', r'\\N ', text)

def on_response(self, dialog, response):
    if response == Gtk.ResponseType.OK:
        print("OK button clicked")
    elif response == Gtk.ResponseType.CANCEL:
        print("Cancel button clicked")
    else:
        print("Dialog closed")

    dialog.destroy()

win = EntryWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()

##/
#Lil'app made by SuperYang#7281 and forked by EnderDatsIt#0802
#   Version: beta_1.2
#   Licence: TH is that?
