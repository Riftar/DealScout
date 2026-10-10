from dealscout.verify.util import as_whole_rupiah, prices_agree


def test_juta_figure_matches_whole_rupiah():
    assert prices_agree(885, 885_000_000)
    assert prices_agree(885_000_000, 885)
    assert as_whole_rupiah(885) == 885_000_000


def test_ribu_figure_matches_nearby_whole_rupiah():
    assert prices_agree(850_000, 825_000_000)
    assert as_whole_rupiah(850_000, 825_000_000) == 850_000_000


def test_two_whole_rupiah_prices_must_match_exactly():
    assert prices_agree(875_000_000, 875_000_000)
    assert not prices_agree(777_000_000, 875_000_000)
    assert not prices_agree(75_000_000, 875_000_000)


def test_two_small_unequal_figures_do_not_match():
    assert not prices_agree(60, 62)
    assert not prices_agree(885, 850)
