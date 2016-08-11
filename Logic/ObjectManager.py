"""
This software was designed by Alexander Thiel
Github handle: https://github.com/apockill
Email: Alex.D.Thiel@Gmail.com


The software was designed originaly for use with a robot arm, particularly uArm (Made by uFactory, ufactory.cc)
It is completely open source, so feel free to take it and use it as a base for your own projects.

If you make any cool additions, feel free to share!


License:
    This file is part of uArmCreatorStudio.
    uArmCreatorStudio is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    uArmCreatorStudio is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with uArmCreatorStudio.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
from Logic        import Resources
from Logic.Global import printf, ensurePathExists, getModuleClasses
__author__ = "Alexander Thiel"


class ObjectManager:
    """
    ObjectManager is a platform for storing objects that will be used in multiple .tasks. ie, image recognition
    files, anything that can't be stored in plaintext in the scriptfile that won't change during the program should
    be here. It can load and save objects in a special Resource class that might have derivatives of types:
        TrackableObject  Might contain pictures, image maps, huge arrays with keypoints, who knows.
        MotionPath       Might contain long lists of moves, speeds, or even mathematical functions for the bot to follow
        Function         Contains a commandList and several arguments it can take

    All loading, adding replacing, and saving of objects should be done through this class
    """

    def __init__(self, directory):
        ensurePathExists(directory)

        self.__directory = directory
        self.__objects   = []  # A list of the loaded objects


        # Set different filters that can be used in self.getObjectIDList(objFilter=[One of the following])
        self.TRACKABLE      = Resources.Trackable
        self.TRACKABLEOBJ   = Resources.TrackableObject
        self.TRACKABLEGROUP = Resources.TrackableGroupObject
        self.MOTIONPATH     = Resources.MotionPath
        self.RESOURCE       = Resources.Resource
        self.FUNCTION       = Resources.Function
        self.PICKUP         = "PICKUP"  # Any trackable object + group, NOT incuding the Robot Marker object

        self.__loadAllObjects()


    def saveObject(self, newObject):
        # If not new, replace self
        wasNew = self.__addObject(newObject)
        if not wasNew:
            printf("ObjectManager| Tried to add object that already existed, ", newObject.name)

        newObject.save(self.__getDirectory(newObject))

    def refreshGroups(self):
        """
        Creates a TrackableGroup for every uniqe tag every object has, and replaces old TrackableGroups.

        This should only be used by the GUI when a group is added or deleted, or when a vision object is deleted.
        """


        # Remove existing groups from self.__objects
        for obj in self.__objects[:]:
            # Since multiple objects are being deleted in the same array, use [:] to copy it so it doesnt change size
            if isinstance(obj, Resources.TrackableGroupObject):
                self.__objects.remove(obj)


        # Use a temporary dictionary to record which objs belong to which groups
        groups = {}  # Example: {"tag": [obj, obj, obj], "tag2":[obj]}


        # Go through all objects and record which objects belong in which groups
        for obj in self.__objects:
            # Only TrackableObjects can be in TrackableGroups
            if not isinstance(obj, Resources.TrackableObject): continue

            tags = obj.getTags()

            for tag in tags:
                # Make sure groups has the appropriate keys with arrays for each tag
                if tag not in groups: groups[tag] = []

                # Add the object to each tag
                groups[tag].append(obj)  # Change to be "obj"


        # Create the TrackableGroup objects and add them
        for group in groups:
            newGroupObj = Resources.TrackableGroupObject(name=group, members=groups[group])
            self.__addObject(newGroupObj)


    def getObject(self, objectID):
        # Ask for an object by name, and get the object class. If it's nonexistent, return None
        for obj in self.__objects:
            if obj.name == objectID: return obj

        return None

    def getObjectNameList(self, typeFilter=None):
        """
        Returns a list of object names. This is used in ObjectManager, or any situation when you need to know if a
        particular object is loaded. If objFilter is not None, then only return objects of that type

        :param typeFilter: If you only want objects of a particular type
        :return: A list of object names, like ["name1", "name2", "name3"] in alphabetical order
        """

        """
        Notes for Future Me:
            type(obj) == TrackableObject            # Works
            isinstance(trackable, TrackableObject)  # Works
            issubclass(type(trackable), Trackable)  # Works
        """

        # Returns true if 'obj' is of any type inside of typeList
        isType = lambda obj, typeList: any(isinstance(obj, t) for t in typeList)

        nameList = []
        for obj in self.__objects:
            # If the user just wants a list of every object
            if typeFilter is None:
                nameList.append(obj.name)
                continue

            # If object is capable of being picked up by the robot with any pickup function
            if typeFilter == self.PICKUP:
                if obj.name == "Robot Marker": continue

                if isType(obj, (Resources.TrackableObject, Resources.TrackableGroupObject)):
                    nameList.append(obj.name)

                continue

            # A catch-all filter for filtering by "Type"
            if isinstance(obj, typeFilter):
                nameList.append(obj.name)
                continue

        return nameList

    def getForbiddenNames(self):
        """
            Returns a list of strings that the user cannot use as the name of an object.
            This includes names of objects, names of tags, and names of objects like Robot Marker that are reserved
            It also includes things like "Trackable" or "TrackableObject" for good measure
            It also includes things like "Task" so that the user can't name things in a confusing way
        """


        forbidden = self.getObjectNameList()
        forbidden += ["Trackable", "Robot Marker", "TrackableObject", "TrackableGroup", "Face", "Smile", "Eyes",
                      "MotionPath", "Function", "Task"]
        return forbidden

    def deleteObject(self, objectID):
        """
        Deletes an object- both the file and in the loaded memory.

        :param objectID: Objects string name
        """

        printf("ObjectManager| Deleting ", objectID, " permanently")

        for obj in self.__objects:
            if not objectID == obj.name: continue

            # Do a special case for deleting TrackableGroups
            if isinstance(obj, Resources.TrackableGroupObject):
                for taggedObj in obj.getMembers():
                    taggedObj.removeTag(obj.name)
                    self.saveObject(taggedObj)
                self.__objects.remove(obj)
                return True


            # If the object is a Resource, then delete the directory
            else:  # if issubclass(type(obj), Resources.Resource):
                # Get all the items in the objects folder, and delete them one by one
                objDirectory = self.__getDirectory(obj)

                # Make sure everything is deleted in the directory
                while len(os.listdir(objDirectory)):
                    for item in os.listdir(objDirectory):
                        os.remove(os.path.join(objDirectory, item))

                # Now that the folder is empty, delete it too
                os.rmdir(objDirectory)
                self.__objects.remove(obj)

                # If a TrackableObject is deleted, make sure that all references in groups are deleted as well
                if isinstance(obj, Resources.TrackableObject):
                    self.refreshGroups()
                return True



            # Delete the object from the objects array


        printf("ObjectManager| Could not find object ", objectID, " in order to delete it!")
        return False



    def __addObject(self, newObject):
        """
        The reason this is private is because objects should only be added through self.saveNewObject or loadAllObj's
        Checks if the object already exists. If it does, then replace the existing object with the new one.

        :param newObject: A subclass of Resource
        """

        for obj in self.__objects:
            if newObject.name == obj.name:
                printf("ObjectManager| ERROR: Tried adding an object that already existed: ", obj.name)
                return False


        # If the object doesn't already exist, adds the object to the pool of loaded objects.
        self.__objects.append(newObject)


        # Sort in alphabetical order, by name, for simplicity in GUI functions that display objects
        self.__objects = sorted(self.__objects, key=lambda obj: obj.name)
        return True

    def __getDirectory(self, obj):
        """
        Gets the propper directory name for the object with the propper formatting
        :param obj: Any object that is a subclass of Resource
        """
        filename = obj.__class__.__name__ + " " + obj.name  # Build the filename
        directory = os.path.join(self.__directory, filename)


        return directory

    def __loadAllObjects(self):
        # Load all objects into the ObjectManager

        foldersAndItems = os.listdir(self.__directory)

        resourceClasses = getModuleClasses(Resources)


        for folder in foldersAndItems:
            path = os.path.join(self.__directory, folder)

            if not os.path.isdir(path):
                printf("ObjectManager| ERROR: Could not find directory ", path)
                continue


            # Get the type and name of the object by breaking up the filename into words
            words = folder.split(' ', 1)
            if len(words) < 2:
                printf("ObjectManager| ERROR: File ", folder, " did not have the correct format!")
                continue   # If there isn't a 'TYPE NAME' format
            newType = str(words[0])
            name    = words[1]


            # Check that that type of resource exists

            if newType not in resourceClasses:
                printf("ObjectManager| ERROR: Tried to create a resource that is not in Resources.py!")
                continue

            # Get the type, then instantiate it
            newType = resourceClasses[newType]
            newObj  = newType(name, path)

            if newObj.loadSuccess: self.__addObject(newObj)

        # Search through vision objects tags and generate TrackableGroup objects for each of them
        self.refreshGroups()









