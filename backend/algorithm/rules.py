from .classes import Rule, RuleType, Hand_Size, Preferability, Connectivity, Game_Type, Usage, User_Type
from . import config
from database.models import Ergonomy, Price_History, SessionLocal


def _latest_price(mouse):
    """Most recent Price_History row for a mouse, or None. Plain SQLAlchemy."""
    with SessionLocal() as session:
        return (
            session.query(Price_History)
            .filter_by(mouse_id=mouse.id)
            .order_by(Price_History.date.desc())
            .first()
        )


# ── General rule helpers ──────────────────────────────────────────────────────

def _hand_size_compatible(facts: dict, mouse) -> bool:
    hand_size = facts.get("hand_size")
    length = mouse.length
    if length is None:
        return False
    if hand_size == Hand_Size.SMALL:
        return length < config.SMALL_HAND_SIZE
    if hand_size == Hand_Size.MEDIUM:
        return config.SMALL_HAND_SIZE <= length <= config.MEDIUM_HAND_SIZE
    if hand_size == Hand_Size.LARGE:
        return length > config.MEDIUM_HAND_SIZE
    return False

def _hand_size_explanation(facts: dict, mouse) -> str:
    hand_size = facts.get("hand_size")
    length = mouse.length
    if length is None:
        return "No size data available for this mouse"
    label = hand_size.value if hand_size else "unknown"
    if hand_size == Hand_Size.SMALL:
        if length >= config.SMALL_HAND_SIZE:
            return f"At {length}mm this mouse is too large for small hands (under {config.SMALL_HAND_SIZE}mm)"
        return f"At {length}mm this mouse fits small hands well"
    if hand_size == Hand_Size.MEDIUM:
        if length < config.SMALL_HAND_SIZE:
            return f"At {length}mm this mouse is too compact for medium hands"
        if length > config.MEDIUM_HAND_SIZE:
            return f"At {length}mm this mouse is too long for medium hands (max {config.MEDIUM_HAND_SIZE}mm)"
        return f"At {length}mm this mouse is a comfortable fit for medium hands"
    if hand_size == Hand_Size.LARGE:
        if length <= config.MEDIUM_HAND_SIZE:
            return f"At {length}mm this mouse is too small for large hands (needs over {config.MEDIUM_HAND_SIZE}mm)"
        return f"At {length}mm this mouse gives large hands plenty of room"
    return f"Mouse length {length}mm does not match your {label} hand size"


# Filter Price_History to the latest price entry per mouse, used for budget check
def _price_of(facts: dict, mouse):
    """Latest price for a mouse. Prefers a preloaded facts['prices'] map (fast,
    one query for all mice); falls back to a direct lookup if absent."""
    prices = facts.get("prices")
    if prices is not None:
        return prices.get(mouse.id)
    row = _latest_price(mouse)
    return row.price if row is not None else None

def _budget_compatible(facts: dict, mouse) -> bool:
    budget: tuple[float, float] = facts.get("budget")
    budget_midpoint = (budget[0] + budget[1]) / 2
    budget_buffer = (
        budget[0] - budget_midpoint * (1 - config.BUDGET_BUFFER),
        budget[1] + budget_midpoint * (1 - config.BUDGET_BUFFER),
    )
    mouse_price = _price_of(facts, mouse)
    if mouse_price is None:
        return False
    return budget_buffer[0] <= mouse_price <= budget_buffer[1]

def _budget_explanation(facts: dict, mouse) -> str:
    budget: tuple[float, float] = facts.get("budget")
    price = _price_of(facts, mouse)
    if price is None:
        return "No pricing information is available for this mouse"
    if price > budget[1]:
        return f"Priced at ${price:.2f}, this mouse exceeds your maximum budget of ${budget[1]:.2f}"
    if price < budget[0]:
        return f"Priced at ${price:.2f}, this mouse falls below your minimum budget of ${budget[0]:.2f}"
    return f"Priced at ${price:.2f}, this mouse fits within your budget of ${budget[0]:.2f}–${budget[1]:.2f}"


# ── Value for money (soft) ────────────────────────────────────────────────────
# A continuous nudge that rewards a lower price: +ve below the budget top,
# 0 at the top, -ve above it — normalised by the budget span so it's more
# sensitive for tighter budgets. Independent of the hard budget filter and the
# 25% price-tag band, which are left untouched.

