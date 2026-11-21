import {
    americanToDecimal,
    americanToProb,
    noVigProbs,
    expectedValue,
    marketSummary,
} from "../src/utils/oddsMath.js";

describe("odds conversion", () => {
    test("American odds to decimal", () => {
        expect(americanToDecimal(130)).toBeCloseTo(2.3, 4);
        expect(americanToDecimal(-150)).toBeCloseTo(1.6667, 4);
    });

    test("American odds to implied probability", () => {
        expect(americanToProb(-150)).toBeCloseTo(0.6, 4);
        expect(americanToProb(130)).toBeCloseTo(0.4348, 4);
        expect(americanToProb(100)).toBeCloseTo(0.5, 4);
    });

    test("invalid odds are rejected", () => {
        expect(() => americanToProb(50)).toThrow();
        expect(() => americanToProb(0)).toThrow();
        expect(() => americanToProb(NaN)).toThrow();
    });
});

describe("no-vig probabilities", () => {
    test("remove the bookmaker's margin so both sides add to 1", () => {
        const fair = noVigProbs(-150, 130);
        expect(fair.home).toBeCloseTo(0.5798, 4);
        expect(fair.away).toBeCloseTo(0.4202, 4);
        expect(fair.home + fair.away).toBeCloseTo(1, 10);
    });
});

describe("expected value", () => {
    test("positive when the model likes a side more than the price", () => {
        expect(expectedValue(0.62, -150)).toBeCloseTo(0.0333, 4);
    });

    test("negative when the model likes a side less than the price", () => {
        expect(expectedValue(0.38, 130)).toBeCloseTo(-0.126, 4);
    });
});

describe("marketSummary", () => {
    test("gives implied, no-vig, model, edge and EV for both sides", () => {
        const m = marketSummary(-150, 130, 0.62);
        expect(m.home).toEqual({ implied_prob: 0.6, no_vig_prob: 0.5798, model_prob: 0.62, edge: 0.0402, ev: 0.0333 });
        expect(m.away).toEqual({ implied_prob: 0.4348, no_vig_prob: 0.4202, model_prob: 0.38, edge: -0.0402, ev: -0.126 });
    });

    test("is null when odds are missing", () => {
        expect(marketSummary(null, 130, 0.62)).toBeNull();
    });

    test("without a model it still gives implied and no-vig, with model fields null", () => {
        const m = marketSummary(-150, 130, null);
        expect(m.home).toEqual({ implied_prob: 0.6, no_vig_prob: 0.5798, model_prob: null, edge: null, ev: null });
        expect(m.away.model_prob).toBeNull();
    });
});