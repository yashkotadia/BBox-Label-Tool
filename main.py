#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      Qiushi
# Created:     06/06/2014

#
#-------------------------------------------------------------------------------
from __future__ import division
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import glob
import random

LABEL = {
    'car': 0,
    'truck': 1,
    'bus': 2,
    'rickshaw': 3,
    'motorcycle': 4,
    'person': 5,
    'helmet': 6
}

COLOR = ['red', 'blue', 'yellow', 'pink', 'cyan', 'brown', 'green']

# image sizes for the examples
SIZE = 256, 256

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None
        self.label = None
        self.highlight = []

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None
        self.groupList = []

        # ----------------- GUI stuff ---------------------
        """# dir entry & load
                                self.dirLabel = Label(self.frame, text = "Image Dir:")
                                self.dirLabel.grid(row = 0, column = 0, sticky = E)
                                self.entry = Entry(self.frame)
                                self.entry.grid(row = 0, column = 1, sticky = W+E)
                                self.ldBtn = Button(self.frame, text = "Load", command = self.loadDir)
                                self.ldBtn.grid(row = 0, column = 2, sticky = W+E)"""

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("a", self.prevImage) # press 'a' to go backforward
        self.parent.bind("d", self.nextImage) # press 'd' to go forward
        self.mainPanel.grid(row = 0, column = 1, rowspan = 4, sticky = W+N, pady=25, padx=10)

        # showing bbox info & delete bbox
        self.boxPanel = Frame(self.frame)
        self.boxPanel.grid(row = 0, column = 2, sticky = W+E, pady=20)
        self.lb1 = Label(self.boxPanel, text = 'Bounding boxes:')
        self.lb1.pack()
        self.listbox = Listbox(self.boxPanel, width = 30, height = 12, selectmode=EXTENDED)
        self.listbox.pack(fill=X)
        self.listbox.bind("<ButtonRelease-1>", self.highlightBox)
        self.listbox.bind("<KeyRelease-Up>", self.highlightBox)
        self.listbox.bind("<KeyRelease-Down>", self.highlightBox)
        self.btnDel = Button(self.boxPanel, text = 'Delete', command = self.delBBox)
        self.btnDel.pack(fill=X)
        self.btnClear = Button(self.boxPanel, text = 'ClearAll', command = self.clearBBox)
        self.btnClear.pack(fill=X)

        # grouping
        self.groupPanel = Frame(self.frame)
        self.groupPanel.grid(row = 1, column = 2, sticky = W+E, pady=20)
        self.lb2 = Label(self.groupPanel, text = 'Grouping:')
        self.lb2.pack()
        self.btnGroupSelection = Button(self.groupPanel, text = 'Add Group', command = self.addGroup)
        self.btnGroupSelection.pack(fill=X)
        self.groupListbox = Listbox(self.groupPanel, width = 30, height = 5, selectmode=SINGLE)
        self.groupListbox.pack(fill=X)
        self.groupListbox.bind("<ButtonRelease-1>", self.highlightGroup)
        self.groupListbox.bind("<KeyRelease-Up>", self.highlightGroup)
        self.groupListbox.bind("<KeyRelease-Down>", self.highlightGroup)
        self.btnDelGroup = Button(self.groupPanel, text = 'Delete', command = self.delGroup)
        self.btnDelGroup.pack(fill=X)
        #self.btnClearGroup = Button(self.groupPanel, text = 'ClearAll', command = self.clearBBox)
        #self.btnClearGroup.pack(fill=X)

        # selecting the current labelling class
        self.classPanel = Frame(self.frame)
        self.classPanel.grid(row = 2, column = 2, sticky = W+E, pady=20)
        self.lb3 = Label(self.classPanel, text = 'Classes:')
        self.lb3.pack()
        self.btnCar = Button(self.classPanel, text = 'Car/गाडी', command = self.selectCar, bg=COLOR[LABEL['car']])
        self.btnCar.pack(fill=X)
        self.btnTruck = Button(self.classPanel, text = 'Truck/ट्रक', command = self.selectTruck, bg=COLOR[LABEL['truck']])
        self.btnTruck.pack(fill=X)
        self.btnBus = Button(self.classPanel, text = 'Bus/बस', command = self.selectBus, bg=COLOR[LABEL['bus']])
        self.btnBus.pack(fill=X)
        self.btnRickshaw = Button(self.classPanel, text = 'Rickshaw/रिक्शा', command = self.selectRickshaw, bg=COLOR[LABEL['rickshaw']])
        self.btnRickshaw.pack(fill=X)
        self.btnMotorcycle = Button(self.classPanel, text = 'Motorcycle/मोटरसाइकिल', command = self.selectMotorcycle, bg=COLOR[LABEL['motorcycle']])
        self.btnMotorcycle.pack(fill=X)
        self.btnPerson = Button(self.classPanel, text = 'Person/आदमी', command = self.selectPerson, bg=COLOR[LABEL['person']])
        self.btnPerson.pack(fill=X)
        self.btnHelmet = Button(self.classPanel, text = 'Helmet/हेलमेट', command = self.selectHelmet, bg=COLOR[LABEL['helmet']])
        self.btnHelmet.pack(fill=X,)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 2, column = 1, columnspan = 1, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        """
        # example pannel for illustration
        self.egPanel = Frame(self.frame, border = 10)
        self.egPanel.grid(row = 1, column = 0, rowspan = 5, sticky = N)
        self.tmpLabel2 = Label(self.egPanel, text = "Examples:")
        self.tmpLabel2.pack(side = TOP, pady = 5)
        self.egLabels = []
        for i in range(3):
            self.egLabels.append(Label(self.egPanel))
            self.egLabels[-1].pack(side = TOP)
        """


        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)
        
        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(3, weight = 1)
        
        self.loadDir()

        # for debugging