def _value_weight(facts: dict, mouse) -> float:
    budget = facts.get("budget")
    if budget is None:
        return 0.0
    price = _price_of(facts, mouse)
    if price is None:
        return 0.0
    low, high = budget
    span = (high - low) or high or 1.0
    relative = (high - price) / span   # +1 at the budget floor, 0 at the ceiling
    relative = max(-1.5, min(1.5, relative))
    return relative * config.VALUE_FACTOR

def _value_explanation(facts: dict, mouse) -> str:
    budget = facts.get("budget")
    price = _price_of(facts, mouse)
    if budget is None or price is None:
        return "No budget set to judge value against"
    low, high = budget
    if price <= low:
        return f"At ${price:.2f} this is at the low end of your budget — strong value for money"
    if price <= high:
        return f"At ${price:.2f} this sits comfortably inside your ${low:.0f}–${high:.0f} budget"
    return f"At ${price:.2f} this is above your ${high:.0f} budget — you're paying a premium for it"


_CONN_LABEL = {
    Connectivity.STRICTLY_WIRELESS: "strictly wireless",
    Connectivity.BOTH: "wired + wireless",
    Connectivity.STRICTLY_WIRED: "strictly wired",
}


def _mouse_conn_type(mouse):
    """The mouse's connectivity type from its boolean flags, or None."""
    conn = mouse.connectivity
    if conn is None:
        return None
    wireless = bool(conn.bluetooth or conn.dongle)
    wired = bool(conn.wired)
    if wireless and wired:
        return Connectivity.BOTH
    if wireless:
        return Connectivity.STRICTLY_WIRELESS
    if wired:
        return Connectivity.STRICTLY_WIRED
    return None


def _conn_acceptable(desired, actual) -> bool:
    """Whether a mouse's connectivity type satisfies the desired type. A `both`
    mouse satisfies a wireless- or wired-only wish (it can do either)."""
    if actual is None:
        return False
    if desired == Connectivity.BOTH:
        return actual == Connectivity.BOTH
    if desired == Connectivity.STRICTLY_WIRELESS:
        return actual in (Connectivity.STRICTLY_WIRELESS, Connectivity.BOTH)
    if desired == Connectivity.STRICTLY_WIRED:
        return actual in (Connectivity.STRICTLY_WIRED, Connectivity.BOTH)
    return True


def _connectivity_rule_type(facts: dict) -> RuleType:
    # A definitive choice (yes/no on wireless) filters; "preferably" only scores.
    return RuleType.HARD if facts.get("connectivity_strict") else RuleType.SOFT


def _connectivity_compatible(facts: dict, mouse) -> bool:
    desired = facts.get("connectivity")
    if desired is None:
        return True
    return _conn_acceptable(desired, _mouse_conn_type(mouse))


def _connectivity_weight(facts: dict, mouse) -> float:
    desired = facts.get("connectivity")
    if desired is None:
        return 0.0
    actual = _mouse_conn_type(mouse)
    if actual is None:
        return config.NEGATIVE_NORMAL_FACTOR
    if actual == desired:
        return config.MAJOR_FACTOR          # exact product-type match
    if _conn_acceptable(desired, actual):
        return config.MINOR_FACTOR           # usable but not the ideal type
    return config.NEGATIVE_MAJOR_FACTOR       # wrong type


def _connectivity_explanation(facts: dict, mouse) -> str:
    desired = facts.get("connectivity")
    actual = _mouse_conn_type(mouse)
    if actual is None:
        return "No connectivity information is available for this mouse"
    want = _CONN_LABEL.get(desired, "your preference")
    have = _CONN_LABEL.get(actual, "unknown")
    if actual == desired:
        return f"This is a {have} mouse, exactly the connectivity you want"
    if _conn_acceptable(desired, actual):
        return f"This is a {have} mouse — it covers your {want} need, though it isn't strictly that type"
    return f"This is a {have} mouse, but you want {want}"


def _left_hand_compatible(facts: dict, mouse) -> bool:
    return mouse.left_fit

def _left_hand_explanation(facts: dict, mouse) -> str:
    if not mouse.left_fit:
        return "This mouse is shaped for right-handed use and may be uncomfortable for left-handed users"
    return "This mouse is compatible with left-handed use"


