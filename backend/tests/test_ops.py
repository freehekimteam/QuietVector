from app.core.ops import OpTracker


def test_op_tracker_flow():
    t = OpTracker()
    op = t.create('snapshot_restore', {'collection': 'c1'})
    assert op.stage == 'created'
    t.update(op.id, stage='saving', bytes_total=123)
    d = t.to_dict(op.id)
    assert d['stage'] == 'saving'
    assert d['meta']['bytes_total'] == 123
    t.update(op.id, stage='completed')
    assert t.to_dict(op.id)['stage'] == 'completed'