##        self.setImage()
##        self.loadDir()

    def loadDir(self, dbg = False):
        if not dbg:
            self.parent.focus()
        else:
            return
        
        # get image list
        self.imageDir = os.path.join(r'./Images')
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        if len(self.imageList) == 0:
            print('No .JPG images found in the specified dir!')
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

         # set up output dir
        self.outDir = os.path.join(r'./Labels')
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        """
        # load example bboxes
        self.egDir = os.path.join(r'./Examples', '%03d' %(self.category))
        if not os.path.exists(self.egDir):
            return
        filelist = glob.glob(os.path.join(self.egDir, '*.JPEG'))
        self.tmp = []
        self.egList = []
        random.shuffle(filelist)
        for (i, f) in enumerate(filelist):
            if i == 3:
                break
            im = Image.open(f)
            r = min(SIZE[0] / im.size[0], SIZE[1] / im.size[1])
            new_size = int(r * im.size[0]), int(r * im.size[1])
            self.tmp.append(im.resize(new_size, Image.ANTIALIAS))
            self.egList.append(ImageTk.PhotoImage(self.tmp[-1]))
            self.egLabels[i].config(image = self.egList[-1], width = SIZE[0], height = SIZE[1])
        """

        self.loadImage()
        print('%d images loaded' %(self.total))

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        size = self.img.size
        self.factor = max(size[0]/1000, size[1]/1000., 1.)
        self.img = self.img.resize((int(size[0]/self.factor) , int(size[1]/self.factor)))
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))

        # load labels
        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        bbox_cnt = int(line.strip())
                        continue

                    elif i <= bbox_cnt:
                        tmp = [int(t.strip()) for t in line.split()]                 
                        tmp[1] = int(int(tmp[1])/self.factor)
                        tmp[2] = int(int(tmp[2])/self.factor)
                        tmp[3] = int(int(tmp[3])/self.factor)
                        tmp[4] = int(int(tmp[4])/self.factor)

                        self.bboxList.append(tuple(tmp))

                        tmp[0] = [ key for key in LABEL if LABEL[key]==tmp[0]][0]

                        tmpId = self.mainPanel.create_rectangle(tmp[1], tmp[2], \
                                                                tmp[3], tmp[4], \
                                                                width = 2, \
                                                                outline = COLOR[LABEL[tmp[0]]])
                        self.bboxIdList.append(tmpId)
                        self.listbox.insert(END, '%d. %s: (%d, %d) -> (%d, %d)' %(self.listbox.size() ,tmp[0], tmp[1], tmp[2], tmp[3], tmp[4]))
                        self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLOR[LABEL[tmp[0]]])
                        continue

                    elif i == bbox_cnt+1:
                        group_cnt = int(line.strip())
                        continue

                    else:
                        group = [int(t.strip()) for t in line.split()]
                        self.groupList.append(group)
                        self.groupListbox.insert(END, group)

        self.writeText()

    def saveImage(self):
        with open(self.labelfilename, 'w') as f:
            f.write('%d\n' %len(self.bboxList))
            for bbox in self.bboxList:
                f.write("{} {} {} {} {}\n".format(bbox[0], int(int(bbox[1])*self.factor), int(int(bbox[2])*self.factor), int(int(bbox[3])*self.factor), int(int(bbox[4])*self.factor)))
            f.write('%d\n' %len(self.groupList))
            for group in self.groupList:
                f.write(' '.join(map(str, group)) + '\n')
        print('Image No. %s saved' %(self.labelfilename))


    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            self.bboxList.append(( LABEL[self.label] ,x1, y1, x2, y2))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '%d. %s: (%d, %d) -> (%d, %d)' %(self.listbox.size() ,self.label, x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLOR[LABEL[self.label]])
            self.writeText()
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                            event.x, event.y, \
                                                            width = 2, \
                                                            outline = COLOR[LABEL[self.label]])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return

        idx = int(sel[0])

        self.updateGroupList(idx)
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx, END)
        self.mainPanel.delete(self.highlight)

        # Delete the texts which fall after the selected BBox
        self.mainPanel.delete('text')

        for b in self.bboxList[idx:]:
            i = self.bboxList.index(b)
            self.listbox.insert(END, '%d. %s: (%d, %d) -> (%d, %d)' %(i, self.findKey(b[0]), b[1], b[2], b[3], b[4]))
            self.listbox.itemconfig(self.listbox.size() - 1, fg = COLOR[b[0]])

        self.writeText()


    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.groupListbox.delete(0, len(self.groupList))
        self.groupList = []
        self.bboxIdList = []
        self.bboxList = []
        self.writeText()
        self.mainPanel.delete('high')

    def addGroup(self):
        selList = list(self.listbox.curselection())

        selClasses = [self.bboxList[sel][0] for sel in selList]

        if selClasses.count(LABEL['person']) > 5 or selClasses.count(LABEL['person']) < 1:
            messagebox.showwarning('', 'Select 1-5 persons only')
            return
        if selClasses.count(LABEL['motorcycle'])!=1:
            messagebox.showwarning('','Select 1 and only 1 motorcycle')
            return

        groupMembers = sum(self.groupList, [])
        if any(member in selList for member in groupMembers):
            messagebox.showwarning('','The group members must be unique')
            return

        self.groupList.append(selList)
        self.groupListbox.insert(END, selList)


    def selectCar(self): self.label = 'car'
    def selectMotorcycle(self): self.label = 'motorcycle'
    def selectTruck(self): self.label = 'truck'
    def selectBus(self): self.label = 'bus'
    def selectRickshaw(self): self.label = 'rickshaw'
    def selectPerson(self): self.label = 'person'
    def selectHelmet(self): self.label = 'helmet'

    def highlightBox(self, event):
        # Retireve the selection list of bounding boxes
        sel = self.listbox.curselection()

        self.mainPanel.delete('high')

        self.highlight = []

        # Stop if no item is selected
        if len(sel)<1: return

        for idx in sel:
            tmp = self.bboxList[idx]
            self.highlight.append(self.mainPanel.create_rectangle(tmp[1], tmp[2], \
                                                    tmp[3], tmp[4], \
                                                    width = 4, tag = 'high', \
                                                    outline = 'white'))

    def highlightGroup(self, event):
        # Retireve the selection list of bounding boxes
        sel = self.groupListbox.curselection()
        sel = self.groupListbox.get(sel)

        self.mainPanel.delete('high')

        self.highlight = []

        # Stop if no item is selected
        if len(sel)<1: return

        for idx in sel:
            tmp = self.bboxList[idx]
            self.highlight.append(self.mainPanel.create_rectangle(tmp[1], tmp[2], \
                                                    tmp[3], tmp[4], \
                                                    width = 4, tag = 'high',\
                                                    outline = 'white'))

    def updateGroupList(self, sel):

        self.groupListbox.delete(0,len(self.groupList))

        for i, group in enumerate(self.groupList):
            for j, member in enumerate(group):
                if sel==member:
                    self.groupList.pop(i)
                if member>sel:
                    self.groupList[i][j] = member-1

        for group in self.groupList:
            self.groupListbox.insert(END, group)

    def delGroup(self):
        sel = self.groupListbox.curselection()
        self.groupListbox.delete(sel)
        self.mainPanel.delete('high')

    def prevImage(self, event = None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

    def findKey(self, x):
        for name in LABEL:    # for name, age in list.items():  (for Python 3.x)
            if LABEL[name] == x:
                return name

    def writeText(self):
        self.mainPanel.delete('text')
        for i, entry in enumerate(self.listbox.get(0,END)):
            x = self.bboxList[i][1]
            y = self.bboxList[i][2]
            self.mainPanel.create_text(x, y, text=i , anchor=SW, fill='white', tag='text')


if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width =  True, height = True)
    root.mainloop()