def _type_of_user_weight(facts: dict, mouse) -> float:
    user_type = facts.get("user_type")
    gaming_mouse = mouse.gaming_specs
    battery_life = mouse.min_battery_life
    required_battery_life = battery_life > 60

    if user_type == User_Type.GAMER:
        if gaming_mouse is not None:
            return config.MODERATE_FACTOR
    elif user_type == User_Type.OFFICE_WORKER:
        if gaming_mouse is not None:
            return gaming_mouse.rgb * config.NEGATIVE_MINOR_FACTOR + required_battery_life * config.NORMAL_FACTOR
        return required_battery_life * config.NORMAL_FACTOR
    else:
        return required_battery_life * config.MODERATE_FACTOR
    return 0.0

def _type_of_user_explanation(facts: dict, mouse) -> str:
    user_type = facts.get("user_type")
    gaming_mouse = mouse.gaming_specs
    battery_life = mouse.min_battery_life
    has_good_battery = battery_life > 60

    if user_type == User_Type.GAMER:
        if gaming_mouse is not None:
            return "This is a gaming mouse with dedicated specs suited for gaming"
        return "This mouse lacks dedicated gaming features such as a high-performance sensor or gaming software"

    if user_type == User_Type.OFFICE_WORKER:
        issues = []
        positives = []
        if gaming_mouse is not None and gaming_mouse.rgb:
            issues.append("RGB lighting can look out of place in a professional office setting")
        if not has_good_battery:
            issues.append(f"Battery life of {battery_life}h is under 60h — you may need to recharge frequently at the office")
        else:
            positives.append(f"Good battery life ({battery_life}h) keeps you productive without interruptions")
        if gaming_mouse is None:
            positives.append("Non-gaming design gives it a clean, professional appearance")
        if issues:
            return "; ".join(issues)
        return "; ".join(positives) if positives else "Suitable for office use"

    # STUDENT
    if not has_good_battery:
        return f"Battery life of {battery_life}h is under 60h — may run low during long study sessions away from a charger"
    return f"Battery life of {battery_life}h is solid for a student who is often away from a power source"


# ── General rules dict ────────────────────────────────────────────────────────

GENERAL_RULES: dict[str, Rule] = {

    config.HAND_SIZE: Rule(
        id=config.HAND_SIZE,
        rule_type=RuleType.HARD,
        description="Mouse size matches user hand size",
        applicable_to_users=lambda facts: facts.get("hand_size") is not None,
        mouse_compatibility=_hand_size_compatible,
        explanation=_hand_size_explanation,
    ),

    config.CONNECTIVITY: Rule(
        id=config.CONNECTIVITY,
        rule_type=_connectivity_rule_type,
        description="Mouse connectivity type matches the user's preference",
        applicable_to_users=lambda facts: facts.get("connectivity") is not None,
        mouse_compatibility=_connectivity_compatible,
        weight=_connectivity_weight,
        explanation=_connectivity_explanation,
    ),

    config.BUDGET: Rule(
        id=config.BUDGET,
        rule_type=RuleType.HARD,
        description="Mouse price falls within user budget",
        applicable_to_users=lambda facts: facts.get("budget") is not None,
        mouse_compatibility=_budget_compatible,
        explanation=_budget_explanation,
    ),

    config.VALUE: Rule(
        id=config.VALUE,
        rule_type=RuleType.SOFT,
        description="Cheaper mice score higher for value for money",
        applicable_to_users=lambda facts: facts.get("budget") is not None,
        mouse_compatibility=True,
        weight=_value_weight,
        explanation=_value_explanation,
    ),

    config.LEFT_HANDED: Rule(
        id=config.LEFT_HANDED,
        rule_type=RuleType.HARD,
        description="Mouse supports left-handed use",
        applicable_to_users=lambda facts: facts.get("left_hand") is not None,
        mouse_compatibility=_left_hand_compatible,
        explanation=_left_hand_explanation,
    ),

    config.USER_TYPE: Rule(
        id=config.USER_TYPE,
        rule_type=RuleType.SOFT,
        description="Mouse traits suit the user's usage type",
        applicable_to_users=lambda facts: facts.get("user_type") is not None,
        mouse_compatibility=True,
        weight=_type_of_user_weight,
        explanation=_type_of_user_explanation,
    ),
}


