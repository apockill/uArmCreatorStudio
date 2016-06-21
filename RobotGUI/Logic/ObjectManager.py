import os
import cv2          # For image saving
import numpy as np  # For np array saving
import errno
import json
from collections           import namedtuple
from RobotGUI.Logic.Global import printf


def ensurePathExists(path):
    '''
        This is a cross platform, race-condition free way of checking if a directory exists. It's used every time
        an object is loaded and saved
    '''

    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


class ObjectManager:
    """
    Objects are immutable: This means that any object cannot be changed. If you attempt to add an object that already
    exists, it will replace the old object and overwrite the save file.

    This is a platform for storing "Heavy" objects that will be used in the program. ie, image recognition
    files, anything that can't be stored in plaintext in the scriptfile that won't change during the program should
    be here. It can load and save objects in a special uObject class that might have derivatives of types:
        uVisionObject       Might contain pictures, image maps, huge arrays with keypoints, who knows.
        uMotionPathObject   Might contain long lists of moves, speeds, or even mathematical functions for the bot to
                            follow.
        uScriptObject       Might contain a whole other script within it that would be able to run entirely within
                            the program and spawn its own environment and interpreter.

    All loading, adding replacing, and saving of objects should be done through this class
    """


    def __init__(self):
        self.__objects = []  # A list of the loaded objects
        self.__directory = None

    def setDirectory(self, filename):
        # Set the directory that this object will use to load and save files in
        self.__directory = filename
        ensurePathExists(self.__directory)


    def loadAllObjects(self):
        # Load all objects into the environment

        # Checks if an interpreter is currently running before doing anything.
        foldersAndItems = os.listdir(self.__directory)


        newTrackable = lambda folder, directory: TrackableObject(folder.replace("TrackerObject ", ""), directory)
        for folder in foldersAndItems:
            path = self.__directory + "\\" + folder

            # Handle any TrackableObject loading
            if "TrackerObject" in folder and os.path.isdir(path):
                newObj = newTrackable(folder, path)
                if newObj.loadSuccess:
                    self.__addObject(newObj)


        # files = []
        # for (dirpath, dirnames, filenames) in os.walk(self.__directory):
        #     print('path', dirpath)
        #     print('names', dirnames)
        #
        #     print('files', filenames)

    def saveNewObject(self, newObject):
        # If not new, replace self
        wasNew = self.__addObject(newObject)
        if not wasNew:
            printf("ObjectManager.saveNewObject(): Tried to add object that already existed, ", newObject.name)
            return

        newObject.save(self.__directory)



    def getObject(self, objectID):
        # Ask for an object by name, and get the object class. If it's nonexistent, return None
        for obj in self.__objects:
            if obj.name == objectID: return obj

        return None

    def getObjectIDList(self, objectType=None):
        # Returns a list of object names. This is used in ObjectManager, or any situation when you need to know if a
        # particular object is loaded. If objectType is not None, then only return objects of that type

        nameList = []
        for obj in self.__objects:
            if objectType is None or objectType is type(obj):
                nameList.append(obj.name)

        return nameList


    def __addObject(self, newObject):
        # The reason this is private is because objects should only be added through self.saveNewObject or loadAllObj's


        # Checks if the object already exists. If it does, then replace the existing object with the new one.
        for obj in self.__objects:
            if newObject.name == obj.name:
                printf("Environment.addObject(): ERROR: Tried adding an object that already existed")
                return False


        # If the object doesn't already exist, adds the object to the pool of loaded objects.
        self.__objects.append(newObject)
        return True

    def deleteObject(self, objectID):
        printf("ObjectManager.deleteObject(): Deleting ", objectID, " permanently")

        for obj in self.__objects:
            if objectID == obj.name:
                # Make sure nothing weird is going on...
                if obj.directory is None:
                    return False

                # Get all the items in the objects folder, and delete them one by one
                foldersAndItems = os.listdir(obj.directory)
                for item in foldersAndItems:
                    os.remove(obj.directory + "\\" + item)

                # Now that the folder is empty, delete it too
                os.rmdir(obj.directory)

                self.__objects.remove(obj)
                return True

        printf("ObjectManager.deleteObject(): ERROR: Could not find object ", objectID, " in order to delete it!")
        return False


