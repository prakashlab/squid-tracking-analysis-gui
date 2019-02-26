# -*- coding: utf-8 -*-
"""
Created on Sun Sep 16 20:36:28 2018

@author: Francois & Deepak
"""

import numpy as np
from pyqtgraph.Qt import QtWidgets,QtCore, QtGui
import pyqtgraph as pg
import cv2 as cv2
import time as time
import os


font = cv2.FONT_HERSHEY_SIMPLEX

'''
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#                         Image_Widget
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
''' 
   
class ImageWidget(pg.GraphicsLayoutWidget):
    
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.view=self.addViewBox()
        
        ## lock the aspect ratio so pixels are always square
        self.view.setAspectLocked(True)
        
        ## Create image item
        self.img=pg.ImageItem(border='w')
        self.view.addItem(self.img)
        
    def refresh_image(self, image_bgr):      
        image_gray=cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        image_gray=cv2.rotate(image_gray,cv2.ROTATE_90_CLOCKWISE) #pgItem display the image with 90° anticlockwise rotation
        
        clahe = cv2.createCLAHE(clipLimit=4, tileGridSize=(12,12))
                
        image_gray = clahe.apply(image_gray)
        
        self.img.setImage(image_gray)
        
        
'''
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#                            Video_widget
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
'''         