# ── Gamer rule helpers ────────────────────────────────────────────────────────

def _type_of_game_rule_type(facts: dict) -> RuleType:
    if facts.get("type_of_game") == Game_Type.MMORPG:
        return RuleType.HARD
    return RuleType.SOFT

def _type_of_game_compatibility(facts: dict, mouse) -> bool:
    type_of_game = facts.get("type_of_game")
    if type_of_game == Game_Type.MMORPG:
        return mouse.number_of_buttons >= config.MINIMUM_BUTTONS_MMORPG
    return True

def _type_of_game_weight(facts: dict, mouse) -> float:
    type_of_game = facts.get("type_of_game")
    gaming_mouse_specs = mouse.gaming_specs
    if gaming_mouse_specs is not None:
        tracking_speed = gaming_mouse_specs.tracking_speed
    dpi = mouse.max_DPI
    polling_rate = mouse.max_polling_rate
    weight = mouse.weight

    if type_of_game == Game_Type.MMORPG or type_of_game == Game_Type.NOT_MENTIONED:
        return 0.0
    elif type_of_game == Game_Type.FPS:
        required_dpi = dpi >= config.REQUIRED_DPI_FPS
        required_mouse_weight = weight <= config.REQUIRED_MOUSE_WEIGHT_FPS
        if gaming_mouse_specs is not None:
            required_tracking_speed = tracking_speed >= config.REQUIRED_TRACKING_SPEED_FPS
            return (required_dpi + required_mouse_weight + required_tracking_speed) * config.MODERATE_FACTOR
        return (required_dpi + required_mouse_weight) * config.MAJOR_FACTOR
    elif type_of_game == Game_Type.RTS:
        required_dpi = dpi >= config.REQUIRED_DPI_RTS
        required_polling_rate = polling_rate >= config.REQUIRED_POLLING_RATE_RTS
        return (required_dpi + required_polling_rate) * config.MODERATE_FACTOR
    elif type_of_game == Game_Type.MOBA:
        required_dpi = dpi >= config.REQUIRED_DPI_MOBA
        required_polling_rate = polling_rate >= config.REQUIRED_POLLING_RATE_MOBA
        return (required_dpi + required_polling_rate) * config.NORMAL_FACTOR
    return 0.0

def _type_of_game_explanation(facts: dict, mouse) -> str:
    type_of_game = facts.get("type_of_game")
    buttons = mouse.number_of_buttons
    gaming_specs = mouse.gaming_specs
    dpi = mouse.max_DPI
    polling_rate = mouse.max_polling_rate
    weight = mouse.weight

    if type_of_game == Game_Type.MMORPG:
        if buttons < config.MINIMUM_BUTTONS_MMORPG:
            return (
                f"MMORPGs need at least {config.MINIMUM_BUTTONS_MMORPG} buttons for ability bindings — "
                f"this mouse only has {buttons}"
            )
        return f"With {buttons} buttons this mouse handles MMORPG keybinds comfortably"

    if type_of_game == Game_Type.FPS:
        issues, positives = [], []
        if dpi >= config.REQUIRED_DPI_FPS:
            positives.append(f"high DPI ({dpi}) for precise aiming")
        else:
            issues.append(f"DPI of {dpi} is below the {config.REQUIRED_DPI_FPS} recommended for FPS")
        if weight <= config.REQUIRED_MOUSE_WEIGHT_FPS:
            positives.append(f"lightweight at {weight}g for fast flicks")
        else:
            issues.append(f"at {weight}g it is heavier than the recommended {config.REQUIRED_MOUSE_WEIGHT_FPS}g for FPS")
        if gaming_specs is not None and gaming_specs.tracking_speed < config.REQUIRED_TRACKING_SPEED_FPS:
            issues.append(f"tracking speed of {gaming_specs.tracking_speed} IPS is below the {config.REQUIRED_TRACKING_SPEED_FPS} IPS ideal for FPS")
        if issues:
            return "FPS concerns: " + "; ".join(issues)
        return "FPS-ready: " + ", ".join(positives)

    if type_of_game == Game_Type.RTS:
        issues, positives = [], []
        if dpi >= config.REQUIRED_DPI_RTS:
            positives.append(f"DPI of {dpi} suits rapid unit selection")
        else:
            issues.append(f"DPI of {dpi} is below the {config.REQUIRED_DPI_RTS} recommended for RTS")
        if polling_rate >= config.REQUIRED_POLLING_RATE_RTS:
            positives.append(f"polling rate of {polling_rate}Hz gives responsive cursor tracking")
        else:
            issues.append(f"polling rate of {polling_rate}Hz is below the {config.REQUIRED_POLLING_RATE_RTS}Hz needed for RTS")
        if issues:
            return "RTS concerns: " + "; ".join(issues)
        return "RTS-ready: " + ", ".join(positives)

    if type_of_game == Game_Type.MOBA:
        issues, positives = [], []
        if dpi >= config.REQUIRED_DPI_MOBA:
            positives.append(f"DPI of {dpi} supports accurate skill shots")
        else:
            issues.append(f"DPI of {dpi} is below the {config.REQUIRED_DPI_MOBA} recommended for MOBA")
        if polling_rate >= config.REQUIRED_POLLING_RATE_MOBA:
            positives.append(f"polling rate of {polling_rate}Hz keeps inputs responsive")
        else:
            issues.append(f"polling rate of {polling_rate}Hz is below the {config.REQUIRED_POLLING_RATE_MOBA}Hz needed for MOBA")
        if issues:
            return "MOBA concerns: " + "; ".join(issues)
        return "MOBA-ready: " + ", ".join(positives)

    return "No game-specific requirements to evaluate"


