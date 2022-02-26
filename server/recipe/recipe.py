from multiprocessing import Lock


N = 10
SPEED = 1  # between 0-1
SERVICE_FUNC_NO_FEEDER = 1
SERVICE_FUNC_NO_CARTRIDGE = 1
SERVICE_FUNC_NO_DOSING = 1
''' Station '''
FEED_Z_UP = 10000 * SPEED
FEED_Z_DOWN = 15000 * SPEED
FEED_DANCE = 40000
STATION_Z_OUTPUT = 70
STATION_Z_OUTPUT_SAFE = STATION_Z_OUTPUT - 30

# Vision
ALIGN_SPEED_DOSING = 25000
ALIGN_SPEED_HOLDER = 25000
VISION_RETRIES_HOLDER = [3, 2, 2, 2]
VISION_RETRIES_DOSING = [4, 3, 3, 3, 3]

''' Robot '''
FEED_X_FORWARD = 23000 * SPEED  # 30000
FEED_X_BACKWARD = 28000 * SPEED  # 280000
FEED_X_SHORT = 35000 * SPEED
FEED_Y_UP = 35000 * SPEED * .5
FEED_Y_DOWN = 40000 * SPEED * .5
FEED_Y_DOWN_CAP = 8000 * SPEED * .5
FEED_Y_DOWN_PRESS = 5000 * SPEED * .5

# Park
X_PARK = 10
Y_PARK = 40

# Capping
Y_CAPPING_DOWN = 10
assert Y_CAPPING_DOWN < Y_PARK

''' Rail '''
FEED_RAIL_FREE = 25000 * SPEED  # 30000
FEED_RAIL_INTACT = 16000 * SPEED
JERK_RAIL_FREE = 2000
JERK_RAIL_INTACT = 4500

D_STANDBY = 250
D_MIN = -1  # D_STANDBY - 25 * N
assert D_MIN >= -5
T_RAIL_JACK1 = 1.5
T_RAIL_JACK2 = 1.2
T_RAIL_FEEDER_JACK = 0.5
assert T_RAIL_FEEDER_JACK < T_RAIL_JACK1

''' Feeder '''
FEED_FEEDER_FEED = 25000 * SPEED  # 25000
FEED_FEEDER_DELIVER = 28000 * SPEED  # 30000
FEED_FEEDER_COMEBACK = 27000 * SPEED  # 28000

JERK_FEEDER_FEED = 60000
JERK_FEEDER_DELIVER = 10000

FEEDER_Z_IDLE = 16
FEEDER_Z_DELIVER = 718


VALUES_DEFINITION = [
    # 'name' 'value' 'speedy' 'no_change' 'no_save' 'range' 'description'
    {'name': 'NO_FEEDER', 'value': False, 'no_save': True}
]


class Recipe(object):
    def __init__(self):
        # inits values_dict, values_def, values_snapshot
        self.create_values_dict_from_list()
        self.set_speed(1)
        self.lock = Lock()

    def create_values_dict_from_list(self):
        self.values_dict = {item['name']: item['value']
                            for item in VALUES_DEFINITION}
        self.values_def = {item['name']: item for item in VALUES_DEFINITION}

    def set_speed(self, speed):
        assert 0.01 <= speed < 1.5
        self.speed = speed

    def sanity_check(self, values_dict):
        try:
            assert True
        except:
            return False
        return True

    def save_to_json(self):
        pass

    def load_from_json(self):
        pass

    def save_to_redis(self):
        pass

    def load_from_redis(self):
        pass

    def set_value(self, *args, **kwargs):
        # wrapper to run _set_value only once simultaneously
        self.lock.acquire()
        try:
            self._set_value(*args, **kwargs)
        finally:
            self.lock.release()

    def _set_value(self, name, value):
        # check name, value, range
        values_dict_new = self.get_snapshot()
        values_dict_new[name] = value
        res = self.sanity_check(values_dict_new)
        if res:
            self.values_dict = values_dict_new

    def get_snapshot(self, apply_speed=False):
        values_snapshot = self.values_dict.copy()
        if apply_speed:
            speed_snapshot = self.speed
            for value_name in values_snapshot:
                value_def = self.values_def[value_name]
                is_speedy = value_def.get('speedy', False)
                if is_speedy:
                    values_snapshot[value_name] *= speed_snapshot
        return values_snapshot


class RecipeSnapshot(object):
    def __init__(self, recipe):
        self.main_recipe = recipe
        self.update()

    def update(self):
        updates = []
        for key, value in self.main_recipe.get_snapshot(apply_speed=True).items():
            old_value = getattr(self, key, None)
            if value != old_value:
                setattr(self, key, value)
                updates.append(key)

        return updates
