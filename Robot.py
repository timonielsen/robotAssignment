import Particle
import math

connected = True
try:
    from gopigo import *
except ImportError:
    connected = False

import sys
import time


class Robot:
    def __init__(self, _maze, _speed, _rotationSpeed): #give it a maze as input!
        
        self.maze = _maze
        ###Variables for robot###
        self.x = 5.0 #location, initiliased to zero as the robot initialy has no clue where it is
        self.y = 25.0
        self.orientation = 0.6*(math.pi/2) #[0, 2PI]
        self.prVirtual = Particle.Particle(self.x, self.y, self.orientation) #virtual location for when robot is not connected
        self.pr = Particle.Particle(self.x, self.y, self.orientation) #belief location
        self.pr.set_noise(5.0, 1.0, 1.0) # these are for movement and sense distribution
        
        self.speed = _speed; #Speed with which the robot moves forwards
        self.rotationSpeed = _rotationSpeed; #
        
        self.movement = [0,0] # stores the last movement [length moved, rotation]
        self.measurement = [0.0,0.0,0.0,0.0,0.0] #we can always re evaluate number of points here. DO NOT MAKE ANY HARD CODED LOOPS.
        
        #The following are hard coded values found from measurements of the precision of robot movement. Length of arrays to be determined
        self.moveVar = [0,0,0,0,0] #variance in distance actually moved
        self.moveMean = [0,0,0,0,0]
        self.moveOrientVar = [0,0,0,0,0] #variance in orientation when moving forward
        self.moveOrientMean = [0,0,0,0,0]
        self.orientVar = [0,0,0,0,0] #variance in orientation when rotating
        self.orientMean = [0,0,0,0,0]
        self.measurementVar = [0,0,0,0,0] #variance in orientation when rotating
        self.measurementMean = [0,0,0,0,0]
        self.measurementLimHigh = 1e10 #limit for measurement. Set to some desired value
        self.measurementLimLow = 0

        self.distFromSensorToRotCenter = 7.5 #cm

    

    def move(self):
        if connected:
            self.rotate(self.movement[1])
            self.drive(self.movement[0])
        else:
            self.simulateMove(self.movement[1],self.movement[0])
            return 0

    def drive(self, _distance):
        """Moves the robot. postive values=forward, negative values=backward"""
        if connected:
            distance = _distance #cm INPUT
            speed = 160 #constant
            unitSpeed = 11.11 #Units/second CONSTANT
            cmPrUnit = 1.1483 #Constant

            unitDist = int(round(distance/cmPrUnit)) #Be careful with int and doubles
            sleepTime = unitDist/unitSpeed * 1.3

            set_speed(speed)  
            enc_tgt(1,1,unitDist)
            if(_distance > 0):
                fwd()
            else:
                bwd()
            time.sleep(sleepTime)
        return 0

    def rotate(self, _angle):
        if abs(_angle) < 0.001:
            return 0
        """Rotate robot. Be aware of sign of angle. We need to figure out if CW is positive"""
        if connected:
            if _angle < math.pi:
                fullCircle = 32 #units
                partsOfCircle = 2*math.pi/_angle #how big a part of a full circle is rotated. eg 90 degrees = 4
                sleeptime = 5 #CHANGE BY MEASURE!

                units = int(round(fullCircle/partsOfCircle))
                set_speed(80)  #DO NOT CHANGS UNLESS NEW TESTS ARE MADE WITH ROBOT TO CHECK HOW MANY UNITS GO TO FULL CIRCLE
                enc_tgt(1,1,units)
                right_rot() #Choose whether it should be clockwise or counterclockwise
                time.sleep(sleepTime)
            else:
                angle = 2*math.pi-_angle
                fullCircle = 32 #units
                partsOfCircle = 2*math.pi/angle #how big a part of a full circle is rotated. eg 90 degrees = 4
                sleeptime = 5 #CHANGE BY MEASURE!

                units = int(round(fullCircle/partsOfCircle))
                set_speed(80)  #DO NOT CHANGS UNLESS NEW TESTS ARE MADE WITH ROBOT TO CHECK HOW MANY UNITS GO TO FULL CIRCLE
                enc_tgt(1,1,units)
                left_rot() #Choose whether it should be clockwise or counterclockwise
                time.sleep(sleepTime)


        return 0

    def measure(self): 
        """Updates measurement[] with a series of measurements."""
        if connected:
            angles = []
            sleepTime = 0.5 #Set time between measures (has to be there for the program to wait with the next command until rotation is done)
            '''calculate angles to measure'''
            for i in range(0, len(self.measurement)):
                angle = (len(self.measurement)-i-1) * math.pi / (len(self.measurement)-1) # calculates the angles for which the sensors measure
                angle %= 2*math.pi
                angles.append(int(round(angle*180/math.pi)))

            ''' perform measurement'''
            for i in range(0, len(self.measurement)):
                servo(angles[i])
                time.sleep(sleepTime)
                measurement = us_dist(15)
                if measurement > 150: #hardcoded, not pretty... But is a bit bigger than the diagnoal of the maze
                    self.measurement[i] = -1
                else:
                    self.measurement[i] = measurement            
        else:
            self.measurement = self.simulateMeasurements()
        return self.measurement

    def updateBelief(self, _particleFilter): #updates x, y and rotation
        """updates x, y and rotation"""
        return 0

    def findPath(self):
        """Finds the shortest path out of the maze. 
        No need to have maze as input as the maze is a variable for the robot"""
        return 0

    def rotateServo(self):
        """this function might just be moved to be a part of the measure() function.""" 
        return 0

    def simulateMeasurements(self):
        self.prVirtual.calcDistance(self.maze)
        return self.prVirtual.measurements

    def simulateMove(self,_angle,_distance):
        print(self.pr.x)
        self.pr.move(_angle,_distance,self.maze)
        self.prVirtual.move(_angle,_distance,self.maze)
        self.x = int(round(self.prVirtual.x))
        self.y = int(round(self.prVirtual.y))
        self.orientation = self.prVirtual.orientation
        print(self.pr.x)
        print("done here")
        return 0

    def getSimulatedLocation(self):
        return self.prVirtual.getStateofParticle()

    def calculateMovementOnPath(self, _distance, _maze):
        if _distance == 0 or len(_maze.path) == 0:
            self.movement = [0,0]
            return


        path = _maze.path
        cellsToTravel = int(_distance/_maze.cellSize)

        startcellY = int(_maze.allNodes[path[len(path)-1]][0])
        startcellX = int(_maze.allNodes[path[len(path)-1]][1])
        

        if cellsToTravel > len(path):
            endCellY = int(_maze.allNodes[path[0]][0])
            endCellX = int(_maze.allNodes[path[0]][1])
        else:
            endCellY =  int(_maze.allNodes[path[len(path)-cellsToTravel]][0])
            endCellX =  int(_maze.allNodes[path[len(path)-cellsToTravel]][1])

        xDist = endCellX - startcellX
        yDist = endCellY - startcellY

        distance = pythagoras(endCellX-startcellX, endCellY-startcellY)
        orientation = math.atan2(-xDist,yDist)

        rotation = orientation - self.orientation
        self.movement = [distance,rotation]
        
        return 0

    def reset(self):
        self.pr.rayTracedNodes = {}
        self.measurement = []

    def updateBelief(self, _x, _y, _orient):
        self.pr.x = _x
        self.pr.y =_y
        self.pr.orientation = _orient

    def correct(self, _correctionDistance):
        '''corrects for the fact that there is distance between sensor and center of rotation'''
        self.pr.correct(self.maze.dimX, self.maze.dimY,_correctionDistance)
        self.prVirtual.correct(self.maze.dimX, self.maze.dimY, _correctionDistance)
        self.x = int(round(self.prVirtual.x))
        self.y = int(round(self.prVirtual.y))



