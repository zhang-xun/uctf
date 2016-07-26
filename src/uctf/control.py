from __future__ import print_function

import math
import sys
import time

from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool
from mavros_msgs.srv import CommandTOL
from mavros_msgs.srv import CommandTOLRequest
import rospy
from sensor_msgs.msg import NavSatFix


vehicles = {}


def control_team(color):
    """Instantiate a Vehicle instance for each vehicle."""
    rospy.init_node('controller_%s' % color, anonymous=True)

    namespaces = get_namespaces(color)
    for namespace in namespaces:
        vehicles[namespace] = Vehicle(color, namespace)

    rospy.spin()


def get_namespaces(color):
    """Get the namespaces of all vehicles in a given team."""
    namespaces = []
    # spawn 50 vehicles
    for i in range(1, 51):
        # valid MAV_SYS_IDs 1 to 250
        # BLUE uses 1 to 50
        # GOLD uses 101 to 150
        mav_sys_id = i
        if color == 'gold':
            mav_sys_id += 100

        # the first 25 vehicles per team are iris
        # the second 25 vehicles per team are plane
        vehicle_type = 'iris' if i <= 25 else 'plane'

        namespaces.append('%s_%d' % (vehicle_type, mav_sys_id))
    return namespaces


STATE_IDLE = 0
STATE_FLYING = 1
STATE_LANDING = 2
STATE_DONE = 3
STATE_ERROR = 4


class Vehicle(object):
    """A Vehicle will subscribe to its topics and then arm, takeoff, and land."""

    def __init__(self, color, namespace):
        self.color = color
        self.namespace = namespace
        self._set_state(STATE_IDLE)

        self.last_state = None
        self.start_position = None

        self.state_subscriber = None
        self.position_subscriber = None

        self._subscribe()

    def _set_state(self, state):
        self.state = state
        self.state_changed = time.time()

    def _subscribe(self):
        assert self.state_subscriber is None
        assert self.position_subscriber is None
        self.state_subscriber = rospy.Subscriber(
            '%s/mavros/state' % self.namespace, State,
            callback=self._state_callback)
        self.position_subscriber = rospy.Subscriber(
            '%s/mavros/global_position/global' % self.namespace, NavSatFix,
            callback=self._position_callback)

    def _state_callback(self, msg):
        if self.state == STATE_ERROR:
            self.state_subscriber.unregister()
            self.state_subscriber = None
            return

        if self.last_state is None:
            print(self.namespace, 'found')
            if msg.armed:
                print(self.namespace, 'already armed')

        self.last_state = msg

        # arm vehicle
        if self.state == STATE_IDLE and not msg.armed:
            armed = self._arm()
            if not armed:
                self._set_state(STATE_ERROR)
                return

        # take off
        if msg.armed and self.start_position and self.state == STATE_IDLE:
            tookoff = self._takeoff()
            if not tookoff:
                self._set_state(STATE_ERROR)
            return

        if self.state == STATE_FLYING:
            if time.time() - self.state_changed < 10.0:
                # just do nothing for now
                pass
            else:
                # return home
                returning = self._return_home()
                if not returning:
                    self._set_state(STATE_ERROR)
                return

        if self.state == STATE_LANDING and not msg.armed:
            print(self.namespace, 'done')
            self._set_state(STATE_DONE)

    def _position_callback(self, msg):
        print(self.namespace, 'start position')
        self.start_position = msg
        self.position_subscriber.unregister()
        self.position_subscriber = None

    def _arm(self):
        print(self.namespace, 'arming')
        service_name = '%s/mavros/cmd/arming' % self.namespace
        rospy.wait_for_service(service_name)
        try:
            service = rospy.ServiceProxy(service_name, CommandBool)
            resp = service(True)
        except rospy.ServiceException as e:
            print(self.namespace, 'service call to arm failed:', str(e),
                  file=sys.stderr)
            return False
        if not resp.success:
            print(self.namespace, 'failed to arm', file=sys.stderr)
            return False
        print(self.namespace, 'armed')
        return True

    def _takeoff(self):
        print(self.namespace, 'takeoff')
        req = CommandTOLRequest()
        req.min_pitch = 0.3
        req.yaw = 0.0 if self.color == 'blue' else -math.pi
        req.latitude = self.start_position.latitude
        req.longitude = self.start_position.longitude
        req.altitude = self.start_position.altitude + 5.0

        service_name = '%s/mavros/cmd/takeoff' % self.namespace
        rospy.wait_for_service(service_name)
        try:
            service = rospy.ServiceProxy(service_name, CommandTOL)
            resp = service.call(req)
        except rospy.ServiceException as e:
            print(self.namespace, 'service call to takeoff failed:', str(e),
                  file=sys.stderr)
            return False
        if not resp.success:
            print(self.namespace, 'failed to takeoff: %d' % resp.result, file=sys.stderr)
            return False
        print(self.namespace, 'taking off')
        self._set_state(STATE_FLYING)
        return True

    def _return_home(self):
        print(self.namespace, 'land')
        req = CommandTOLRequest()
        req.min_pitch = 0.0
        req.yaw = -math.pi if self.color == 'blue' else 0.0
        req.latitude = self.start_position.latitude
        req.longitude = self.start_position.longitude
        req.altitude = self.start_position.altitude

        service_name = '%s/mavros/cmd/land' % self.namespace
        rospy.wait_for_service(service_name)
        try:
            service = rospy.ServiceProxy(service_name, CommandTOL)
            resp = service.call(req)
        except rospy.ServiceException as e:
            print(self.namespace, 'service call to land failed:', str(e),
                  file=sys.stderr)
            return False
        if not resp.success:
            print(self.namespace, 'failed to land', file=sys.stderr)
            return False
        print(self.namespace, 'landing')
        self._set_state(STATE_LANDING)
        return True