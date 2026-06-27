from pathlib import Path
import random

import pandas as pd


PLATES = ["SRC", "WORK", "OUT"]
ROWS = "ABCDEFGH"
COLS = range(1, 13)
WELLS = [f"{p}:{r}{c:02d}" for p in PLATES for r in ROWS for c in COLS]
START_WELLS = [f"SRC:{r}{c:02d}" for r in "ABCD" for c in range(1, 7)]
ACTIVE_WELLS = [f"WORK:{r}{c:02d}" for r in ROWS for c in range(1, 13)] + [
    f"OUT:{r}{c:02d}" for r in "ABCD" for c in range(1, 13)
]


def empty_well():
    return {"vol": 0.0, "a": 0.0, "b": 0.0, "buffer": 0.0, "carry": 0.0}


def add_payload(well, vol, a, b, buffer, carry):
    if vol <= 0:
        return
    old = well["vol"]
    new = old + vol
    well["a"] = (well["a"] * old + a * vol) / new
    well["b"] = (well["b"] * old + b * vol) / new
    well["buffer"] = (well["buffer"] * old + buffer * vol) / new
    well["vol"] = new
    well["carry"] = max(well["carry"], carry)


def remove_payload(well, vol):
    taken = min(max(float(vol), 0.0), well["vol"])
    payload = {
        "vol": taken,
        "a": well["a"],
        "b": well["b"],
        "buffer": well["buffer"],
        "carry": well["carry"],
    }
    well["vol"] -= taken
    if well["vol"] <= 1e-9:
        well.update(empty_well())
    return payload


def reagent_profile(name):
    if name == "ANTIGEN_A":
        return 1.0, 0.0, 0.0, 0.0
    if name == "ANTIGEN_B":
        return 0.0, 1.0, 0.0, 0.0
    if name == "BUFFER":
        return 0.0, 0.0, 1.0, 0.0
    if name == "RINSE":
        return 0.0, 0.0, 1.0, 0.03
    raise ValueError(name)


def execute(state, op):
    parts = op.split()
    cmd = parts[0]
    if cmd == "SEED":
        _, reagent, dst, vol = parts
        add_payload(state[dst], float(vol), *reagent_profile(reagent))
    elif cmd == "PIPET":
        _, src, dst, vol, loss = parts
        payload = remove_payload(state[src], float(vol))
        delivered = payload["vol"] * (1.0 - float(loss))
        add_payload(state[dst], delivered, payload["a"], payload["b"], payload["buffer"], payload["carry"])
    elif cmd == "FANOUT":
        _, src, dst1, dst2, dst3, vol, r1, r2, loss = parts
        payload = remove_payload(state[src], float(vol))
        delivered = payload["vol"] * (1.0 - float(loss))
        ratios = [float(r1), float(r2), max(0.0, 1.0 - float(r1) - float(r2))]
        for dst, ratio in zip([dst1, dst2, dst3], ratios):
            add_payload(state[dst], delivered * ratio, payload["a"], payload["b"], payload["buffer"], payload["carry"])
    elif cmd == "DILUTE":
        _, dst, reagent, vol = parts
        add_payload(state[dst], float(vol), *reagent_profile(reagent))
    elif cmd == "EVAP":
        _, dst, frac = parts
        state[dst]["vol"] *= max(0.0, 1.0 - float(frac))
    elif cmd == "DECAY":
        _, dst, a_frac, b_frac = parts
        state[dst]["a"] *= max(0.0, 1.0 - float(a_frac))
        state[dst]["b"] *= max(0.0, 1.0 - float(b_frac))
    elif cmd == "RINSE":
        _, dst, vol, retain = parts
        payload = remove_payload(state[dst], state[dst]["vol"])
        add_payload(state[dst], payload["vol"] * float(retain), payload["a"], payload["b"], payload["buffer"], payload["carry"])
        add_payload(state[dst], float(vol), *reagent_profile("RINSE"))
    elif cmd == "CARRY":
        _, src, dst, ppm = parts
        src_w = state[src]
        add_payload(
            state[dst],
            src_w["vol"] * float(ppm) / 1_000_000.0,
            src_w["a"],
            src_w["b"],
            src_w["buffer"],
            max(src_w["carry"], 0.10),
        )
    elif cmd == "CAP":
        _, dst, max_vol = parts
        state[dst]["vol"] = min(state[dst]["vol"], float(max_vol))


