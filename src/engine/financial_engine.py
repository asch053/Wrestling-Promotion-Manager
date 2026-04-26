from src.models.promotion.company import Company
from src.models.promotion.event import Event, EventScale
from src.models.wrestler.wrestler import KayfabeStatus
from src.engine.models.financial_report import FinancialReport
from src.engine.championship_manager import calculate_saturation_penalty, get_champion_prestige
from src.engine.dojo_engine import calculate_dojo_maintenance
from src.engine.stipulation_logic_handler import MatchStipulation, get_modifiers

def process_event_finances(company: Company, event: Event,
                           stipulation: MatchStipulation = MatchStipulation.STANDARD) -> FinancialReport:
    if company.game_state.current_day != 2:
        raise PermissionError("Finances can only be processed on The Ledger (Day 2).")

    # Scale multipliers
    scale_multipliers = {
        EventScale.HOUSE_SHOW: 1.0,
        EventScale.TV_TAPING: 2.0,
        EventScale.PPV: 5.0,
        EventScale.MEGA_EVENT: 10.0
    }
    
    scale_mult = scale_multipliers[event.scale]
    
    # 1. Staleness
    staleness_penalty = 1.0
    travel_cost = 10000
    if company.past_events:
        if company.past_events[-1].location == event.location:
            staleness_penalty = 0.8
            travel_cost = 0
            
    # 2. Company stats
    company_hype = company.calculate_current_hype()
    company_excitement = company.calculate_current_excitement()
    
    # 3. Revenue
    # Merch (Fluid Alignment + Champion Bonus)
    merch_revenue = 0
    talent_merch_cut = 0
    for idx, w in enumerate(company.current_roster):
        if w.kayfabe_status == KayfabeStatus.TWEENER:
            base_merch = min(int(w.popularity.hype * 60), 4000)
        else:
            base_merch = int(w.popularity.hype * 50)
        
        # Champion merch bonus: find if this wrestler holds a title
        # We need a way to match roster wrestlers to championship holders.
        # Use a roster-index-based UUID lookup if available, otherwise check by name.
        w_merch = base_merch
        # Check all championships for this wrestler (by matching current_holder)
        for c in company.championships:
            if c.is_active and c.current_holder is not None:
                # If champion prestige is available, apply bonus
                # We'll use the prestige of the highest belt
                champion_prestige = get_champion_prestige(c.current_holder, company.championships)
                if champion_prestige > 0:
                    w_merch = int(base_merch * (1 + champion_prestige / 100))
                break
        
        merch_revenue += w_merch
        if w.contract:
            talent_merch_cut += int(w_merch * w.contract.merch_cut_percentage)
            
    # Gate (with saturation penalty)
    stip_modifiers = get_modifiers(stipulation)
    
    saturation_penalty = calculate_saturation_penalty(company)
    gate_revenue = int(((company_hype * 10) + (company_excitement * 20)) * scale_mult * staleness_penalty) - saturation_penalty
    
    # Stipulation: deduct production cost (cage hire, ladder rig, etc.)
    gate_revenue -= stip_modifiers.production_cost
    
    # Stipulation staleness: update usage counter, apply -10% if overused
    stip_key = stipulation.value
    prev_count = company.stipulation_usage.get(stip_key, 0)
    # Reset all other counters when switching stipulation
    for k in list(company.stipulation_usage.keys()):
        if k != stip_key:
            company.stipulation_usage[k] = 0
    company.stipulation_usage[stip_key] = prev_count + 1
    
    if company.stipulation_usage[stip_key] > 3:
        gate_revenue = int(gate_revenue * 0.9)
    
    gate_revenue = max(0, gate_revenue)
    
    # TV Deal
    tv_revenue = int(company_hype * 50 * scale_mult)
    
    total_revenue = merch_revenue + gate_revenue + tv_revenue
    
    # 4. Expenses
    talent_appearance_fees = sum(w.contract.appearance_fee for w in company.current_roster if w.contract)
    talent_cost = talent_appearance_fees + talent_merch_cut
    
    staging_costs = {
        EventScale.HOUSE_SHOW: 5000,
        EventScale.TV_TAPING: 15000,
        EventScale.PPV: 50000,
        EventScale.MEGA_EVENT: 200000
    }
    staging_cost = staging_costs[event.scale]
    
    overhead_cost = 5000 + (len(company.past_events) * 100)
    
    # Medical Staff Expense
    medical_expense = company.medical_staff_level * 2000
    
    # Dojo Maintenance Expense (all owned Dojos)
    dojo_expense = sum(calculate_dojo_maintenance(d) for d in company.dojos)
    
    total_expenses = talent_cost + staging_cost + travel_cost + overhead_cost + medical_expense + dojo_expense
    
    # 5. Finalize
    net_profit = total_revenue - total_expenses
    
    company.bank_balance += net_profit
    company.past_events.append(event)
    
    return FinancialReport(
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        net_profit=net_profit,
        revenue_breakdown={
            "gate": gate_revenue,
            "merch": merch_revenue,
            "tv": tv_revenue
        },
        expense_breakdown={
            "talent": talent_cost,
            "staging": staging_cost,
            "travel": travel_cost,
            "overhead": overhead_cost,
            "medical": medical_expense,
            "dojo": dojo_expense,
            "production": stip_modifiers.production_cost,
        }
    )
