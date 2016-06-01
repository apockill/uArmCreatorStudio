

class Environment:
    def __init__(self, shared):
        """
        This will be a platform for storing "Heavy" objects that will be used in the program. ie, image recognition
        files, anything that can't be stored in plaintext in the scriptfile that won't change during the program should
        be here. It can load and save objects in a special uObject class that might have derivatives of types:
            uVisionObject       Might contain pictures, image maps, huge arrays with keypoints, who knows.
            uMotionPathObject   Might contain long lists of moves, speeds, or even mathematical functions for the bot to
                                follow.
            uScriptObject       Might contain a whole other script within it that would be able to run entirely within
                                the program and spawn its own environment and interpreter.

        All loading, adding replacing, and saving of objects should be done through this class.
        All objects will have a "getSaveData" implimented.

        :param file:
        :return:
        """

        # This keeps track of objects that have been self.addObject()'d, so self.saveObjects() actually saves them.
        self.changedObjects = []
        self.__shared = shared

    def saveObjects(self, filename):
        # Any objects that have been "changed" will be saved. All other objects won't be touched.
        # This should lead to faster save times, since the user will probably save on a whim.

        # Checks if an interpreter is currently running before doing anything.
        pass

    def loadObjects(self, filename):
        # Load all objects into the environment

        # Checks if an interpreter is currently running before doing anything.
        pass

    def addObject(self, object):
        # Adds an object to the pool.

        # Checks if an interpreter is currently running before doing anything.

        # Checks if the object already exists, if so, it will replace the old one, and put itself in self.changedObjects




    def getInterpreter(self, scriptData):
        # Returns an Interpreter() object with the script loaded and parsed.
        pass

class Interpreter:
    def __init__(self, shared, ):
        pass

    def startThread(self):
        # Start the program thread

        pass

    def endThread(self):
        # Close the thread that is currently running at the first chance it gets. Return True or False

        pass

    def programThread(self):
        # This is where the script you create actually gets run. This is run on a seperate thread, self.mainThread

        pass


    def isReady(self):
        """
        The interpreter will now check comprehensively every function you have, if it requires a camera, if it requires
        a robot, if it requires an object, and check if all of those things are ready (query the robot, check the
        vStream, check the objects saved in the Environment. If everything is ready, it will start a thread and begin
        running.
        :return:
        """

        pass

    def getStatus(self):
        pass




















