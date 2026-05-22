import os
import re
import fire
from tkinter import *
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
w = tk.Tk()
w.title("导入界面")
w.geometry("600x500")
def info():
    messagebox.showinfo("提醒","导入成功!")
    w.destroy()
def but1():
    folder_selecte = filedialog.askdirectory()
    files = os.path.normpath(folder_selecte)
    return files
y1 = tk.Button(w,text='File_path',width=10,height=2,command=but1)
y1.place(x=250,y=200)
File_path = but1()
y2 = tk.Label(w,text='File path',width= 25,height=2)
y2.place(x=50,y=190)
y3 = tk.Entry(w,width=30)
y3.place(x=250,y=250)
y4 = tk.Label(w,text='API',width= 25,height=2)
y4.place(x=50,y=240)
API = y3.get()
b2 = tk.Button(w,text='API',width=10,height=2,command=info)
b2.place(x=250,y=300)
w.mainloop()
import Core_code_reading,Code_structure_reading,Interface_code_reading
def main():

    msg1 = Code_structure_reading.main()
    msg2 = Interface_code_reading.main()
    msg3 = Core_code_reading.main()
    print (msg1)
    print (msg2)
    print (msg3)
 
if __name__ == '__main__':
    fire.Fire(main)