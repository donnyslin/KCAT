from tkinter import *
import tkinter
from tkinter.ttk import *  # Frame, Button, Label, Style, Scrollbar
import tkinter.font as tkFont
import re
from collections import deque
import pickle
import os.path
import platform
from tkinter import messagebox as mBox
from tkinter.filedialog import askdirectory,askopenfilenames,askopenfiles
import sys

class Example(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.Version = "KCAT Manager"
        self.OS = platform.system().lower()
        self.parent = parent
        self.fileName = ""
        # default GUI display parameter

        self.textColumn = 3

        self.initUI()

    def initUI(self):

        self.parent.title(self.Version)
        self.pack(fill=BOTH, expand=True)

        for idx in range(0, self.textColumn):
            if idx == 1:
                self.columnconfigure(idx, weight=10)
            else:
                self.columnconfigure(idx, weight=1)
        # for idx in range(0,2):
        #     self.rowconfigure(idx, weight =1)
        the_font = ('TkDefaultFont', 16,)
        style0 = Style()
        style0.configure(".", font=the_font, )

        width_size = 30

        abtn = Button(self, text="Multi-Annotator Analysis", command=self.multiFiles, width=width_size)
        abtn.grid(row=0, column=1)

        recButton = Button(self, text="Pairwise Comparison", command=self.compareTwoFiles, width=width_size)
        recButton.grid(row=1, column=1)

        cbtn = Button(self, text="Quit", command=self.quit, width=width_size)
        cbtn.grid(row=2, column=1)

    def ChildWindow(self, input_list, result_matrix):
        print(input_list)
        file_list = []
        for dir_name in input_list:
            if ".ann" in dir_name:
                dir_name = dir_name[:-4]
            if "/" in dir_name:
                file_list.append(dir_name.split('/')[-1])
            else:
                file_list.append(dir_name)

        # Create menu
        self.popup = Menu(self.parent, tearoff=0)
        self.popup.add_command(label="Next", command=self.selection)
        self.popup.add_separator()

        def do_popup(event):
            # display the popup menu
            try:
                self.popup.selection = self.tree.set(self.tree.identify_row(event.y))
                self.popup.post(event.x_root, event.y_root)
            finally:
                # make sure to release the grab (Tk 8.0a1 only)
                self.popup.grab_release()

        # Create Treeview
        win2 = Toplevel(self.parent)
        new_element_header = file_list
        treeScroll = Scrollbar(win2)
        treeScroll.pack(side=RIGHT, fill=Y)
        title_string = "Accuracy"
        self.tree = Treeview(win2, columns=[title_string] + file_list, show="headings")

        self.tree.heading(title_string, text=title_string, anchor=CENTER)
        self.tree.column(title_string, stretch=YES, minwidth=60, width=100, anchor=CENTER)
        for each_file in file_list:
            self.tree.heading(each_file, text=each_file, anchor=CENTER)
            self.tree.column(each_file, stretch=YES, minwidth=50, width=100, anchor=CENTER)
        for idx in range(len(file_list)):
            self.tree.insert("", 'end', text=file_list[idx], values=[file_list[idx]] + result_matrix[idx],
                             tags=('chart',))
        the_font = ('Times New Roman', 16,)
        self.tree.tag_configure('chart', font=the_font)
        style = Style()
        style.configure(".", font=the_font, )
        style.configure("Treeview", )
        style.configure("Treeview.Heading", font=the_font, )  # <----
        self.tree.pack(side=TOP, fill=BOTH)
        # self.tree.grid()

        self.tree.bind("<Button-3>", do_popup)

        win2.minsize(50, 50)

    def selection(self):
        print
        self.popup.selection

    def multiFiles(self):

        # ftypes = [('txt files')]
        # filez = askopenfilenames(parent=self.parent, filetypes=ftypes, title='Choose a file')
        # if len(filez) < 2:
        #     mBox.showinfo("Monitor Error", "Selected less than two files!\n\nPlease select at least two files!")
        # else:
        #     result_matrix = generate_report_from_list(filez)
        #     self.ChildWindow(filez, result_matrix)
        path = askdirectory()
        dirs = os.listdir(path)
        result_matrix = self.cal_acc(path, dirs)
        self.ChildWindow(dirs, result_matrix)

    def cal_acc(self, path, dirs):
        matrix = []
        files = []
        for _, _ , file in os.walk(path + os.sep + dirs[0]):
            for f in file:
                files.append(f)
        for i, dir1 in enumerate(dirs):
            matrix.append([])
            for j, dir2 in enumerate(dirs):
                types1 = []
                types2 = []
                if (i == j):
                    matrix[-1].append('/')
                    continue
                for file in files:
                    t1 = self.get_labels(path + os.sep + dir1 + os.sep + file)
                    t2 = self.get_labels(path + os.sep + dir2 + os.sep + file)
                    types1.extend(t1)
                    types2.extend(t2)
                l = len(types1)
                corr = 0
                for k in range(l):
                    if types1[k] == types2[k]:
                        corr += 1
                matrix[-1].append(int(float(corr) / l * 1000) / 10.0)

        return matrix

    def compareTwoFiles(self):
        ftypes = [('txt files', '.txt')]
        filez = askopenfilenames(parent=self.parent, filetypes=ftypes, title='Choose a file')
        if len(filez) != 2:
            mBox.showinfo("Compare Error", "Please select exactly two files!")
        else:
            t1 = self.get_labels(filez[0])
            t2 = self.get_labels(filez[1])
            correct = 0
            total = len(t1)
            for i in range(total):
                if t1[i] == t2[i]:
                    correct += 1
            mBox.showinfo("accuracy", str(int(float(correct)/total*1000+0.5) / 10))
            #print("accuracy: %.2f" % (float(correct)/total))

    def get_labels(self, file):
        flag = 0
        tt = []
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                if flag:
                    tt.append(line.strip().split('\t')[-1])
                if line.strip() == '%%TYPE_ANNOTATIONS%%':
                    flag = 1
                    continue
        return tt

def main():
    print("SUTDAnnotator launched!")
    print(("OS:%s") % (platform.system()))
    root = Tk()
    root.geometry("400x100")
    app = Example(root)

    root.mainloop()


if __name__ == '__main__':
    main()