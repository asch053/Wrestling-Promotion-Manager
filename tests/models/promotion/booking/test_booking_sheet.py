import pytest
from uuid import uuid4
from pydantic import ValidationError
from src.models.promotion.booking.booking_sheet import BookingSheet, MatchType, ScriptingStyle
from src.models.promotion.booking.runsheet import Runsheet

def test_valid_called_in_ring_booking():
    wrestler_1 = uuid4()
    wrestler_2 = uuid4()
    
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[wrestler_1], [wrestler_2]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=wrestler_1,
        expected_runsheet=None
    )
    
    assert booking.scripting_style == ScriptingStyle.CALLED_IN_RING
    assert booking.expected_runsheet is None

def test_valid_strict_booking():
    wrestler_1 = uuid4()
    wrestler_2 = uuid4()
    move_1 = uuid4()
    
    runsheet = Runsheet(spots=[move_1])
    
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[wrestler_1], [wrestler_2]],
        scripting_style=ScriptingStyle.STRICT,
        designated_winner=wrestler_2,
        expected_runsheet=runsheet
    )
    
    assert booking.scripting_style == ScriptingStyle.STRICT
    assert booking.expected_runsheet is not None
    assert len(booking.expected_runsheet.spots) == 1

def test_valid_winner():
    wrestler_1 = uuid4()
    wrestler_2 = uuid4()
    
    booking = BookingSheet(
        match_type=MatchType.ONE_ON_ONE,
        teams=[[wrestler_1], [wrestler_2]],
        scripting_style=ScriptingStyle.CALLED_IN_RING,
        designated_winner=wrestler_1
    )
    
    flat_participants = [w_id for team in booking.teams for w_id in team]
    assert booking.designated_winner in flat_participants

def test_strict_booking_missing_runsheet():
    wrestler_1 = uuid4()
    wrestler_2 = uuid4()
    
    with pytest.raises(ValidationError) as exc_info:
        BookingSheet(
            match_type=MatchType.ONE_ON_ONE,
            teams=[[wrestler_1], [wrestler_2]],
            scripting_style=ScriptingStyle.STRICT,
            designated_winner=wrestler_1,
            expected_runsheet=None
        )
    assert "expected_runsheet must be provided" in str(exc_info.value).lower()

def test_audible_booking_missing_runsheet():
    wrestler_1 = uuid4()
    wrestler_2 = uuid4()
    
    with pytest.raises(ValidationError) as exc_info:
        BookingSheet(
            match_type=MatchType.ONE_ON_ONE,
            teams=[[wrestler_1], [wrestler_2]],
            scripting_style=ScriptingStyle.AUDIBLE,
            designated_winner=wrestler_1,
            expected_runsheet=None
        )
    assert "expected_runsheet must be provided" in str(exc_info.value).lower()

def test_invalid_winner():
    wrestler_1 = uuid4()
    wrestler_2 = uuid4()
    random_guy = uuid4() # Not in match
    
    with pytest.raises(ValidationError) as exc_info:
        BookingSheet(
            match_type=MatchType.ONE_ON_ONE,
            teams=[[wrestler_1], [wrestler_2]],
            scripting_style=ScriptingStyle.CALLED_IN_RING,
            designated_winner=random_guy
        )
    assert "must be one of the participants" in str(exc_info.value).lower()
