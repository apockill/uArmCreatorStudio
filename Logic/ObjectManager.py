import json
import os
import sys   # For getting size of oan object
import cv2   # For image saving
import numpy as np
from Logic        import Paths
from collections  import namedtuple
from Logic.Global import printf, ensurePathExists


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
        directory = Paths.objects_dir
        ensurePathExists(directory)

        self.__directory = directory
        self.__objects   = []  # A list of the loaded objects


        # Set different filters that can be used in self.getObjectIDList(objFilter=[One of the following])
        self.TRACKABLE      = Trackable
        self.TRACKABLEOBJ   = TrackableObject
        self.TRACKABLEGROUP = TrackableGroupObject
        self.PICKUP         = "PICKUP"        # Any trackable object + group, NOT incuding the Robot Marker object
        self.MOTIONPATH     = MotionPath

    def loadAllObjects(self):
        # Load all objects into the ObjectManager

        foldersAndItems = os.listdir(self.__directory)



        for folder in foldersAndItems:
            path = self.__directory + "\\" + folder
            newObj    = None
            createObj = lambda objType, prefix, directory: objType(folder.replace(prefix + " ", ""), path)

            if not os.path.isdir(path):
                printf("ERROR: Could not find directory ", path)
                continue


            # Handle any TrackableObject loading
            if "Trackable"  in folder: newObj = createObj(TrackableObject, "Trackable", folder)
            if "MotionPath" in folder: newObj = createObj(MotionPath, "MotionPath", folder)

            # Check that loading is complete and add the object if it was created successfully
            if newObj is None:
                printf("ERROR: Could not find relevant object for folder: ", folder)
                continue

            if newObj.loadSuccess: self.__addObject(newObj)

        self.refreshGroups()

    def saveObject(self, newObject):
        # If not new, replace self
        wasNew = self.__addObject(newObject)
        if not wasNew:
            printf("Tried to add object that already existed, ", newObject.name)

        newObject.save(self.__getDirectory(newObject))

    def refreshGroups(self):
        # Creates a TrackableGroup for every uniqe tag every object has, and replaces old TrackableGroups
        printf("Refreshing Groups!")

        # Remove existing groups from self.__objects
        for obj in self.__objects[:]:
            # Since multiple objects are being deleted in the same array, use [:] to copy it so it doesnt change size
            if isinstance(obj, TrackableGroupObject):
                printf("Removing ", obj.name, " from self.__objects")
                self.__objects.remove(obj)

        # Use a temporary dictionary to record which objs belong to which groups
        groups = {}  # Example: {"tag": [obj, obj, obj], "tag2":[obj]}

        # Go through all objects and record which objects belong in which groups
        for obj in self.__objects:
            # Only TrackableObjects can be in TrackableGroups
            if not isinstance(obj, TrackableObject): continue

            tags = obj.getTags()

            for tag in tags:
                # Make sure groups has the appropriate keys with arrays for each tag
                if not tag in groups: groups[tag] = []

                # Add the object to each tag
                groups[tag].append(obj)  # Change to be "obj"


        # Create the TrackableGroup objects and add them
        for group in groups:
            printf("Adding group ", group)
            newGroupObj = TrackableGroupObject(name=group, members=groups[group])
            self.__addObject(newGroupObj)


    def getObject(self, objectID):
        # Ask for an object by name, and get the object class. If it's nonexistent, return None
        for obj in self.__objects:
            if obj.name == objectID: return obj

        return None

    def getObjectNameList(self, objFilter=None):
        # Returns a list of object names. This is used in ObjectManager, or any situation when you need to know if a
        # particular object is loaded. If objFilter is not None, then only return objects of that type

        """
        Notes for Future Me:
            type(obj) == TrackableObject               # Works
            isinstance(trackable, TrackableObject)  # Works
            issubclass(type(trackable), Trackable)        # Works

        """

        # Returns true if 'obj' is of any type inside of typeList
        isType = lambda obj, typeList: any(isinstance(obj, t) for t in typeList)

        nameList = []
        for obj in self.__objects:
            # If the user just wants a list of every object
            if objFilter is None:
                nameList.append(obj.name)
                continue

            # If object is capable of being picked up by the robot with any pickup function
            if objFilter == self.PICKUP:
                if obj.name == "Robot Marker": continue
                if isType(obj, (TrackableObject, TrackableGroupObject)):
                    nameList.append(obj.name)
                continue

            # A catch-all filter for filtering by "Type"
            if isinstance(obj, objFilter):
                nameList.append(obj.name)
                continue

        return nameList

    def getForbiddenNames(self):
        # Returns a list of strings that the user cannot use as the name of an object.
        # This includes names of objects, names of tags, and names of objects like "Robot Marker" that are reserved
        # It also includes things like "Trackable" or "TrackableObject" for good measure
        forbidden = self.getObjectNameList()
        forbidden += ['Trackable', 'Robot Marker', "Trackable", "TrackableGroup", "Face"]
        return forbidden


    def __addObject(self, newObject):
        # The reason this is private is because objects should only be added through self.saveNewObject or loadAllObj's

        # Checks if the object already exists. If it does, then replace the existing object with the new one.
        for obj in self.__objects:
            if newObject.name == obj.name:
                printf("ERROR: Tried adding an object that already existed: ", obj.name)
                return False


        # If the object doesn't already exist, adds the object to the pool of loaded objects.
        self.__objects.append(newObject)


        # Sort in alphabetical order, by name, for simplicity in GUI functions that display objects
        self.__objects = sorted(self.__objects, key=lambda obj: obj.name)
        return True

    def __getDirectory(self, object):
        # Creates the directory name for the object with the propper formatting
        directory = self.__directory
        if isinstance(object, TrackableObject):
            directory += "Trackable"

        if isinstance(object, MotionPath):
            directory += "MotionPath"

        directory += " " + object.name + "\\"
        return directory


    def deleteObject(self, objectID):
        printf("Deleting ", objectID, " permanently")

        for obj in self.__objects:
            if not objectID == obj.name: continue


            # If the object is a Resource, then deleete the directory
            if issubclass(type(obj), Resource) and not isinstance(obj, TrackableGroupObject):
                # Get all the items in the objects folder, and delete them one by one
                objDirectory = self.__getDirectory(obj)
                # foldersAndItems = os.listdir(objDirectory)

                # Make sure everything is deleted in the directory
                while len(os.listdir(objDirectory)):
                    for item in os.listdir(objDirectory):
                        os.remove(objDirectory + item)

                # Now that the folder is empty, delete it too
                os.rmdir(objDirectory)
                self.__objects.remove(obj)

                # If a TrackableObject is deleted, make sure that all references in groups are deleted as well
                if isinstance(obj, TrackableObject):
                    self.refreshGroups()
                return True

            if isinstance(obj, TrackableGroupObject):
                for taggedObj in obj.getMembers():
                    taggedObj.removeTag(obj.name)

                    taggedObj.save(self.__directory)
                self.__objects.remove(obj)
                return True
            # Delete the object from the objects array


        printf("Could not find object ", objectID, " in order to delete it!")
        return False