class VideoWindow(QtWidgets.QWidget):
    
    update_plot=QtCore.pyqtSignal(float)
    update_3Dplot=QtCore.pyqtSignal(float)
    imageName=QtCore.pyqtSignal(str)
    record_signal=QtCore.pyqtSignal(bool)
    image_to_record=QtCore.pyqtSignal(np.ndarray, str)
    
    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)

        #Video parameters
        self.image_directory=''
        # Dictionary containing the subfolder address of all images
        self.image_dict = {}
        self.Time_Image=np.array([])
        self.Image_Names=[]
        self.Image_Time = []
        
        self.timer=QtCore.QTimer()
        self.timer.setInterval(0) #in ms
        self.timer.timeout.connect(self.play_refresh)
        self.current_track_time=0
        self.current_computer_time=0
        
        self.current_track_index = 0        # Add image index
        self.prev_track_index = 0    
         
        self.isRecording=False
        
        # No:of frames to advance for recording purposes
        self.frames = 20
        #Gui Component
        
        self.image_widget=ImageWidget()
        
        self.playButton = QtGui.QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setCheckable(True)
        self.playButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)
        
        self.recordButton = QtGui.QPushButton()
        self.recordButton.setEnabled(False)
        self.recordButton.setCheckable(True)
        self.recordButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogYesButton))
        self.recordButton.clicked.connect(self.record)

        self.positionSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.setEnabled(False)
        self.positionSlider_prevValue=0
        
        self.positionSpinBox=QtGui.QDoubleSpinBox()
        self.positionSpinBox.setRange(0, 0)
        self.positionSpinBox.setSingleStep(0.01)
        self.positionSpinBox.setEnabled(False)
        self.positionSpinBox_prevValue=0
        
        self.positionSlider.valueChanged.connect(self.positionSpinBox_setValue)
        self.positionSpinBox.valueChanged.connect(self.positionSlider_setValue)

        # Create layouts to place inside widget
        controlLayout = QtGui.QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)
        controlLayout.addWidget(self.positionSpinBox)
        controlLayout.addWidget(self.recordButton)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.image_widget)
        layout.addLayout(controlLayout)


        self.setLayout(layout)
        
    def refreshImage(self,image_name):
        # Changed so that it can handle images being split among multiple sub-directories.
        file_directory= os.path.join(self.image_directory, self.image_dict[image_name],image_name)

        print(file_directory)

        image=cv2.imread(file_directory)
        
        if(len(self.Image_Time) is not 0):
            currTime = self.Image_Time[self.current_track_index]
            print('Current Image Time: {}'.format(currTime))
            cv2.putText(image, str(np.round(currTime, decimals = 2))+'s', (30, 30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

        self.image_widget.refresh_image(image)
        self.imageName.emit(image_name)
        if self.isRecording:
            print('Current Image : {}'.format(image_name))
            self.image_to_record.emit(image, image_name)
        
    def initialize_directory(self,directory, image_dict):
        # Making this more robust by passing the actual folder name containing images instead of assuming they are in /images/

        # This is the root directory containing the dataset
        self.image_directory=directory

        # This is the dictionary which contains the subdirectory address for all images.
        self.image_dict = image_dict

       
#    def initialize_image_index(self,image_index):   # Add image index
#        self.Image_Index = image_index
        
    def initialize_image_names(self,image_names):
        self.Image_Names=image_names
        if len(self.Image_Names)>0:
            self.refreshImage(self.Image_Names[0])
        
    def initialize_image_time(self,image_time):
        self.Image_Time=image_time
        self.positionSlider.setRange(0,len(self.Image_Time)-1)
        self.positionSlider.setEnabled(True)
        self.positionSpinBox.setRange(self.Image_Time[0],self.Image_Time[-1])
        self.positionSpinBox.setEnabled(True)
        
    def initialize_parameters(self):
        if self.playButton.isChecked():
            self.playButton.setChecked(False)
            self.timer.stop()
            self.positionSlider.setEnabled(True)
            self.positionSpinBox.setEnabled(True)
            
        self.current_track_index = 0
        self.current_track_time=0
        self.current_computer_time=0
        self.positionSlider.setValue(0)
        self.positionSpinBox_prevValue=0
        self.positionSlider_prevValue=0
        
    def positionSpinBox_setValue(self,value):
        newvalue=self.Image_Time[value]
        self.positionSpinBox.setValue(newvalue)
        self.positionSlider_prevValue=value
        
    def positionSlider_setValue(self,value):
        newvalue, hasToChange=self.find_slider_index(value)
       
        self.current_track_index = newvalue
        if hasToChange:
            self.positionSlider.setValue(newvalue)
            self.positionSpinBox.setValue(self.Image_Time[newvalue])
            self.positionSpinBox_prevValue=self.Image_Time[newvalue]
            
#            self.prev_track_index = newvalue
#            self.prev_track_index = self.Image_Index[newvalue]
            
            self.positionSlider_prevValue=newvalue
            self.refreshImage(self.Image_Names[newvalue])
            self.update_plot.emit(self.Image_Time[newvalue])
            self.update_3Dplot.emit(self.Image_Time[newvalue])
            
            
            
            
    def find_slider_index(self,value):
        #
        index=0
        found=False
        hasToChange=True
        
        if self.positionSpinBox_prevValue<value: 
            for i in range(0,len(self.Image_Time)):
                if self.Image_Time[i]-value>=0 and not(found):
                    index=i
                    found=True
            if not(found):
                index=len(self.Image_Time)-1
                
        elif self.positionSpinBox_prevValue>value:
            for i in range(len(self.Image_Time)-1,-1,-1):
                if self.Image_Time[i]-value<=0 and not(found):
                    index=i
                    found=True
            if not(found):
                index=0
        else:
            hasToChange=False
            
        return index,hasToChange
                

            
    def play(self):
        if self.playButton.isChecked():
            self.current_computer_time = time.time()
            self.current_track_time = self.positionSpinBox_prevValue
            # Set the prev index to the current index
            self.prev_track_index = self.current_track_index
            self.timer.start(0)
            self.positionSlider.setEnabled(False)
            self.positionSpinBox.setEnabled(False)
        else:
            self.timer.stop()
            self.positionSlider.setEnabled(True)
            self.positionSpinBox.setEnabled(True)
            
    
    def play_refresh(self):
        timediff=time.time()-self.current_computer_time
        
        index=np.argmin(abs(self.Image_Time-(timediff+self.current_track_time)))
        if index>self.positionSlider_prevValue:
            self.current_computer_time+=timediff
            self.current_track_time+=timediff
            self.positionSlider.setValue(index)
            
    # Implementing a new play function where images are played sequentially and not according to a time difference.        
#    def play_refresh(self):
##        timediff=time.time()-self.current_computer_time
#        
#        
#        self.current_track_index = self.prev_track_index + self.frames
#        
#        self.positionSlider.setValue(self.current_track_index)
#        
#        self.prev_track_index = self.current_track_index
#        
#        
#        
#        index = self.prevIndex + 1
#        index=np.argmin(abs(self.Image_Time-(timediff+self.current_track_time)))
#        if index>self.positionSlider_prevValue:
#            self.current_computer_time+=timediff
#            self.current_track_time+=timediff
#            self.positionSlider.setValue(index)
            
            
            
    def record(self):
        self.isRecording=self.recordButton.isChecked()
        self.record_signal.emit(self.isRecording)
        print('start-recording-signal')
            