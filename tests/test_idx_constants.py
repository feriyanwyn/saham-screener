"""Unit tests for IDX Market Constants, Tick Sizes, and ARA/ARB rules."""
from config.idx_constants import get_tick_size, align_to_tick, get_ara_arb_limits, LOT_SIZE


def test_lot_size():
    assert LOT_SIZE == 100


def test_tick_sizes():
    # Kelompok < Rp200: Fraksi Rp1
    assert get_tick_size(50) == 1
    assert get_tick_size(199) == 1

    # Kelompok Rp200 - < Rp500: Fraksi Rp2
    assert get_tick_size(200) == 2
    assert get_tick_size(498) == 2

    # Kelompok Rp500 - < Rp2000: Fraksi Rp5
    assert get_tick_size(500) == 5
    assert get_tick_size(1995) == 5

    # Kelompok Rp2000 - < Rp5000: Fraksi Rp10
    assert get_tick_size(2000) == 10
    assert get_tick_size(4990) == 10

    # Kelompok >= Rp5000: Fraksi Rp25
    assert get_tick_size(5000) == 25
    assert get_tick_size(9850) == 25


def test_align_to_tick():
    # Fraksi Rp1
    assert align_to_tick(150.4) == 150
    assert align_to_tick(150.4, round_up=True) == 151

    # Fraksi Rp2 (Harga 350)
    assert align_to_tick(351) == 350
    assert align_to_tick(351, round_up=True) == 352

    # Fraksi Rp5 (Harga 1200)
    assert align_to_tick(1203) == 1200
    assert align_to_tick(1203, round_up=True) == 1205

    # Fraksi Rp10 (Harga 3400)
    assert align_to_tick(3407) == 3400
    assert align_to_tick(3407, round_up=True) == 3410

    # Fraksi Rp25 (Harga 9800)
    assert align_to_tick(9812) == 9800
    assert align_to_tick(9812, round_up=True) == 9825


def test_ara_arb_limits():
    # Saham harga 100: Batas 35% -> ARA = 135, ARB = 65
    ara, arb = get_ara_arb_limits(100)
    assert ara == 135
    assert arb == 65

    # Saham harga 1000: Batas 25% -> ARA = 1250, ARB = 750
    ara, arb = get_ara_arb_limits(1000)
    assert ara == 1250
    assert arb == 750

    # Saham harga 10000: Batas 20% -> ARA = 12000, ARB = 8000
    ara, arb = get_ara_arb_limits(10000)
    assert ara == 12000
    assert arb == 8000
