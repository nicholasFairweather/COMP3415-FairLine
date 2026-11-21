// Same formulas as Owen's ml/src/betting/odds_math.py, so the site and the model agree.

function checkOdds(odds) {
    if (!Number.isFinite(odds) || (odds > -100 && odds < 100)) {
        throw new Error(`Invalid odds value: ${odds}`);
    }
}

export function americanToDecimal(odds) {
    checkOdds(odds);
    return odds > 0 ? odds / 100 + 1 : 100 / Math.abs(odds) + 1;
}

export function americanToProb(odds) {
    checkOdds(odds);
    return odds > 0 ? 100 / (odds + 100) : Math.abs(odds) / (Math.abs(odds) + 100);
}

export function noVigProbs(homeOdds, awayOdds) {
    const home = americanToProb(homeOdds);
    const away = americanToProb(awayOdds);
    const total = home + away;
    return { home: home / total, away: away / total };
}

export function expectedValue(modelProb, odds) {
    const profit = americanToDecimal(odds) - 1;
    return modelProb * profit - (1 - modelProb);
}

const round4 = (x) => Math.round(x * 10000) / 10000;

// everything the game page shows for both sides.
export function marketSummary(homeOdds, awayOdds, homeModelProb) {
    if (homeOdds == null || awayOdds == null) return null;

    const fair = noVigProbs(homeOdds, awayOdds);
    const hasModel = homeModelProb != null;
    const side = (odds, fairProb, modelProb) => ({
        implied_prob: round4(americanToProb(odds)),
        no_vig_prob: round4(fairProb),
        model_prob: hasModel ? round4(modelProb) : null,
        edge: hasModel ? round4(modelProb - fairProb) : null,
        ev: hasModel ? round4(expectedValue(modelProb, odds)) : null,
    });

    return {
        home: side(homeOdds, fair.home, homeModelProb),
        away: side(awayOdds, fair.away, hasModel ? 1 - homeModelProb : null),
    };
}