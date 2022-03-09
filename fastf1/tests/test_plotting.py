import pytest
from fastf1.plotting import TEAM_COLORS, TEAM_TRANSLATE


def test_team_colors_dict_warning():
    with pytest.raises(KeyError):
        with pytest.warns(UserWarning):
            TEAM_COLORS['Ferrari']

    with pytest.warns(UserWarning):
        TEAM_COLORS.get('Ferrari', None)

    TEAM_COLORS['ferrari']
    TEAM_COLORS.get('ferrari', None)


def test_team_color_name_abbreviation_integrity():
    for value in TEAM_TRANSLATE.values():
        assert value in TEAM_COLORS
    assert len(TEAM_COLORS) == len(TEAM_TRANSLATE)
