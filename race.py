from controls import TOTAL_LAPS


class RaceManager:
    def __init__(self, cars, track):
        self.cars = cars
        self.track = track
        self.started = False
        self.race_time = 0.0
        self.finished_order = []
        self.grace_timer = None

    def update(self, dt):
        if not self.started:
            return
        self.race_time += dt
        for car in self.cars:
            if not car.finished and car.lap >= TOTAL_LAPS:
                car.finished = True
                car.finish_time = self.race_time
                self.finished_order.append(car)
                if self.grace_timer is None:
                    self.grace_timer = 5.0
        if self.grace_timer is not None:
            self.grace_timer -= dt

    def get_positions(self):
        def key(car):
            if car.finished:
                return (-TOTAL_LAPS - 1, car.finish_time or 0)
            return (-car.lap, -car.waypoint_idx)
        return sorted(self.cars, key=key)

    def is_finished(self):
        if all(c.finished for c in self.cars):
            return True
        if self.grace_timer is not None and self.grace_timer <= 0:
            for car in self.cars:
                if not car.finished:
                    car.finished = True
                    car.finish_time = self.race_time
                    self.finished_order.append(car)
            return True
        return False

    def get_winner(self):
        return self.finished_order[0] if self.finished_order else None
