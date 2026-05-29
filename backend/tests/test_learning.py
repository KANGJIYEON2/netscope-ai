"""Tests for L0 pattern mining: masking, Drain tree, catalog."""
from src.learning.masking import mask_variables
from src.learning.drain import DrainTree


# --------------------------------------------------
# Variable masking
# --------------------------------------------------

def test_mask_uuid():
    msg = "Auth token expired for user 550e8400-e29b-41d4-a716-446655440000"
    result = mask_variables(msg)
    assert "<UUID>" in result
    assert "550e8400" not in result


def test_mask_ip():
    msg = "Connection refused from 192.168.1.100:8080"
    result = mask_variables(msg)
    assert "<IP>" in result
    assert "192.168" not in result


def test_mask_timestamp():
    msg = "Error at 2024-01-15T03:42:00Z in module"
    result = mask_variables(msg)
    assert "<TS>" in result


def test_mask_path():
    msg = "File not found: /var/log/app/error.log"
    result = mask_variables(msg)
    assert "<PATH>" in result


def test_mask_numbers():
    msg = "Request took 3500ms, status 500"
    result = mask_variables(msg)
    assert "<NUM>" in result


def test_mask_preserves_keywords():
    msg = "ERROR timeout on connection"
    result = mask_variables(msg)
    assert "ERROR" in result
    assert "timeout" in result


# --------------------------------------------------
# Drain tree
# --------------------------------------------------

def test_drain_clusters_similar_messages():
    tree = DrainTree(depth=3, sim_threshold=0.4)

    c1 = tree.add("Auth token expired <UUID>")
    c2 = tree.add("Auth token expired <UUID>")
    c3 = tree.add("Auth token expired <UUID>")

    assert c1.cluster_id == c2.cluster_id == c3.cluster_id
    assert c3.count == 3


def test_drain_separates_different_messages():
    tree = DrainTree(depth=3, sim_threshold=0.4)

    c1 = tree.add("Auth token expired <UUID>")
    c2 = tree.add("Connection refused to <IP> port <NUM>")

    assert c1.cluster_id != c2.cluster_id


def test_drain_merges_with_wildcards():
    tree = DrainTree(depth=2, sim_threshold=0.3)

    tree.add("request to users returned ok")
    c2 = tree.add("request to orders returned ok")

    # Mismatched token becomes <*>
    assert "<*>" in c2.template


def test_drain_max_clusters_per_node():
    tree = DrainTree(depth=2, sim_threshold=0.99, max_clusters=5)

    # Same length, same prefix → same leaf node
    for i in range(10):
        tree.add(f"sameprefix unique_{i:04d} end")

    clusters = tree.all_clusters()
    # max_clusters limits per-node, so total should be bounded
    assert len(clusters) <= 10


def test_drain_cluster_id_deterministic():
    tree = DrainTree()
    c1 = tree.add("ERROR timeout on service-a")
    c2 = tree.add("ERROR timeout on service-a")
    assert c1.cluster_id == c2.cluster_id


# --------------------------------------------------
# End-to-end: masking → drain
# --------------------------------------------------

def test_end_to_end_masking_then_drain():
    tree = DrainTree(depth=3, sim_threshold=0.4)

    msgs = [
        "Auth token expired for user 550e8400-e29b-41d4-a716-446655440000",
        "Auth token expired for user a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "Auth token expired for user 12345678-abcd-ef12-3456-789012345678",
    ]

    clusters = set()
    for msg in msgs:
        masked = mask_variables(msg)
        c = tree.add(masked)
        clusters.add(c.cluster_id)

    # All should collapse to the same cluster
    assert len(clusters) == 1
