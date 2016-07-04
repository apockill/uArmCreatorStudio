import json
import os
import cv2   # For image saving
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

    def __init__(self, directory):
        ensurePathExists(directory)

        self.__directory = directory
        self.__objects   = []  # A list of the loaded objects


        # Set different filters that can be used in self.getObjectIDList(objFilter=[One of the following])
        self.TRACKABLE      = Trackable
        self.TRACKABLEOBJ   = TrackableObject
        self.TRACKABLEGROUP = TrackableGroup
        self.PICKUP         = "PICKUP"        # Any trackable object + group, NOT incuding the Robot Marker object


    def loadAllObjects(self):
        # Load all objects into the ObjectManager

        foldersAndItems = os.listdir(self.__directory)

        newTrackable = lambda folder, directory: TrackableObject(folder.replace("TrackerObject ", ""), directory)
        for folder in foldersAndItems:
            path = self.__directory + "\\" + folder

            # Handle any TrackableObject loading
            if "TrackerObject" in folder and os.path.isdir(path):
                newObj = newTrackable(folder, path)
                if newObj.loadSuccess:
                    self.__addObject(newObj)

        self.refreshGroups()

    def saveObject(self, newObject):
        # If not new, replace self
        wasNew = self.__addObject(newObject)
        if not wasNew:
            printf("ObjectManager.saveObject(): Tried to add object that already existed, ", newObject.name)

        newObject.save(self.__directory)

    def refreshGroups(self):
        # Creates a TrackableGroup for every uniqe tag every object has, and replaces old TrackableGroups
        printf("ObjectManager.refreshGroups(): Refreshing Groups!")

        # Remove existing groups from self.__objects
        for obj in self.__objects:
            if isinstance(obj, TrackableGroup): self.__objects.remove(obj)

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
            newGroupObj = TrackableGroup(name=group, members=groups[group])
            self.__addObject(newGroupObj)


    def getObject(self, objectID):
        # Ask for an object by name, and get the object class. If it's nonexistent, return None
        for obj in self.__objects:
            if obj.name == objectID: return obj

        return None

    def getObjectIDList(self, objFilter=None):
        # Returns a list of object names. This is used in ObjectManager, or any situation when you need to know if a
        # particular object is loaded. If objFilter is not None, then only return objects of that type

        """
        Notes for Future Me:
            type(obj) == TrackableObject               # Works
            isinstance(trackable, TrackableObject)  # Works
            issubclass(type(trackable), Trackable)        # Works

        """

        nameList = []
        for obj in self.__objects:
            # If None, then just add every object
            if objFilter is None:
                nameList.append(obj.name)
                continue

            if objFilter == self.PICKUP and issubclass(type(obj), Trackable):
                if obj.name == "Robot Marker": continue
                nameList.append(obj.name)
                continue

            if isinstance(obj, objFilter):
                nameList.append(obj.name)
                continue

        return nameList

    def getForbiddenNames(self):
        # Returns a list of strings that the user cannot use as the name of an object.
        # This includes names of objects, names of tags, and names of objects like "Robot Marker" that are reserved
        # It also includes things like "Trackable" or "TrackableObject" for good measure
        forbidden = self.getObjectIDList()
        forbidden += ['TrackerObject', 'Robot Marker', "Trackable"]
        return forbidden

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

        for obj in self.__objects[:]:
            if not objectID == obj.name: continue


            # If the object is a TrackableObject, then deleete the directory
            if isinstance(obj, TrackableObject):
                objDirectory = self.__directory + "TrackerObject " + obj.name + "\\"
                # Get all the items in the objects folder, and delete them one by one
                foldersAndItems = os.listdir(objDirectory)
                for item in foldersAndItems:
                    os.remove(objDirectory + item)

                # Now that the folder is empty, delete it too
                os.rmdir(objDirectory)

                self.__objects.remove(obj)
                return True

            if isinstance(obj, TrackableGroup):
                for taggedObj in obj.getMembers():
                    taggedObj.removeTag(obj.name)
                    taggedObj.save(self.__directory)
                self.__objects.remove(obj)
                return True
            # Delete the object from the objects array


        printf("ObjectManager.deleteObject(): Could not find object ", objectID, " in order to delete it!")
        return False



class Trackable:
    def __init__(self, name):
        self.name  = name
        self.views = []

    def addView(self, view):
        self.views.append(view)

    def getViews(self):
        return self.views

    def equalTo(self, otherObjectID):
        return self.name == otherObjectID

class TrackableObject(Trackable):
    View = namedtuple('View', 'name, viewID, height, pickupRect, rect, image')

    def __init__(self, name, loadFromDirectory = None):
        super(TrackableObject, self).__init__(name)
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

        # self.directory    = loadFromDirectory  # Used in objectmanager for deleting object. Set here, or in self.save
        self.loadSuccess  = False
        self.__tags       = []                 # A list of strings. This determines what groups the object is placed in.

        if loadFromDirectory is not None:
            self.loadSuccess = self.__load(loadFromDirectory)


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

        printf("TrackableObject.save(): Saving self to directory ", directory)

        # Make sure the "objects" directory exists
        filename                    = directory + "TrackerObject " + self.name + "\\"
        ensurePathExists(filename)



        dataJson = {"tags": self.__tags, "Orientations": {}}
        # Save images and numpy arrays as seperate folders
        for index, view in enumerate(self.views):
            # Save the image
            cv2.imwrite(filename + "Orientation_" + str(index) + "_Image.png", view.image)

            # Add any view data to the dataJson
            dataJson["Orientations"]["Orientation_" + str(index)] = {"rect":  view.rect,
                                                                     "pickupRect": view.pickupRect,
                                                                     "height":     view.height}

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
            printf("TrackableObject.__load(): ERROR: Data file ", dataFile, " was not found!")
            return False
        except ValueError:
            printf("TrackableObject.__load(): ERROR: Object in ", directory, " is corrupted!")
            return False

        # For each view, load the image associated with it, and build the appropriate view
        orientationData = loadedData["Orientations"]
        for key in orientationData:
            imageFile = directory + '\\' + key + "_Image.png"
            image     = cv2.imread(imageFile)

            if image is None:
                printf("TrackableObject.__load(): ERROR: Image File ", imageFile, " was unable to be loaded!")
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
            printf("TrackableObject.addTag(): Adding new tag: ", tagString, " to ", self.name)
            self.__tags.append(tagString)

    def removeTag(self, tagString):
        self.__tags.remove(tagString)

    def getIcon(self, maxWidth, maxHeight):
        # Create an icon of a cropped image of the 1st View, and resize it to the parameters.


        #  Get the cropped image of just the object
        fullImage = self.views[0].image
        rect      = self.views[0].rect
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

    def getTags(self):
        return self.__tags


class TrackableGroup(Trackable):
    # self.name is the Group name

    def __init__(self, name, members):
        super(TrackableGroup, self).__init__(name)
        self.name    = name
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