class Resource:
    def __init__(self, name, loadFromDirectory):
        self.name        = name
        self.loadSuccess = False
        self.dataJson    = {}

        if loadFromDirectory is not None:
            self.loadSuccess = self._load(loadFromDirectory)

    def save(self, directory):
        ensurePathExists(directory)

        # Long form (human readable:
        json.dump(self.dataJson, open(directory + "data.txt", 'w'), sort_keys=False, separators=(',', ': '))

    def _load(self, directory):
        # Check if the directory exists (just in case)
        if not os.path.isdir(directory):
            printf("ERROR: Could not find directory", directory)
            return False


        # Try to load the data.txt json
        dataFile   = directory + "\data.txt"
        try:
            loadedData = json.load( open(dataFile))
            self.dataJson = loadedData
        except IOError:
            printf("ERROR: Data file ", dataFile, " was not found!")
            return False
        except ValueError:
            printf("ERROR: Object in ", directory, " is corrupted!")
            return False
        return True

class MotionPath(Resource):
    def __init__(self, name, loadFromDirectory=None):
        self.__motionPath = []

        # Unpacked motionPath data looks like this [time, gripper, anglea, angleb, anglec, angled]
        super(MotionPath, self).__init__(name, loadFromDirectory)

    def setMotionPath(self, motionPath):
        self.dataJson["motionPath"] = motionPath

    def getMotionPath(self):
        # Return a copy of the motionPath
        return self.dataJson["motionPath"][:]

class Trackable(Resource):
    """
    Any "Trackable" should be capable of being put into a vision/tracking function and track an object or objects.
    """
    def __init__(self, name, loadFromDirectory):
        self.views = []
        super(Trackable, self).__init__(name, loadFromDirectory)

    def addView(self, view):
        self.views.append(view)

    def getViews(self):
        return self.views

    def equalTo(self, otherObjectID):
        # Test if two objects are are the same (used when seeing if something was recognized)
        # This method is overrided in TrackableGroup
        return self.name == otherObjectID

