import math
from globalDefinition import (
    BATTERY_CAPACITY,
    MASS,
    GRAVITY,
    CI,
    CR,
    C1,
    C2,
    CD, 
    AF, 
    PA, 
    ED,EM,EB
)

def getPowerMotor(acceleration, velocity, road_grade):
    road_grade_radian = (road_grade/180)*math.pi
    power_of_wheel = 0
    power_of_motor = 0
    gradient_resistance_force = MASS*GRAVITY*math.sin(road_grade_radian)
    rolling_resistance_force = MASS*GRAVITY*math.cos(road_grade_radian)*CR*(C1*velocity+C2)/1000
    aerodynamic_drag_force = 0.5*(PA*AF*CD*math.pow(velocity,2))
    Inertia_resistance_force = CI*MASS * acceleration
    power_of_wheel = (gradient_resistance_force+rolling_resistance_force+aerodynamic_drag_force+Inertia_resistance_force)*velocity
    power_of_motor = power_of_wheel/(ED*EM*EB)
    return power_of_motor

def getStateOfCharge(acceleration,velocity,road_grade):
    power= getPowerMotor(acceleration,velocity,road_grade)
    total_power = 0
    if acceleration<0 and power<0:
        ER = 1/math.exp(0.0411/abs(acceleration))
        total_power = ER*power
    elif power<0:
        ER = 0.7
        total_power = ER*power
    else:
        total_power = power
    return (total_power)/(3600*BATTERY_CAPACITY)