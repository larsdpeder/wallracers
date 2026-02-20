import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_track_creation():
    from track import Track
    t = Track()
    assert t.num_waypoints == 600
    assert len(t.lanes) == 3
    for lane in t.lanes:
        assert len(lane) == 600

def test_waypoints_form_closed_loop():
    from track import Track
    import math
    t = Track()
    first = t.centerline[0]
    last = t.centerline[-1]
    dist = math.hypot(first[0] - last[0], first[1] - last[1])
    assert dist < 50, f"Track not closed: gap of {dist}"

def test_lanes_are_offset():
    from track import Track
    import math
    t = Track()
    for i in range(0, 600, 60):
        left = t.lanes[0][i]
        center = t.lanes[1][i]
        right = t.lanes[2][i]
        lc = math.hypot(left[0]-center[0], left[1]-center[1])
        cr = math.hypot(center[0]-right[0], center[1]-right[1])
        assert 30 < lc < 55, f"Left-center offset {lc} out of range at {i}"
        assert 30 < cr < 55, f"Center-right offset {cr} out of range at {i}"

if __name__ == "__main__":
    test_track_creation()
    test_waypoints_form_closed_loop()
    test_lanes_are_offset()
    print("All track tests passed!")