class TrackableObject(Trackable):
    View = namedtuple('View', 'name, viewID, height, pickupRect, rect, image')

    def __init__(self, name, loadFromDirectory = None):
        """
        Name: A String of the objects unique name. It must be unique for file saving and lookup purposes.

        "Views" is a list [View, View, View] of Views.
        An View is a namedTuple that looks like this:
                {
                    'image': cv2Frame,
                    'rect': (x1,y1,x2,y2),
                    'pickupRect': (x1,y1,x2,y2),
                    'height': 3
                }

        Views are used to record objects at different orientations and help aid tracking in that way.
        """
        self.__tags       = []
        super(TrackableObject, self).__init__(name, loadFromDirectory)

    def save(self, directory):
        """
        Everything goes into a folder called TrackableObject_OBJECTNAMEHERE

        Saves images for each View, with the format View#,
        and a data.txt folder is saved as a json, with this structure:
        {
            "Orientation_1": {
                            "rect": (0, 0, 10, 10),
                            "pickupRect": (0, 0, 10, 10),
                        },

            "Orientation_1": {
                            "rect": (0, 0, 10, 10),
                            "pickupRect": (0, 0, 10, 10),
                        },
        }
        """

        printf("Saving self to directory ", directory)

        # Make sure the "objects" directory exists
        ensurePathExists(directory)


        dataJson = {"tags": self.__tags, "Orientations": {}}


        # Save images and numpy arrays as seperate folders
        for index, view in enumerate(self.views):
            # Save the image
            cv2.imwrite(directory + "Orientation_" + str(index) + "_Image.png", view.image)

            # Add any view data to the dataJson
            dataJson["Orientations"]["Orientation_" + str(index)] = {"rect":  view.rect,
                                                                     "pickupRect": view.pickupRect,
                                                                     "height":     view.height}

        json.dump(dataJson, open(directory + "data.txt", 'w'), sort_keys=False, indent=3, separators=(',', ': '))

    def _load(self, directory):
        # Should only be called during initialization

        # Check if the directory exists (just in case)
        if not os.path.isdir(directory):
            printf("ERROR: Could not find directory", directory)
            return False


        # Try to load the data.txt json
        dataFile = directory + "\data.txt"
        try:
            loadedData = json.load( open(dataFile))

        except IOError:
            printf("ERROR: Data file ", dataFile, " was not found!")
            return False
        except ValueError:
            printf("ERROR: Object in ", directory, " is corrupted!")
            return False

        # For each view, load the image associated with it, and build the appropriate view
        orientationData = loadedData["Orientations"]
        for key in orientationData:
            imageFile = directory + '\\' + key + "_Image.png"
            image     = cv2.imread(imageFile)

            if image is None:
                printf("ERROR: Image File ", imageFile, " was unable to be loaded!")
                return False

            self.addNewView(image      = image,
                            rect       = orientationData[key]["rect"],
                            pickupRect = orientationData[key]["pickupRect"],
                            height     = orientationData[key]["height"])


        for tag in loadedData["tags"]:
            self.addTag(tag)
        return True


    def addNewView(self, image, rect, pickupRect, height):
        newView = self.View(name   = self.name, viewID      = len(self.views),
                            height =    height, pickupRect  =      pickupRect,
                            rect   =      rect, image       =           image)
        self.views.append(newView)

    def addTag(self, tagString):
        # Make sure there's never duplicates
        if tagString not in self.__tags:
            self.__tags.append(tagString)

    def removeTag(self, tagString):
        self.__tags.remove(tagString)


    def getIcon(self, maxWidth, maxHeight, drawPickupRect=True):
        # Create an icon of a cropped image of the 1st View, and resize it to the parameters.
        # if drawPickupRect is True, it will also overlay the position of the robots pickup area for the object

        #  Get the full image and crop it
        fullImage = self.views[0].image
        rect      = self.views[0].rect
        image     = fullImage[rect[1]:rect[3], rect[0]:rect[2]]

        # Draw the pickupArea on it before resizing
        if drawPickupRect and self.views[0].pickupRect is not None:
            x0, y0, x1, y1  = self.views[0].pickupRect
            quad            = np.int32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])

            print(quad)
            cv2.polylines(image, [quad], True, (255, 255, 255), 2)


        #  Resize it to fit within maxWidth and maxHeight
        height, width, _ = image.shape
        if height > maxHeight:
            image = cv2.resize(image, (int(float(maxHeight) / height * width), maxHeight))

        height, width, _ = image.shape
        if width > maxWidth:
            image = cv2.resize(image, (maxWidth, int(float(maxWidth) / width * height)))

        height, width, _ = image.shape


        return image.copy()

    def getTags(self):
        return self.__tags

class TrackableGroupObject(Trackable):
    """
    A group of TrackableObjects that works just like any other Trackable and can be used for detection purposes.
    EqualTo will look to see if the said TrackableObject is inside of the group

    GetViews returns every view of every object in the group, and is how the trackableGroup is tracked.

    self.name is the Group name
    """


    def __init__(self, name, members):
        super(TrackableGroupObject, self).__init__(name, None)
        self.__members = members  # List of Trackable objects that belong to the group
        self.__memberIDs = [obj.name for obj in self.__members]

    def getViews(self):
        views = []
        for obj in self.__members:
            views += obj.getViews()

        return views

    def getMembers(self):
        return self.__members

    def equalTo(self, otherObjectID):
        return otherObjectID in self.__memberIDs