def _mouse_weight_weightage(facts: dict, mouse) -> float:
    weight = mouse.weight
    if weight <= config.LIGHT_WEIGHT:
        return config.MAJOR_FACTOR
    elif weight <= config.MODERATE_WEIGHT:
        return config.NORMAL_FACTOR
    return 0.0

def _mouse_weight_explanation(facts: dict, mouse) -> str:
    weight = mouse.weight
    if weight <= config.LIGHT_WEIGHT:
        return f"At {weight}g this is a lightweight mouse — ideal for fast flicks and low fatigue during long sessions"
    elif weight <= config.MODERATE_WEIGHT:
        return f"At {weight}g this mouse is moderately heavy — manageable but may feel fatiguing over very long sessions"
    return f"At {weight}g this mouse is on the heavier side, which can slow reaction time and cause wrist fatigue for gamers"


def _mouse_rgb_weightage(facts: dict, mouse) -> float:
    gaming_mouse = mouse.gaming_specs
    if gaming_mouse is not None:
        return gaming_mouse.rgb * config.MINOR_FACTOR
    return 0.0

def _mouse_rgb_explanation(facts: dict, mouse) -> str:
    gaming_specs = mouse.gaming_specs
    if gaming_specs is not None and gaming_specs.rgb:
        return "This mouse features RGB lighting, matching your preference for a vibrant gaming setup"
    return "This mouse does not have RGB lighting"


# ── Gamer rules dict ──────────────────────────────────────────────────────────

GAMER_RULES: dict[str, Rule] = {

    config.TYPE_OF_GAME: Rule(
        id=config.TYPE_OF_GAME,
        rule_type=_type_of_game_rule_type,
        description="Mouse specs suit the user's game genre",
        applicable_to_users=lambda facts: facts.get("type_of_game") is not None,
        mouse_compatibility=_type_of_game_compatibility,
        weight=_type_of_game_weight,
        explanation=_type_of_game_explanation,
    ),

    config.LIGHT_WEIGHT_MOUSE: Rule(
        id=config.LIGHT_WEIGHT_MOUSE,
        rule_type=RuleType.SOFT,
        description="User prefers a lightweight mouse",
        applicable_to_users=lambda facts: facts.get("light_weight") is not None,
        mouse_compatibility=True,
        weight=_mouse_weight_weightage,
        explanation=_mouse_weight_explanation,
    ),

    config.RGB_LIGHTING: Rule(
        id=config.RGB_LIGHTING,
        rule_type=RuleType.SOFT,
        description="User wants RGB lighting",
        applicable_to_users=lambda facts: facts.get("rgb") is not None,
        mouse_compatibility=True,
        weight=_mouse_rgb_weightage,
        explanation=_mouse_rgb_explanation,
    ),
}


