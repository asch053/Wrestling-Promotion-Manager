import pytest
from src.models.promotion.company import Company
from src.models.promotion.event import Event, EventScale
from src.models.wrestler.wrestler import Wrestler, InRingSkill, Psychology, Backstage, Popularity
from src.models.wrestler.contract import Contract
from src.engine.models.match_report import MatchReport
from src.engine.financial_engine import process_event_finances

@pytest.fixture
def sample_company():
    w1 = Wrestler(
        name="Wrestler A",
        in_ring=InRingSkill(strength=80, agility=80, stamina=100),
        psychology=Psychology(work_rate=80, selling=80),
        backstage=Backstage(ego=50, professionalism=80),
        popularity=Popularity(hype=100, heat=0, pop=100),
        contract=Contract(appearance_fee=5000, weekly_salary=2000, merch_cut_percentage=0.5)
    )
    
    w2 = Wrestler(
        name="Wrestler B",
        in_ring=InRingSkill(strength=70, agility=70, stamina=100),
        psychology=Psychology(work_rate=70, selling=70),
        backstage=Backstage(ego=50, professionalism=80),
        popularity=Popularity(hype=10, heat=10, pop=0),
        contract=Contract(appearance_fee=500, weekly_salary=200, merch_cut_percentage=0.05)
    )
    
    return Company(
        name="AWF",
        bank_balance=1000000,
        current_roster=[w1, w2]
    )

def test_company_decay_math(sample_company):
    assert sample_company.calculate_current_hype() == 110 # 100 + 10
    
    w3 = Wrestler(
        name="Legend",
        in_ring=InRingSkill(strength=80, agility=80, stamina=100),
        psychology=Psychology(work_rate=80, selling=80),
        backstage=Backstage(ego=50, professionalism=80),
        popularity=Popularity(hype=100, heat=0, pop=100)
    )
    sample_company.past_roster.append(w3)
    
    # Decay is 0.8
    assert sample_company.calculate_current_hype() == 110 + (100 * 0.8)

def test_financial_engine_profit(sample_company):
    event = Event(
        name="Mega Brawl",
        location="New York",
        scale=EventScale.HOUSE_SHOW,
        match_reports=[]
    )
    
    initial_balance = sample_company.bank_balance
    report = process_event_finances(sample_company, event)
    
    assert report.net_profit != 0
    assert sample_company.bank_balance == initial_balance + report.net_profit
    assert len(sample_company.past_events) == 1

def test_staleness_penalty_and_travel(sample_company):
    event1 = Event(name="Show 1", location="Chicago", scale=EventScale.HOUSE_SHOW, match_reports=[])
    report1 = process_event_finances(sample_company, event1)
    
    assert report1.expense_breakdown["travel"] == 10000
    
    # Event 2 same location
    event2 = Event(name="Show 2", location="Chicago", scale=EventScale.HOUSE_SHOW, match_reports=[])
    report2 = process_event_finances(sample_company, event2)
    
    assert report2.expense_breakdown["travel"] == 0
    # Gate should be 20% less due to staleness penalty of 0.8.
    # Note: the excitement input changes because past_events changed, but let's just assert the penalty applies
    # Base hype = 110. Base excitement = 50. Gate = (110*10 + 50*20)*1 = 2100.
    # Event 2: Excitement = 50. Gate = 2100 * 0.8 = 1680.
    assert report2.revenue_breakdown["gate"] == int(report1.revenue_breakdown["gate"] * 0.8)

def test_merch_commission(sample_company):
    event = Event(name="Show", location="NY", scale=EventScale.HOUSE_SHOW, match_reports=[])
    report = process_event_finances(sample_company, event)
    
    # W1 hype 100 * 50 = 5000 merch. cut = 0.5 -> 2500
    # W2 hype 10 * 50 = 500 merch. cut = 0.05 -> 25
    assert report.expense_breakdown["talent"] == 5000 + 500 + 2500 + 25
