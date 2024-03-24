import tkinter as tk
from tkinter import ttk, scrolledtext
import psutil
import subprocess
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np

class SystemMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("System Monitor")
        # Ensure the cpu_usage_history is initialized with a fixed size, filled with zeros
        self.cpu_usage_history = np.zeros(100)  # Initialize with 100 zeros
        self.memory_usage_history = np.zeros(100)  # Initialize with 100 zeros
        self.setup_ui()
        self.update_process_list()

    def setup_ui(self):
        # Top frame for graphs
        top_frame = tk.Frame(self.root, height=350)
        top_frame.pack(side=tk.TOP, fill=tk.BOTH)

        # Frame for CPU graph
        cpu_frame = tk.Frame(top_frame, bg='black')
        cpu_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame for Memory graph
        memory_frame = tk.Frame(top_frame, bg='black')
        memory_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # CPU graph setup
        cpu_fig = Figure(figsize=(3, 2), dpi=100, facecolor='black')
        cpu_ax = cpu_fig.add_subplot(111)
        cpu_ax.set_facecolor('black')
        cpu_ax.tick_params(axis='x', colors='white')
        cpu_ax.tick_params(axis='y', colors='white')
        cpu_ax.spines['bottom'].set_color('white')
        cpu_ax.spines['left'].set_color('white')
        cpu_ax.spines['top'].set_color('white')
        cpu_ax.spines['right'].set_color('white')
        cpu_ax.set_title('CPU Usage (%)', color='white')
        cpu_fig.tight_layout()

        cpu_canvas = FigureCanvasTkAgg(cpu_fig, master=cpu_frame)
        cpu_canvas_widget = cpu_canvas.get_tk_widget()
        cpu_canvas_widget.pack(fill=tk.BOTH, expand=True)

        # Memory graph setup
        memory_fig = Figure(figsize=(3, 2), dpi=100, facecolor='black')
        memory_ax = memory_fig.add_subplot(111)
        memory_ax.set_facecolor('black')
        memory_ax.tick_params(axis='x', colors='white')
        memory_ax.tick_params(axis='y', colors='white')
        memory_ax.spines['bottom'].set_color('white')
        memory_ax.spines['left'].set_color('white')
        memory_ax.spines['top'].set_color('white')
        memory_ax.spines['right'].set_color('white')
        memory_ax.set_title('Memory Usage (%)', color='white')
        memory_fig.tight_layout()

        memory_canvas = FigureCanvasTkAgg(memory_fig, master=memory_frame)
        memory_canvas_widget = memory_canvas.get_tk_widget()
        memory_canvas_widget.pack(fill=tk.BOTH, expand=True)

        # Bottom frame for the processes list
        bottom_frame = tk.Frame(self.root, bg='black')
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Treeview in bottom frame
        self.tree = ttk.Treeview(bottom_frame, columns=('PID', 'Name', 'CPU Usage', 'Memory Usage'), show='headings')
        self.tree.heading('PID', text='PID')
        self.tree.heading('Name', text='Name')
        self.tree.heading('CPU Usage', text='CPU Usage')
        self.tree.heading('Memory Usage', text='Memory Usage')
        self.tree.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure("Treeview", background="black", foreground="white", fieldbackground="black")
        style.configure("Treeview.Heading", foreground='white', background='black')
        self.tree.bind("<Double-1>", self.on_item_double_click)
        self.tree.bind('<Double-3>', self.kill_process)  # Bind right-click to show_context_menu method

        # Start updating graphs
        self.animate_cpu = FuncAnimation(cpu_fig, lambda frame: self.update_usage_plot(frame, cpu_ax, self.cpu_usage_history, 'CPU Usage (%)'), interval=55, cache_frame_data=False)
        self.animate_memory = FuncAnimation(memory_fig, lambda frame: self.update_usage_plot(frame, memory_ax, self.memory_usage_history, 'Memory Usage (%)'), interval=55, cache_frame_data=False)


    def kill_process(self, event):
        try:
            # Identify the row under cursor and select it
            rowid = self.tree.identify_row(event.y)
            if rowid:
                self.tree.selection_set(rowid)
                # Get the PID from the selected row
                selection = self.tree.selection()
                if selection:
                    item = self.tree.item(selection)
                    pid = item['values'][0]  # PID is the first value
                    # Kill the process
                    proc = psutil.Process(pid)
                    proc.kill()
                    messagebox.showinfo("Success", f"Process {pid} killed successfully.")
        except psutil.NoSuchProcess:
            messagebox.showerror("Error", "Process not found or already terminated.")
        except psutil.AccessDenied:
            messagebox.showerror("Error", "Access denied. Cannot terminate process.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to terminate process: {e}")


    def get_process_list(self):
        process_list = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            process_list.append(proc.info)
        #process_list.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return process_list


    def update_process_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for proc in self.get_process_list():
            self.tree.insert('', tk.END, values=(proc['pid'], proc['name'], f"{proc['cpu_percent']}%", f"{proc['memory_percent']}%"))
        self.root.after(1000, self.update_process_list)  # Update the list every second


    def on_item_double_click(self, event):
        # Get the selected item
        item = self.tree.selection()[0]
        pid = self.tree.item(item, 'values')[0]

        # Show process status for the selected PID
        self.show_process_status(pid)


    def update_usage_plot(self, frame, ax, history, title):
        # This function updates either CPU or Memory usage plot
        if title == 'CPU Usage (%)':
            usage = psutil.cpu_percent()
        else:  # Memory usage
            usage = psutil.virtual_memory().percent

        history[:-1] = history[1:]  # Shift data
        history[-1] = usage  # Add latest usage value

        ax.clear()
        ax.plot(history, '-o', color='tab:blue')
        ax.set_title(title)
        ax.set_ylim(0, 100)  # Assume max usage is 100%


    def show_process_status(self, pid):

      output = subprocess.run(['cat', f'/proc/{pid}/status'], capture_output=True, text=True, check=True).stdout
    # Open a new window to display the output
      detail_window = tk.Toplevel(self.root, bg = 'black')
      detail_window.title(f"Process Status for PID {pid}")
      text_area = scrolledtext.ScrolledText(detail_window, width=60, height=20, bg='black', fg='white')
      text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
      text_area.insert(tk.INSERT, output)
      text_area.config(state=tk.DISABLED)


def run_gui():
    root = tk.Tk()
    app = SystemMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
