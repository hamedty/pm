from multiprocessing import Lock


VALUES_DEFINITION = [
    # 'name' 'value' 'speedy': False 'no_change': False 'no_save': False 'range' 'description'
    {'name': 'name', 'value': 'Basalin'},

    # General
    {'name': 'N', 'value': 10, 'no_change': True},
    {'name': 'SERVICE_FUNC_NO_FEEDER', 'value': False, 'no_save': True},
    {'name': 'SERVICE_FUNC_NO_CARTRIDGE', 'value': False, 'no_save': True},
    {'name': 'SERVICE_FUNC_NO_DOSING', 'value': False, 'no_save': True},

    # Station
    {'name': 'FEED_Z_UP', 'value': 10000, 'speedy': True},
    {'name': 'FEED_Z_DOWN', 'value': 15000, 'speedy': True},
    {'name': 'FEED_DANCE', 'value': 40000, 'speedy': True},
    {'name': 'STATION_Z_OUTPUT', 'value': 70},
    {'name': 'STATION_Z_OUTPUT_SAFE', 'value': 40},

    # Station - Vision
    {'name': 'ALIGN_SPEED_DOSING', 'value': 25000},
    {'name': 'ALIGN_SPEED_HOLDER', 'value': 25000},
    {'name': 'VISION_RETRIES_HOLDER', 'value': [3, 2, 2, 2]},
    {'name': 'VISION_RETRIES_DOSING', 'value': [4, 3, 3, 3, 3]},

    # Robot
    {'name': 'FEED_X_FORWARD', 'value': 23000, 'speedy': True},  # 30000
    {'name': 'FEED_X_BACKWARD', 'value': 28000, 'speedy': True},
    {'name': 'FEED_X_SHORT', 'value': 35000, 'speedy': True},
    {'name': 'FEED_Y_UP', 'value': 35000 * .5, 'speedy': True},
    {'name': 'FEED_Y_DOWN', 'value': 40000 * .5, 'speedy': True},
    {'name': 'FEED_Y_DOWN_CAP', 'value': 8000 * .5, 'speedy': True},
    {'name': 'FEED_Y_DOWN_PRESS', 'value': 5000 * .5, 'speedy': True},

    # Robot - Park
    {'name': 'X_PARK', 'value': 10},
    {'name': 'Y_PARK', 'value': 40},
    {'name': 'Y_CAPPING_DOWN', 'value': 10},

    # Rail
    {'name': 'FEED_RAIL_FREE', 'value': 25000, 'speedy': True},  # 30000
    {'name': 'FEED_RAIL_INTACT', 'value': 10000, 'speedy': True},  # 16000
    {'name': 'JERK_RAIL_FREE', 'value': 2000},
    {'name': 'JERK_RAIL_INTACT', 'value': 4500},
    {'name': 'D_STANDBY', 'value': 250},
    {'name': 'D_MIN', 'value': -1},  # D_STANDBY - 25 * N
    {'name': 'T_RAIL_JACK1', 'value': 1.5},
    {'name': 'T_RAIL_JACK2', 'value': 1.2},
    {'name': 'T_RAIL_FEEDER_JACK', 'value': 0.5},

    # Feeder
    {'name': 'FEED_FEEDER_FEED', 'value': 25000, 'speedy': True},
    {'name': 'FEED_FEEDER_DELIVER', 'value': 28000, 'speedy': True},
    {'name': 'FEED_FEEDER_COMEBACK', 'value': 27000, 'speedy': True},
    {'name': 'JERK_FEEDER_FEED', 'value': 60000},
    {'name': 'JERK_FEEDER_DELIVER', 'value': 10000},
    {'name': 'FEEDER_Z_IDLE', 'value': 16},
    {'name': 'FEEDER_Z_DELIVER', 'value': 718},
]


class Recipe(object):
    def __init__(self, redis):
        # inits values_dict, values_def, values_snapshot
        self.create_values_dict_from_list()
        self.set_speed(1)
        self.lock = Lock()
        self.redis = redis

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
            # assert Y_CAPPING_DOWN < Y_PARK
            # assert D_MIN >= -5
            # assert T_RAIL_FEEDER_JACK < T_RAIL_JACK1

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