class TrackableObject:
    Sample = namedtuple(  'Sample',   'name, image, rect, pickupRect')

    def __init__(self, name, loadFromDirectory = None):
        """
        Name: A String of the objects unique name. It must be unique for file saving purposes.

        "Samples" is a list [sample, sample, sample] of samples.
        A Sample is a dictionary that looks like this:
                {   'image': cv2Frame,
                    'rect': (x1,y1,x2,y2),
                    'pickupRect': (x1,y1,x2,y2),
                    'keypoints': np arr of keypoints of the object,
                    'descrs': np array of the descriptors of the object
                }

        Samples are used to record objects at different orientations and help aid tracking in that way.
        """

        self.name        = name
        self.samples     = []
        self.directory   = loadFromDirectory  # Used in objectmanager for deleting object. Set here, or in self.save
        self.loadSuccess = False

        if loadFromDirectory is not None:
            self.loadSuccess = self.__load(loadFromDirectory)

    def save(self, directory):
        """
        Everything goes into a folder called TrackableObject_OBJECTNAMEHERE

        Saves images for each sample, with the format Sample_#,
        and a data.txt folder is saved as a json, with this structure:
        {
            "Sample_1": {
                            "rect": (0, 0, 10, 10),
                            "pickupRect": (0, 0, 10, 10),
                        },

            "Sample_2": {
                            "rect": (0, 0, 10, 10),
                            "pickupRect": (0, 0, 10, 10),
                        },
        }
        """

        printf("TrackableObject.save(): Saving self to directory ", directory)
        # Make sure the "objects" directory exists
        filename                    =  directory  + "\\" + "TrackerObject " + self.name
        self.directory              = filename
        ensurePathExists(filename)
        filename += "\\"


        dataJson = {}
        # Save images and numpy arrays as seperate folders
        for index, sample in enumerate(self.samples):
            # Save the image
            cv2.imwrite(filename + "Sample_" + str(index) + "_Image.png", sample.image)

            # Add any sample data to the dataJson
            dataJson["Sample_" + str(index)] = {"rect":       sample.rect,
                                                "pickupRect": sample.pickupRect}

        json.dump(dataJson, open(filename + "data.txt", 'w'), sort_keys=False, indent=3, separators=(',', ': '))




    def __load(self, directory):
        # Should only be called during initialization

        # Check if the directory exists (just in case)
        if not os.path.isdir(directory):
            printf("TrackableObject.__load(): ERROR: Could not find directory", directory)
            return False


        # Try to load the data.txt json
        dataFile = directory + "\data.txt"
        try:
            loadedData = json.load( open(dataFile))

        except IOError:
            printf("TrackableObject.__load() ERROR: Data file ", dataFile, " was not found!")
            return False


        # For each sample, load the image associated with it, and build the appropriate sample
        for key in loadedData:
            imageFile = directory + '\\' + key + "_Image.png"
            image     = cv2.imread(imageFile)

            if image is None:
                printf("TrackableObject.__load() ERROR: Image File", imageFile, " was unable to be loaded!")
                return False

            sample = self.Sample(name=self.name, image=image, rect=loadedData[key]["rect"],
                                 pickupRect=loadedData[key]["pickupRect"])

            self.addSample(sample)

        return True

    def addSample(self, sample):
        newSample = self.Sample(name=self.name, image=sample.image, rect=sample.rect, pickupRect=sample.pickupRect)
        self.samples.append(newSample)

    def getSamples(self):
        return self.samples

    def getIcon(self, maxWidth, maxHeight):
        # Create an icon of a cropped image of the 1st sample, and resize it to the parameters.


        #  Get the cropped image of just the object
        fullImage = self.samples[0].image
        rect      = self.samples[0].rect
        image     = fullImage[rect[1]:rect[3], rect[0]:rect[2]]



        #  Resize it to fit within maxWidth and maxHeight
        height, width, _ = image.shape
        if height > maxHeight:
            image = cv2.resize(image, (int(float(maxHeight)/height*width), maxHeight))

        height, width, _ = image.shape
        if width > maxWidth:
            image = cv2.resize(image, (maxWidth, int(float(maxWidth)/width*height)))

        height, width, _ = image.shape

        return image.copy()






