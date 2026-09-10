from txhash import tx_hash


def test_tx_hash_is_deterministic():
    assert tx_hash("a:b:c") == tx_hash("a:b:c")
    assert tx_hash("a:b:c") != tx_hash("a:b:d")
    assert len(tx_hash("seed")) == 16
