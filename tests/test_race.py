import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_race_positions():
    from track import Track
    from car import Car
    from race import RaceManager
    t = Track()
    c0 = Car(0, t)
    c1 = Car(1, t)
    c0.lap = 2
    c0.waypoint_idx = 100
    c1.lap = 1
    c1.waypoint_idx = 300
    rm = RaceManager([c0, c1], t)
    positions = rm.get_positions()
    assert positions[0] is c0, "Car with more laps should be first"

def test_race_finish():
    from track import Track
    from car import Car
    from race import RaceManager
    from controls import TOTAL_LAPS
    t = Track()
    c0 = Car(0, t)
    c1 = Car(1, t)
    rm = RaceManager([c0, c1], t)
    rm.started = True
    c0.lap = TOTAL_LAPS
    c0.finished = True
    c0.finish_time = 60.0
    rm.finished_order.append(c0)
    c1.lap = TOTAL_LAPS
    c1.finished = True
    c1.finish_time = 62.0
    rm.finished_order.append(c1)
    assert rm.is_finished()
    assert rm.get_winner() is c0

def test_item_boost_pickup():
    from track import Track
    from car import Car
    from items import Item
    t = Track()
    c = Car(0, t)
    c.pos = list(t.lanes[1][100])
    item = Item(t, 100, 1, "boost_pickup")
    assert c.boost_charges == 0
    hit = item.check_collision(c)
    assert hit
    assert c.boost_charges == 1

def test_item_oil_slick():
    from track import Track
    from car import Car
    from items import Item
    t = Track()
    c = Car(0, t)
    c.pos = list(t.lanes[1][200])
    item = Item(t, 200, 1, "oil_slick")
    item.check_collision(c)
    assert c.slow_timer > 0

def test_shield_blocks_oil():
    from track import Track
    from car import Car
    from items import Item
    t = Track()
    c = Car(0, t)
    c.has_shield = True
    c.pos = list(t.lanes[1][200])
    item = Item(t, 200, 1, "oil_slick")
    item.check_collision(c)
    assert c.slow_timer == 0
    assert not c.has_shield

if __name__ == "__main__":
    test_race_positions()
    test_race_finish()
    test_item_boost_pickup()
    test_item_oil_slick()
    test_shield_blocks_oil()
    print("All race/item tests passed!")