# ── Student rule helpers ──────────────────────────────────────────────────────

def _travel_portability_weight(facts: dict, mouse) -> float:
    usage = facts.get("travel_portability")
    weight = mouse.weight
    conn = mouse.connectivity
    bluetooth = conn.bluetooth
    dongle = conn.dongle
    required_weight = weight <= config.REQUIRED_WEIGHT_PORT
    is_wireless = bluetooth or dongle

    if usage == Usage.MOST_OF_THE_TIME:
        return (is_wireless + required_weight) * config.DOMINANT_FACTOR
    elif usage == Usage.OFTEN:
        return (is_wireless + required_weight) * config.MAJOR_FACTOR
    elif usage == Usage.OCCASIONALLY:
        return (is_wireless + required_weight) * config.MODERATE_FACTOR
    elif usage == Usage.RARELY:
        return (is_wireless + required_weight) * config.NORMAL_FACTOR
    elif usage == Usage.NEVER:
        return (is_wireless + required_weight) * config.MINOR_FACTOR
    return 0.0

def _travel_portability_explanation(facts: dict, mouse) -> str:
    usage = facts.get("travel_portability")
    weight = mouse.weight
    conn = mouse.connectivity
    bluetooth = conn.bluetooth if conn else False
    dongle = conn.dongle if conn else False
    is_wireless = bluetooth or dongle

    frequency = {
        Usage.MOST_OF_THE_TIME: "most of the time",
        Usage.OFTEN: "often",
        Usage.OCCASIONALLY: "occasionally",
        Usage.RARELY: "rarely",
        Usage.NEVER: "never",
    }.get(usage, "sometimes")

    issues, positives = [], []
    if not is_wireless:
        issues.append("wired connection limits portability")
    else:
        conn_type = "Bluetooth" if bluetooth else "wireless dongle"
        positives.append(f"wireless ({conn_type})")
    if weight > config.REQUIRED_WEIGHT_PORT:
        issues.append(f"heavier than the {config.REQUIRED_WEIGHT_PORT}g portability threshold at {weight}g")
    else:
        positives.append(f"light at {weight}g")

    base = f"You travel with your mouse {frequency}"
    if issues:
        return f"{base} — portability concerns: {'; '.join(issues)}"
    return f"{base} — {' and '.join(positives)} makes it easy to carry"


def _extra_buttons_weight_student(facts: dict, mouse) -> float:
    user = facts.get("extra_buttons")
    extra_buttons = mouse.number_of_buttons >= config.NUMBER_OF_BUTTONS
    if user == Preferability.YES:
        return extra_buttons * config.MODERATE_FACTOR
    elif user == Preferability.PREFERABLY:
        return extra_buttons * config.NORMAL_FACTOR
    return 0.0

def _extra_buttons_explanation_student(facts: dict, mouse) -> str:
    user = facts.get("extra_buttons")
    buttons = mouse.number_of_buttons
    has_extra = buttons >= config.NUMBER_OF_BUTTONS

    if user == Preferability.YES:
        if has_extra:
            return f"This mouse has {buttons} buttons, giving you the extra keys needed for shortcuts and macros"
        return f"You need extra buttons, but this mouse only has {buttons} (minimum {config.NUMBER_OF_BUTTONS} required)"
    if user == Preferability.PREFERABLY:
        if has_extra:
            return f"This mouse has {buttons} buttons — a nice bonus for productivity"
        return f"You'd prefer extra buttons; this mouse only has {buttons}"
    return "Extra buttons are not a requirement for you"


# ── Student rules dict ────────────────────────────────────────────────────────

STUDENT_RULES: dict[str, Rule] = {

    config.TRAVEL_PORTABILITY: Rule(
        id=config.TRAVEL_PORTABILITY,
        rule_type=RuleType.SOFT,
        description="Mouse is portable for students who travel with a laptop",
        applicable_to_users=lambda facts: facts.get("travel_portability") is not None,
        mouse_compatibility=True,
        weight=_travel_portability_weight,
        explanation=_travel_portability_explanation,
    ),

    config.EXTRA_BUTTONS_REQUIRED: Rule(
        id=config.EXTRA_BUTTONS_REQUIRED,
        rule_type=RuleType.SOFT,
        description="Mouse has extra buttons for shortcuts",
        applicable_to_users=lambda facts: facts.get("extra_buttons") is not None,
        mouse_compatibility=True,
        weight=_extra_buttons_weight_student,
        explanation=_extra_buttons_explanation_student,
    ),
}