def build_case(rng, idx):
    state = {well: empty_well() for well in WELLS}
    active = rng.sample(ACTIVE_WELLS, rng.randint(7, 13))
    sources = rng.sample(START_WELLS, 4)
    ops = []

    for src, reagent in zip(sources, ["ANTIGEN_A", "ANTIGEN_B", "BUFFER", rng.choice(["ANTIGEN_A", "ANTIGEN_B"])]):
        vol = rng.choice([60, 80, 100, 120])
        op = f"SEED {reagent} {src} {vol}"
        ops.append(op)
        execute(state, op)

    for src in sources[:3]:
        dst = rng.choice(active)
        vol = rng.choice([12, 18, 24, 30, 36])
        loss = rng.choice([0.00, 0.02, 0.04, 0.07])
        op = f"PIPET {src} {dst} {vol} {loss:.2f}"
        ops.append(op)
        execute(state, op)

    step_count = rng.randint(12, 28)
    for _ in range(step_count):
        occupied = [w for w, s in state.items() if s["vol"] > 0.5]
        cmd = rng.choices(
            ["PIPET", "FANOUT", "DILUTE", "EVAP", "DECAY", "RINSE", "CARRY", "CAP"],
            weights=[6, 3, 3, 2, 2, 2, 2, 1],
        )[0]
        if cmd == "PIPET" and occupied:
            src = rng.choice(occupied)
            dst = rng.choice(active)
            op = f"PIPET {src} {dst} {rng.choice([4, 6, 8, 12, 16, 20])} {rng.choice([0.00, 0.02, 0.05, 0.08]):.2f}"
        elif cmd == "FANOUT" and occupied:
            src = rng.choice(occupied)
            dst1, dst2, dst3 = rng.sample(active, 3)
            r1 = rng.choice([0.20, 0.30, 0.40, 0.50])
            r2 = rng.choice([0.20, 0.30, 0.40])
            if r1 + r2 >= 0.90:
                r2 = 0.30
            op = f"FANOUT {src} {dst1} {dst2} {dst3} {rng.choice([9, 12, 18, 24])} {r1:.2f} {r2:.2f} {rng.choice([0.00, 0.03, 0.06]):.2f}"
        elif cmd == "DILUTE":
            dst = rng.choice(active)
            op = f"DILUTE {dst} {rng.choice(['BUFFER', 'RINSE', 'ANTIGEN_A', 'ANTIGEN_B'])} {rng.choice([5, 8, 10, 15, 20])}"
        elif cmd == "EVAP" and occupied:
            op = f"EVAP {rng.choice(occupied)} {rng.choice([0.02, 0.05, 0.08, 0.12, 0.18]):.2f}"
        elif cmd == "DECAY" and occupied:
            op = f"DECAY {rng.choice(occupied)} {rng.choice([0.00, 0.05, 0.10, 0.15]):.2f} {rng.choice([0.00, 0.04, 0.09, 0.14]):.2f}"
        elif cmd == "RINSE" and occupied:
            op = f"RINSE {rng.choice(occupied)} {rng.choice([8, 12, 16, 20])} {rng.choice([0.01, 0.03, 0.06, 0.10]):.2f}"
        elif cmd == "CARRY" and occupied:
            op = f"CARRY {rng.choice(occupied)} {rng.choice(active)} {rng.choice([250, 750, 1500, 3000, 6000])}"
        else:
            op = f"CAP {rng.choice(active)} {rng.choice([25, 40, 55, 70, 90])}"
        ops.append(op)
        execute(state, op)

    target = rng.choice(active)
    final = state[target]
    denom = max(final["a"] + final["b"] + final["buffer"], 1e-9)
    return {
        "case_id": f"adl_{idx:06d}",
        "target_well": target,
        "protocol_text": " ; ".join(ops),
        "operation_count": len(ops),
        "deck_format": rng.choice(["two_plate_bridge", "source_to_assay", "three_zone_validation"]),
        "head_mode": rng.choice(["single_tip", "span8", "eight_channel"]),
        "stress_regime": rng.choice(["low_loss", "carryover_prone", "evaporation_prone", "mixed_stress"]),
        "volume_ul": round(final["vol"], 5),
        "antigen_a_pct": round(100.0 * final["a"] / denom, 5),
        "antigen_b_pct": round(100.0 * final["b"] / denom, 5),
        "buffer_pct": round(100.0 * final["buffer"] / denom, 5),
        "carryover_risk": round(final["carry"], 5),
    }


def main():
    rng = random.Random(971331)
    rows = [build_case(rng, i) for i in range(3200)]
    out = Path("raw") / "data.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
