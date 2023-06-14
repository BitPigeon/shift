from threading import Thread
import tkinter as tk
import subprocess
import getpass
import socket
import os

class CommandThread(Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stopped = False

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Shift ~ A Terminal for Anyone")
        self.geometry("750x500")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.terminal = Terminal(self)
        self.terminal.grid(row=0, column=0, sticky="nsew")
    def on_close(self):
        try:
            if self.terminal.output_thread and self.terminal.output_thread.is_alive():
                self.terminal.output_thread.stopped = True
                self.terminal.output_thread.join()
            self.destroy()
        except:
            self.destroy()

class Terminal(tk.Text):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(font=("Liberation Mono", 9), background="black", foreground="light gray", insertbackground="dark gray", insertwidth=0, highlightthickness=0)
        self.tag_configure("sel", foreground="black", background="light gray")
        self.tag_configure("cursor", foreground="black", background="light gray")
        self.tag_configure("special", font=("Liberation Mono", 9, "bold"))
        self.tag_configure("output", foreground="dark gray")
        self.tag_configure("error", foreground="#9F0000")
        self.tag_raise("sel")
        self.path = os.path.expanduser("~")
        self.query_len = 0
        self.bind("<BackSpace>", self.backspace)
        self.bind("<Return>", self.new_prompt)
        self.bind("<KeyPress>", self.key)
        self.bind("<Control-c>", self.cancel)
        self.init()
        self.focus()

    def cancel(self, event):
        if self.output_thread and self.output_thread.is_alive():
            self.output_thread.stopped = True
    
    def init(self):
        self.query_len = 0
        message = "\n" + getpass.getuser() + "@" + socket.gethostname() + " ~" + self.path + " $"
        self.insert("end-1c", getpass.getuser(), "special")
        self.insert("end-1c", "@")
        self.insert("end-1c", socket.gethostname(), "special")
        self.insert("end-1c", " ~")
        self.insert("end-1c", self.path)
        self.insert("end-1c", " $  ")
        self.mark_set("insert", "end-2c")
        self.focus_set()
        self.query_len = len(message)
    
    def new_prompt(self, event):
        self.output_thread = CommandThread(target=self.run)
        self.output_thread.start()
        return "break"

    def backspace(self, event):
        position = self.index("insert")
        line, column = map(int, position.split("."))
        last_line, last_column = map(int, self.index("end-2c").split("."))
        insert_pos = self.index("insert-1c").split(".")
        if not int(insert_pos[1]) < self.query_len and not line < last_line:
            self.delete("insert - 1 char")
        return "break"
    
    def focus(self):
        self.tag_remove("cursor", "1.0", "end")
        position = self.index("insert")
        line, column = map(int, position.split("."))
        last_line, last_column = map(int, self.index("end-2c").split("."))
        if column > int(self.index("insert lineend - 1 char").split(".")[1]):
            self.mark_set("insert", "insert lineend - 1 char")
        elif column < self.query_len:
            self.mark_set("insert", f"{line}.{self.query_len}")
        elif line < last_line:
            self.mark_set("insert", "end-2c")
        self.see("insert")
        self.tag_add("cursor", "insert", "insert + 1 char")
        self.after(1, self.focus)

    def key(self, event):
        position = self.index("insert")
        line, column = map(int, position.split("."))
        last_line, last_column = map(int, self.index("end-2c").split("."))
        if column > int(self.index("insert lineend - 1 char").split(".")[1]):
            return "break"
        elif column < self.query_len:
            return "break"
        elif line < last_line:
            return "break"

    def run(self):
        position = self.index("insert")
        line, column = map(int, position.split("."))
        last_line, last_column = map(int, self.index("end-2c").split("."))
        command = self.get(f"{line}.{self.query_len}", f"{line}.{self.query_len} lineend - 1 char").split(" ")
        if len(command) >= 1 and not command[0] == "":
            try:
                process = subprocess.Popen(command, cwd=self.path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)
                for line in iter(process.stdout.readline, ''):
                    line = line.rstrip()
                    self.update_output(line)
                    if self.output_thread.stopped:
                        break
                process.stdout.close()
                process.wait()
            except FileNotFoundError:
                if not command[0] == "cd":
                    self.insert("end-1c", f"\nshift: {command[0]}: command not found", "error")
                else:
                    if len(command) >= 2:
                        if os.path.exists(os.path.join(self.path, command[1])) and os.path.isdir(os.path.join(self.path, command[1])):
                            self.path = os.path.join(self.path, command[1])
                        else:
                            if not os.path.exists(os.path.join(self.path, command[1])):
                                self.insert("end-1c", f"\nshift: cd: {command[1]}: no such file or directory ", "error")
                            else:
                                if not os.path.isdir(os.path.join(self.path, command[1])):
                                    self.insert("end-1c", f"\nshift: cd: {command[1]}: not a directory ", "error")
                    else:
                        self.path = os.path.expanduser("~")
        self.create_new_query()

    def create_new_query(self):
        self.query_len = 0
        message = "\n" + getpass.getuser() + "@" + socket.gethostname() + " ~" + self.path + " $"
        self.insert("end-1c", "\n")
        self.insert("end-1c", getpass.getuser(), "special")
        self.insert("end-1c", "@")
        self.insert("end-1c", socket.gethostname(), "special")
        self.insert("end-1c", " ~")
        self.insert("end-1c", self.path)
        self.insert("end-1c", " $  ")
        self.mark_set("insert", "end-2c")
        self.query_len = len(message)
    
    def update_output(self, output):
        self.insert('end', "\n" + output + " ", "output")
        self.query_len = len("\n" + output) - 1
        self.mark_set("insert", "end-1c")
        self.see('end')

if __name__ == "__main__":
    root = Application()
    root.mainloop()