# ── Office rule helpers ───────────────────────────────────────────────────────

def _work_long_hours(facts: dict, mouse) -> float:
    hours_worked = facts.get("hours_worked")
    ergonomy = mouse.ergonomy
    ergonomic = ergonomy == Ergonomy.ERGONOMIC

    if hours_worked == Usage.MOST_OF_THE_TIME:   # 10+ hours
        return ergonomic * config.ERGONOMY_FACTOR
    elif hours_worked == Usage.OFTEN:             # 7–10 hours
        return ergonomic * config.DOMINANT_FACTOR
    elif hours_worked == Usage.OCCASIONALLY:      # 4–7 hours
        return ergonomic * config.MAJOR_FACTOR
    elif hours_worked == Usage.RARELY:            # 2–4 hours
        return ergonomic * config.MODERATE_FACTOR
    else:                                         # 0–2 hours
        return ergonomic * config.MINOR_FACTOR

def _work_long_hours_explanation(facts: dict, mouse) -> str:
    hours_worked = facts.get("hours_worked")
    ergonomy = mouse.ergonomy
    is_ergonomic = ergonomy == Ergonomy.ERGONOMIC

    hours_label = {
        Usage.MOST_OF_THE_TIME: "10 or more hours",
        Usage.OFTEN:            "7–10 hours",
        Usage.OCCASIONALLY:     "4–7 hours",
        Usage.RARELY:           "2–4 hours",
        Usage.NEVER:            "under 2 hours",
    }.get(hours_worked, "extended periods")

    if is_ergonomic:
        return (
            f"You work {hours_label} a day — this ergonomic mouse is shaped to reduce wrist strain "
            "during long sessions"
        )
    return (
        f"You work {hours_label} a day — this mouse is not ergonomic, which may cause discomfort "
        "or repetitive strain over time"
    )


def _extra_buttons_weight_office(facts: dict, mouse) -> float:
    user = facts.get("extra_buttons")
    extra_buttons = mouse.number_of_buttons >= config.NUMBER_OF_BUTTONS
    if user == Preferability.YES:
        return extra_buttons * config.MODERATE_FACTOR
    elif user == Preferability.PREFERABLY:
        return extra_buttons * config.NORMAL_FACTOR
    return 0.0

def _extra_buttons_explanation_office(facts: dict, mouse) -> str:
    user = facts.get("extra_buttons")
    buttons = mouse.number_of_buttons
    has_extra = buttons >= config.NUMBER_OF_BUTTONS

    if user == Preferability.YES:
        if has_extra:
            return f"This mouse has {buttons} buttons, ideal for assigning office shortcuts and macros"
        return f"You need extra buttons for shortcuts, but this mouse only has {buttons} (minimum {config.NUMBER_OF_BUTTONS} required)"
    if user == Preferability.PREFERABLY:
        if has_extra:
            return f"This mouse has {buttons} buttons — useful for productivity shortcuts"
        return f"You'd prefer extra buttons for macros; this mouse only has {buttons}"
    return "Extra shortcut buttons are not a requirement for you"


# ── Office rules dict ─────────────────────────────────────────────────────────

OFFICE_RULES: dict[str, Rule] = {

    config.LONG_HOURS: Rule(
        id=config.LONG_HOURS,
        rule_type=RuleType.SOFT,
        description="Ergonomic mouse for users who work long hours",
        applicable_to_users=lambda facts: facts.get("hours_worked") is not None,
        mouse_compatibility=True,
        weight=_work_long_hours,
        explanation=_work_long_hours_explanation,
    ),

    config.SHORTCUT_BUTTONS_REQUIRED: Rule(
        id=config.SHORTCUT_BUTTONS_REQUIRED,
        rule_type=RuleType.SOFT,
        description="Mouse has enough buttons for office shortcuts",
        applicable_to_users=lambda facts: facts.get("extra_buttons") is not None,
        mouse_compatibility=True,
        weight=_extra_buttons_weight_office,
        explanation=_extra_buttons_explanation_office,
    ),
}