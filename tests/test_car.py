import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_car_advances():
    from track import Track
    from car import Car
    t = Track()
    c = Car(0, t)
    start_idx = c.waypoint_idx
    c.update(1 / 60)
    assert c.waypoint_idx >= start_idx, "Car should advance along waypoints"

def test_lane_switch():
    from track import Track
    from car import Car
    t = Track()
    c = Car(0, t)
    assert c.lane == 1
    c.switch_lane()
    assert c.lane == 2
    c.switch_lane()
    assert c.lane == 0

def test_boost():
    from track import Track
    from car import Car
    t = Track()
    c = Car(0, t)
    assert not c.activate_boost()
    c.boost_charges = 1
    assert c.activate_boost()
    assert c.boost_charges == 0
    assert c.boost_timer > 0

def test_lap_detection():
    from track import Track
    from car import Car
    t = Track()
    c = Car(0, t)
    c.waypoint_idx = t.num_waypoints - 2
    c.pos = list(t.lanes[1][c.waypoint_idx])
    c.base_speed = 10.0
    old_lap = c.lap
    for _ in range(120):
        c.update(1 / 60)
    assert c.lap > old_lap, "Car should have completed a lap"

if __name__ == "__main__":
    test_car_advances()
    test_lane_switch()
    test_boost()
    test_lap_detection()
    print("All car tests passed!")