def pythagoras(length1, length2):
    """caulcates the hypothenuse length of a diagonal of a right angled triangle"""
    return math.sqrt(math.pow(length1,2) + math.pow(length2,2))






'''
#Variables
x, y; #int
float orientation;
int speed, rotationSpeed;
int[2] movement; #array of distance forward as well as rotation. 
float[] measurement; #array of measurements. Most likely of size 5
Maze maze; #robot stores the maze in it's own memory

float[] moveVar, moveMean, moveRotVar, moveRotMean; #normal Distribution values for moving forward/backward. Array so values for different speeds can be stored. These values are constants that we hard code. moveRotVar is for the expected rotation while moving forward/backward
float[] rotVar, rotMean; #Normal distribution for rotation
float[] measurementVar, measurementMean; #Normal distribution for measurement

float measurementLimHigh,measurementLimLow; #hard coded limits for measurements

#Functions
void move(float distance); #postive values=forward, negative values=backward
void rotate(float angle); #negative or positive values
void measure(); #Updates measurement[] with a series of measurements.
void updateBelief(Particlefilter particleFilter); #updates x, y and rotation
void findPath() #Finds the shortest path out of the maze. No need to have maze as input as the maze is a variable for the robot
void rotateServo() # this function might just be moved to be a part of the measure() function.
'''